#!/usr/bin/env python3
"""
block_analysis_hills.py

Standalone block analysis for metadynamics along a 1D CV (e.g. D.z) using a PLUMED HILLS file.

It reconstructs a sequence of cumulative bias potentials exactly like many "FES vs time" scripts:
  F_bias(x) = sum_i h_i * exp(-(x - D0_i)^2/(2*sigma_i^2))
  FES(x)    = -F_bias(x)  (up to a constant)
and then (optionally) normalizes by subtracting the minimum inside a ROI.

From the time-ordered snapshots, it computes:
  F_A(t) = min(FES(x) in region A)
  F_B(t) = min(FES(x) in region B)
  ΔF(t)  = F_B(t) - F_A(t)

Finally, it performs block averaging on ΔF(t) for multiple block sizes and outputs:
  - deltaF_timeseries.csv
  - block_analysis.csv
  - block_analysis.png

Usage example:
  python block_analysis_hills.py HILLS out \
      --cv D.z \
      --A 0.0 0.6 \
      --B 1.2 2.0 \
      --roi 0 7 \
      --start-last-ns 100 \
      --n-grid 400

If your HILLS has no 'time' field, you can use:
  --start-last-hills 20000
"""
import argparse
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Region:
    lo: float
    hi: float


def read_fields(hills_file: str) -> List[str]:
    fields = None
    with open(hills_file, "r") as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                fields = line.split()[2:]
                break
    if fields is None:
        raise RuntimeError("No se encontró la línea '#! FIELDS' en el HILLS.")
    return fields


def load_hills_as_array(hills_file: str) -> np.ndarray:
    # PLUMED HILLS: comment lines start with '#'
    return np.loadtxt(hills_file, comments="#")


def build_grid(D0: np.ndarray, sigma: np.ndarray, n_grid: int = 400) -> np.ndarray:
    Dmin = float(D0.min() - 2.0 * sigma.max())
    Dmax = float(D0.max() + 2.0 * sigma.max())
    return np.linspace(Dmin, Dmax, n_grid)


def cumulative_snapshots_bias(grid: np.ndarray, D0: np.ndarray, sigma: np.ndarray, h: np.ndarray,
                              start_idx: int = 0) -> List[np.ndarray]:
    """
    Returns list of cumulative bias potentials F_bias (NOT negated), starting from start_idx.
    Each snapshot is a copy of the cumulative F_bias at that hill index.
    """
    F = np.zeros_like(grid)
    snaps: List[np.ndarray] = []
    for i, (Di, si, hi) in enumerate(zip(D0, sigma, h)):
        F += hi * np.exp(-(grid - Di) ** 2 / (2.0 * si * si))
        if i >= start_idx:
            snaps.append(F.copy())
    return snaps


def fes_from_bias_snapshot(F_bias_snapshot: np.ndarray,
                           grid: np.ndarray,
                           roi: Optional[Region] = None) -> np.ndarray:
    """
    Convert cumulative bias snapshot to a "FES-like" profile:
      FES = -F_bias
    and normalize by subtracting the minimum (either global or within ROI).
    """
    fes = -F_bias_snapshot.copy()
    if roi is None:
        fes -= fes.min()
        return fes
    mask = (grid >= roi.lo) & (grid <= roi.hi)
    if not np.any(mask):
        # fallback to global
        fes -= fes.min()
        return fes
    fes -= fes[mask].min()
    return fes


def min_in_region(grid: np.ndarray, fes: np.ndarray, region: Region, min_points: int = 10) -> float:
    mask = (grid >= region.lo) & (grid <= region.hi)
    n = int(mask.sum())
    if n < min_points:
        raise ValueError(
            f"No hay suficientes puntos en la región [{region.lo}, {region.hi}]. "
            f"(hay {n}, se necesitan >= {min_points}). "
            f"Sugerencia: aumenta --n-grid o ensancha el rango."
        )
    return float(np.min(fes[mask]))


def deltaF_timeseries(grid: np.ndarray,
                      bias_snapshots: List[np.ndarray],
                      regionA: Region,
                      regionB: Region,
                      roi: Optional[Region] = None,
                      min_points: int = 10) -> np.ndarray:
    deltas = []
    for snap in bias_snapshots:
        fes = fes_from_bias_snapshot(snap, grid, roi=roi)
        FA = min_in_region(grid, fes, regionA, min_points=min_points)
        FB = min_in_region(grid, fes, regionB, min_points=min_points)
        deltas.append(FB - FA)
    return np.asarray(deltas, dtype=float)


def block_stats(series: np.ndarray, block_size: int) -> Tuple[int, float, float]:
    """
    series: ΔF(t) values
    Returns: (n_blocks, mean, sem) using block means.
    """
    n = len(series)
    n_blocks = n // block_size
    if n_blocks < 2:
        return 0, np.nan, np.nan
    trimmed = series[: n_blocks * block_size]
    blocks = trimmed.reshape(n_blocks, block_size)
    block_means = blocks.mean(axis=1)
    mean = float(block_means.mean())
    sem = float(block_means.std(ddof=1) / np.sqrt(n_blocks))
    return int(n_blocks), mean, sem


def choose_start_index(fields: List[str],
                       data: np.ndarray,
                       start_last_ns: Optional[float],
                       start_last_hills: Optional[int]) -> int:
    """
    Replicates a common choice:
      - if time exists and start_last_ns is provided: keep only last start_last_ns (ns)
      - else if start_last_hills is provided: keep only last N hills
      - else: keep all
    """
    total = data.shape[0]

    if start_last_ns is not None:
        if "time" not in fields:
            raise ValueError("Pediste --start-last-ns pero el HILLS no tiene columna 'time'. "
                             "Usa --start-last-hills en su lugar.")
        idx_time = fields.index("time")
        time_ps = data[:, idx_time]
        time_ns = time_ps / 1000.0
        time_total_ns = float(time_ns[-1])
        t0 = time_total_ns - float(start_last_ns)
        start_idx = int(np.searchsorted(time_ns, t0))
        return max(0, min(start_idx, total - 1))

    if start_last_hills is not None:
        n_last = int(start_last_hills)
        n_last = min(n_last, total)
        return max(0, total - n_last)

    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hills", help="Ruta al archivo HILLS")
    ap.add_argument("out_dir", help="Carpeta de salida")
    ap.add_argument("--cv", default="D.z", help="Nombre del campo CV en HILLS (default: D.z)")
    ap.add_argument("--A", nargs=2, type=float, required=True, metavar=("A_LO", "A_HI"),
                    help="Rango (en CV) para el estado A: A_LO A_HI")
    ap.add_argument("--B", nargs=2, type=float, required=True, metavar=("B_LO", "B_HI"),
                    help="Rango (en CV) para el estado B: B_LO B_HI")
    ap.add_argument("--roi", nargs=2, type=float, default=None, metavar=("ROI_LO", "ROI_HI"),
                    help="Si se da, normaliza restando el mínimo de la FES dentro de este ROI (como en muchos PMF scripts).")
    ap.add_argument("--min-points", type=int, default=10,
                    help="Mínimo de puntos de grilla dentro de cada región (default: 10)")
    ap.add_argument("--n-grid", type=int, default=400, help="Número de puntos de grilla (default: 400)")
    ap.add_argument("--start-last-ns", type=float, default=None,
                    help="Usar solo los últimos X ns (requiere columna 'time' en ps)")
    ap.add_argument("--start-last-hills", type=int, default=None,
                    help="Usar solo los últimos N hills (fallback si no hay 'time')")
    ap.add_argument("--max-blocks", type=int, default=50,
                    help="Número máximo de tamaños de bloque a probar (default: 50)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    fields = read_fields(args.hills)
    data = load_hills_as_array(args.hills)

    if args.cv not in fields:
        raise SystemExit(f"No encuentro el campo CV '{args.cv}' en HILLS. Campos disponibles: {fields}")

    idx_cv = fields.index(args.cv)
    D0 = data[:, idx_cv]

    # sigma/h: intentamos nombres típicos de PLUMED (sigma, height)
    # Si tu HILLS usa otros nombres, cambia aquí o pásalos por el campo en el propio HILLS.
    if "sigma" in fields:
        idx_sigma = fields.index("sigma")
    elif "sigma_" + args.cv in fields:
        idx_sigma = fields.index("sigma_" + args.cv)
    else:
        # muy típico: "sigma" a secas; si no existe, no podemos reconstruir
        raise SystemExit("No encuentro 'sigma' (ni 'sigma_<cv>') en HILLS. No puedo reconstruir la FES.")

    if "height" in fields:
        idx_h = fields.index("height")
    elif "bias" in fields:
        idx_h = fields.index("bias")
    else:
        raise SystemExit("No encuentro 'height' (ni 'bias') en HILLS. No puedo reconstruir la FES.")

    sigma = data[:, idx_sigma]
    h = data[:, idx_h]

    grid = build_grid(D0, sigma, n_grid=args.n_grid)

    start_idx = choose_start_index(fields, data, args.start_last_ns, args.start_last_hills)

    snaps = cumulative_snapshots_bias(grid, D0, sigma, h, start_idx=start_idx)

    regionA = Region(*args.A)
    regionB = Region(*args.B)
    roi = Region(*args.roi) if args.roi is not None else None

    dF = deltaF_timeseries(grid, snaps, regionA, regionB, roi=roi, min_points=args.min_points)

    # Save timeseries
    df_ts = pd.DataFrame({
        "snapshot_index": np.arange(len(dF), dtype=int),
        "deltaF": dF
    })
    ts_path = os.path.join(args.out_dir, "deltaF_timeseries.csv")
    df_ts.to_csv(ts_path, index=False)

    # Choose block sizes
    n = len(dF)
    max_block_size = max(1, n // 2)
    candidate = sorted(set(
        [1, 2, 3, 4, 5, 10] +
        list(np.linspace(1, max_block_size, num=min(args.max_blocks, max_block_size)).astype(int))
    ))
    candidate = [bs for bs in candidate if bs >= 1 and (n // bs) >= 2]

    rows = []
    for bs in candidate:
        n_blocks, mean, sem = block_stats(dF, bs)
        rows.append({"block_size": bs, "n_blocks": n_blocks, "deltaF_mean": mean, "deltaF_sem": sem})

    df_blk = pd.DataFrame(rows)
    blk_path = os.path.join(args.out_dir, "block_analysis.csv")
    df_blk.to_csv(blk_path, index=False)

    # Plot SEM vs block size
    plt.figure()
    plt.plot(df_blk["block_size"], df_blk["deltaF_sem"], marker="o")
    plt.xlabel("Block size (snapshots por bloque)")
    plt.ylabel("SEM de ΔF (a partir de medias de bloque)")
    plt.title("Block analysis de ΔF")
    plt.tight_layout()
    fig_path = os.path.join(args.out_dir, "block_analysis.png")
    plt.savefig(fig_path, dpi=200)
    plt.close()

    # Print conservative estimate using the largest tested block size
    if len(df_blk) > 0:
        last = df_blk.iloc[-1]
        print(f"ΔF (bloques): {last['deltaF_mean']:.6f} ± {last['deltaF_sem']:.6f} (SEM) "
              f"con block_size={int(last['block_size'])} y {int(last['n_blocks'])} bloques.")
    print(f"Guardado: {ts_path}")
    print(f"Guardado: {blk_path}")
    print(f"Guardado: {fig_path}")


if __name__ == "__main__":
    main()

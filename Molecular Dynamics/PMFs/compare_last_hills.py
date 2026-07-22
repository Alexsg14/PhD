#!/usr/bin/env python3
# compare_last_hills.py  (Python 3.7 compatible)
#
# Runs block_analysis_hills.py multiple times for different --start-last-hills N values,
# then creates subplots (SEM vs block_size) for each N and a summary CSV.

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def run_one(py_script: str,
            hills: str,
            outdir: Path,
            cv: str,
            A: Tuple[float, float],
            B: Tuple[float, float],
            roi: Optional[Tuple[float, float]],
            last_hills: Optional[int]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, py_script,
        hills, str(outdir),
        "--cv", cv,
        "--A", str(A[0]), str(A[1]),
        "--B", str(B[0]), str(B[1]),
    ]
    if roi is not None:
        cmd += ["--roi", str(roi[0]), str(roi[1])]
    if last_hills is not None:
        cmd += ["--start-last-hills", str(last_hills)]

    log_file = outdir / "run.log"
    with open(str(log_file), "w") as log:
        p = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, universal_newlines=True)

    if p.returncode != 0:
        raise RuntimeError("Run failed for last_hills={}. See {}".format(last_hills, log_file))


def pick_conservative_point(df: pd.DataFrame, min_blocks: int) -> pd.Series:
    """
    Conservative pick:
    - require n_blocks >= min_blocks
    - choose the largest block_size among those
    - fallback: largest block_size overall
    """
    d = df.sort_values("block_size").copy()
    ok = d[d["n_blocks"] >= min_blocks]
    if len(ok) > 0:
        return ok.iloc[-1]
    return d.iloc[-1]


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Compare ΔF block analysis for multiple --start-last-hills values (Python 3.7 compatible)."
    )
    ap.add_argument("--py-script", required=True, help="Path to block_analysis_hills.py")
    ap.add_argument("--hills", required=True, help="Path to HILLS")
    ap.add_argument("--outdir", required=True, help="Base output directory for comparisons")
    ap.add_argument("--cv", default="D.z", help="CV name (default: D.z)")
    ap.add_argument("--A", nargs=2, type=float, required=True, metavar=("A_LO", "A_HI"))
    ap.add_argument("--B", nargs=2, type=float, required=True, metavar=("B_LO", "B_HI"))
    ap.add_argument("--roi", nargs=2, type=float, default=None, metavar=("ROI_LO", "ROI_HI"))
    ap.add_argument("--last-hills", nargs="+", type=int, required=True,
                    help="List of N values for --start-last-hills, e.g. 10000 20000 40000 80000")
    ap.add_argument("--min-blocks", type=int, default=15,
                    help="Minimum number of blocks required for conservative pick (default: 15)")
    ap.add_argument("--figure", default="compare_sem_vs_blocksize.png",
                    help="Output figure filename (saved inside outdir)")
    args = ap.parse_args()

    base_out = Path(args.outdir)
    base_out.mkdir(parents=True, exist_ok=True)

    roi = (args.roi[0], args.roi[1]) if args.roi is not None else None
    A = (args.A[0], args.A[1])
    B = (args.B[0], args.B[1])
    Ns = list(args.last_hills)  # type: List[int]

    # 1) Run analyses
    print("=== Running block analyses ===")
    for N in Ns:
        run_out = base_out / "lastHILLS_{}".format(N)
        print(" - last_hills={} -> {}".format(N, run_out))
        run_one(args.py_script, args.hills, run_out, args.cv, A, B, roi, N)

    # 2) Collect results
    print("\n=== Collecting results ===")
    results = []
    dfs = []  # list of (N, df)

    for N in Ns:
        run_out = base_out / "lastHILLS_{}".format(N)
        ba_path = run_out / "block_analysis.csv"
        if not ba_path.exists():
            raise FileNotFoundError("Missing {}".format(ba_path))

        df = pd.read_csv(str(ba_path))
        dfs.append((N, df))

        pick = pick_conservative_point(df, args.min_blocks)
        results.append({
            "last_hills": N,
            "picked_block_size": int(pick["block_size"]),
            "picked_n_blocks": int(pick["n_blocks"]),
            "deltaF_mean": float(pick["deltaF_mean"]),
            "deltaF_sem": float(pick["deltaF_sem"]),
        })

    res_df = pd.DataFrame(results).sort_values("last_hills")
    res_csv = base_out / "compare_summary.csv"
    res_df.to_csv(str(res_csv), index=False)

    # 3) Subplots: SEM vs block_size for each N
    n = len(Ns)
    ncols = 2 if n > 1 else 1
    nrows = int(np.ceil(float(n) / float(ncols)))

    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(7 * ncols, 4.5 * nrows))
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])
    axes = axes.flatten()

    for ax_i, (N, df) in enumerate(sorted(dfs, key=lambda x: x[0])):
        ax = axes[ax_i]
        d = df.sort_values("block_size")

        ax.plot(d["block_size"].values, d["deltaF_sem"].values, marker="o", linewidth=1)
        ax.set_title("last_hills = {}".format(N))
        ax.set_xlabel("block_size (snapshots por bloque)")
        ax.set_ylabel("SEM(ΔF)")

        pick = pick_conservative_point(d, args.min_blocks)
        ax.scatter([pick["block_size"]], [pick["deltaF_sem"]], s=80, zorder=3)

        txt = "ΔF = {:.3f} ± {:.3f}\n(block={}, n_blocks={})".format(
            float(pick["deltaF_mean"]), float(pick["deltaF_sem"]),
            int(pick["block_size"]), int(pick["n_blocks"])
        )
        ax.text(0.02, 0.98, txt, transform=ax.transAxes, va="top")

    # turn off unused axes
    for j in range(len(dfs), len(axes)):
        axes[j].axis("off")

    fig.suptitle("Comparativa block analysis (SEM vs block_size) para distintos últimos N HILLS", y=1.02)
    fig.tight_layout()

    fig_path = base_out / args.figure
    fig.savefig(str(fig_path), dpi=200)

    print("\n=== Done ===")
    print("Summary CSV: {}".format(res_csv))
    print("Figure:      {}".format(fig_path))
    print("\nResumen rápido (ΔF ± SEM, punto conservador):")
    print(res_df.to_string(index=False))


if __name__ == "__main__":
    main()

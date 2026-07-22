#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib as mpl
import sys
import datetime
mpl.use("Agg")  # backend no interactivo para guardar figuras en servidores/HPC
import matplotlib.pyplot as plt
from tqdm import tqdm
import json, platform

ORIENTATION_BIAS = 1.0
X_LIM = 5
FP_MAIN   = None
FP_TITLE  = None
FP_AXIS   = None
FP_TICKS  = None
FP_LEGEND = None


# === SciPy opcional para Savitzky–Golay ===
try:
    from scipy.signal import savgol_filter
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False

# === Importar MDAnalysis de forma segura (para permitir modo -plot sin MDAnalysis instalado) ===
try:
    import MDAnalysis as mda
    from MDAnalysis.transformations import unwrap, center_in_box
    from MDAnalysis.lib.distances import distance_array  # añadido para z/contacts
    MDA_OK = True
except Exception:
    MDA_OK = False
# =====================================
# 
# Utilidades de formato
# 
# =====================================

# =========================
# Estilo global (DEFAULT vs CUSTOM) + FontProperties
# =========================
import matplotlib as mpl

USE_CUSTOM_FONT = True  # cámbialo a False para volver a default rápido


def setup_plot_style(use_custom: bool = True,
                     font_main_ttf: str = "avenir-next-medium.ttf",
                     font_bold_ttf: str = "avenir-next-demi.ttf"):
    """
    Resetea SIEMPRE a defaults y luego aplica (opcionalmente) un estilo custom.
    Devuelve un dict con FontProperties (o None si default).
    """
    # 🔁 reset total SIEMPRE (para poder "llamar a default" en cualquier momento)
    mpl.rcdefaults()

    # defaults razonables comunes (también para modo custom)
    mpl.rcParams.update({
        "svg.fonttype": "none",
        "axes.titlesize": 14,
        "axes.labelsize": 16,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 16,
    })

    if not use_custom:
        # --- DEFAULT MATPLOTLIB ---
        mpl.rcParams.update({
            "font.family": "DejaVu Sans",
            "font.size": 11,
        })
        return {
            "fp_main": 16,
            "fp_title": 14,
            "fp_legend": 16,
            "fp_axis": 14,
            "fp_ticks": 16,
        }

    # --- CUSTOM FONT: registrar y aplicar ---
    import matplotlib.font_manager as fm
    from matplotlib.font_manager import FontProperties

    fm.fontManager.addfont(font_main_ttf)
    fm.fontManager.addfont(font_bold_ttf)

    # Perfiles (ajusta tamaños aquí a tu gusto)
    fp_main   = FontProperties(fname=font_main_ttf, size=20)
    fp_title  = FontProperties(fname=font_main_ttf, size=26)
    fp_legend = FontProperties(fname=font_main_ttf, size=16)
    fp_axis   = FontProperties(fname=font_main_ttf, size=24)
    fp_ticks  = FontProperties(fname=font_bold_ttf, size=24)

    # Aplicación global (familia base)
    mpl.rcParams.update({
        "font.family": fp_main.get_name(),  # nombre real de la fuente registrada
        "font.size": fp_main.get_size(),

        # 🔢 fuente SOLO para símbolos matemáticos
        "mathtext.fontset": "custom",
        "mathtext.rm": "DejaVu Sans",
        "mathtext.it": "DejaVu Sans:italic",
        "mathtext.bf": "DejaVu Sans:bold",
    })

    return {
        "fp_main": fp_main,
        "fp_title": fp_title,
        "fp_legend": fp_legend,
        "fp_axis": fp_axis,
        "fp_ticks": fp_ticks,
    }


# Context manager opcional: aplica estilo dentro del bloque y al salir vuelve a default
from contextlib import contextmanager

@contextmanager
def plotting_style(use_custom: bool = True,
                   font_main_ttf: str = "avenir-next-medium.ttf",
                   font_bold_ttf: str = "avenir-next-demi.ttf"):
    fps = setup_plot_style(use_custom, font_main_ttf, font_bold_ttf)
    try:
        yield fps
    finally:
        mpl.rcdefaults()


# =========================
# Ejemplo de uso dentro de UNA función de plot
# (copia el patrón a tus plot_* donde quieras afinar)
# =========================
def _example_plot(ax, fps):
    # Título / ejes con FontProperties (afinable por elemento)
    if fps["fp_title"] is not None:
        ax.set_title("Z position evolution", fontproperties=fps["fp_title"])
        ax.set_xlabel("Time (µs)", fontproperties=fps["fp_axis"])
        ax.set_ylabel("Z position (Å)", fontproperties=fps["fp_axis"])
        # ticks: aquí no existe fontproperties directo; usa labelsize o rcParams
        ax.tick_params(axis="both", labelsize=fps["fp_ticks"].get_size())
        ax.legend(prop=fps["fp_legend"])
    else:
        # default: no pasas fontproperties y Matplotlib usa rcParams
        ax.set_title("Z position evolution")
        ax.set_xlabel("Time (µs)")
        ax.set_ylabel("Z position (Å)")
        ax.legend()


# =========================
# Cómo llamarlo en tu main()
# =========================
# Opción A (simple): aplica una vez y ya (afecta a todos los plots)
# FPS = setup_plot_style(USE_CUSTOM_FONT)
#
# y luego en tus plot_* usa FPS para fontproperties cuando quieras
#
# Opción B (por bloque): solo para la generación de plots
# with plotting_style(USE_CUSTOM_FONT) as FPS:
#     ... generar plots usando FPS ...
def apply_tick_font(ax, fp_ticks):
    if fp_ticks is None:
        return
    for label in ax.get_xticklabels():
        label.set_fontproperties(fp_ticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fp_ticks)

# =========================
# Utilidades numéricas
# =========================
def parser_defaults_dict(parser: argparse.ArgumentParser):
    d = {}
    for a in parser._actions:
        # saltar el -h/--help
        if getattr(a, "dest", None) and a.dest != "help":
            d[a.dest] = a.default
    return d


def moving_average(x, w):
    x = np.asarray(x, dtype=float)
    if w <= 1:
        return x
    return np.convolve(x, np.ones(w)/w, mode='valid')

def forward_fill_nan(a):
    a = np.asarray(a, dtype=float)
    mask = np.isnan(a)
    if not np.any(mask):
        return a
    idx = np.where(~mask, np.arange(len(a)), 0)
    np.maximum.accumulate(idx, out=idx)
    return a[idx]

def interp_nan(a):
    a = np.asarray(a, dtype=float)
    x = np.arange(len(a))
    mask = ~np.isnan(a)
    if mask.sum() < 2:
        return forward_fill_nan(a)
    return np.interp(x, x[mask], a[mask])

# =========================
# Carga y PBC
# =========================

def load_universe(topology, trajectory):
    if not MDA_OK:
        raise RuntimeError("MDAnalysis no disponible. Instálalo o usa -plot con CSVs existentes.")
    return mda.Universe(topology, trajectory)

# --- NUEVO: detección automática de membrana admitida ---
ALLOWED_MEM_RESNAMES = {"POPC", "POPE", "POPS", "TBPI", "CARD", "CHOL"}

def _auto_membrane_selection(u):
    present = {r.resname for r in u.residues}
    mems = sorted(ALLOWED_MEM_RESNAMES.intersection(present))
    if not mems:
        return None, None, []
    membrane_sel = " or ".join(f"resname {r}" for r in mems)
    membrane = u.select_atoms(membrane_sel)
    # Cabezas: PO4 para fosfolípidos, ROH para colesterol
    head_terms = []
    for r in mems:
        if r == "CHOL":
            head_terms.append("(resname CHOL and name ROH)")
        else:
            head_terms.append(f"(resname {r} and name PO4)")
    heads_query = " or ".join(head_terms)
    mem_heads = u.select_atoms(heads_query)
    if mem_heads.n_atoms == 0:
        mem_heads = membrane
    return membrane, mem_heads, mems

def apply_pbc_transforms(u, sel_protein="protein and name BB", sel_lipids="resname POPC"):
    """Aplica unwrap + centrado por membrana. Ahora autodetecta membrana si es posible.
    Mantiene firma para no tocar llamadas existentes.
    """
    # Intentar auto detección de membrana
    membrane_auto, _, _ = _auto_membrane_selection(u)
    lipids = membrane_auto if membrane_auto is not None and membrane_auto.n_atoms > 0 else u.select_atoms(sel_lipids)
    peptide = u.select_atoms(sel_protein)
    u.trajectory.add_transformations(
        unwrap(lipids),
        unwrap(peptide),
        center_in_box(lipids, wrap=True)
    )
    return peptide, lipids


def compute_com(u, atom_selection):
    """Compute center of mass for given atom selection (string)."""
    sel = u.select_atoms(atom_selection)
    return sel.center_of_mass()

def estimate_orientation_bias(
    w,
    peptide_sel="name BB",      # selección del péptido (Martini usa 'BB')
    head_sel="name PO4",        # selección de cabezas lipídicas
    margin=0.0,                 # ±3 unidades alrededor del COM medio de PO4
    min_pct=0.25                # umbral del 25%
):
    """
    Recorre la trayectoria y estima si el péptido pasa suficiente tiempo
    por encima (bias=+1.0) o por debajo (bias=-1.0) del plano de referencia.
    El plano de referencia se define por el COM_z medio de PO4.
    """
    # Guardar frame actual
    try:
        current_frame = w.trajectory.frame
    except Exception:
        current_frame = None

    z_ref_vals = []
    pep_z_vals = []

    for ts in w.trajectory:
        z_ref_vals.append(w.select_atoms(head_sel).center_of_mass()[2])
        pep_z_vals.append(w.select_atoms(peptide_sel).center_of_mass()[2])

    # Restaurar frame
    if current_frame is not None:
        w.trajectory[current_frame]

    z_ref = float(np.mean(z_ref_vals))
    pep_z = np.asarray(pep_z_vals, dtype=float)

    above = np.sum(pep_z >= (z_ref + margin))
    below = np.sum(pep_z <= (z_ref - margin))
    total = pep_z.size if pep_z.size > 0 else 1

    pct_above = above / total
    pct_below = below / total

    if pct_above >= min_pct and pct_above > pct_below:
        bias = 1.0
    elif pct_below >= min_pct and pct_below > pct_above:
        bias = -1.0
    else:
        bias = 1.0  # por defecto; cambia a 0.0 si prefieres "sin sesgo"

    return bias, pct_above, pct_below, z_ref

def compute_rolling_angle(u, orientation_bias=1.0):
    """Compute the rolling angle for the CURRENT FRAME in a Martini model (usa 'BB')."""
    hydrophobicity = {
        'ASP': -0.77, 'GLU': -0.64, 'LYS': -0.99, 'ARG': -1.01, 'HIS': 0.13,
        'GLY': 0.0, 'ALA': 0.31, 'VAL': 1.22, 'LEU': 1.70, 'ILE': 1.80,
        'PRO': 0.72, 'PHE': 1.79, 'MET': 1.23, 'TRP': 2.25, 'SER': -0.04,
        'THR': 0.26, 'CYS': 1.54, 'TYR': 0.96, 'ASN': -0.60, 'GLN': -0.22
    }

    bb_sel = u.select_atoms("name BB")
    if len(bb_sel) < 8:
        raise ValueError("Not enough backbone beads (need at least 8).")
    bb_pos = bb_sel.center_of_mass()

    res_atoms_coeffs = []
    for residue in u.residues:
        bb = residue.atoms.select_atoms("name BB")
        if len(bb) > 0:
            resname = residue.resname.upper()
            coeff = hydrophobicity.get(resname, 0.0)
            if resname not in hydrophobicity:
                pass
            res_atoms_coeffs.append((bb[0].id, coeff))

    VECTOR = np.zeros(3)
    for atom_id, coeff in res_atoms_coeffs:
        atom_pos = u.select_atoms(f'bynum {atom_id}').positions[0]
        vec = atom_pos - bb_pos
        VECTOR += coeff * vec

    bb_ids = sorted([atom.id for atom in bb_sel])
    nterm_ids = bb_ids[:4]
    cterm_ids = bb_ids[-4:]

    nterm_pos = compute_com(u, ' or '.join([f'bynum {aid}' for aid in nterm_ids]))
    cterm_pos = compute_com(u, ' or '.join([f'bynum {aid}' for aid in cterm_ids]))

    b = cterm_pos - nterm_pos
    mod_b = np.linalg.norm(b)
    if mod_b == 0:
        raise ValueError("Nterm and Cterm coincide.")
    unit_b = b / mod_b

    k = VECTOR
    mod_k = np.linalg.norm(k)
    if mod_k == 0:
        raise ValueError("VECTOR has zero length.")
    unit_k = k / mod_k

    dot_uk_ub = np.dot(unit_k, unit_b)
    k_trans = unit_k - dot_uk_ub * unit_b
    mod_kt = np.linalg.norm(k_trans)
    if mod_kt == 0:
        return 90.0
    unit_kt = k_trans / mod_kt

    # <<< AQUI APLICAMOS LA BIAS >>>
    z = orientation_bias * np.array([0.0, 0.0, 1.0])  # +1.0 o -1.0 según el pre-cálculo
    #z = np.array([0.0, 0.0, 1.0])

    b_cross_z = np.cross(unit_b, z)
    t = np.cross(b_cross_z, unit_b)
    mod_t = np.linalg.norm(t)
    if mod_t == 0:
        raise ValueError("t vector has zero length.")
    unit_t = t / mod_t

    dot_t_kt = np.clip(np.dot(unit_t, unit_kt), -1.0, 1.0)
    roll_angle = np.arccos(-dot_t_kt)

    t_cross_kt = np.cross(unit_t, unit_kt)
    mu = np.dot(unit_b, t_cross_kt)
    sign_mu = np.sign(mu) if mu != 0 else 1.0

    rolling_rad = sign_mu * roll_angle
    return np.degrees(rolling_rad)

def compute_rolling_timeseries(u, skip=100):
    """Devuelve DataFrame con frame, time_ps, rolling_deg (salta frames cada 'skip')."""
    frames, times, angles = [], [], []
    for ts in tqdm(u.trajectory[::max(1, int(skip))], desc=f"Rolling (skip={skip})"):
        try:
            ang = compute_rolling_angle(u, orientation_bias=ORIENTATION_BIAS)
        except ValueError as e:
            ang = np.nan
        frames.append(ts.frame)
        times.append(ts.time)
        angles.append(ang)
    return pd.DataFrame({"frame": frames, "time_ps": times, "rolling_deg": angles})

def save_rolling_csv(df, out_csv):
    df.to_csv(out_csv, index=False)


def nine_or_less(n):
    """Devuelve una ventana impar <= 9 y <= n (utilidad para savgol)."""
    for w in (9,7,5,3):
        if n >= w:
            return w
    return 3


def _odd_not_bigger_than(n, w):
    # devuelve el impar más grande <= w y <= n
    w = min(int(w), int(n))
    if w % 2 == 0:
        w -= 1
    return max(w, 1)

def smooth_series(y, window, poly=2, nan_policy="interp"):
    """
    Suavizado centrado. Usa Savitzky–Golay si SciPy está disponible; 
    si no, cae a moving average (mode='same' para no introducir lag).
    """
    y = np.asarray(y, dtype=float)

    # Manejo de NaN
    if np.isnan(y).any():
        if nan_policy == "ffill":
            y = forward_fill_nan(y)
        else:  # "interp" (default)
            y = interp_nan(y)

    n = len(y)
    if n == 0 or window <= 1:
        return y

    if SCIPY_OK:
        # Savitzky–Golay requiere ventana impar y > poly
        w = _odd_not_bigger_than(n, window)
        if w <= poly:
            w = min(_odd_not_bigger_than(n, poly + 3), n if n % 2 == 1 else n-1)
        w = max(w, poly + 2 if (poly + 2) % 2 == 1 else poly + 3)
        w = min(w, n if n % 2 == 1 else n-1)
        if w < 3:  # series muy cortas
            return y
        return savgol_filter(y, window_length=w, polyorder=min(poly, w-1))
    else:
        # Fallback: promedio móvil centrado (sin desplazamiento)
        kernel = np.ones(int(max(1, window))) / float(max(1, window))
        return np.convolve(y, kernel, mode='same')

# =========================
# Cálculo de tilt y azimut
# =========================

def compute_tilt_azim(u,
                      sel_protein="protein and name BB",
                      sel_phosphates="resname POPC and name PO4",
                      nan_mode="gap"):
    """
    Calcula tilt (0-180°) y azimut (0-360° respecto a +X) corrigiendo hoja (v_eff).
    
    El angulo (TILT) que forma el peptido siempre es que 0 grados implica que el peptido esta
    paralelo a la normal de referencia
    N->C
        0° → eje del péptido perpendicular a la membrana y apuntando hacia fuera de la hoja.
        * Hoja superior: C mira a +Z (outward).
        * Hoja inferior: C mira a -Z (outward).

        90° → eje del péptido paralelo al plano de la membrana.

        180° → eje del péptido perpendicular apuntando hacia el interior de la bicapa (inward).
        * Hoja superior: C mira a -Z (inward).
        * Hoja inferior: C mira a +Z (inward).

    Devuelve DataFrame con time_ps, tilt_deg, azim_deg.
    """
    peptide = u.select_atoms(sel_protein)

    # --- NUEVO: usar auto detección si es posible para fosfatos de membrana ---
    _, mem_heads_auto, _ = _auto_membrane_selection(u)
    if mem_heads_auto is not None and mem_heads_auto.n_atoms > 0:
        phosph = mem_heads_auto
    else:
        phosph  = u.select_atoms(sel_phosphates)

    Z  = np.array([0.0, 0.0, 1.0])
    EX = np.array([1.0, 0.0, 0.0])

    times_ps, tilt_deg, azim_deg = [], [], []

    for ts in tqdm(u.trajectory, desc="Analizando frames", total=len(u.trajectory)):
        v = peptide.positions[-1] - peptide.positions[0]
        v /= np.linalg.norm(v)

        z_mem  = phosph.positions[:, 2].mean()
        z_pept = peptide.center_of_mass()[2]

        v_eff = v if (z_pept >= z_mem) else -v

        cos_t = np.dot(v_eff, Z)
        sin_t = np.linalg.norm(np.cross(v_eff, Z))
        tilt  = np.degrees(np.arctan2(sin_t, cos_t))

        t1 = EX - np.dot(EX, Z) * Z
        n1 = np.linalg.norm(t1)
        if n1 < 1e-12:
            t1 = np.array([0.0, 1.0, 0.0])
            n1 = 1.0
        t1 /= n1
        t2 = np.cross(Z, t1)

        v_par = v_eff - np.dot(v_eff, Z) * Z
        nv = np.linalg.norm(v_par)

        if nv < 1e-8:
            azim = np.nan
        else:
            v_par /= nv
            x = np.dot(v_par, t1)
            y = np.dot(v_par, t2)
            azim = np.degrees(np.arctan2(y, x))
            if azim < 0:
                azim += 360.0

        times_ps.append(ts.time)
        tilt_deg.append(tilt)
        azim_deg.append(azim)

    df = pd.DataFrame({
        "time_ps": np.asarray(times_ps, dtype=float),
        "tilt_deg": np.asarray(tilt_deg, dtype=float),
        "azim_deg": np.asarray(azim_deg, dtype=float),
    })
    return df

# =========================
# Densidad conjunta P(φ, tilt)
# =========================

# def compute_density(df_angles,
#                     phi_bins=np.linspace(0.0, 360.0, 73),
#                     tilt_bins=np.linspace(0.0, 180.0, 37)):
#     phi  = df_angles["azim_deg"].to_numpy(dtype=float)
#     tilt = df_angles["tilt_deg"].to_numpy(dtype=float)

    
#     mask = np.isfinite(phi) & np.isfinite(tilt)
#     phi = phi[mask]
#     tilt = tilt[mask]

#     phi_ext  = np.concatenate([phi,  phi + 360.0])
#     tilt_ext = np.concatenate([tilt, tilt])

#     H, phi_edges, tilt_edges = np.histogram2d(phi_ext, tilt_ext, bins=[phi_bins, tilt_bins])
#     P = H / H.sum() if H.sum() > 0 else H
#     return P, phi_edges, tilt_edges

def compute_density(df_angles,
                    phi_bins=np.linspace(0.0, 360.0, 73),
                    tilt_bins=np.linspace(0.0, 180.0, 37),
                    time_min_ns=0.0,
                    time_max_ns=5000.0):
    """
    Densidad conjunta P(phi, tilt) como PROBABILIDAD POR BIN.
    - Comparable entre sistemas
    - Suma total = 1
    - Phi tratado como periódico en [0, 360)
    """

    # ns → ps (las times del dataframe están en ps)
    time_min_ps = time_min_ns * 1000.0
    time_max_ps = time_max_ns * 1000.0

    # Filtro temporal
    df_sel = df_angles[
        (df_angles["time_ps"] >= time_min_ps) &
        (df_angles["time_ps"] <= time_max_ps)
    ]

    # Extraer ángulos
    phi  = df_sel["azim_deg"].to_numpy(dtype=float)
    tilt = df_sel["tilt_deg"].to_numpy(dtype=float)

    # Filtrar valores finitos
    mask = np.isfinite(phi) & np.isfinite(tilt)
    phi  = phi[mask]
    tilt = tilt[mask]

    # Periodicidad azimutal correcta
    phi = np.mod(phi, 360.0)

    # Histograma 2D
    H, phi_edges, tilt_edges = np.histogram2d(
        phi, tilt, bins=[phi_bins, tilt_bins]
    )

    # Normalización: probabilidad por bin
    H = H.astype(float)
    total = H.sum()
    P = H / total if total > 0 else H

    return P, phi_edges, tilt_edges


# =========================
# Guardar / Cargar CSV
# =========================

def save_angles_csv(df, out_csv):
    df.to_csv(out_csv, index=False)

def load_angles_csv(csv_path):
    return pd.read_csv(csv_path)

def save_density_csv(P, phi_edges, tilt_edges, out_folder):
    np.savetxt(os.path.join(out_folder, "density_P.csv"), P, delimiter=",")
    np.savetxt(os.path.join(out_folder, "density_phi_edges.csv"), phi_edges, delimiter=",")
    np.savetxt(os.path.join(out_folder, "density_tilt_edges.csv"), tilt_edges, delimiter=",")

def load_density_csv(in_folder):
    P = np.loadtxt(os.path.join(in_folder, "density_P.csv"), delimiter=",")
    phi_edges = np.loadtxt(os.path.join(in_folder, "density_phi_edges.csv"), delimiter=",")
    tilt_edges = np.loadtxt(os.path.join(in_folder, "density_tilt_edges.csv"), delimiter=",")
    return P, phi_edges, tilt_edges


# =========================
# === NUEVO BLOQUE: Z & CONTACTOS (modular) ===
# =========================

def zc_run_analysis(u, out_dir, skip=10, cutoff=6.0, window_size=1):
    """Ejecuta análisis de un único péptido (BB) vs agua/membrana (auto-detectada).
    Guarda CSVs y figuras en out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Selecciones
    membrane, mem_heads, mem_list = _auto_membrane_selection(u)
    if membrane is None or membrane.n_atoms == 0:
        raise RuntimeError("No se detectó membrana válida (POPC/POPE/POPS/TBPI/CARD/CHOL).")

    water   = u.select_atoms("resname W")
    peptide = u.select_atoms("protein and name BB")
    if peptide.n_atoms == 0:
        raise RuntimeError("No se detectaron átomos del péptido (protein and name BB).")
    
    # Identificar primer y último BB del péptido
    pep_res = peptide.residues
    if len(pep_res) < 1:
        raise RuntimeError("No hay residuos BB en el péptido.")
    
    bb_first = pep_res[0].atoms.select_atoms("name BB")
    bb_last  = pep_res[-1].atoms.select_atoms("name BB")
    if bb_first.n_atoms == 0 or bb_last.n_atoms == 0:
        raise RuntimeError("No se encontró BB en el primer o último residuo del péptido.")

    contacts_pw, contacts_pm = [], []
    z_pep, z_center, z_up, z_low = [], [], [], []
    z_bb_first_rel, z_bb_last_rel = [], []
    times = []


    # Iterar frames con stride
    stride = max(1, int(skip))
    total_frames = (len(u.trajectory) + stride - 1) // stride
    for ts in tqdm(u.trajectory[::stride], total=total_frames, desc="Z/Contactos"):
        # Tiempo a µs desde ps almacenados en MDAnalysis
        time_us = ts.time / 1e6
        times.append(time_us)

        # Contactos
        if water.n_atoms > 0:
            d_pw = distance_array(peptide.positions, water.positions, box=u.dimensions)
            contacts_pw.append(int(np.sum(d_pw < cutoff)))
        else:
            contacts_pw.append(0)

        d_pm = distance_array(peptide.positions, mem_heads.positions, box=u.dimensions)
        contacts_pm.append(int(np.sum(d_pm < cutoff)))

        # Z relative (minimum image via wrap handled by transforms; medimos relativos)
        mem_com_z = membrane.center_of_mass()[2]
        pep_com_z = peptide.center_of_mass()[2]
        z_pep.append(abs(pep_com_z - mem_com_z))

        heads_z = mem_heads.positions[:, 2]
        upper = heads_z[heads_z > mem_com_z]
        lower = heads_z[heads_z < mem_com_z]
        z_center.append(0.0)
        z_up.append(float(np.mean(upper) - mem_com_z) if upper.size > 0 else 0.0)
        z_low.append(float(np.mean(lower) - mem_com_z) if lower.size > 0 else 0.0)

        # --- NUEVO: Z relativa (con signo) del primer y último BB --- 
        bb1_z = bb_first.positions[0, 2]
        bbN_z = bb_last.positions[0, 2]
        z_bb_first_rel.append(abs(bb1_z - mem_com_z))
        z_bb_last_rel.append(abs(bbN_z - mem_com_z))


    # Guardar CSVs
    contacts_csv = os.path.join(out_dir, "contactos_totales.csv")
    with open(contacts_csv, "w") as f:
        f.write("Time (µs),peptides_water,peptides_mem_heads\n")
        for i in range(len(times)):
            f.write(f"{times[i]},{contacts_pw[i]},{contacts_pm[i]}\n")

    z_csv = os.path.join(out_dir, "posiciones_z.csv")
    with open(z_csv, "w") as f:
        f.write("Time (µs),PEPTIDE,Membrane_Center,Membrane_Upper_Heads,Membrane_Lower_Heads,BB_First_RelZ,BB_Last_RelZ\n")
        for i in range(len(times)):
            f.write(
                f"{times[i]},{z_pep[i]},{z_center[i]},{z_up[i]},{z_low[i]},{z_bb_first_rel[i]},{z_bb_last_rel[i]}\n"
            )


    # Plots
    zc_plot_from_csv(out_dir, out_dir, window_size)

    return contacts_csv, z_csv


# =========================
# Plots
# =========================

def plot_rolling(df, out_png, time_min_ns=0.0, time_max_ns=5000.0):
    times = df["time_ps"].to_numpy(float) / 1000000
    angles = df["rolling_deg"].to_numpy(float)

        # Filtrar por rango de tiempo (convertido de ns → µs)
    tmin_us = time_min_ns / 1000.0
    tmax_us = time_max_ns / 1000.0
    mask_time = (times >= tmin_us) & (times <= tmax_us)
    times = times[mask_time]
    angles = angles[mask_time]

    ang_for_filt = angles.copy()
    if np.isnan(ang_for_filt).all():
        smoothed = ang_for_filt
    else:
        ang_for_filt[np.isnan(ang_for_filt)] = np.nanmean(ang_for_filt)
        if SCIPY_OK and len(ang_for_filt) >= 5:
            win = min(len(ang_for_filt) if len(ang_for_filt)%2==1 else len(ang_for_filt)-1,  nine_or_less(len(ang_for_filt)))
            smoothed = savgol_filter(ang_for_filt, window_length=win, polyorder=2)
        else:
            w = 5 if len(ang_for_filt) >= 5 else 1
            mv = moving_average(ang_for_filt, w)
            smoothed = np.concatenate([np.full(len(ang_for_filt)-len(mv), mv[0]), mv])

    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 6), dpi=600, facecolor='white')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # ax.fill_between(times, angles, color='#1f77b4', alpha=0.2, label='Rolling Angle Data')
    # ax.plot(times, angles, color='#1f77b4', linewidth=1, alpha=0.8)
    ax.plot(times, smoothed, color='#d62728', linewidth=2.5) #label='Smoothed')

    ax.set_xlabel(r"Time ($\mu$s)", fontsize=12, weight='bold')
    ax.set_ylabel('Rolling Angle (°)', fontsize=12, weight='bold')
    ax.set_title('Rolling Angle vs Time (Martini Protein)', fontsize=14, weight='bold', pad=15)
    ax.set_ylim(-180, 180)
    ax.set_xlim(tmin_us, tmax_us)
    ax.set_yticks(np.arange(-180, 181, 45))
    ax.grid(True, linestyle='--', alpha=0.5, color='gray')
    ax.legend(fontsize=10, frameon=True, facecolor='white', edgecolor='black', framealpha=1.0)
    ax.tick_params(axis='both', which='major', labelsize=10, direction='out', length=5)

    plt.tight_layout()
    plt.savefig(out_png, dpi=600, bbox_inches='tight', facecolor='white', transparent=True)
    plt.close()

def plot_time_series(df, out_folder, smooth_w=50, nan_mode="gap"):
    os.makedirs(out_folder, exist_ok=True)

    times_ps = df["time_ps"].to_numpy(float)
    tilt_deg = df["tilt_deg"].to_numpy(float)
    azim_deg = df["azim_deg"].to_numpy(float)

    t_us = times_ps/1e3/1e3

    if nan_mode == "ffill":
        az_plot = forward_fill_nan(azim_deg)
    elif nan_mode == "interp":
        az_plot = interp_nan(azim_deg)
    else:
        az_plot = azim_deg
    '''
    tilt_s = moving_average(tilt_deg, smooth_w)
    az_s   = moving_average(az_plot, smooth_w)

    t_us_tilt = t_us[-len(tilt_s):]
    t_us_az   = t_us[-len(az_s):]
    '''
    # Aplica el suavizado centrado: USANDO SAV-GOL
    tilt_s = smooth_series(tilt_deg, window=smooth_w, poly=2, nan_policy="interp")
    az_s   = smooth_series(az_plot,  window=smooth_w, poly=2,
                           nan_policy=("ffill" if nan_mode=="ffill" else "interp"))

    # Como ahora el largo no cambia, NO necesitas recortar/ajustar ejes:
    t_us_tilt = t_us
    t_us_az   = t_us

    plt.figure(figsize=(10,6))

    #plt.plot(t_us, tilt_deg, label="Tilt", color="#002D7B")


    plt.scatter(
        t_us,
        tilt_deg,
        s=20,                 # tamaño del círculo
        facecolors="white",   # relleno blanco
        edgecolors="#7aa6d6", # azul clarito
        alpha=0.5,
        linewidths=0.8,
    )

    plt.plot(
        t_us_tilt,
        tilt_s,
        # label=f"Tilt (smoothed {smooth_w})",
        label=f"Tilt (°)",
        color="#002D7B"
    )

    plt.axhline(90, color="red", linestyle="--", linewidth=1, label="90°")

    plt.xlabel(r"Time ($\mu$s)", fontproperties=FP_AXIS)
    plt.ylabel("Tilt (°)", fontproperties=FP_AXIS)
    plt.title("Tilt Angle", fontproperties=FP_TITLE)
    plt.tick_params(axis="both", labelsize=16)

    ax = plt.gca()
    apply_tick_font(ax, FP_TICKS)

    plt.ylim(0, 190)
    plt.xlim(0, 5)

    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "tilt_timeseries.png"), dpi=600, transparent=True)
    plt.close()


    fig, (ax, ax_hist) = plt.subplots(
        1, 2,
        figsize=(12, 6),
        gridspec_kw={"width_ratios": [4, 1], "wspace": 0.05},
        sharey=True
    )

    # --- Panel izquierdo: serie temporal ---
    ax.scatter(
        t_us,
        tilt_deg,
        s=20,
        facecolors="white",
        edgecolors="#7aa6d6",
        alpha=0.5,
        linewidths=0.8,
    )

    ax.plot(
        t_us_tilt,
        tilt_s,
        label=f"Tilt (°)",
        color="#002D7B"
    )

    ax.axhline(90, color='red', linestyle='--', linewidth=1, label="90°")

    ax.set_xlabel(r"Time ($\mu$s)", fontproperties=FP_AXIS)
    ax.set_ylabel("Tilt (°)", fontproperties=FP_AXIS)
    ax.set_title("Tilt Angle", fontproperties=FP_TITLE)
    ax.tick_params(axis='both', labelsize=16)
    ax.set_ylim(0, 190)
    ax.set_xlim(0, 5)
    ax.legend()

    # --- Panel derecho: histograma de densidad ---
    ax_hist.hist(
        tilt_deg[np.isfinite(tilt_deg)],
        bins=100,
        orientation="horizontal",
        density=True,
        alpha=0.6,
        facecolor="#7aa6d6",   # relleno
        edgecolor="#002D7B",   # borde azul más oscuro
        linewidth=0.8
    )

    ax_hist.set_xlabel("", fontsize=0)
    ax_hist.tick_params(axis='x', labelbottom=False)
    ax_hist.tick_params(axis='y', left=False, labelleft=False)
    ax_hist.spines["left"].set_visible(True)
    ax_hist.spines["top"].set_visible(True)
    ax_hist.spines["right"].set_visible(True)

    # --- Aplicar fuente de ticks (tu sistema global) ---
    apply_tick_font(ax, FP_TICKS)
    apply_tick_font(ax_hist, FP_TICKS)

    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "tilt_timeseries_HISTORGRAM.png"),dpi=600, bbox_inches="tight", pad_inches = 0.15, transparent=True)
    plt.close(fig)


    plt.figure(figsize=(10,6))
    plt.plot(t_us, az_plot, label=f"Azimuth (mode {nan_mode})")
    plt.plot(t_us_az, az_s, label=f"Azimuth (smoothed {smooth_w})")
    plt.xlabel(r"Time ($\mu$s)", fontproperties=FP_AXIS)
    plt.ylabel("Azimuth (°)", fontproperties=FP_AXIS)
    plt.title("Azimuth 0-360° respect to +X projected")
    plt.tick_params(axis='both', labelsize=16)
    ax = plt.gca()
    apply_tick_font(ax, FP_TICKS)
    plt.ylim(0, 370)
    plt.xlim(0,5)
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "azimut_timeseries.png"), dpi=600, transparent=True)
    plt.close()

    az_unw = np.degrees(np.unwrap(np.radians(az_plot)))
    plt.figure(figsize=(12,4))
    plt.plot(t_us, az_unw, label="Unwrapped Azimuth")
    plt.xlabel(r"Time ($\mu$s)", fontproperties=FP_AXIS)
    plt.ylabel("Azimuth (°)", fontproperties=FP_AXIS)
    plt.title("Unwrapped Azimuth", fontproperties=FP_TITLE)
    plt.tick_params(axis='both', labelsize=16)
    ax = plt.gca()
    apply_tick_font(ax, FP_TICKS)
    plt.xlim(0,5)
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "azimut_unwrapped.png"), dpi=600, transparent=True)
    plt.close()


def plot_polar_maps(df, out_folder):
    os.makedirs(out_folder, exist_ok=True)

    times_ps = df["time_ps"].to_numpy(float)
    tilt_deg = df["tilt_deg"].to_numpy(float)
    azim_deg = df["azim_deg"].to_numpy(float)

    mask2 = np.isfinite(tilt_deg)
    phi_t = np.radians(tilt_deg[mask2])
    r_t   = np.clip(np.sin(np.radians(tilt_deg[mask2])), 0.0, 1.0)
    t_ns_tilt = times_ps[mask2]/1000000.0

    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='polar')
    pc = ax.scatter(phi_t, np.ones_like(phi_t), c=t_ns_tilt, s=6, cmap='viridis', vmin=0, vmax=5)
    cb = fig.colorbar(pc, ax=ax, pad=0.1); cb.set_label(r"Time ($\mu$s)")
    ax.set_title("Tilt/Time mapped to radius, Time as color")
    ax.set_rticks([])
    ax = plt.gca()
    apply_tick_font(ax, FP_MAIN)
    apply_tick_font(cb.ax, FP_MAIN)
    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "polar_tilt_timecolor.png"), dpi=600, transparent=True)
    plt.close()

    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='polar')
    pc = ax.scatter(phi_t, t_ns_tilt, c=t_ns_tilt, s=6, cmap='viridis', vmin=0, vmax=5)
    ax.set_rlim(0,5.2)
    cb = fig.colorbar(pc, ax=ax, pad=0.1)
    cb.set_label(r"Time ($\mu$s)")
    ax.set_title("Tilt (0–180°) / radius and color respect to time")
    ax.set_rticks([])
    ax.tick_params(axis="x", pad=10.5)
    ax = plt.gca()
    apply_tick_font(ax, FP_MAIN)
    apply_tick_font(cb.ax, FP_MAIN)
    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "polar_tilt_time_radio_color.png"), dpi=600, transparent=True)
    plt.close()

    mask_azim = np.isfinite(azim_deg)
    phi_azim  = np.radians(azim_deg[mask_azim])
    t_ns_azim = times_ps[mask_azim] / 1000000.0

    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='polar')
    pc_azim = ax.scatter(phi_azim, t_ns_azim, c=t_ns_azim, s=6, cmap='viridis', vmin=0, vmax=5)
    ax.set_rlim(0,5)
    cb = fig.colorbar(pc_azim, ax=ax, pad=0.1)
    cb.set_label(r"Time ($\mu$s)")
    ax.set_title("Azimuth (0–360°) time and radius respect to time")
    ax.set_rticks([])
    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "polar_azimut_time_radio_color.png"), dpi=600, transparent=True)
    plt.close()


# def plot_density_only(P, phi_edges, tilt_edges, out_folder, fname="density_heatmap.png"):
#     os.makedirs(out_folder, exist_ok=True)
#     Phi, Tilt = np.meshgrid(phi_edges, tilt_edges, indexing='ij')
#     plt.figure(figsize=(6.5,5))
#     im = plt.pcolormesh(Phi, Tilt, P, shading='auto', cmap="viridis")
#     cb = plt.colorbar(im); cb.set_label("Probabilidad")
#     plt.xlim(0, 360); plt.ylim(0, 180)
#     plt.xlabel("Azimut φ (°)"); plt.ylabel("Tilt (°)")
#     plt.title("Densidad conjunta P(φ, tilt)")
#     plt.tight_layout()
#     plt.savefig(os.path.join(out_folder, fname), dpi=220)
#     plt.close()


# def plot_helix_plus_density(df, P, phi_edges, tilt_edges, out_folder, fname="helix_plus_density.png"):
#     os.makedirs(out_folder, exist_ok=True)

#     times_ps = df["time_ps"].to_numpy(float)
#     tilt_deg = df["tilt_deg"].to_numpy(float)
#     azim_deg = df["azim_deg"].to_numpy(float)

#     mask = np.isfinite(tilt_deg) & np.isfinite(azim_deg)
#     t_ns = times_ps[mask]/1000000.0
#     phi  = np.radians(azim_deg[mask])
#     tilt = tilt_deg[mask]

#     r = np.clip(np.sin(np.radians(tilt)), 0.0, 1.0)
#     x, y, z = r*np.cos(phi), r*np.sin(phi), t_ns

#     fig = plt.figure(figsize=(12,5))
#     ax1 = fig.add_subplot(1,2,1, projection="3d")
#     sc = ax1.scatter(x, y, z, c=t_ns, s=4, cmap='viridis', vmin=0, vmax=5)
#     ax1.set_zlim(0,5)
#     cb1 = fig.colorbar(sc, ax=ax1, pad=0.1); cb1.set_label("Tiempo (µs)")
#     ax1.set_xlabel("X (r·cos φ)"); ax1.set_ylabel("Y (r·sin φ)"); ax1.set_zlabel("Tiempo (ns)")
#     ax1.set_title("Trayectoria 3D: φ(t) con tilt→radio"); ax1.view_init(elev=30, azim=45)

#     ax2 = fig.add_subplot(1,2,2)
#     Phi, Tilt = np.meshgrid(phi_edges, tilt_edges, indexing='ij')
#     im = ax2.pcolormesh(Phi, Tilt, P, shading='auto', cmap='viridis')
#     cb2 = fig.colorbar(im, ax=ax2); cb2.set_label("Probabilidad")
#     ax2.set_xlim(0, 360); ax2.set_ylim(0, 180)
#     ax2.set_xlabel("Azimut φ (°)"); ax2.set_ylabel("Tilt (°)")
#     ax2.set_title("Densidad conjunta P(φ, tilt)")

#     plt.tight_layout()
#     plt.savefig(os.path.join(out_folder, fname), dpi=230)
#     plt.close()


def plot_density_only(P, phi_edges, tilt_edges, out_folder, fname="density_heatmap_AAA.png", time_min_ns=0.0, time_max_ns=5000.0):

    os.makedirs(out_folder, exist_ok=True)

    Phi, Tilt = np.meshgrid(phi_edges, tilt_edges, indexing='ij')
    plt.figure(figsize=(6.5,5))

    im = plt.pcolormesh(Phi, Tilt, P, shading='auto', cmap="viridis",
                    vmin=0.0, vmax=1.55938e-02)
    cb = plt.colorbar(im); cb.set_label("Probability")

    plt.xlim(0, 360); plt.ylim(0, 180)
    plt.xlabel(r"Azimuth ($\varphi$) (°)", fontproperties=FP_AXIS)
    plt.ylabel(r"Tilt (°)", fontproperties=FP_AXIS)

    plt.title(
        rf"Density $P(\varphi,\ \mathrm{{tilt}})$ "
        rf"(t = {time_min_ns}-{time_max_ns/1000} $\mu$s)",
        fontsize=14
    )

    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, fname), dpi=600, transparent=True)
    plt.close()

def plot_helix_3d(df, out_folder, time_min_ns=0.0, time_max_ns=5000.0):

    os.makedirs(out_folder, exist_ok=True)

    # Filtrar por tiempo en ns
    mask_time = (df["time_ps"] >= time_min_ns*1000.0) & (df["time_ps"] <= time_max_ns*1000.0)
    df_sel = df[mask_time]

    times_ps = df_sel["time_ps"].to_numpy(float)
    tilt_deg = df_sel["tilt_deg"].to_numpy(float)
    azim_deg = df_sel["azim_deg"].to_numpy(float)

    mask = np.isfinite(tilt_deg) & np.isfinite(azim_deg)
    t_ns = times_ps[mask]/1000000.0
    phi  = np.radians(azim_deg[mask])
    tilt = tilt_deg[mask]

    r = np.clip(np.sin(np.radians(tilt)), 0.0, 1.0)
    x, y, z = r*np.cos(phi), r*np.sin(phi), t_ns

    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111, projection='3d')
    sc = ax.scatter(x, y, z, c=t_ns, s=4, cmap='viridis', vmin=time_min_ns, vmax=time_max_ns/1000)
    cb = fig.colorbar(sc, ax=ax, pad=0.1)
    cb.set_label(r"Time ($\mu$s)")
    ax.set_xlabel(r"X $r\cdot\cos(\varphi)$", labelpad=16, fontproperties=FP_AXIS)
    ax.set_ylabel(r"Y $r\cdot\sin(\varphi)$", labelpad=16, fontproperties=FP_AXIS)
    ax.set_zlabel(r"Time ($\mu$s)",labelpad=8, fontproperties=FP_AXIS)
    ax.zaxis.set_rotate_label(False)      # 👈 desactiva auto-rotación
    ax.zaxis.label.set_rotation(90)    
    ax.set_zlim(time_min_ns, time_max_ns/1000)
    ax.set_title(
    rf"3D azimuth $\varphi$ (t) wt Tilt as radius (t = {time_min_ns}-{time_max_ns/1000} $\mu$s)")
    ax.view_init(elev=30, azim=45)
    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, "helix3d.png"), dpi=600, transparent=True)
    plt.close()


def plot_helix_plus_density(df, P, phi_edges, tilt_edges, out_folder, fname="helix_plus_density.png",
                            time_min_ns=0.0, time_max_ns=5000.0):
    os.makedirs(out_folder, exist_ok=True)

    # Filtrar por tiempo en ns
    mask_time = (df["time_ps"] >= time_min_ns*1000.0) & (df["time_ps"] <= time_max_ns*1000.0)
    df_sel = df[mask_time]

    times_ps = df_sel["time_ps"].to_numpy(float)
    tilt_deg = df_sel["tilt_deg"].to_numpy(float)
    azim_deg = df_sel["azim_deg"].to_numpy(float)

    mask = np.isfinite(tilt_deg) & np.isfinite(azim_deg)
    t_ns = times_ps[mask] / 1000000.0  # convertir ps→ns
    phi  = np.radians(azim_deg[mask])
    tilt = tilt_deg[mask]

    r = np.clip(np.sin(np.radians(tilt)), 0.0, 1.0)
    x, y, z = r*np.cos(phi), r*np.sin(phi), t_ns

    fig = plt.figure(figsize=(12,5))
    ax1 = fig.add_subplot(1,2,1, projection="3d")
    sc = ax1.scatter(x, y, z, c=t_ns, s=4, cmap='viridis',
                     vmin=time_min_ns, vmax=time_max_ns/1000)
    ax1.set_zlim(time_min_ns, time_max_ns/1000)
    cb1 = fig.colorbar(sc, ax=ax1, pad=0.1)
    cb1.set_label(r"Time ($\mu$s)")

    ax1.set_xlabel(r"X ($r\cdot\cos(\varphi)$)", labelpad=16, fontproperties=FP_AXIS)
    ax1.set_ylabel(r"Y ($r\cdot\sin(\varphi)$)", labelpad=16, fontproperties=FP_AXIS)
    ax1.set_zlabel(r"Time ($\mu$s)", fontproperties=FP_AXIS)
    ax1.zaxis.set_rotate_label(False)      # 👈 desactiva auto-rotación
    ax1.zaxis.label.set_rotation(90)  

    ax1.set_title(
        rf"3D azimuth $\varphi(t)$ wt Tilt as radius "
        rf"(t = {time_min_ns}-{time_max_ns/1000} $\mu$s)"
    )
    ax1.view_init(elev=30, azim=45)

    ax2 = fig.add_subplot(1,2,2)
    Phi, Tilt = np.meshgrid(phi_edges, tilt_edges, indexing='ij')
    im = ax2.pcolormesh(Phi, Tilt, P, shading='auto', cmap='viridis')
    cb2 = fig.colorbar(im, ax=ax2); cb2.set_label("Probability")
    ax2.set_xlim(0, 360); ax2.set_ylim(0, 180)
    ax2.set_xlabel(r"Azimuth ($\varphi$) (°)")
    ax2.set_ylabel(r"Tilt (°)", fontproperties=FP_AXIS)

    ax2.set_title(
        rf"Probability Density $P(\varphi,\ \mathrm{{tilt}})$ "
        rf"(t = {time_min_ns}-{time_max_ns/1000} $\mu$s)"
    )

    plt.tight_layout()
    plt.savefig(os.path.join(out_folder, fname), dpi=600, bbox_inches="tight", pad_inches=0.5, transparent=True)
    plt.close()

def zc_plot_from_csv(csv_dir, out_dir, window_size=10,time_min_us=0.0, time_max_us=5.0):

    os.makedirs(out_dir, exist_ok=True)

    contacts_csv = os.path.join(csv_dir, "contactos_totales.csv")
    z_csv = os.path.join(csv_dir, "posiciones_z.csv")

    if not (os.path.isfile(contacts_csv) and os.path.isfile(z_csv)):
        raise FileNotFoundError("Faltan contactos_totales.csv o posiciones_z.csv en csv_dir")

    contacts_df = pd.read_csv(contacts_csv)
    z_df = pd.read_csv(z_csv)

    time_vals = contacts_df.iloc[:,0].values
    mask_time = (time_vals >= time_min_us) & (time_vals <= time_max_us)

    grouped = {
        "Peptides-Water": "peptides_water",
        "Peptides-Mem Heads": "peptides_mem_heads",
    }

    for label, col in grouped.items():
        plt.figure(figsize=(10, 6))
        data = contacts_df[col].values
        t_sel = time_vals[mask_time]
        d_sel = data[mask_time]

        # smoothed = moving_average(d_sel, window_size)
        
        # plt.plot(t_sel[:len(smoothed)], smoothed, label=label)

        smoothed = smooth_series(d_sel, window=window_size, poly=2, nan_policy="interp") #SAV-GOL SMOOTHED
        plt.plot(t_sel, smoothed, label=label)

        plt.title(f"{label} Contacts along the trajectory", fontproperties=FP_TITLE)
        plt.xlabel("Time ($\\mu$S)", fontproperties=FP_AXIS)
        plt.ylabel("Number of contacts", fontproperties=FP_AXIS)
        plt.ylim(-1, 140); plt.xlim(left=0)
        plt.xlim(time_min_us,time_max_us)
        plt.tick_params(axis='both', labelsize=16)
        ax = plt.gca()
        apply_tick_font(ax, FP_TICKS)
        plt.legend(); plt.grid(True)
        plt.savefig(os.path.join(out_dir, f"{label.replace(' ', '_').lower()}_smoothed_plot.png"), transparent=True)
        plt.close()

    plt.figure(figsize=(10, 6))
    color_map = {
    "Peptides-Water": "#3262D2",      # azul
    "Peptides-Mem Heads": "#2BEC64",  # rojo
    }          

    for label, col in grouped.items():
        data = contacts_df[col].values
        t_sel = time_vals[mask_time]
        d_sel = data[mask_time]
        # smoothed = moving_average(d_sel, window_size)
        # plt.plot(t_sel[:len(smoothed)], smoothed, label=label)
        smoothed = smooth_series(d_sel, window=window_size, poly=2, nan_policy="interp") #SAV-GOL SMOOTHED
        plt.plot(
            t_sel,
            smoothed,
            label=label,
            color=color_map.get(label, None)
        )

    plt.title("Contacts along the trajectory", fontproperties=FP_TITLE)
    plt.xlabel("Time ($\\mu$s)", fontproperties=FP_AXIS)
    plt.ylabel("Number of contacts", fontproperties=FP_AXIS)
    plt.ylim(-1, 140); plt.xlim(time_min_us, time_max_us)
    plt.legend(); plt.grid(True)
    plt.tick_params(axis='both', labelsize=16)
    ax = plt.gca()
    apply_tick_font(ax, FP_TICKS)
    plt.savefig(os.path.join(out_dir, "contactos_grupos_smoothed_plot.png"), dpi=600, bbox_inches="tight", pad_inches = 0.15, transparent=True)
    plt.close()

    # Z plots
    time_vals = z_df.iloc[:, 0].values
    mask_time = (time_vals >= time_min_us) & (time_vals <= time_max_us)

    # Orden recomendado y sin duplicados; solo se grafican las que existan
    col_order = [
        "PEPTIDE",
        "BB_First_RelZ",
        "BB_Last_RelZ",
        "Membrane_Upper_Heads",
        "Membrane_Center",
        
        # "Membrane_Lower_Heads",

    ]

    label_map = {
    "PEPTIDE": "Peptide",
    "Membrane_Center": "Membrane COM",
    "Membrane_Upper_Heads": "Lipid Heads",
    # "Membrane_Lower_Heads": "Lower leaflet (PO4)",
    "BB_First_RelZ": "Peptide N-term",
    "BB_Last_RelZ": "Peptide C-term",
}

    color_map = {
        "PEPTIDE": "#2451B9",               # azul
        "BB_First_RelZ": "#2BEC64",         # rojo
        "BB_Last_RelZ": "#B9033A",          # naranja
        "Membrane_Center": "#000000",
        "Membrane_Upper_Heads": "#790080",  # verde
        #"Membrane_Lower_Heads": "#98df8a",  # verde claro

    }
    cols_present = [c for c in col_order if c in z_df.columns]

    plt.figure(figsize=(10, 6))

    for col in cols_present:
        data = z_df[col].values
        t_sel = time_vals[mask_time]
        d_sel = data[mask_time]
        smoothed = moving_average(d_sel, window_size)

        plt.plot(t_sel[:len(smoothed)], smoothed,
                label=label_map.get(col, col),
                color=color_map.get(col, None)
          )

    plt.title("Z coordinate", fontproperties=FP_TITLE)
    plt.xlabel("Time ($\\mu$s)", fontproperties=FP_AXIS)
    plt.ylabel("Z coordinate (Å)", fontproperties=FP_AXIS)
    plt.xlim(time_min_us, time_max_us)
    plt.ylim(-1, 150)
    plt.tick_params(axis='both', labelsize=16)
    ax = plt.gca()
    apply_tick_font(ax, FP_TICKS)
    plt.legend(fontsize=16)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "posiciones_z_plot.png"), dpi=600, transparent=True)
    plt.close()
# =========================
# Main / CLI
# =========================

def main():
    global ORIENTATION_BIAS


    parser = argparse.ArgumentParser(
        description="Análisis de tilt/azimut de un péptido en membrana + gráficos (incluye modo -plot).\n Ejemplo de ejecucion: python Analisis_modulizado.py -top md.tpr -traj traj_skip100.xtc -out Resultados_finales --do_all_plots"
    )
    # Entrada de datos
    parser.add_argument("-top", "--topology", type=str, help="Archivo de topología (TPR/GRO)", default="md.tpr")
    parser.add_argument("-traj", "--trajectory", type=str, help="Archivo de trayectoria (XTC/TRR)", default="traj_skip100.xtc")
    parser.add_argument("-plot", action="store_true", help="Solo graficar desde CSV (no recalcular)")
    # Carpetas
    parser.add_argument("-out", "--output_dir", type=str, default="Resultados_finales", help="Carpeta de salida")
    parser.add_argument("-csv_dir", type=str, default=None, help="Carpeta con CSVs (por defecto = output_dir)")
    # Selección de análisis (extendida con 'zcontacts')
    parser.add_argument("--analyses", nargs="+", choices=["tilt", "rolling", "zcontacts"], default=["tilt", "rolling", "zcontacts"],
                        help="Qué análisis ejecutar/plotear (uno o varios). Por defecto: tilt rolling")
    # Parámetros análisis/plot
    parser.add_argument("--nan_mode", type=str, choices=["gap","ffill","interp"], default="gap", help="Tratamiento de NaN en azimut")
    parser.add_argument("--smooth_w", type=int, default=50, help="Ventana de suavizado (puntos)")
    parser.add_argument("--phi_bins", type=int, default=72, help="Número de bins de azimut (72≈5°)")
    parser.add_argument("--tilt_bins", type=int, default=36, help="Número de bins de tilt (36≈5°)")
    parser.add_argument("--do_all_plots", action="store_true", help="Generar todas las figuras disponibles")
    # Rolling angle
    parser.add_argument("--compute_rolling", action="store_true", help="Calcular también rolling angle")
    parser.add_argument("--rolling_skip", type=int, default=1, help="Stride para rolling angle (frames)")
    parser.add_argument("--rolling_csv", type=str, default="rolling_angles.csv", help="CSV de rolling angle")
    parser.add_argument("--rolling_png", type=str, default="rolling_angle.png", help="PNG de rolling angle")
    # --- NUEVO: parámetros Z/Contactos ---
    parser.add_argument("--zc_skip", type=int, default=1, help="Stride para Z/Contactos (frames)")
    parser.add_argument("--zc_cutoff", type=float, default=6.0, help="Cutoff de contacto (Å, Martini)")
    parser.add_argument("--zc_window", type=int, default=25, help="Ventana de suavizado para plots Z/Contactos")

    parser.add_argument("-t","--time", type=int, default=5000, help="Tiempo maximo de graficacion")

    args = parser.parse_args()
    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd_log = os.path.join(out_dir, "run_command.txt")

    # === Guardar metadata: argumentos efectivos, defaults del parser y entorno ===
    meta_path = os.path.join(out_dir, "run_metadata.json")

    # argumentos efectivos (incluye defaults ya “resueltos” donde no pasaste flags)
    effective_args = vars(args).copy()

    # defaults definidos en el parser (tal cual quedaron en cada action)
    declared_defaults = parser_defaults_dict(parser)

    # entorno / condiciones de ejecución
    env_info = {
        "timestamp": timestamp,                  # ya lo calculas antes
        "python": sys.version,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "cwd": os.getcwd(),
        "numpy": getattr(np, "__version__", None),
        "pandas": getattr(pd, "__version__", None),
        "matplotlib": getattr(mpl, "__version__", None),
        "scipy": None if not SCIPY_OK else __import__("scipy").__version__,
        "MDAnalysis": None if not MDA_OK else __import__("MDAnalysis").__version__,
        "SCIPY_OK": SCIPY_OK,
        "MDA_OK": MDA_OK,
    }

    # algunos parámetros que calculas en tiempo de ejecución y pueden ser útiles
    derived = {
        "ORIENTATION_BIAS": ORIENTATION_BIAS,
        "TIME_MAX_ns": effective_args.get("time", None),
        "output_dir": out_dir,
        "csv_dir": os.path.abspath(effective_args["csv_dir"]) if effective_args.get("csv_dir") else out_dir,
    }

    with open(meta_path, "w") as f:
        json.dump(
            {
                "command_line": sys.argv,
                "effective_args": effective_args,
                "parser_declared_defaults": declared_defaults,
                "environment": env_info,
                "derived": derived,
            },
            f,
            indent=2,
            default=str
        )

    print(f"[INFO] Metadata guardada en: {meta_path}")

    with open(cmd_log, "a") as f:
        f.write("\n# Effective args\n")
        f.write(json.dumps(effective_args, indent=2) + "\n")
        f.write("# Parser declared defaults\n")
        f.write(json.dumps(declared_defaults, indent=2) + "\n")


    

    
    
    with open(cmd_log, "a") as f:
        f.write(f"# Command executed on {timestamp}\n")
        f.write("python " + " ".join(sys.argv) + "\n")

    print(f"[INFO] Command line saved in: {cmd_log}")

    csv_dir = os.path.abspath(args.csv_dir) if args.csv_dir else out_dir

    # Rutas de CSVs
    angles_csv = os.path.join(out_dir, "angles_time.csv")
    rolling_csv = os.path.join(out_dir, args.rolling_csv)
    rolling_png = os.path.join(out_dir, args.rolling_png)
    TIME_MAX = args.time

    FPS = setup_plot_style(USE_CUSTOM_FONT)

    global FP_MAIN, FP_TITLE, FP_AXIS, FP_AXIS_X, FP_AXIS_Y, FP_TICKS, FP_LEGEND

    FP_MAIN   = FPS["fp_main"]
    FP_TITLE  = FPS["fp_title"]
    FP_AXIS   = FPS["fp_axis"]
    FP_TICKS  = FPS["fp_ticks"]
    FP_LEGEND = FPS["fp_legend"]


    # ================== MODO PLOT-ONLY ==================
    if args.plot:
        if "tilt" in args.analyses:
            angles_src = os.path.join(csv_dir, "angles_time.csv")
            if not os.path.isfile(os.path.join(csv_dir, "angles_time.csv")):
                raise FileNotFoundError(f"No existe {os.path.join(csv_dir,'angles_time.csv')} (usa análisis primero).")
            df = pd.read_csv(os.path.join(csv_dir, angles_src))
            plot_time_series(df, out_dir, smooth_w=args.smooth_w, nan_mode=args.nan_mode)
            plot_helix_3d(df, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)
            plot_polar_maps(df, out_dir)

            # Uncomment si el recalculo de la densidad no funciona
            # need_density = False
            # try:
            #     P, phi_edges, tilt_edges = load_density_csv(csv_dir)
            # except Exception:
            #     need_density = True

            # if need_density:
            #     phi_bins = np.linspace(0, 360, args.phi_bins+1)
            #     tilt_bins = np.linspace(0, 180, args.tilt_bins+1)
            #     P, phi_edges, tilt_edges = compute_density(df, phi_bins, tilt_bins, time_min_ns=0.0, time_max_ns=TIME_MAX)
            #     save_density_csv(P, phi_edges, tilt_edges, out_dir)

        # 🔄 Recalcular SIEMPRE densidad para el rango deseado
            phi_bins = np.linspace(0, 360, args.phi_bins+1)
            tilt_bins = np.linspace(0, 180, args.tilt_bins+1)
            P, phi_edges, tilt_edges = compute_density(
                df, phi_bins, tilt_bins,
                time_min_ns=0.0,
                time_max_ns=TIME_MAX
            )
            save_density_csv(P, phi_edges, tilt_edges, out_dir)

            plot_density_only(P, phi_edges, tilt_edges, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)
            if args.do_all_plots:
                plot_helix_plus_density(df, P, phi_edges, tilt_edges, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)

        if "rolling" in args.analyses:
            rolling_src = os.path.join(csv_dir, os.path.basename(rolling_csv))
            if not os.path.isfile(rolling_src):
                print(f"[WARN] No existe {rolling_src}; omitiendo plot de rolling en modo -plot.")
            else:
                df_roll = pd.read_csv(rolling_src)
                plot_rolling(df_roll, rolling_png, time_min_ns=0.0, time_max_ns=TIME_MAX)

        # --- NUEVO: plots Z/Contactos desde CSV ---
        if "zcontacts" in args.analyses:
            try:
                zc_plot_from_csv(csv_dir, out_dir, window_size=args.zc_window, time_min_us=0.0, time_max_us=TIME_MAX/1000)
            except FileNotFoundError as e:
                print(f"[WARN] {e}")

        print(f"[OK] Gráficos generados en: {out_dir}")
        return

    # ================== MODO ANÁLISIS (con cálculo) ==================
    if not MDA_OK:
        raise RuntimeError("MDAnalysis no disponible. Instálalo o usa -plot con CSVs existentes.")
    
    # if "rolling" in args.analyses:
    #     print("NO SE APLICAN TRANSFORMACIONES EN EL CODIGO")
    #     w = load_universe(args.topology, args.trajectory)
    #     apply_pbc_transforms(w)
    # else:
    #     print("SE APLICAN TRANSFORMACIONES EN EL CODIGO")
    u = load_universe(args.topology, args.trajectory)
    apply_pbc_transforms(u)

    bias, pct_above, pct_below, z_ref = estimate_orientation_bias(
    u,
    peptide_sel="name BB",
    head_sel="name PO4",
    margin=0.0,
    min_pct=0.25)

    
    ORIENTATION_BIAS = bias


    print(f"[INFO] orientation_bias={bias}  %encima={pct_above:.2%}  %debajo={pct_below:.2%}  mem_com={z_ref:.3f}")

    if "tilt" in args.analyses:
        df = compute_tilt_azim(u)
        save_angles_csv(df, angles_csv)

        phi_bins = np.linspace(0, 360, args.phi_bins+1)
        tilt_bins = np.linspace(0, 180, args.tilt_bins+1)
        P, phi_edges, tilt_edges = compute_density(df, phi_bins, tilt_bins, time_min_ns=0.0, time_max_ns=TIME_MAX)
        save_density_csv(P, phi_edges, tilt_edges, out_dir)

        plot_time_series(df, out_dir, smooth_w=args.smooth_w, nan_mode=args.nan_mode)
        plot_helix_3d(df, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)
        plot_polar_maps(df, out_dir)
        plot_density_only(P, phi_edges, tilt_edges, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)
        if args.do_all_plots:
            plot_helix_plus_density(df, P, phi_edges, tilt_edges, out_dir, time_min_ns=0.0, time_max_ns=TIME_MAX)

    if "rolling" in args.analyses:
        df_roll = compute_rolling_timeseries(u, skip=args.rolling_skip)
        save_rolling_csv(df_roll, rolling_csv)
        plot_rolling(df_roll, rolling_png,time_min_ns=0.0, time_max_ns=TIME_MAX)
        print(f"[OK] Rolling angle guardado en: {rolling_csv} y figura en: {rolling_png}")

    # --- NUEVO: ejecutar Z/Contactos ---
    if "zcontacts" in args.analyses:
        contacts_csv_path, z_csv_path = zc_run_analysis(
            u, out_dir, skip=args.zc_skip, cutoff=args.zc_cutoff, window_size=args.zc_window,
        )
        print(f"[OK] Z/Contactos guardados en: {contacts_csv_path} y {z_csv_path}")

    print(f"[OK] Análisis y gráficos guardados en: {out_dir}")

if __name__ == "__main__":
    main()


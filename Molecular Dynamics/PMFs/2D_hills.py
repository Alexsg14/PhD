#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
    2D_hills.py — FES / PMF analysis for two CVs (D.z and ANGLE)
===============================================================================

This script processes a PLUMED HILLS file containing **two collective variables**:
    • D.z      (distance to membrane or COM axis)
    • ANGLE    (orientation angle of peptide)

It generates:
    ✓ 1D FES for D.z
    ✓ 1D FES for ANGLE (cos(angle) representation)
    ✓ 2D FES surface (D.z vs cos(angle))
    ✓ Subplot figure combining:
            – top: 1D FES of D.z
            – center: 2D FES heatmap
            – right: 1D FES of ANGLE
            – colorbar outside on the far right
    ✓ 1D convergence figures with cumulative hills (blue gradient)
    ✓ Optional videos:
            – 1D movie (D.z only)
            – 2D movie
            – Subplot movie (same layout as static figure)
    ✓ COLVAR analysis:
            – Automatic detection of angle representation (raw or cos)
            – 3 subplots in a vertical layout (D.z / ANGLE / bias)
            – Individual figures for each CV
            – Time converted to microseconds (µs)

The script keeps consistent visual orientation by automatically:
    – Flipping the D.z axis (x → –x) if the minimum D.z < –2 nm.
    – Never flipping the angle axis.
    – Applying the flip consistently in 1D, 2D, subplots and movies.

Energy normalization rules:
    – Static figures → FES minimum = 0.
    – Movies → raw accumulated energy (no normalization).

Optional well-tempered correction:
    – If the HILLS file contains a biasf column, the script can apply:
            F(s) = −(γ / (γ − 1)) * V_bias(s)
      via the flag --fes-wt.
    – Without the flag, or without biasf in the file, the correction is skipped.

Optional ΔG representation (plateau-referenced):
    – If a plateau is detected in the D.z 1D FES, the script can produce:
            FES_subplots_dG.png
      via the flag --dg-subplots.
    – If no plateau is detected → a warning is shown and no ΔG plot is produced.


===============================================================================
                                  USAGE
===============================================================================

    python 2D_hills.py HILLS_FILE OUTDIR [FLAGS...]

Example:

    python 2D_hills.py /path/to/HILLS results/ --all --movie-all --colvar COLVAR

===============================================================================
                                 FLAGS
===============================================================================

--------------------------------------------
  A) FIGURES
--------------------------------------------

--1d
    Produce 1D FES plots for D.z and ANGLE.

--2d
    Produce 2D FES contour map.

--subplots
    Produce combined subplot figure:
        (top)      1D FES D.z
        (center)   2D FES
        (right)    1D FES ANGLE
        (right+)   colorbar

--all
    Generate all static figures: 1D + 2D + subplots + convergence.

(Default: if no figure flag is given, --all is used.)

--------------------------------------------
  B) VIDEOS
--------------------------------------------

--movie-1d
    Generate 1D FES movie (D.z only).

--movie-2d
--movie
    Generate 2D FES movie.

--movie-subplots
    Generate movie of the full subplot layout (1D+2D+1D).

--movie-all
    Generate all available movies: 1D + 2D + subplots.


--------------------------------------------
  C) COLVAR PROCESSING
--------------------------------------------

--colvar FILE
    Process a COLVAR file and generate:
        • D.z vs time (µs)
        • ANGLE vs time (µs)
        • bias vs time (µs)
        • Combined 3-subplot figure

    Multiple COLVAR files can be processed by repeating the flag:
    
        --colvar colvar1 --colvar colvar2 ...

Angle autodetection:
    – If values appear between –1 and 1 → interpreted as cos(angle)
    – Otherwise → raw angle values


--------------------------------------------
  D) WELL–TEMPERED / ΔG OPTIONS
--------------------------------------------

--fes-wt
    Apply well-tempered free-energy correction using the biasfactor from HILLS:
        F(s) = −(γ / (γ − 1)) * V_bias(s)
    Only applied if a biasf column exists; otherwise a warning is shown.

--dg-subplots
    Generate an additional subplot figure in ΔG (energy referenced to a plateau).
    Requires detection of a plateau in D.z 1D FES.
    If no plateau is found → figure is not produced.


--------------------------------------------
  E) OTHER OPTIONS
--------------------------------------------

--no-hills
    Skip all HILLS-based FES analysis.
    Only COLVAR processing will run.

--help
    Show short help message.


===============================================================================
                          EXAMPLE WORKFLOWS
===============================================================================

1) Full analysis (figures + movies):

    python 2D_hills.py HILLS OUT --all --movie-all --colvar COLVAR

2) Only static figures:

    python 2D_hills.py HILLS OUT --all

3) Only 2D movie:

    python 2D_hills.py HILLS OUT --movie-2d

4) Only COLVAR plots:

    python 2D_hills.py HILLS OUT --no-hills --colvar COLVAR

5) Subplots only:

    python 2D_hills.py HILLS OUT --subplots

6) Well–tempered FES + ΔG plateaus:

    python 2D_hills.py HILLS OUT --all --fes-wt --dg-subplots

===============================================================================
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import subprocess

def _colormap(nombre_cmap, min_frac=0.2, max_frac=0.8, N=256):
    base = plt.cm.get_cmap(nombre_cmap)
    colores = base(np.linspace(min_frac, max_frac, N))
    return LinearSegmentedColormap.from_list(
        f"{nombre_cmap}_recortado",
        colores,
        N=N
    )


# Barra de progreso para los vídeos
try:
    from tqdm import tqdm
except ImportError:
    # Si no está instalado tqdm, que el código siga funcionando sin barra
    def tqdm(x, *args, **kwargs):
        return x

# ============================================================
# CONFIGURACIÓN GLOBAL
# ============================================================

COLORMAP = _colormap("inferno_r", 0, 1.0)      # Cambiable fácilmente
N_GRID = 250            # Resolución FES
MAX_FRAMES = 15       # Frames máximos para vídeos
DIST_COLNAME = "D.z"    # CV distancia
ANGLE_COLNAME = "ANGLE" # CV ángulo (bruto)

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================


def phys_to_plot(x, flip):
    """Convierte una coordenada física de D.z en coordenada de ploteo
    teniendo en cuenta si se ha espejado el eje."""
    return -x if flip else x


def flip_1d_for_plot(grid, F, flip):
    """Devuelve (x, F) tal cual o espejados, para plots."""
    if not flip:
        return grid, F
    return -grid[::-1], F[::-1]


def flip_2d_for_plot(XX, YY, F, flip):
    """Devuelve (XX, YY, F) tal cual o espejados en X, para plots."""
    if not flip:
        return XX, YY, F
    XXp = -XX[:, ::-1]
    YYp = YY[:, ::-1]
    Fp  = F[:, ::-1]
    return XXp, YYp, Fp

def detect_plateau_1D(x, F, roi, tail_fraction=0.25, plateau_tol=2.0):
    """Detecta un plateau en una FES 1D dentro de un ROI.

    roi = (xmin, xmax) en las unidades de D.z (no espejado).
    tail_fraction = fracción del extremo derecho para definir el plateau.
    plateau_tol = variación máxima (max-min) permitida en el plateau (kJ/mol).
    """
    mask = (x >= roi[0]) & (x <= roi[1])
    if mask.sum() < 10:
        return None
    x_roi = x[mask]
    F_roi = F[mask]

    # mínimo en la ROI
    min_idx = np.argmin(F_roi)
    min_x = x_roi[min_idx]
    min_F = F_roi[min_idx]

    # tramo de cola (derecha)
    n = len(x_roi)
    start_tail = int((1.0 - tail_fraction) * n)
    if start_tail >= n - 3:
        return None
    x_tail = x_roi[start_tail:]
    F_tail = F_roi[start_tail:]

    if F_tail.max() - F_tail.min() > plateau_tol:
        return None

    plateau_x = float(x_tail.mean())
    plateau_F = float(F_tail.mean())
    return min_x, min_F, plateau_x, plateau_F


# ============================================================
# FUNCIONES DE LECTURA
# ============================================================

def read_fields(path):
    with open(path) as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                return line.split()[2:]
    raise RuntimeError("No se encontró #! FIELDS en el archivo.")

# ============================================================
# AUTODETECCIÓN ÁNGULO (cos, rad, deg)
# ============================================================

def detect_angle_mode(angle_array):
    a_min, a_max = angle_array.min(), angle_array.max()

    if -1.2 <= a_min and a_max <= 1.2:
        print("[INFO] ANGLE detectado como cos(angle).")
        return "cos", angle_array

    if 0 <= a_min and a_max <= (2*np.pi + 0.2):
        print("[INFO] ANGLE detectado como radianes → convirtiendo a cos.")
        return "rad", np.cos(angle_array)

    if 0 <= a_min and a_max <= 360:
        print("[INFO] ANGLE detectado como grados → convirtiendo a cos.")
        return "deg", np.cos(np.deg2rad(angle_array))

    print("[WARNING] Rango desconocido para ANGLE → usando valores brutos.")
    return "raw", angle_array

# ============================================================
# FES 1D
# ============================================================

def compute_fes_1D(grid, centers, sigmas, heights, normalize=True, wt_factor=1.0):
    """Compute 1D FES-like profile from HILLS.

    wt_factor:
        Escala de well-tempered:
            F_wt(s) = wt_factor * (-V_bias(s)) + const
        Para metad simple: wt_factor = 1.0
    """
    F = np.zeros_like(grid)
    for Di, si, hi in zip(centers, sigmas, heights):
        F += hi * np.exp(-(grid - Di)**2 / (2 * si * si))
    F = -F * wt_factor
    if normalize:
        F -= F.min()
    return F

# ============================================================
# FES 2D
# ============================================================

def compute_fes_2D(grid_x, grid_y, D0, A0, sD, sA, h, normalize=True, wt_factor=1.0):
    """Compute 2D FES-like surface from HILLS (D.z, ANGLE)."""
    XX, YY = np.meshgrid(grid_x, grid_y)
    F = np.zeros_like(XX)
    for Di, Ai, sDi, sAi, hi in zip(D0, A0, sD, sA, h):
        F += hi * np.exp(
            -((XX - Di)**2)/(2*sDi*sDi)
            -((YY - Ai)**2)/(2*sAi*sAi)
        )
    F = -F * wt_factor
    if normalize:
        F -= F.min()
    return XX, YY, F

# ============================================================
# PLOTS 1D
# ============================================================

def plot_fes_1D(x, F, xlabel, outpath, walls_black=None, wall_gray=None):
    plt.figure(figsize=(6,5))
    plt.plot(x, F, color="#08306A")

    # Paredes opcionales
    if walls_black is not None:
        for w in walls_black:
            plt.axvline(w, color="black", linestyle="-.", linewidth=1.0)
    if wall_gray is not None:
        for w in wall_gray:
            plt.axvline(w, color=(0.5, 0.5, 0.5), linestyle="--", linewidth=1.0)

    plt.xlabel(xlabel)
    plt.ylabel(r'$\Delta G$ (kJ/mol)')
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"[OK] Guardado → {outpath}")


def plot_fes_1D_convergence(grid, centers, sigmas, heights,
                            time_us, flip, xlabel, outpath,
                            n_curves=80):
    """
    Dibuja muchas curvas FES 1D acumuladas (cada vez con más hills),
    con un degradado de color desde azul claro (antiguas) a azul oscuro
    (más recientes). Sirve para ver la convergencia de la FES.
    """
    N = len(centers)
    if N < 2:
        print("[INFO] Muy pocos hills para hacer convergencia 1D.")
        return

    n_curves = min(n_curves, N)
    idx_list = np.linspace(0, N-1, n_curves, dtype=int)

    # Precalcular todas las FES para tener un rango común de Y
    all_F = []
    for i in idx_list:
        Fi = compute_fes_1D(
            grid,
            centers[:i+1],
            sigmas[:i+1],
            heights[:i+1],
            normalize=True  # cada curva con min = 0
        )
        all_F.append(Fi)
    all_F = np.array(all_F)
    y_min = all_F.min()
    y_max = all_F.max() * 1.05

    cmap = plt.get_cmap("Blues")

    plt.figure(figsize=(6,5))
    for k, i in enumerate(idx_list):
        Fi = all_F[k]
        x_plot, F_plot = flip_1d_for_plot(grid, Fi, flip)

        frac = k / max(1, n_curves - 1)   # 0 → antiguo, 1 → reciente
        color = list(cmap(frac))
        alpha = 0.2 + 0.8 * frac          # más reciente = más opaco
        color[-1] = alpha

        plt.plot(x_plot, F_plot, color=color, linewidth=1)

            # Paredes en -1 y 9 (negras -.), y en 0 (gris --)
        walls_black = [-1.0, 9.0]
        wall_gray   = [0.0]
        if flip:
            walls_black = [-w for w in walls_black]
            wall_gray   = [-w for w in wall_gray]

        for w in walls_black:
            plt.axvline(w, color="black", linestyle="-.", linewidth=1.0)
        for w in wall_gray:
            plt.axvline(w, color=(0.5, 0.5, 0.5), linestyle="--", linewidth=1.0)


    plt.xlabel(xlabel)
    plt.ylabel(r'$\Delta G$ (kJ/mol)')
    plt.ylim(y_min, y_max)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"[OK] Guardado curvas acumuladas 1D → {outpath}")


# ============================================================
# PLOT 2D
# ============================================================

def plot_fes_2D(XX, YY, F, outpath):
    plt.figure(figsize=(6,5))
    plt.contourf(XX, YY, F, 60, cmap=COLORMAP)
    plt.colorbar(label=r'$\Delta G$ (kJ/mol)')
    plt.xlabel(f"{DIST_COLNAME} (nm)")
    plt.ylabel(r"$\cos(\theta)$")
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"[OK] Guardado → {outpath}")

# ============================================================
# SUBPLOTS (1D arriba, 2D centro, 1D derecha)
# ============================================================

def plot_fes_subplots(XX, YY, F, grid_x, Fx, grid_y, Fy, outpath):
    fig = plt.figure(figsize=(10,8))
    gs = fig.add_gridspec(2,2, width_ratios=[4,1], height_ratios=[1,4])

    # 1D distancia (arriba izquierda)
    ax_top = fig.add_subplot(gs[0,0])
    ax_top.plot(grid_x, Fx, color="#08306A")
    ax_top.set_ylabel("Energy (kJ/mol)")
    ax_top.set_xticklabels([])
    ax_top.set_xlim(grid_x.min(), grid_x.max())   # <-- forzar a los extremos
    ax_top.margins(x=0)    
    # ax_top.set_xlim(-7, 0)
    ax_top.set_xlim(0, 7)

    # 1D ángulo (abajo derecha)
    ax_right = fig.add_subplot(gs[1,1])
    ax_right.plot(Fy, grid_y, color="#08306A")
    ax_right.set_xlabel("Energy (kJ/mol)")
    ax_right.set_yticklabels([])
    ax_right.set_ylim(grid_y.min(), grid_y.max())   # <-- forzar a los extremos
    ax_right.margins(y=0)    

    # 2D FES (abajo izquierda)
    ax_main = fig.add_subplot(gs[1,0])
    c = ax_main.contourf(XX, YY, F, 60, cmap=COLORMAP)
    # Líneas de contorno
    cs = ax_main.contour(
        XX, YY, F,
        levels=15,          # número de líneas (ajústalo)
        colors='black',     # color de las líneas
        linewidths=0.8
    )

    # Etiquetas en las líneas (opcional)
    ax_main.clabel(cs, inline=True, fontsize=8)
    ax_main.set_xlabel(f"{DIST_COLNAME} (nm)")
    ax_main.set_ylabel(r"$\cos(\theta)$")
    ax_main.set_ylim(-1,1)
    ax_main.set_xlim(0,7)
    # ax_main.set_xlim(-7,0)


    # Colorbar EXTERNA, pegada al subplot derecho
    divider = make_axes_locatable(ax_right)
    cax = divider.append_axes("right", size="12%", pad=0.2)
    cb = fig.colorbar(c, cax=cax)
    cb.set_label("Energy (kJ/mol)")

    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"[OK] Guardado → {outpath}")



def plot_fes_subplots_dG(XX, YY, dG2D, xD, dG_D, xA, dG_A,
                         min_x_plot, plateau_x_plot, outpath):
    """Subplots en términos de ΔG relativa a un plateau detectado.

    Layout:
        (0,0) : ΔG(D.z)
        (1,0) : ΔG(D.z, cos(angle)) 2D
        (1,1) : ΔG vs cos(angle)
        Colorbar: fuera, a la derecha del subplot derecho
    """
    fig = plt.figure(figsize=(10,8))
    gs = fig.add_gridspec(2,2, width_ratios=[4,1], height_ratios=[1,4])

    # ---------------------
    # 1D ΔG(D.z)
    # ---------------------
    ax_top = fig.add_subplot(gs[0,0])
    ax_top.plot(xD, dG_D, color="black")
    ax_top.axvline(min_x_plot, color="red", linestyle="--", linewidth=1.2)
    ax_top.axvline(plateau_x_plot, color="orange", linestyle="--", linewidth=1.0)
    ax_top.set_ylabel("ΔG (kJ/mol)")
    ax_top.set_xticklabels([])
    ax_top.set_xlim(grid_x.min(), grid_x.max())   # <-- forzar a los extremos
    ax_top.margins(x=0)                           # <-- sin margen extra

    # ---------------------
    # 1D ΔG(angle)
    # ---------------------
    ax_right = fig.add_subplot(gs[1,1])
    ax_right.plot(dG_A, xA, color="black")
    ax_right.set_xlabel("ΔG (kJ/mol)")
    ax_right.set_yticklabels([])
    ax_right.set_ylim(grid_y.min(), grid_y.max())   # <-- forzar a los extremos
    ax_right.margins(y=0)                           # <-- sin margen extra

    # ---------------------
    # 2D ΔG
    # ---------------------
    ax_main = fig.add_subplot(gs[1,0])
    c = ax_main.contourf(XX, YY, dG2D, 60, cmap=COLORMAP)
    ax_main.set_xlabel(f"{DIST_COLNAME} (nm)")
    ax_main.set_ylabel(r"$\cos(\theta)$")

    # ---------------------
    # COLORBAR EXTERNA
    # ---------------------
    divider = make_axes_locatable(ax_right)
    cax = divider.append_axes("right", size="12%", pad=0.2)
    cb = fig.colorbar(c, cax=cax)
    cb.set_label("ΔG (kJ/mol)")

    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()
    print(f"[OK] Guardado subplots ΔG → {outpath}")


# ============================================================
# VIDEO 1D
# ============================================================

def make_movie_1D(grid, centers, sigmas, heights, time_us, outdir, label, fname, flip_D=False):
    frames_dir = os.path.join(outdir, f"_frames_1D_{label}")
    os.makedirs(frames_dir, exist_ok=True)

    NN = len(centers)
    N_FRAMES = min(MAX_FRAMES, NN)
    idx = np.linspace(0, NN-1, N_FRAMES, dtype=int)

    print(f"[INFO] Generando video 1D ({label}) con {N_FRAMES} frames")

    for k, i in enumerate(tqdm(idx, desc=f"movie 1D ({label})", unit="frame")):
        F = compute_fes_1D(grid, centers[:i+1], sigmas[:i+1], heights[:i+1], normalize=False)
        x_plot, F_plot = flip_1d_for_plot(grid, F, flip_D)
        plt.figure(figsize=(6,5))
        plt.plot(x_plot, F_plot, color="black")
        plt.xlabel(label)
        plt.ylabel("Energy")
        plt.title(f"hill {i+1}/{NN}   t = {time_us[i]:.3f} µs")

        frame = os.path.join(frames_dir, f"frame_{k:05d}.png")
        plt.savefig(frame, dpi=200)
        plt.close()

    out_mp4 = os.path.join(outdir, fname)
    cmd = [
        "ffmpeg","-y","-framerate","12",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v","1", out_mp4
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Video guardado → {out_mp4}")
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir,f))
        os.rmdir(frames_dir)
    except:
        print("[WARNING] ffmpeg falló, se conservan los frames.")

# ============================================================
# VIDEO 2D
# ============================================================

def make_movie_2D(grid_x, grid_y, D0, A0, sD, sA, h, time_us, outdir, flip_D=False):
    frames_dir = os.path.join(outdir, "_frames_2D")
    os.makedirs(frames_dir, exist_ok=True)

    NN = len(h)
    N_FRAMES = min(MAX_FRAMES, NN)
    idx = np.linspace(0, NN-1, N_FRAMES, dtype=int)

    print(f"[INFO] Generando video 2D con {N_FRAMES} frames")

    for k, i in enumerate(tqdm(idx, desc="movie 2D", unit="frame")):
        XX, YY, F = compute_fes_2D(grid_x, grid_y,
                                D0[:i+1], A0[:i+1], sD[:i+1], sA[:i+1], h[:i+1],
                                normalize=False)
        XXp, YYp, Fp = flip_2d_for_plot(XX, YY, F, flip_D)                        
        plt.figure(figsize=(6,5))
        plt.contourf(XXp, YYp, Fp, 60, cmap=COLORMAP)
        plt.xlabel(f"{DIST_COLNAME} (nm)")
        plt.ylabel(r"$\cos(\theta)$")
        plt.title(f"hill {i+1}/{NN}   t = {time_us[i]:.3f} µs")
        plt.colorbar(label="Energy")

        frame = os.path.join(frames_dir, f"frame_{k:05d}.png")
        plt.savefig(frame, dpi=200)
        plt.close()

    outmp4 = os.path.join(outdir, "movie_2D.mp4")
    cmd = ["ffmpeg","-y","-framerate","12",
           "-i", os.path.join(frames_dir,"frame_%05d.png"),
           "-qscale:v","1", outmp4]

    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Video guardado → {outmp4}")
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir,f))
        os.rmdir(frames_dir)
    except:
        print("[WARNING] ffmpeg falló → se conservan frames.")

# ============================================================
# VIDEO SUBPLOTS
# ============================================================

def make_movie_subplots(grid_x, grid_y, D0, A0, sD, sA, h, time_us, outdir, flip_D=False):
    frames_dir = os.path.join(outdir, "_frames_subplots")
    os.makedirs(frames_dir, exist_ok=True)

    NN = len(h)
    if NN == 0:
        print("[WARNING] No hay hills → no se puede generar movie_subplots.")
        return

    N_FRAMES = min(MAX_FRAMES, NN)
    idx = np.linspace(0, NN-1, N_FRAMES, dtype=int)

    print(f"[INFO] Generando video subplots con {N_FRAMES} frames")

    # ============================================================
    # 1) Escala fija de color para TODOS los frames
    # ============================================================
    XX_full, YY_full, F2_full = compute_fes_2D(
        grid_x, grid_y,
        D0, A0, sD, sA, h,
        normalize=False
    )
    # Flip solo para ploteo; el rango de energías es el mismo
    XX_full_p, YY_full_p, F2_full_p = flip_2d_for_plot(XX_full, YY_full, F2_full, flip_D)
    Fmin, Fmax = F2_full_p.min(), F2_full_p.max()

    # Para fijar límites de los ejes 1D con el flip ya aplicado
    xD_plot_full, _tmp = flip_1d_for_plot(grid_x, np.zeros_like(grid_x), flip_D)
    xD_min, xD_max = xD_plot_full.min(), xD_plot_full.max()
    yA_min, yA_max = grid_y.min(), grid_y.max()

    # ============================================================
    # 2) Crear FIGURA, ejes y COLORBAR solo una vez (layout fijo)
    # ============================================================
    fig = plt.figure(figsize=(10, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[4, 1], height_ratios=[1, 4])

    # Ejes fijos
    ax_t = fig.add_subplot(gs[0, 0])  # 1D D.z
    ax_m = fig.add_subplot(gs[1, 0])  # 2D FES
    ax_r = fig.add_subplot(gs[1, 1])  # 1D ángulo
    ax_title = fig.add_subplot(gs[0, 1])  # cuadro de texto con hill / tiempo
    ax_title.axis("off")

    # Primer contourf solo para anclar la colorbar con escala fija
    c = ax_m.contourf(
        XX_full_p, YY_full_p, F2_full_p, 60,
        cmap=COLORMAP, vmin=Fmin, vmax=Fmax
    )

    ax_m.set_xlabel(f"{DIST_COLNAME} (nm)")
    ax_m.set_ylabel(r"$\cos(\theta)$")

    divider = make_axes_locatable(ax_r)
    cax = divider.append_axes("right", size="12%", pad=0.2)
    cb = fig.colorbar(c, cax=cax)
    cb.set_label("Energy (kJ/mol)")
    cb.ax.yaxis.set_label_position('right')
    cb.ax.yaxis.labelpad = 15

    # Ajuste suave pero fijo del layout (no usar tight_layout en cada frame)
    fig.subplots_adjust(top=0.95, wspace=0.1, hspace=0.1)

    # ============================================================
    # 3) Bucle de frames: solo ACTUALIZAR datos, no layout
    # ============================================================
    for k, i in enumerate(tqdm(idx, desc="movie subplots", unit="frame")):
        # FES parciales (hasta el hill i)
        XX, YY, F2 = compute_fes_2D(
            grid_x, grid_y,
            D0[:i+1], A0[:i+1], sD[:i+1], sA[:i+1], h[:i+1],
            normalize=False
        )

        F1D_D = compute_fes_1D(
            grid_x, D0[:i+1], sD[:i+1], h[:i+1],
            normalize=False
        )
        F1D_A = compute_fes_1D(
            grid_y, A0[:i+1], sA[:i+1], h[:i+1],
            normalize=False
        )

        # Aplicar flip solo para ploteo
        xD_plot, F1D_D_plot = flip_1d_for_plot(grid_x, F1D_D, flip_D)
        XXp, YYp, F2p = flip_2d_for_plot(XX, YY, F2, flip_D)

        # ---------------------
        # 1D D.z (arriba)
        # ---------------------
        ax_t.cla()
        ax_t.plot(xD_plot, F1D_D_plot, color="black")
        ax_t.set_xticklabels([])
        ax_t.set_xlim(xD_min, xD_max)
        ax_t.margins(x=0)
        ax_t.set_ylabel("Energy (kJ/mol)")

        # ---------------------
        # 1D ángulo (derecha)
        # ---------------------
        ax_r.cla()
        ax_r.plot(F1D_A, grid_y, color="black")
        ax_r.set_yticklabels([])
        ax_r.set_ylim(yA_min, yA_max)
        ax_r.margins(y=0)
        ax_r.set_xlabel("Energy (kJ/mol)")

        # ---------------------
        # 2D FES (centro)
        # ---------------------
        ax_m.cla()
        c = ax_m.contourf(
            XXp, YYp, F2p, 60,
            cmap=COLORMAP, vmin=Fmin, vmax=Fmax
        )
        ax_m.set_xlabel(f"{DIST_COLNAME} (nm)")
        ax_m.set_ylabel(r"$\cos(\theta)$")

        # Actualizar la colorbar con el nuevo mappable, pero
        # manteniendo el MISMO eje (no cambia posición ni tamaño)
        cb.update_normal(c)

        # ---------------------
        # Título (arriba derecha)
        # ---------------------
        ax_title.cla()
        ax_title.axis("off")
        title_str = f"hill {i+1}/{NN}\n t = {time_us[i]:.3f} µs"
        ax_title.text(
            0.5, 0.5, title_str,
            ha="center", va="center",
            transform=ax_title.transAxes
        )

        # Guardar frame
        frame = os.path.join(frames_dir, f"frame_{k:05d}.png")
        fig.savefig(frame, dpi=150)

    plt.close(fig)

    # ============================================================
    # 4) Ensamblar vídeo con ffmpeg y limpiar frames
    # ============================================================
    outmp4 = os.path.join(outdir, "movie_subplots.mp4")
    cmd = [
        "ffmpeg", "-y", "-framerate", "12",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v", "1", outmp4
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Video guardado → {outmp4}")
        for f in os.listdir(frames_dir):
            os.remove(os.path.join(frames_dir, f))
        os.rmdir(frames_dir)
    except Exception as e:
        print(f"[WARNING] ffmpeg falló ({e}) → se conservan frames.")


# ============================================================
# COLVAR — Subplots (D, Angle, Bias)
# ============================================================

def plot_colvar_subplots(colvar_file, outdir):
    print(f"[INFO] Procesando COLVAR → {colvar_file}")

    fields = read_fields(colvar_file)
    data = np.loadtxt(colvar_file)

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if "time" not in fields:
        print("[ERROR] COLVAR sin columna time.")
        return

    time_ps = data[:, fields.index("time")]
    time_us = time_ps / 1_000_000.0

    D = data[:, fields.index(DIST_COLNAME)] if DIST_COLNAME in fields else None
    A_raw = data[:, fields.index(ANGLE_COLNAME)] if ANGLE_COLNAME in fields else None
    bias = data[:, fields.index("metad.bias")] if "metad.bias" in fields else None

    if A_raw is not None:
        _, A = detect_angle_mode(A_raw)
    else:
        A = None

    fig, axs = plt.subplots(3,1, figsize=(10,10), sharex=True)

    if D is not None:
        axs[0].plot(time_us, D, lw=1)
        axs[0].set_ylabel(f"{DIST_COLNAME} (nm)")

    if A is not None:
        axs[1].plot(time_us, A, lw=1)
        axs[1].set_ylabel(r"$\cos(\theta)$")

    if bias is not None:
        axs[2].plot(time_us, bias, lw=1, color="#355070")
        axs[2].set_ylabel("Bias (kJ/mol)")

    axs[2].set_xlabel("Time (µs)")

    plt.tight_layout()
    out = os.path.join(outdir, "COLVAR_subplots.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] Guardado → {out}")

# ============================================================
# COLVAR — Gráficos individuales
# ============================================================

def plot_colvar_individuals(colvar_file, outdir):
    fields = read_fields(colvar_file)
    data = np.loadtxt(colvar_file)
    if data.ndim == 1:
        data = data.reshape(1, -1)

    time_us = data[:, fields.index("time")] / 1_000_000.0

    if DIST_COLNAME in fields:
        D = data[:, fields.index(DIST_COLNAME)]
        plt.figure(figsize=(8,4))
        plt.plot(time_us, D, lw=1)
        plt.xlabel("Time (µs)")
        plt.ylabel(f"{DIST_COLNAME} (nm)")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir,"COLVAR_D.png"), dpi=300)
        plt.close()

    if ANGLE_COLNAME in fields:
        _, A = detect_angle_mode(data[:, fields.index(ANGLE_COLNAME)])
        plt.figure(figsize=(8,4))
        plt.plot(time_us, A, lw=1)
        plt.xlabel("Time (µs)")
        plt.ylabel(r"$\cos(\theta)$")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir,"COLVAR_Angle.png"), dpi=300)
        plt.close()

    if "metad.bias" in fields:
        bias = data[:, fields.index("metad.bias")]
        plt.figure(figsize=(8,4))
        plt.plot(time_us, bias, lw=1)
        plt.xlabel("Time (µs)")
        plt.ylabel("Bias (kJ/mol)")
        plt.tight_layout()
        plt.savefig(os.path.join(outdir,"COLVAR_Bias.png"), dpi=300)
        plt.close()

    print("[OK] Plots COLVAR individuales generados.")

# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 3:
        print("Uso: python fes_1D_2D.py HILLS outdir [flags]")
        sys.exit(1)

    hills = sys.argv[1]
    outdir = sys.argv[2]
    flags = sys.argv[3:]
    os.makedirs(outdir, exist_ok=True)

    # Flags de figuras
    do_1D = ("--1d" in flags) or ("--all" in flags) or len(flags)==0
    do_2D = ("--2d" in flags) or ("--all" in flags) or len(flags)==0
    do_sub = ("--subplots" in flags) or ("--all" in flags) or len(flags)==0

    # Flags de energía libre / ΔG
    fes_wt = "--fes-wt" in flags          # aplicar corrección well-tempered (si hay biasfactor)
    dg_sub = "--dg-subplots" in flags     # generar figura extra en ΔG con plateau


    # Flags de vídeo
    movie_1D = "--movie-1d" in flags or "--movie-all" in flags
    movie_2D = "--movie-2d" in flags or "--movie" in flags or "--movie-all" in flags
    movie_sub = "--movie-subplots" in flags or "--movie-all" in flags

    # Flag COLVAR
    colvar_file = None
    if "--colvar" in flags:
        i = flags.index("--colvar")
        if i+1 >= len(flags):
            print("[ERROR] --colvar necesita un archivo")
            sys.exit(1)
        colvar_file = flags[i+1]

    # ============================================================
    # Leer HILLS
    # ============================================================
    fields = read_fields(hills)
    data = np.loadtxt(hills)
    if data.ndim == 1:
        data = data.reshape(1, -1)

    idx_D  = fields.index(DIST_COLNAME)
    idx_A  = fields.index(ANGLE_COLNAME)
    idx_sD = fields.index(f"sigma_{DIST_COLNAME}")
    idx_sA = fields.index(f"sigma_{ANGLE_COLNAME}")
    idx_h  = fields.index("height")
    idx_t  = fields.index("time") if "time" in fields else None

    D0 = data[:, idx_D]
    A_raw = data[:, idx_A]
    sD = data[:, idx_sD]
    sA = data[:, idx_sA]
    h  = data[:, idx_h]

        # --------- biasfactor para well-tempered (si existe) ---------
    biasfactor = None
    for name in ("biasf", "metad.biasf", "biasfactor", "metad.biasfactor"):
        if name in fields:
            idx_bf = fields.index(name)
            biasfactor = float(data[0, idx_bf])
            break

    wt_factor = 1.0
    if fes_wt:
        if biasfactor is None:
            print("[WARNING] --fes-wt activado pero no se encontró biasfactor en HILLS → se usa wt_factor = 1.0.")
        else:
            if biasfactor <= 1.0:
                print(f"[WARNING] biasfactor={biasfactor:.3f} <= 1 → se ignora corrección WT.")
            else:
                wt_factor = biasfactor / (biasfactor - 1.0)
                print(f"[INFO] Usando corrección well-tempered: biasfactor={biasfactor:.3f} → wt_factor={wt_factor:.3f}")
    else:
        print("[INFO] Corrección WT desactivada (usar --fes-wt para activarla).")

    # --------- criterio de flip en D.z ---------
    flip_D = D0.min() < -2.0
    if flip_D:
        print(f"[INFO] Min {DIST_COLNAME} = {D0.min():.3f} < -2 → se espeja el eje X en todos los plots.")
    else:
        print(f"[INFO] Min {DIST_COLNAME} = {D0.min():.3f} → no se espeja el eje X.")

    # Tiempo → µs
    if idx_t is not None:
        time_ps = data[:, idx_t]
        time_us = time_ps / 1_000_000.0
    else:
        time_us = np.arange(len(D0)) * 0.001  # fallback

    # Autodetección ángulo
    _, A0 = detect_angle_mode(A_raw)

    # ============================================================
    # Grids
    # ============================================================
    grid_D = np.linspace(D0.min()-2*sD.max(), D0.max()+2*sD.max(), N_GRID)
    grid_A = np.linspace(A0.min(), A0.max(), N_GRID)

    # ============================================================
    # FES (se calculan SIEMPRE, luego se decide qué plotea)
    # ============================================================
    F1D_D = compute_fes_1D(grid_D, D0, sD, h, normalize=True, wt_factor=wt_factor)
    F1D_A = compute_fes_1D(grid_A, A0, sA, h, normalize=True, wt_factor=wt_factor)
    XX, YY, F2D = compute_fes_2D(grid_D, grid_A, D0, A0, sD, sA, h, normalize=True, wt_factor=wt_factor)


    # --------- aplicar flip solo para los PLOTS (no cambia datos originales) ----------
    xD_plot, F1D_D_plot = flip_1d_for_plot(grid_D, F1D_D, flip_D)
    xA_plot, F1D_A_plot = grid_A, F1D_A   # el ángulo no se espeja

    XX_plot, YY_plot, F2D_plot = flip_2d_for_plot(XX, YY, F2D, flip_D)

    # ============================================================
    # PLOTS 1D / 2D / SUBPLOTS
    # ============================================================
    if do_1D:
        # Paredes en coordenadas de ploteo (tienen en cuenta flip_D)
        walls_black = [phys_to_plot(-1.0, flip_D), phys_to_plot(9.0, flip_D)]
        wall_gray   = [phys_to_plot(0.0,  flip_D)]

        plot_fes_1D(
            xD_plot, F1D_D_plot, DIST_COLNAME,
            os.path.join(outdir,"FES_D.png"),
            walls_black=walls_black,
            wall_gray=wall_gray
        )

        plot_fes_1D(xA_plot, F1D_A_plot, "cos(angle)",
                    os.path.join(outdir,"FES_Angle.png"))
            # Figura de convergencia 1D para D.z
        plot_fes_1D_convergence(
            grid_D,         # grid de D.z
            D0,             # centros D.z
            sD,             # sigmas D.z
            h,              # alturas
            time_us,        # tiempo en µs
            flip_D,         # mismo flip que la FES final
            DIST_COLNAME,
            os.path.join(outdir, "FES_D_convergence.png")
        )

        # (Opcional) convergencia también para el ángulo:
        plot_fes_1D_convergence(
            grid_A,
            A0,
            sA,
            h,
            time_us,
            False,   # el ángulo no se espeja
            "cos(angle)",
            os.path.join(outdir, "FES_Angle_convergence.png")
        )


    if do_2D:
        plot_fes_2D(XX_plot, YY_plot, F2D_plot,
                    os.path.join(outdir,"FES_2D.png"))

    if do_sub:
        plot_fes_subplots(
            XX_plot, YY_plot, F2D_plot,
            xD_plot, F1D_D_plot,
            xA_plot, F1D_A_plot,
            os.path.join(outdir,"FES_subplots.png")
        )

    # ============================================================
    # SUBPLOTS extra en ΔG (requiere plateau)
    # ============================================================
    if dg_sub:
        # ROI para buscar plateau (como en tu script original)
        if D0.min() < -2.0:
            roi = (-7.0, 0.0)
        else:
            roi = (0.0, 7.0)

        info = detect_plateau_1D(grid_D, F1D_D, roi=roi)
        if info is None:
            print("[WARNING] No se detecta plateau en FES 1D de D.z → no se genera FES_subplots_dG.png.")
        else:
            min_x, min_F, plat_x, plat_F = info
            # Construir ΔG relativa al plateau
            dG_D = F1D_D - plat_F
            dG_A = F1D_A - plat_F
            dG_2D = F2D   - plat_F

            # convertir a coordenadas de ploteo (por si hay flip)
            def x_to_plot(x):
                return -x if flip_D else x

            min_x_plot = x_to_plot(min_x)
            plat_x_plot = x_to_plot(plat_x)

            # aplicar flip para los datos de ploteo
            xD_dG_plot, dG_D_plot = flip_1d_for_plot(grid_D, dG_D, flip_D)
            xA_dG_plot, dG_A_plot = grid_A, dG_A
            XX_dG_plot, YY_dG_plot, dG2D_plot = flip_2d_for_plot(XX, YY, dG_2D, flip_D)

            plot_fes_subplots_dG(
                XX_dG_plot, YY_dG_plot, dG2D_plot,
                xD_dG_plot, dG_D_plot,
                xA_dG_plot, dG_A_plot,
                min_x_plot, plat_x_plot,
                os.path.join(outdir, "FES_subplots_dG.png")
            )


    # ============================================================
    # VÍDEOS (usan energía SIN normalizar y mismo flip)
    # ============================================================
    if movie_1D:
        make_movie_1D(grid_D, D0, sD, h, time_us,
                      outdir, DIST_COLNAME, "movie_1D_D.mp4", flip_D=flip_D)
        make_movie_1D(grid_A, A0, sA, h, time_us,
                      outdir, "cos(angle)", "movie_1D_Angle.mp4", flip_D=False)

    if movie_2D:
        make_movie_2D(grid_D, grid_A, D0, A0, sD, sA, h,
                      time_us, outdir, flip_D=flip_D)

    if movie_sub:
        make_movie_subplots(
            grid_D, grid_A,     # grids en X e Y
            D0, A0,             # centros
            sD, sA,             # sigmas
            h,                  # alturas
            time_us,            # tiempo en µs
            outdir,             # carpeta de salida
            flip_D=flip_D       # mismo flip que el resto de plots
        )


    # ============================================================
    # COLVAR
    # ============================================================
    if colvar_file is not None:
        plot_colvar_subplots(colvar_file, outdir)
        plot_colvar_individuals(colvar_file, outdir)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import os
import subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")  # para que funcione en servidores sin pantalla
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec


# Para elegir columna de coordenada (como en tu código PMF)
# Cambia esto entre "D.z" y "D" según el sistema
D = "D.z"


def read_fields(hills_file):
    fields = None
    with open(hills_file) as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                fields = line.split()[2:]
                break
    if fields is None:
        raise RuntimeError("No se encontró la línea '#! FIELDS' en el HILLS")
    return fields


def compute_fes_profile(grid, D0, sigma, h, n_hills=None):
    """
    Devuelve la FES acumulada hasta n_hills (si es None, usa todos).
    Convención: pozo visible, valores negativos, 0 como máximo.
    (Esta versión es la que usan las figuras "fes" y los vídeos clásicos)
    """
    if n_hills is None:
        n_hills = len(D0)
    F = np.zeros_like(grid)
    for Di, si, hi in zip(D0[:n_hills], sigma[:n_hills], h[:n_hills]):
        F += hi * np.exp(-(grid - Di) ** 2 / (2 * si * si))
    Fi = -F
    Fi -= Fi.min()
    Fi -= Fi.max()
    return Fi


# ------------------------- VÍDEOS CLÁSICOS ------------------------- #

def make_movie_og(hills_file, out_dir, fields, data, D0, sigma, h, flip_x=False):
    """
    Genera un vídeo MP4 de la FES acumulada usando ffmpeg.
    Guarda frames PNG en una carpeta temporal y los borra al final si todo va bien.

    flip_x: si True, se representa la coordenada espejada (x -> -x),
            pero no se modifican los datos originales.
    """
    try:
        idx_time = fields.index("time")
    except ValueError:
        print("No hay columna 'time' en el HILLS; no se puede hacer el vídeo.")
        return

    time = data[:, idx_time]
    total = len(D0)

    # Grilla en la coordenada colectiva
    Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
    grid = np.linspace(Dmin, Dmax, 400)

    # Límites de x para la representación (con espejo si flip_x)
    if flip_x:
        x_left, x_right = -Dmax, -Dmin
    else:
        x_left, x_right = Dmin, Dmax

    N_FRAMES = min(2000, total)
    frame_indices = np.linspace(0, total - 1, N_FRAMES, dtype=int)

    frames_dir = os.path.join(out_dir, "_frames_fes_movie")
    os.makedirs(frames_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 5))
    line, = ax.plot([], [], lw=1, color="#08306A")
    ax.set_xlim(x_left, x_right)
    ax.set_xlabel(D)
    ax.set_ylabel("Energy (kJ/mol)")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    title = ax.set_title("")

    print(f"Generando {N_FRAMES} frames en {frames_dir} ...")

    for k, i in enumerate(frame_indices):
        Fi = compute_fes_profile(grid, D0, sigma, h, n_hills=i + 1)
        x_plot = -grid if flip_x else grid
        line.set_data(x_plot, Fi)
        ax.set_ylim(Fi.min() * 1.05, Fi.max() * 1.05)
        title.set_text(f"HILLS – hill {i+1}/{total} (time = {time[i]:.0f})")
        frame_path = os.path.join(frames_dir, f"frame_{k:05d}.png")
        fig.savefig(frame_path, dpi=250)

    plt.close(fig)

    out_movie = os.path.join(out_dir, "fes_movie.mp4")
    cmd = [
        "ffmpeg", "-y", "-framerate", "15",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v", "1", out_movie,
    ]
    print("Llamando a ffmpeg para crear el vídeo...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Vídeo creado: {out_movie}")
        print("Borrando frames temporales...")
        for fname in os.listdir(frames_dir):
            if fname.endswith(".png"):
                os.remove(os.path.join(frames_dir, fname))
        os.rmdir(frames_dir)
        print("Frames temporales eliminados.")
    except subprocess.CalledProcessError:
        print("⚠ ffmpeg ha fallado; se conservan los PNG en", frames_dir)


def make_movie(hills_file, out_dir, fields, data, D0, sigma, h, flip_x=False):
    """
    Genera un vídeo de la FES acumulada.
    Cada frame muestra TODAS las curvas hasta ese momento,
    con un degradado de color (Blues) de claro (antiguo) a oscuro (reciente).

    flip_x: si True, se representa la coordenada espejada (x -> -x),
            pero no se modifican los datos originales.
    """
    try:
        idx_time = fields.index("time")
    except ValueError:
        print("No hay columna 'time' en el HILLS; no se puede hacer el vídeo.")
        return

    time = data[:, idx_time]
    total = len(D0)

    Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
    grid = np.linspace(Dmin, Dmax, 400)

    if flip_x:
        x_left, x_right = -Dmax, -Dmin
    else:
        x_left, x_right = Dmin, Dmax

    N_FRAMES = min(2000, total)
    frame_indices = np.linspace(0, total - 1, N_FRAMES, dtype=int)

    profiles = []
    for i in frame_indices:
        Fi = compute_fes_profile(grid, D0, sigma, h, n_hills=i + 1)
        profiles.append(Fi)
    profiles = np.array(profiles)
    global_min = profiles.min()
    global_max = profiles.max()

    frames_dir = os.path.join(out_dir, "_frames_fes_movie")
    os.makedirs(frames_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 5), dpi=200)
    cmap = plt.get_cmap("Blues")

    print(f"Generando {N_FRAMES} frames en {frames_dir} ...")

    for k in range(N_FRAMES):
        ax.clear()
        ax.set_xlim(x_left, x_right)
        ax.set_ylim(global_min * 1.05, global_max * 1.05)
        ax.set_xlabel(D)
        ax.set_ylabel("Energy (kJ/mol)")
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        i_hill = frame_indices[k]
        ax.set_title(f"HILLS – hill {i_hill+1}/{total} (time = {time[i_hill]:.0f})")

        for j in range(k + 1):
            Fi = profiles[j]
            frac = j / (N_FRAMES - 1)
            color = cmap(frac)
            alpha = 0.2 + 0.8 * frac
            rgba = list(color)
            rgba[-1] = alpha
            x_plot = -grid if flip_x else grid
            ax.plot(x_plot, Fi, color=rgba, linewidth=1)

        frame_path = os.path.join(frames_dir, f"frame_{k:05d}.png")
        fig.savefig(frame_path, dpi=fig.dpi)

    plt.close(fig)

    out_movie_mp4 = os.path.join(out_dir, "fes_movie_gradient.mp4")
    cmd_mp4 = [
        "ffmpeg", "-y", "-framerate", "15",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-qscale:v", "1", out_movie_mp4,
    ]
    print("Llamando a ffmpeg para crear el vídeo MP4...")
    mp4_ok = False
    try:
        subprocess.run(cmd_mp4, check=True)
        print(f"Vídeo MP4 creado: {out_movie_mp4}")
        mp4_ok = True
    except subprocess.CalledProcessError:
        print("⚠ ffmpeg ha fallado al crear MP4.")

    if mp4_ok:
        print("Borrando frames temporales...")
        for fname in os.listdir(frames_dir):
            if fname.endswith(".png"):
                os.remove(os.path.join(frames_dir, fname))
        os.rmdir(frames_dir)
        print("Frames temporales eliminados.")
    else:
        print("No se pudo crear el vídeo; se conservan los PNG en", frames_dir)


# ------------------------- FIGURAS FES CLÁSICAS (con --limits) ------------------------- #

def generate_plots(out_dir, grid, F, snapshots, D0, flip_x, N_LAST, use_limits):
    """
    Genera las figuras estáticas (fes.png y fes_last_XXXX.png).

    - Si use_limits == False: comportamiento original (sin límites en X,
      y_max basado en el máximo global de F_final).
    - Si use_limits == True:
        * ROI_X = (-7,0) o (0,7) según x_min_real,
        * respeta el espejado (flip_x),
        * y el límite superior en Y es 1.05 * max_y_en_ROI
          (considerando todas las curvas, incluida la final).
    """
# Sufijo para nombres de archivo
    suffix = "_fit" if use_limits else ""

    F_final = -F
    F_final -= F_final.min()

    x_min_real = D0.min()
    x_min_fes = grid[np.argmin(F_final)]

    x_plot = -grid if flip_x else grid
    x_min_plot = -x_min_fes if flip_x else x_min_fes

    ROI_X_plot = None
    if use_limits:
        if x_min_real < -2.0:
            ROI_X = (-7.0, 0.0)
            print(f"[LIMITS] x_min = {x_min_real:.2f} < -2 → ROI_X (original) = {ROI_X}")
        else:
            ROI_X = (0.0, 7.0)
            print(f"[LIMITS] x_min = {x_min_real:.2f} ≥ -2 → ROI_X (original) = {ROI_X}")

        if flip_x:
            ROI_X_plot = (-ROI_X[1], -ROI_X[0])
        else:
            ROI_X_plot = ROI_X

    # y_max según ROI si existe
    if ROI_X_plot is not None:
        mask_roi = (x_plot >= ROI_X_plot[0]) & (x_plot <= ROI_X_plot[1])
        if not np.any(mask_roi):
            print("[LIMITS] Advertencia: la ROI no contiene puntos de la grilla, se usará el máximo global.")
            y_max = F_final.max()
        else:
            y_candidates = [F_final[mask_roi].max()]
            for snap in snapshots:
                Fi = -snap
                Fi -= Fi.min()
                y_candidates.append(Fi[mask_roi].max())
            y_max = max(y_candidates) * 1.05
    else:
        y_max = F_final.max()

    # FIGURA 1: FES final
    plt.figure(figsize=(5, 5))
    plt.plot(x_plot, F_final, color="#08306A")

    plt.axvline(
        0,
        color=(0.6, 0.6, 0.6, 0.4),
        linestyle="--",
        linewidth=1.2,
        label="COMM"
    )
    plt.axvline(
        x_min_plot,
        color=(1, 0, 0, 0.5),
        linestyle="--",
        linewidth=1.5,
        label=f"min @ {x_min_plot:.2f}"
    )

    plt.xlabel(D)
    plt.ylabel("Energy (kJ/mol)")
    plt.title("HILLS")
    plt.ylim(-0.5, y_max)
    if ROI_X_plot is not None:
        plt.xlim(ROI_X_plot[0], ROI_X_plot[1])
    plt.legend(loc="upper left", framealpha=0.6)
    plt.tight_layout()

    out_fes = os.path.join(out_dir, f"fes{suffix}.png")
    plt.savefig(out_fes, dpi=600)
    plt.close()
    print(f"Guardado: {out_fes}")

    # FIGURA 2: últimos N_LAST con colormap
    cmap = cm.get_cmap("Blues", N_LAST)

    plt.figure(figsize=(5, 5))
    plt.axvline(
        0,
        color=(0.6, 0.6, 0.6, 0.4),
        linestyle="--",
        linewidth=1.2,
        label="COMM"
    )
    plt.axvline(
        x_min_plot,
        color=(1, 0, 0, 0.2),
        linestyle="--",
        linewidth=1.0,
        label=f"min @ {x_min_plot:.2f}"
    )
    plt.axvline(
    -1,
    color='black',
    linestyle="-.",
    linewidth=1.0,
    label=f"Lower Wall"
    )
    plt.axvline(
    9,
    color='black',
    linestyle="-.",
    linewidth=1.0,
    label=f"Upper Wall"
    )

    for i, snap in enumerate(snapshots):
        Fi = -snap
        Fi -= Fi.min()
        color = cmap(i)
        alpha = 0.2 + 0.8 * (i / (N_LAST - 1))
        rgba = list(color)
        rgba[-1] = alpha
        plt.plot(x_plot, Fi, color=rgba, linewidth=1)

    plt.xlabel(D)
    plt.ylabel("Energy (kJ/mol)")
    plt.title("HILLS")
    plt.ylim(-0.5, y_max)
    if ROI_X_plot is not None:
        plt.xlim(ROI_X_plot[0], ROI_X_plot[1])
    plt.legend(loc="upper left", framealpha=0.6)
    plt.tight_layout()

    out_last = os.path.join(out_dir, f"fes_trail_.png") #{len(snapshots)}{suffix}.png")
    plt.savefig(out_last, dpi=600)
    plt.close()
    print(f"Guardado: {out_last}")


# ------------------------- FUNCIONES PMF / ÁREAS / ΔG ------------------------- #

def calculate_deltaG_from_areas(
    grid_x,
    fes,
    offset_energy,
    occupied_start,
    occupied_end,
    total_start,
    total_end,
    T=298.0,
    R=8.314472 / 1000.0,
    out_dir="."
):
    """
    Calcula K y DeltaG a partir del ratio de áreas de la probabilidad Z(X).
    Z_rel(X) = exp( (offset_energy - fes(X)) / RT )
    """
    RT = R * T

    Z_rel = np.exp((offset_energy - fes) / RT)

    a_oc, b_oc = (min(occupied_start, occupied_end), max(occupied_start, occupied_end))
    a_tot, b_tot = (min(total_start, total_end), max(total_start, total_end))

    mask_total = (grid_x >= a_tot) & (grid_x <= b_tot)
    if not np.any(mask_total):
        print("🛑 Dominio total de integración vacío: revisa total_start y total_end.")
        return np.nan, np.nan

    X_red = grid_x[mask_total]
    Z_red = Z_rel[mask_total]

    mask_ocupado = (X_red >= a_oc) & (X_red <= b_oc)
    X_ocupado = X_red[mask_ocupado]
    Z_ocupado = Z_red[mask_ocupado]
    area_ocupado = np.trapz(Z_ocupado, X_ocupado) if np.any(mask_ocupado) else 0.0

    mask_libre = (X_red > b_oc) & (X_red <= b_tot)
    X_libre = X_red[mask_libre]
    Z_libre = Z_red[mask_libre]
    area_libre = np.trapz(Z_libre, X_libre) if np.any(mask_libre) else 0.0

    print("-" * 50)
    print("📊 Análisis de DeltaG por Integración de Áreas")
    print(f'Offset Energy (Plateau): {offset_energy:.3f} kJ/mol')
    print(f'Rango Total (Integración): [{a_tot:.3f}, {b_tot:.3f}]')
    print(f'Rango Ocupado (Pozo):     [{a_oc:.3f}, {b_oc:.3f}]')
    print(f'Área Ocupada (Pozo): {area_ocupado:.6f}, Área Libre (Plateau): {area_libre:.6f}')

    if area_libre <= 1e-12 or area_ocupado <= 1e-12:
        print("🛑 Áreas no positivas o numéricamente nulas → K/ΔG indefinidos.")
        K, DeltaG = np.nan, np.nan
    else:
        K = area_ocupado / area_libre
        DeltaG = -RT * np.log(K)
        print(f'K (Ocupado/Libre): {K:.6f}')
        print(f'DeltaG (calculado): {DeltaG:.3f} kJ/mol')
    print("-" * 50)

    plt.figure(figsize=(10, 5))
    plt.plot(X_red, Z_red, color='black', lw=2,
             label=f'Z_rel(X) (Offset={offset_energy:.1f} kJ/mol)')

    plt.fill_between(X_ocupado, Z_ocupado, alpha=0.5,
                     color='orange', label=f'Área Ocupada (Pozo)\nK = {K:.3f}')

    plt.fill_between(X_libre, Z_libre, alpha=0.4,
                     color='skyblue', label=f'Área Libre (Plateau)')

    plt.axvline(a_oc, color='red', ls='--',
                label=f'Límite Ocupado Inf. = {a_oc:.3f}')
    plt.axvline(b_oc, color='red', ls='--',
                label=f'Límite Ocupado Sup. = {b_oc:.3f}')

    plt.xlabel('D (nm)')
    plt.ylabel('Z_rel(X) (Probabilidad relativa re-normalizada)')
    plt.title(f'Integración de Áreas para DeltaG (calculado = {DeltaG:.2f} kJ/mol)')
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    out_path = os.path.join(out_dir, "Area_Offset_DeltaG.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Guardado: {out_path}")

    return K, DeltaG


def calculate_deltaG_from_areas2(
    grid_x,
    fes,
    offset_energy,
    occupied_start,
    occupied_end,
    total_start,
    total_end,
    T=298.0,
    R=8.314472 / 1000.0,
    out_dir="."
):
    """
    Variante alternativa (no se usa por defecto pero la dejo íntegra).
    """
    RT = R * T
    Z_rel = np.exp((offset_energy - fes) / RT)

    a_oc, b_oc = (min(occupied_start, occupied_end), max(occupied_start, occupied_end))
    a_tot, b_tot = (min(total_start, total_end), max(total_start, total_end))

    mask_total = (grid_x >= a_tot) & (grid_x <= b_tot)
    if not np.any(mask_total):
        print("🛑 Dominio total de integración vacío: revisa total_start y total_end.")
        return np.nan, np.nan

    X_red = grid_x[mask_total]
    Z_red = Z_rel[mask_total]

    area_total = np.trapz(Z_red, X_red)

    mask_ocupado = (X_red >= a_oc) & (X_red <= b_oc)
    X_ocupado = X_red[mask_ocupado]
    Z_ocupado = Z_red[mask_ocupado]
    area_ocupado = np.trapz(Z_ocupado, X_ocupado) if np.any(mask_ocupado) else 0.0

    area_libre = area_total - area_ocupado

    print("-" * 50)
    print("📊 Análisis de DeltaG por Integración de Áreas (versión 2)")
    print(f'Offset Energy (Plateau): {offset_energy:.3f} kJ/mol')
    print(f'Rango Total (Integración): [{a_tot:.3f}, {b_tot:.3f}]')
    print(f'Rango Ocupado (Pozo):     [{a_oc:.3f}, {b_oc:.3f}]')
    print(f'Área Ocupada (Pozo): {area_ocupado:.6f}, Área Libre (Plateau): {area_libre:.6f}')

    if area_libre <= 1e-12 or area_ocupado <= 1e-12:
        print("🛑 Áreas no positivas o numéricamente nulas → K/ΔG indefinidos.")
        K, DeltaG = np.nan, np.nan
    else:
        K = area_ocupado / area_libre
        DeltaG = -RT * np.log(K)
        print(f'K (Ocupado/Libre): {K:.6f}')
        print(f'DeltaG (calculado): {DeltaG:.3f} kJ/mol')
    print("-" * 50)

    plt.figure(figsize=(10, 5))
    plt.plot(X_red, Z_red, color='black', lw=2,
             label=f'Z_rel(X) (Offset={offset_energy:.1f} kJ/mol)')

    mask_ocupado = (X_red >= a_oc) & (X_red <= b_oc)
    X_oc2 = X_red[mask_ocupado]
    Z_oc2 = Z_red[mask_ocupado]
    plt.fill_between(X_oc2, Z_oc2, alpha=0.5, color='orange',
                     label=f'Área Ocupada (Pozo)\nK = {K:.3f}')

    mask_libre = (X_red >= a_tot) & (X_red <= b_tot) & ~mask_ocupado
    X_libre = X_red[mask_libre]
    Z_libre = Z_red[mask_libre]
    plt.fill_between(X_libre, Z_libre, alpha=0.4, color='skyblue',
                     label='Área Libre (Plateau)')

    plt.axvline(a_oc, color='red', ls='--',
                label=f'Límite Ocupado Inf. = {a_oc:.3f}')
    plt.axvline(b_oc, color='red', ls='--',
                label=f'Límite Ocupado Sup. = {b_oc:.3f}')

    plt.xlabel('D (nm)')
    plt.ylabel('Z_rel(X) (Probabilidad relativa re-normalizada)')
    plt.title(f'Integración de Áreas para DeltaG (calculado = {DeltaG:.2f} kJ/mol)')
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    out_path = os.path.join(out_dir, "Area_Offset_DeltaG_v2.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Guardado: {out_path}")

    return K, DeltaG


def run_pmf_analysis(out_dir, fields, data, D0, sigma, h, grid):
    with mpl.rc_context({
        "axes.labelsize": 20,
        "axes.titlesize": 22,
        "xtick.labelsize": 18,
        "ytick.labelsize": 18,
        "legend.fontsize": 16,
        "figure.titlesize": 22,
        "font.size": 18,
    }):
            
        """
        Reimplementa toda la lógica de tu script de PMF:
        - ROI_X = (0,7)
        - detección de mínimo y plateau vía derivadas
        - figuras PMF.png y PMF_last_XXX.png (stride + colorbar)
        - cálculo de ΔG mediante integración de áreas
        - imprime todos los mensajes de diagnóstico de áreas y ΔG
        """
        ROI_X = (0.5, 7)

        total = len(D0)

            # ---- determinar rango temporal / número de hills para la convergencia ----
        try:
            idx_time = fields.index("time")
            time_ps = data[:, idx_time]
            time_ns = time_ps / 1000.0

            time_total_ns = time_ns[-1]
            time_start_window_ns = time_total_ns - 100.0

            start_index_100ns = np.searchsorted(time_ns, time_start_window_ns)
            start_index_100ns = max(0, start_index_100ns)

            t_min_cbar = -100.0
            t_max_cbar = 0.0
            cbar_label = "Time before end (ns)"

            N_HILLS_100NS = total - start_index_100ns
            print(f"Detectados {N_HILLS_100NS} hills en los últimos 100 ns.")
            START_IDX_SNAPSHOTS = start_index_100ns

            TITLE_FIG_2 = "PMF"
            # OUT_FIG_2 = f"PMF_last_{N_HILLS_100NS}.png"
            OUT_FIG_2 = f"PMF_last_100ns.png"
        except (ValueError, IndexError):
            print("No se encontró 'time', usando N_LAST=20000 hills por defecto.")
            N_LAST_FALLBACK = 20000
            if N_LAST_FALLBACK > total:
                N_LAST_FALLBACK = total

            START_IDX_SNAPSHOTS = total - N_LAST_FALLBACK

            t_min_cbar = -N_LAST_FALLBACK
            t_max_cbar = 0
            cbar_label = "Hills before end"

            TITLE_FIG_2 = "PMF"
            OUT_FIG_2 = f"PMF_last_{N_LAST_FALLBACK}.png"

            time_ns = np.arange(total)  # fallback ficticio

        # ---- construir F y snapshots ----
        roi_indices = np.where((grid >= ROI_X[0]) & (grid <= ROI_X[1]))
        plot_indices = roi_indices[0] if roi_indices[0].size > 0 else np.arange(len(grid))

        F = np.zeros_like(grid)
        snapshots = []

        for i, (Di, si, hi) in enumerate(zip(D0, sigma, h)):
            F += hi * np.exp(-(grid - Di) ** 2 / (2 * si * si))
            if i >= START_IDX_SNAPSHOTS:
                snapshots.append(F.copy())

        # ---- análisis de FES final ----
        F_final_raw = -F
        min_val_in_roi = F_final_raw[plot_indices].min()
        F_final_norm = F_final_raw - min_val_in_roi

        min_idx_local = F_final_norm[plot_indices].argmin()
        min_idx_global = plot_indices[min_idx_local]
        min_x_coord = grid[min_idx_global]
        min_y_coord = F_final_norm[min_idx_global]

        grid_roi = grid[plot_indices]
        fes_roi = F_final_norm[plot_indices]
        dF_roi = np.gradient(fes_roi, grid_roi[1] - grid_roi[0])

        plateau_start_x_coord = None
        plateau_start_y_coord = None

        search_range_after_min = np.arange(min_idx_local, len(dF_roi))
        if search_range_after_min.size > 0:
            dF_after_min = dF_roi[search_range_after_min]
            positive_slopes_after_min_idx = np.where(dF_after_min > 0)[0]

            if positive_slopes_after_min_idx.size > 0:
                inflection_idx_local_in_range = positive_slopes_after_min_idx[
                    dF_after_min[positive_slopes_after_min_idx].argmax()
                ]
                inflection_idx_local_roi = search_range_after_min[inflection_idx_local_in_range]
                max_slope = dF_roi[inflection_idx_local_roi]

                threshold_slope = max_slope * 0.05
                search_range_for_plateau = np.arange(inflection_idx_local_roi, len(dF_roi))
                dF_in_plateau_range = dF_roi[search_range_for_plateau]
                plateau_start_local_indices = np.where(dF_in_plateau_range < threshold_slope)[0]

                if plateau_start_local_indices.size > 0:
                    plateau_start_idx_local_in_range = plateau_start_local_indices[0]
                    plateau_start_idx_local_roi = search_range_for_plateau[plateau_start_idx_local_in_range]
                    plateau_start_global_idx = plot_indices[plateau_start_idx_local_roi]

                    plateau_start_x_coord = grid[plateau_start_global_idx]
                    plateau_start_y_coord = F_final_norm[plateau_start_global_idx]

        print(f"Mínimo encontrado en {D} = {min_x_coord:.2f} (E = {min_y_coord:.1f})")
        if plateau_start_x_coord is None or plateau_start_y_coord is None:
            print("No se pudo detectar el inicio del plateau con la lógica de derivadas.")
            print("Se omite el cálculo de ΔG por áreas y las líneas de plateau.\n")
            # Aun así podemos sacar un PMF sencillo sin esas líneas si quieres.
        else:
            print(f"Inicio del plateau (pendiente < 5% max) en {D} = "
                f"{plateau_start_x_coord:.2f} (E = {plateau_start_y_coord:.1f})")

        # ---------------- FIGURA PMF.png ----------------

        # Asegurar ROI indices (por seguridad)
        # roi_mask = (grid >= ROI_X[0]) & (grid <= ROI_X[1])
        roi_mask = (grid >= 0.5) & (grid <= 6.5)
        roi_indices = np.where(roi_mask)[0]
        if roi_indices.size == 0:
            roi_indices = np.arange(len(grid))  # fallback raro, pero evita crash

        # Recalcular mínimo y plateau SOLO dentro del ROI (usando la PMF final)
        grid_roi = grid[roi_indices]
        fes_roi = F_final_norm[roi_indices]

        # mínimo en ROI
        min_idx_local = int(np.argmin(fes_roi))
        min_x_coord = float(grid_roi[min_idx_local])
        min_y_coord = float(fes_roi[min_idx_local])

        # derivadas en ROI para detectar plateau
        dF_roi = np.gradient(fes_roi, grid_roi[1] - grid_roi[0])

        plateau_start_x_coord = None
        plateau_start_y_coord = None

        search_range_after_min = np.arange(min_idx_local, len(dF_roi))
        if search_range_after_min.size > 0:
            dF_after_min = dF_roi[search_range_after_min]
            positive_slopes_after_min_idx = np.where(dF_after_min > 0)[0]

            if positive_slopes_after_min_idx.size > 0:
                inflection_idx_local_in_range = positive_slopes_after_min_idx[
                    dF_after_min[positive_slopes_after_min_idx].argmax()
                ]
                inflection_idx_local_roi = search_range_after_min[inflection_idx_local_in_range]
                max_slope = dF_roi[inflection_idx_local_roi]

                threshold_slope = max_slope * 0.05
                search_range_for_plateau = np.arange(inflection_idx_local_roi, len(dF_roi))
                dF_in_plateau_range = dF_roi[search_range_for_plateau]
                plateau_start_local_indices = np.where(dF_in_plateau_range < threshold_slope)[0]

                if plateau_start_local_indices.size > 0:
                    plateau_start_idx_local_in_range = int(plateau_start_local_indices[0])
                    plateau_start_idx_local_roi = int(search_range_for_plateau[plateau_start_idx_local_in_range])

                    plateau_start_x_coord = float(grid_roi[plateau_start_idx_local_roi])
                    plateau_start_y_coord = float(fes_roi[plateau_start_idx_local_roi])

        print(f"Mínimo (en ROI) encontrado en {D} = {min_x_coord:.2f} (E = {min_y_coord:.1f})")
        if plateau_start_x_coord is None or plateau_start_y_coord is None:
            print("No se pudo detectar el inicio del plateau en ROI con la lógica de derivadas.")
        else:
            print(f"Inicio del plateau (en ROI) en {D} = {plateau_start_x_coord:.2f} (E = {plateau_start_y_coord:.1f})")

        fig = plt.figure(figsize=(10, 6))
        gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

        ax = fig.add_subplot(gs[0])
        ax.plot(grid, F_final_norm, color='black', linewidth=2)
        ax.set_xlabel("Distance (nm)")
        ax.set_ylabel("Energy (kJ/mol)")
        ax.set_title("PMF")
        ax.set_xlim(ROI_X[0], ROI_X[1])

        # tu límite fijo (lo mantengo como estaba)
        ax.set_ylim(0, 225)  # 50 o 225

        # --- líneas: ahora garantizadas dentro del ROI ---
        ax.axvline(x=min_x_coord, color='red', linestyle='--', linewidth=1)

        if plateau_start_y_coord is not None:
            ax.axhline(y=plateau_start_y_coord, color='black', linestyle='--', linewidth=1)
        if plateau_start_x_coord is not None:
            ax.axvline(x=plateau_start_x_coord, color='orange', linestyle='--', linewidth=1)
# --- etiquetas tipo "cuadrito" encima de cada línea (como en la figura) ---

        y_top = ax.get_ylim()[1]

        # Mínimo
        ax.annotate(
            f"Min: {min_x_coord:.2f} nm",
            xy=(min_x_coord, y_top),
            xytext=(0, -25),
            textcoords="offset points",
            ha="center",
            va="top",
            color="red",
            fontsize=12,
            fontweight="bold",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                edgecolor=(1, 1, 1, 0.8),
                alpha=0.8
            )
        )

        # Plateau start (vertical naranja)
        if plateau_start_x_coord is not None:
            ax.annotate(
                f"Plateau: {plateau_start_x_coord:.2f} nm",
                xy=(plateau_start_x_coord, y_top),
                xytext=(0, -10),
                textcoords="offset points",
                ha="center",
                va="top",
                color="orange",
                fontsize=12,
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="white",
                    edgecolor=(1, 1, 1, 0.8),
                    alpha=0.8
                )
            )

        # Plateau energy (horizontal)
        if plateau_start_y_coord is not None:
            ax.annotate(
                f"E: {plateau_start_y_coord:.1f} kJ/mol",
                xy=(ROI_X[0], plateau_start_y_coord),
                xytext=(5, 5),
                textcoords="offset points",
                ha="left",
                va="bottom",
                color="black",
                fontsize=11,
                fontweight="bold",
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor="white",
                    edgecolor=(1, 1, 1, 0.8),
                    alpha=0.8
                )
            )

        # ax_leg = fig.add_subplot(gs[1])
        # ax_leg.axis("off")

        # legend_elements = [
        #     Line2D([0], [0], color='red', linestyle='--', lw=2,
        #         label=f"Minimum Distance = {min_x_coord:.2f} nm")
        # ]
        # if plateau_start_y_coord is not None:
        #     legend_elements.append(
        #         Line2D([0], [0], color='black', linestyle='--', lw=2,
        #             label=f"Plateau Energy = {plateau_start_y_coord:.1f} kJ/mol")
        #     )
        # if plateau_start_x_coord is not None:
        #     legend_elements.append(
        #         Line2D([0], [0], color='orange', linestyle='--', lw=2,
        #             label=f"Plateau Start = {plateau_start_x_coord:.2f} nm")
        #     )

        # ax_leg.legend(
        #     handles=legend_elements,
        #     loc='center',
        #     ncol=len(legend_elements),
        #     frameon=False,
        #     fontsize=12
        # )

        fig.tight_layout()
        out_pmf = os.path.join(out_dir, "PMF.png")
        fig.savefig(out_pmf, dpi=600)
        plt.close(fig)
        print(f"Guardado: {out_pmf}")


        # ---------------- FIGURA PMF_last_XXX.png ----------------
        N_IN_SNAPSHOT = len(snapshots)
        if N_IN_SNAPSHOT == 0:
            print("No hay snapshots para la figura de convergencia, se omite PMF_last.")
        else:
            N_STRIDES = min(100, N_IN_SNAPSHOT)
            indices_to_plot = np.linspace(0, N_IN_SNAPSHOT - 1, N_STRIDES, dtype=int)
            cmap_local = cm.get_cmap("Blues")

            # --- ROI mask/indices (por seguridad) ---
            #roi_mask = (grid >= ROI_X[0]) & (grid <= ROI_X[1])
            roi_mask = (grid >= 0.5) & (grid <= 6) #Aqui define el rango para el minimo de x
            roi_indices = np.where(roi_mask)[0]
            if roi_indices.size == 0:
                roi_indices = np.arange(len(grid))  # fallback raro, pero evita crash

            # --- normalizar TODOS los snapshots que se van a dibujar (restando el mínimo en ROI) ---
            all_snaps_norm = []
            for snap_idx in indices_to_plot:
                Fi_raw = -snapshots[snap_idx]
                min_in_roi = Fi_raw[roi_indices].min()
                Fi_norm = Fi_raw - min_in_roi
                all_snaps_norm.append(Fi_norm)

            # límite y global (solo para el set_ylim)
            global_max_fig2 = max(f[roi_indices].max() for f in all_snaps_norm) if all_snaps_norm else 1.0

            # --- calcular mínimo + plateau USANDO EL ÚLTIMO SNAPSHOT DIBUJADO (dentro del ROI) ---
            last_Fi_norm = all_snaps_norm[-1]  # último snapshot que se dibuja
            grid_roi = grid[roi_indices]
            fes_roi = last_Fi_norm[roi_indices]

            # mínimo dentro del ROI (del último snapshot)
            min_idx_local = np.argmin(fes_roi)
            min_x_coord = float(grid_roi[min_idx_local])
            min_y_coord = float(fes_roi[min_idx_local])

            # detectar plateau dentro del ROI (del último snapshot)
            dF_roi = np.gradient(fes_roi, grid_roi[1] - grid_roi[0])

            plateau_start_x_coord = None
            plateau_start_y_coord = None

            search_range_after_min = np.arange(min_idx_local, len(dF_roi))
            if search_range_after_min.size > 0:
                dF_after_min = dF_roi[search_range_after_min]
                positive_slopes_after_min_idx = np.where(dF_after_min > 0)[0]

                if positive_slopes_after_min_idx.size > 0:
                    # punto de máxima pendiente positiva después del mínimo
                    inflection_idx_local_in_range = positive_slopes_after_min_idx[
                        dF_after_min[positive_slopes_after_min_idx].argmax()
                    ]
                    inflection_idx_local_roi = search_range_after_min[inflection_idx_local_in_range]
                    max_slope = dF_roi[inflection_idx_local_roi]

                    threshold_slope = max_slope * 0.05  # 5% de la pendiente máxima
                    search_range_for_plateau = np.arange(inflection_idx_local_roi, len(dF_roi))
                    dF_in_plateau_range = dF_roi[search_range_for_plateau]
                    plateau_start_local_indices = np.where(dF_in_plateau_range < threshold_slope)[0]

                    if plateau_start_local_indices.size > 0:
                        plateau_start_idx_local_in_range = plateau_start_local_indices[0]
                        plateau_start_idx_local_roi = search_range_for_plateau[plateau_start_idx_local_in_range]

                        plateau_start_x_coord = float(grid_roi[plateau_start_idx_local_roi])
                        plateau_start_y_coord = float(fes_roi[plateau_start_idx_local_roi])

            # ----------------- plot -----------------
            fig = plt.figure(figsize=(10, 6))
            gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

            ax = fig.add_subplot(gs[0])

            for i, Fi_norm in enumerate(all_snaps_norm):
                frac = i / (N_STRIDES - 1) if N_STRIDES > 1 else 1.0
                color = cmap_local(frac)
                alpha = 0.2 + 0.8 * frac
                rgba = list(color)
                rgba[-1] = alpha
                ax.plot(grid, Fi_norm, color=rgba, linewidth=1)

            ax.set_xlabel("Distance (nm)")
            ax.set_ylabel("Energy (kJ/mol)")
            ax.set_title(TITLE_FIG_2)
            ax.set_xlim(ROI_X[0], ROI_X[1])

            # Puedes dejar tu límite fijo si lo prefieres:
            ax.set_ylim(0, 225)  # 50 o 225
            # o si prefieres autoset con el último snapshot:
            # ax.set_ylim(bottom=0, top=global_max_fig2 * 1.05)

            # --- líneas (calculadas del último snapshot y dentro del ROI) ---
            ax.axvline(x=min_x_coord, color='r', linestyle='--', linewidth=1.5)
            if plateau_start_y_coord is not None:
                ax.axhline(y=plateau_start_y_coord, color='k', linestyle='--', linewidth=1.5)
            if plateau_start_x_coord is not None:
                ax.axvline(x=plateau_start_x_coord, color='orange', linestyle='--', linewidth=1.5)

            # colorbar (tiempo / hills)
            norm = plt.Normalize(vmin=t_min_cbar, vmax=t_max_cbar)
            sm = cm.ScalarMappable(cmap=cmap_local, norm=norm)
            sm.set_array([])
            fig.colorbar(sm, ax=ax, label=cbar_label)

            # leyenda abajo
            ax_leg = fig.add_subplot(gs[1])
            ax_leg.axis("off")

            legend_elements = [
                Line2D([0], [0], color='red', linestyle='--', lw=2,
                    label=f"Minimum Distance = {min_x_coord:.2f} nm")
            ]
            if plateau_start_y_coord is not None:
                legend_elements.append(
                    Line2D([0], [0], color='black', linestyle='--', lw=2,
                        label=f"Plateau Energy = {plateau_start_y_coord:.1f} kJ/mol")
                )
            if plateau_start_x_coord is not None:
                legend_elements.append(
                    Line2D([0], [0], color='orange', linestyle='--', lw=2,
                        label=f"Plateau Start = {plateau_start_x_coord:.2f} nm")
                )

            fontsize_legend = 12
            ax_leg.legend(
                handles=legend_elements,
                loc='center',
                ncol=len(legend_elements),
                frameon=False,
                fontsize=fontsize_legend
            )

            fig.tight_layout()
            out_last = os.path.join(out_dir, OUT_FIG_2)
            fig.savefig(out_last, dpi=600)
            plt.close(fig)
            print(f"Guardado: {out_last}")

        # -------------- CÁLCULO ΔG POR ÁREAS SOLO SI HAY PLATEAU --------------
        if plateau_start_x_coord is None or plateau_start_y_coord is None:
            print("\nNo se pudo calcular DeltaG por integración, faltan datos del plateau.\n")
            return

        print("\n--- Calculando DeltaG por integración de áreas ---")

        print("\n>>> Caso 1: occupied_start = 0.0 nm")
        K0, DeltaG0 = calculate_deltaG_from_areas(
            grid_x=grid,
            fes=F_final_norm,
            offset_energy=plateau_start_y_coord,
            occupied_start=0.0,
            occupied_end=plateau_start_x_coord,
            total_start=0.0,
            total_end=ROI_X[1],
            out_dir=out_dir
        )

        print(f"\n>>> Caso 2: occupied_start = x_min = {min_x_coord:.3f} nm")
        Kmin, DeltaGmin = calculate_deltaG_from_areas(
            grid_x=grid,
            fes=F_final_norm,
            offset_energy=plateau_start_y_coord,
            occupied_start=min_x_coord,
            occupied_end=plateau_start_x_coord,
            total_start=min_x_coord,
            total_end=ROI_X[1],
            out_dir=out_dir
        )

        print("\n=== Resumen ΔG (por integración de áreas) ===")
        if not np.isnan(DeltaG0):
            print(f"ΔG (occupied_start = 0.0 nm)              = {DeltaG0:.3f} kJ/mol")
        else:
            print("ΔG (occupied_start = 0.0 nm)              = indefinido (problemas numéricos).")

        if not np.isnan(DeltaGmin):
            print(f"ΔG (occupied_start = x_min = {min_x_coord:.3f} nm) = {DeltaGmin:.3f} kJ/mol")
        else:
            print(f"ΔG (occupied_start = x_min = {min_x_coord:.3f} nm) = indefinido (problemas numéricos).")
        print("=============================================\n")

def plot_colvar(colvar_file, out_dir, cv_name=D):
    if not os.path.isfile(colvar_file):
        print(f"⚠ No existe COLVAR: {colvar_file}, no se plotea.")
        return

    print(f"\n--- Plot COLVAR desde '{colvar_file}' ---")

    fields = read_fields(colvar_file)
    data = np.loadtxt(colvar_file)

    # IMPORTANTE: si solo hay una línea de datos, loadtxt devuelve 1D → lo forzamos a 2D
    if data.ndim == 1:
        data = data.reshape(1, -1)

    try:
        idx_time = fields.index("time")
    except ValueError:
        raise RuntimeError("El COLVAR no tiene columna 'time' en #! FIELDS.")

    try:
        idx_cv = fields.index(cv_name)
    except ValueError:
        raise RuntimeError(f"El COLVAR no tiene la columna '{cv_name}' en #! FIELDS.")

    time_ps = data[:, idx_time]
    time_ns = time_ps / 1000.0
    cv = data[:, idx_cv]

    bias = None
    if "metad.bias" in fields:
        idx_bias = fields.index("metad.bias")
        bias = data[:, idx_bias]

    basename = os.path.basename(colvar_file)
    base_noext = os.path.splitext(basename)[0]

    plt.figure(figsize=(8, 6))
    if bias is not None:
        ax1 = plt.gca()
        ax2 = ax1.twinx()

        ln1 = ax1.plot(time_ns, cv, label=cv_name, lw=1.5)
        ln2 = ax2.plot(time_ns, bias, label="metad.bias", lw=1.0, ls="--", alpha=0.7, color="#70C28D")

        ax1.set_xlabel("Time (ns)")
        ax1.set_ylabel(cv_name)
        ax2.set_ylabel("Bias (kJ/mol)")

        ln = ln1 + ln2
        labels = [l.get_label() for l in ln]
        plt.legend(ln, labels, loc="best", framealpha=0.6)
        plt.title(f"COLVAR: {base_noext}")
    else:
        plt.plot(time_ns, cv, lw=1.5)
        plt.xlabel("Time (ns)")
        plt.ylabel(cv_name)
        plt.title(f"COLVAR: {base_noext}")

    plt.tight_layout()
    out_fig = os.path.join(out_dir, f"{base_noext}_plot.png")
    plt.savefig(out_fig, dpi=300)
    plt.close()
    print(f"Guardado plot COLVAR: {out_fig}\n")


# ------------------------- MAIN ------------------------- #
def main():
    if len(sys.argv) < 3:
        print("Uso: python hills_fes.py /ruta/al/HILLS /ruta/salida [--movie] [--limits] [--pmf] [--colvar COLVAR] [--no-hills]")
        sys.exit(1)

    hills_file = sys.argv[1]
    out_dir = sys.argv[2]

    make_movie_flag = False
    use_limits_flag = False
    pmf_flag = False
    colvar_file = None
    no_hills_flag = False  # NUEVO

    # Parseo de flags (permitimos --colvar FICHERO o --colvar=FICHERO)
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        arg = args[i]
        a = arg.lower()

        if a in ("movie", "--movie"):
            make_movie_flag = True
            i += 1
        elif a in ("limits", "--limits"):
            use_limits_flag = True
            i += 1
        elif a in ("pmf", "--pmf"):
            pmf_flag = True
            i += 1
        elif a in ("--no-hills", "no-hills"):
            no_hills_flag = True
            i += 1
        elif a.startswith("--colvar"):
            # puede ser --colvar=FICHERO o --colvar FICHERO
            if "=" in arg:
                colvar_file = arg.split("=", 1)[1]
                if colvar_file == "":
                    print("ERROR: --colvar= necesita un nombre de fichero.")
                    sys.exit(1)
                i += 1
            else:
                if i + 1 >= len(args):
                    print("ERROR: --colvar necesita un nombre de fichero.")
                    sys.exit(1)
                colvar_file = args[i + 1]
                i += 2
        else:
            print(f"Argumento no reconocido: {arg}")
            print("Uso: python hills_fes.py /ruta/al/HILLS /ruta/salida [--movie] [--limits] [--pmf] [--colvar COLVAR] [--no-hills]")
            sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    # Si NO hay HILLS, desactivamos pmf/movie/limits y avisamos
    if no_hills_flag:
        if make_movie_flag or pmf_flag or use_limits_flag:
            print("⚠ Se ha activado --no-hills, así que se ignoran --pmf / --movie / --limits (requieren HILLS).")
        make_movie_flag = False
        pmf_flag = False
        use_limits_flag = False

    # ------------------- BLOQUE HILLS (solo si hay HILLS) ------------------- #
    if not no_hills_flag:
        if not os.path.isfile(hills_file):
            print(f"ERROR: no existe el archivo HILLS: {hills_file}")
            sys.exit(1)

        fields = read_fields(hills_file)
        data = np.loadtxt(hills_file)

        try:
            idx_D = fields.index(D)
            idx_sigma = fields.index(f"sigma_{D}")
            idx_h = fields.index("height")
        except ValueError as e:
            raise RuntimeError(f"Faltan columnas necesarias en HILLS: {e}")

        D0 = data[:, idx_D]
        sigma = data[:, idx_sigma]
        h = data[:, idx_h]

        Dmin, Dmax = D0.min() - 2 * sigma.max(), D0.max() + 2 * sigma.max()
        grid = np.linspace(Dmin, Dmax, 400)

        N_LAST = 2000
        total = len(D0)
        if N_LAST > total:
            N_LAST = total

        F = np.zeros_like(grid)
        snapshots = []

        for i_hill, (Di, si, hi) in enumerate(zip(D0, sigma, h)):
            F += hi * np.exp(-(grid - Di) ** 2 / (2 * si * si))
            if i_hill >= total - N_LAST:
                snapshots.append(F.copy())

        # flip visual según mínimo real
        x_min_real = D0.min()
        flip_x = x_min_real < -2

        if flip_x:
            print(f"El mínimo de {D} es {x_min_real:.3f} (< -2). Se espeja la representación (x → -x).")
        else:
            print(f"El mínimo de {D} es {x_min_real:.3f}. No se espeja la representación.")

        # Figuras FES clásicas
        generate_plots(out_dir, grid, F, snapshots, D0, flip_x, N_LAST, use_limits_flag)

        # PMF extra (plateau, ΔG, etc.) opcional
        if pmf_flag:
            print("\n--- Análisis PMF adicional (--pmf) ---")
            run_pmf_analysis(out_dir, fields, data, D0, sigma, h, grid)

        # Vídeos opcionales
        if make_movie_flag:
            make_movie(hills_file, out_dir, fields, data, D0, sigma, h, flip_x)
            make_movie_og(hills_file, out_dir, fields, data, D0, sigma, h, flip_x)
    else:
        print("Modo --no-hills activado: se omiten todos los análisis basados en HILLS.\n")

    # ------------------- PLOT COLVAR (si se ha pedido) ------------------- #
    if colvar_file is not None:
        plot_colvar(colvar_file, out_dir, cv_name=D)


if __name__ == "__main__":
    main()

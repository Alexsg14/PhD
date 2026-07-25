#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script individual para graficar perfiles PMF / FES a partir de un archivo fes.dat o HILLS
replicando exactamente la estética, colores, leyenda y anotaciones del script PMF_subplots.
Soporta cálculo del perfil FES sobre una ventana de tiempo (ej: últimos 100 ns).
"""

import sys
import os
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import MaxNLocator

# ============================================================
# CONFIGURACIÓN ESTÉTICA DE MATPLOTLIB
# ============================================================
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#334155'
plt.rcParams['axes.linewidth'] = 1.8

# Colores característicos del script original
COLOR_CURVE = plt.get_cmap("Blues")(1.0)  # Azul oscuro (#08306A)
COLOR_MIN_X = "#860203"                    # Rojo oscuro (Mínimo)
COLOR_PLATEAU_X = "#2B8092"                # Turquesa (Posición del plateau)
COLOR_PLATEAU_Y = "#959800"                # Verde Oliva (Energía del plateau)

LINE_MAIN_WIDTH = 2.2
ANNOT_FS = 15

def load_fes_dat(file_path):
    """
    Carga un archivo fes.dat de PLUMED (soporta comentarios # y #!).
    Retorna arrays (x, y).
    """
    x_list, y_list = [], []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    dz = float(parts[0])
                    fe = float(parts[1])
                    x_list.append(dz)
                    y_list.append(fe)
                except ValueError:
                    pass

    if len(x_list) == 0:
        raise ValueError(f"El archivo {file_path} no contiene datos numéricos válidos.")

    return np.array(x_list), np.array(y_list)

def compute_fes_from_hills(hills_path, nbins=300, last_ns=None, min_time=None, max_time=None, custom_biasf=None):
    """
    Calcula el perfil FES acumulado desde un archivo HILLS de PLUMED.
    Si se especifica last_ns (ej: 100), calcula el perfil usando únicamente
    las colinas depositadas en los últimos N nanosegundos de simulación.
    """
    field_names = []
    rows = []

    with open(hills_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#!"):
                parts = line.replace("#!", "").strip().split()
                if len(parts) > 1 and parts[0].upper() == "FIELDS":
                    field_names = parts[1:]
                continue
            if line.startswith("#"):
                continue

            tokens = [float(v) for v in line.split() if not np.isnan(float(v))]
            if len(tokens) >= 4:
                rows.append(tokens)

    if len(rows) == 0:
        raise ValueError(f"No se pudieron leer datos numéricos en {hills_path}")

    # Determinar columnas
    field_lower = [f.lower() for f in field_names]
    time_idx = field_lower.index("time") if "time" in field_lower else 0

    cv_idx = 1
    height_idx = 3
    biasf_idx = -1

    for idx, name in enumerate(field_names):
        n = name.lower()
        if idx != time_idx and not n.startswith("sigma") and n not in ["height", "h", "w", "biasf"]:
            cv_idx = idx
            break

    for idx, name in enumerate(field_names):
        n = name.lower()
        if n in ["height", "h", "w"]:
            height_idx = idx
        elif n in ["biasf", "biasfactor"]:
            biasf_idx = idx

    data = np.array(rows)
    times = data[:, time_idx]
    cv_vals = data[:, cv_idx]

    # Identificar columna sigma
    sigma_idx = cv_idx + 1 if cv_idx + 1 < data.shape[1] else 2
    for idx, name in enumerate(field_names):
        if name.lower().startswith("sigma"):
            sigma_idx = idx
            break

    sigmas = data[:, sigma_idx]
    heights = data[:, height_idx]

    t_start = times[0]
    t_end = times[-1]

    # Determinar ventana de tiempo
    if last_ns is not None and last_ns > 0:
        window_ps = last_ns * 1000.0
        calculated_min_time = max(t_start, t_end - window_ps)
    else:
        calculated_min_time = t_start if min_time is None else min_time

    calculated_max_time = t_end if max_time is None else max_time

    # Filtrar colinas dentro de la ventana de tiempo [min_time, max_time]
    time_mask = (times >= calculated_min_time) & (times <= calculated_max_time)
    if not np.any(time_mask):
        time_mask = np.ones_like(times, dtype=bool)

    sub_cv = cv_vals[time_mask]
    sub_sig = sigmas[time_mask]
    sub_h = heights[time_mask]

    # Calcular factor Well-Tempered
    gamma = 1.0
    if custom_biasf is not None and custom_biasf > 1:
        gamma = custom_biasf
    elif biasf_idx != -1 and biasf_idx < data.shape[1]:
        detected_gamma = data[0, biasf_idx]
        if detected_gamma > 1:
            gamma = detected_gamma

    wt_factor = gamma / (gamma - 1.0) if gamma > 1.0 else 1.0

    # Crear grilla
    min_cv_val, max_cv_val = np.min(cv_vals), np.max(cv_vals)
    margin = 4.0 * np.mean(sigmas)
    grid = np.linspace(min_cv_val - margin, max_cv_val + margin, nbins)

    # Sumatoria de Gaussianas
    v_bias = np.zeros_like(grid)
    for c, s, h in zip(sub_cv, sub_sig, sub_h):
        if h == 0 or s == 0:
            continue
        v_bias += h * np.exp(-((grid - c) ** 2) / (2.0 * s * s))

    fes_raw = -wt_factor * v_bias
    print(f"📊 FES calculado para ventana de tiempo: [{calculated_min_time:.1f} ps - {calculated_max_time:.1f} ps] ({np.sum(time_mask)} colinas)")

    return grid, fes_raw

def plot_single_pmf(
    input_path,
    output_png="pmf_single_plot.png",
    system_name="COV",
    badge_label="PAR-I",
    x_min=1.0,
    x_max=7.0,
    y_min=None,
    y_max=None,
    energy_unit="kJ/mol",
    cv_label="D.z",
    last_ns=None
):
    """
    Genera el gráfico PMF / FES individual con la estética idéntica a PMF_subplots.
    Soporta archivos fes.dat o HILLS. Si es HILLS y last_ns está presente, calcula los últimos N ns.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo: {input_path}")

    # Detectar si es un HILLS o un fes.dat
    is_hills_file = False
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        first_lines = [f.readline() for _ in range(5)]
        for line in first_lines:
            if "FIELDS" in line and ("time" in line.lower() or "height" in line.lower()):
                is_hills_file = True
                break

    if is_hills_file:
        x_raw, y_raw = compute_fes_from_hills(input_path, last_ns=last_ns)
    else:
        x_raw, y_raw = load_fes_dat(input_path)

    # Ordenar por coord de reacción
    sort_idx = np.argsort(x_raw)
    x_full, y_full = x_raw[sort_idx], y_raw[sort_idx]

    # Filtrar por el rango de la ROI [x_min, x_max]
    mask = (x_full >= x_min) & (x_full <= x_max)
    if not np.any(mask):
        mask = np.ones_like(x_full, dtype=bool)

    x = x_full[mask]
    y = y_full[mask]

    # 2. Calcular Mínimo y Plateau dentro del rango ROI
    min_idx = np.argmin(y)
    min_x_val = x[min_idx]
    raw_min_y = y[min_idx]

    # Region del plateau: último 15% de los puntos en x
    plat_threshold = x[-1] - 0.15 * (x[-1] - x[0])
    plat_mask = x >= plat_threshold
    plat_x_val = np.mean(x[plat_mask]) if np.any(plat_mask) else x[-1]
    plat_y_val = np.mean(y[plat_mask]) if np.any(plat_mask) else y[-1]

    # Detectar si la curva ya está desplazada al plateau (F(bulk) ≈ 0)
    if abs(plat_y_val) < 5.0 and raw_min_y < -5.0:
        y_shift = y
        min_y_shift = raw_min_y
        plat_y_level = 0.0
    else:
        # Shift energético: F(bulk) = 0
        y_shift = y - plat_y_val
        min_y_shift = raw_min_y - plat_y_val
        plat_y_level = 0.0

    # 3. Determinación Inteligente de Límites de Eje Y
    actual_min_y = np.min(y_shift)
    actual_max_y = np.max(y_shift)

    if y_min is None:
        plot_y_min = min(0.0, actual_min_y) - 0.08 * abs(actual_min_y - actual_max_y or 1)
    else:
        plot_y_min = float(y_min)

    if y_max is None:
        plot_y_max = max(0.0, actual_max_y) + 0.15 * abs(actual_min_y - actual_max_y or 1)
    else:
        plot_y_max = float(y_max)

    y_range = (plot_y_max - plot_y_min) or 1.0

    # 4. Crear figura Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)

    # Sombrear región entre 0 y la curva
    ax.fill_between(
        x,
        min_y_shift,
        plat_y_level,
        color=COLOR_PLATEAU_Y,
        alpha=0.18,
        zorder=0
    )

    # Línea horizontal discontinua de plateau a y = 0
    ax.axhline(plat_y_level, color="black", linestyle="--", linewidth=1.2, alpha=0.8, zorder=1)

    # Línea horizontal punteada en la profundidad del mínimo
    ax.axhline(min_y_shift, color=COLOR_PLATEAU_Y, linestyle=":", linewidth=1.4, alpha=0.9, zorder=1)

    # Línea vertical discontinua de mínimo (Rojo)
    ax.axvline(min_x_val, color=COLOR_MIN_X, linestyle="--", linewidth=1.4, alpha=0.8, zorder=1)

    # Línea vertical discontinua de plateau (Turquesa)
    ax.axvline(plat_x_val, color=COLOR_PLATEAU_X, linestyle="--", linewidth=1.4, alpha=0.8, zorder=1)

    # Curva principal PMF (Azul marino)
    ax.plot(x, y_shift, color=COLOR_CURVE, linewidth=LINE_MAIN_WIDTH, zorder=3)

    # 5. Anotaciones de texto dinámicas sobre las líneas
    txt_bbox = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.85)

    # Anotación posición del Mínimo (Rojo - Parte superior del gráfico)
    ax.text(
        min_x_val, plot_y_max - 0.05 * y_range,
        f"{min_x_val:.2f}",
        color=COLOR_MIN_X, ha="center", va="top",
        fontsize=ANNOT_FS, fontweight="bold", bbox=txt_bbox, zorder=4
    )

    # Anotación posición del Plateau (Turquesa - Parte superior del gráfico)
    ax.text(
        plat_x_val, plot_y_max - 0.15 * y_range,
        f"{plat_x_val:.2f}",
        color=COLOR_PLATEAU_X, ha="center", va="center",
        fontsize=ANNOT_FS, fontweight="bold", bbox=txt_bbox, zorder=4
    )

    # Anotación energía en el mínimo (Verde Oliva - Flotando sobre la línea punteada)
    ax.text(
        x_min + 0.04 * (x_max - x_min), min_y_shift + 0.04 * y_range,
        f"{abs(min_y_shift):.2f}",
        color=COLOR_PLATEAU_Y, ha="left", va="bottom",
        fontsize=ANNOT_FS, fontweight="bold", bbox=txt_bbox, zorder=4
    )

    # 6. Configurar Límites y Ejes
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(plot_y_min, plot_y_max)

    ax.set_xlabel(f"{cv_label} (nm)", fontsize=18, fontweight="bold", labelpad=8)
    ax.set_ylabel(f"Free Energy ({energy_unit})", fontsize=18, fontweight="bold", labelpad=8)

    # Ticks enteros en X
    start_x_tick = int(np.ceil(x_min))
    end_x_tick = int(np.floor(x_max))
    if end_x_tick >= start_x_tick:
        ax.set_xticks(np.arange(start_x_tick, end_x_tick + 1, 1))

    ax.tick_params(axis='both', which='major', labelsize=16, width=1.5, length=6)
    ax.grid(True, linestyle='-', alpha=0.15, color='#cbd5e1')

    # 7. Título Centrado Superior (si no se desactiva)
    if system_name:
        ax.set_title(system_name, fontsize=24, fontweight="bold", y=1.015, pad=0)

    # 8. Insignia / Badge en la esquina superior derecha (si no se desactiva)
    if badge_label:
        badge_box = dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#1e3a8a", linewidth=1.2)
        ax.text(
            0.96, 0.94, badge_label,
            transform=ax.transAxes, color="#1e3a8a", fontsize=15, fontweight="bold",
            ha="right", va="top", bbox=badge_box, zorder=5
        )

    # 9. Leyenda Multicolumna en la parte superior
    legend_elements = [
        plt.Line2D([0], [0], color=COLOR_CURVE, lw=2.5, label='PMF'),
        plt.Line2D([0], [0], color=COLOR_MIN_X, lw=1.6, ls='--', label='Minimum (nm)'),
        plt.Line2D([0], [0], color=COLOR_PLATEAU_X, lw=1.6, ls='--', label='Plateau pos. (nm)'),
        plt.Line2D([0], [0], color=COLOR_PLATEAU_Y, lw=1.6, ls=':', label=f'Plateau energy ({energy_unit})')
    ]
    ax.legend(
        handles=legend_elements,
        loc='lower center',
        bbox_to_anchor=(0.5, 1.15 if system_name else 1.04),
        ncol=4,
        frameon=True,
        facecolor='white',
        edgecolor='#cbd5e1',
        fontsize=13,
        handlelength=2.5
    )

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico guardado exitosamente en: {output_png}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graficador de PMF / FES individual a partir de fes.dat o HILLS")
    parser.add_argument("input_file", help="Ruta al archivo fes.dat o HILLS de PLUMED")
    parser.add_argument("--output", "-o", default="pmf_single_plot.png", help="Nombre del archivo de salida PNG")
    parser.add_argument("--title", "-t", default="", help="Título del sistema (ej: COV, POPC, dejar vacío para sin título)")
    parser.add_argument("--badge", "-b", default="", help="Etiqueta del cuadro superior derecho (dejar vacío para sin badge)")
    parser.add_argument("--xmin", type=float, default=1.0, help="Límite mínimo del eje X")
    parser.add_argument("--xmax", type=float, default=7.0, help="Límite máximo del eje X")
    parser.add_argument("--ymin", type=float, default=None, help="Límite mínimo del eje Y (auto si no se especifica)")
    parser.add_argument("--ymax", type=float, default=None, help="Límite máximo del eje Y (auto si no se especifica)")
    parser.add_argument("--last-ns", type=float, default=None, help="Si se especifica (ej: 100), calcula la FES acumulada en los últimos N nanosegundos del HILLS")

    args = parser.parse_args()

    plot_single_pmf(
        input_path=args.input_file,
        output_png=args.output,
        system_name=args.title,
        badge_label=args.badge,
        x_min=args.xmin,
        x_max=args.xmax,
        y_min=args.ymin,
        y_max=args.ymax,
        last_ns=args.last_ns
    )

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import io
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.font_manager import FontProperties

from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.legend_handler import HandlerTuple
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import Rectangle

# ============================================================
# === SISTEMA DE FUENTES (basado en tu script original) ======
# ============================================================

USE_CUSTOM_FONT = True

def save_individual_plots(summary_df, profiles, FPS):
    FP_TITLE  = FPS["fp_title"]
    FP_AXIS   = FPS["fp_axis"]
    FP_TICKS  = FPS["fp_ticks"]

        # 👇 Fuente más pequeña SOLO para los individuales
    small_legend_fp = FontProperties(
        fname=FPS["fp_legend"].get_file(),
        size=13.5
    )

    for sim_id in SYSTEM_ORDER:
        for membrane in MEMBRANES:

            fig, ax = plt.subplots(1, 1, figsize=(9, 5))

            plot_single_fes(
                ax,
                sim_id,
                membrane,
                summary_df,
                profiles,
                is_right_col=False,
                is_left_col=True,
                is_bottom_row=True,
                FP_TICKS=FP_TICKS,
                # label_x=0.97,   # <--- ajusta estos dos valores a tu gusto
                # label_y=0.95
                label_x=PEPTIDE_LABEL_X,
                label_y=0.13
            )

            # Título
            ax.set_title(TITLE_MAP[membrane], fontproperties=FP_TITLE)

            # Labels globales
            fig.text(0.06, 0.5, r"Free Energy (kJ/mol)",
                     rotation=90, ha="center", va="center",
                     fontproperties=FP_AXIS)

            fig.text(0.54, 0.04, r"Dz (nm)",
                     rotation=0, ha="center", va="center",
                     fontproperties=FP_AXIS)

            # ---- Leyenda igual que en figura grande (subplots) ---
            line_min_energy = Line2D(
                [0], [0],
                color=COLOR_PLATEAU_Y,
                lw=3,
                linestyle=":"
            )
            patch_dg = Patch(
                facecolor=COLOR_PLATEAU_Y,
                alpha=0.25
            )

            legend_elements = [
                Line2D([0], [0], color=CURVE_COLOR, lw=LINE_MAIN_WIDTH),
                Line2D([0], [0], color=COLOR_MIN_X, lw=2, linestyle="--"),
                Line2D([0], [0], color="black", lw=2, linestyle="--"),
                (line_min_energy, patch_dg),
            ]

            labels = [
                "PMF",
                "Minimum position (nm)",
                "Plateau (y=0)",
                "ΔG region",
            ]

            leg = fig.legend(
                handles=legend_elements,
                labels=labels,
                handler_map={tuple: HandlerTuple(ndivide=None)},
                loc="upper center",
                ncol=4,
                bbox_to_anchor=(0.5, 0.98),
                frameon=True,
                fancybox=True,
                borderaxespad=0.2,
                prop=small_legend_fp
            )

            frame = leg.get_frame()
            frame.set_facecolor("white")
            frame.set_alpha(0.2)
            frame.set_edgecolor("#00000057")
            frame.set_linewidth(1.0)

            plt.tight_layout(rect=[0, 0, 1, 0.93])
            plt.subplots_adjust(left=0.15, right=0.95, bottom=0.14, top=0.79)

            filename = f"SHIFT_PLATEAU_INSET/fes_{sim_id}_{membrane}.png"
            filename_alpha = f"SHIFT_PLATEAU_INSET/fes_{sim_id}_{membrane}_transparent.png"
            plt.savefig(filename, dpi=600, transparent=False)
            plt.savefig(filename_alpha, dpi=600, transparent=True)
            plt.close()

def setup_plot_style(use_custom=True,
                     font_main_ttf="../avenir-next-medium.ttf",
                     font_bold_ttf="../avenir-next-demi.ttf"):

    mpl.rcdefaults()

    mpl.rcParams.update({
        "svg.fonttype": "none",
        "axes.titlesize": 14,
        "axes.labelsize": 16,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 16,
    })

    if not use_custom:
        mpl.rcParams.update({
            "font.family": "DejaVu Sans",
            "font.size": 11,
        })
        return {
            "fp_main": None,
            "fp_title": None,
            "fp_legend": None,
            "fp_axis": None,
            "fp_ticks": None,
        }

    import matplotlib.font_manager as fm
    from matplotlib.font_manager import FontProperties

    fm.fontManager.addfont(font_main_ttf)
    fm.fontManager.addfont(font_bold_ttf)

    fp_main   = FontProperties(fname=font_main_ttf, size=20)
    fp_title  = FontProperties(fname=font_main_ttf, size=26)
    fp_legend = FontProperties(fname=font_main_ttf, size=20.5)
    fp_axis   = FontProperties(fname=font_main_ttf, size=24)
    fp_ticks  = FontProperties(fname=font_bold_ttf, size=20)

    mpl.rcParams.update({
        "font.family": fp_main.get_name(),
        "font.size": fp_main.get_size(),
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

def apply_tick_font(ax, fp_ticks):
    if fp_ticks is None:
        return
    for label in ax.get_xticklabels():
        label.set_fontproperties(fp_ticks)
    for label in ax.get_yticklabels():
        label.set_fontproperties(fp_ticks)

# ============================================================
# ================= CONFIGURACIÓN ============================
# ============================================================

FES_CSV_PATH = "fes_complete_data_arreglado.csv"  # fes_complete_data.csv o fes_complete_data_arreglado.csv

FIGSIZE = (14, 18)

SYSTEM_ORDER = ["PAR-I", "5069", "1339", "3627", "2599", "736"]

SYSTEM_LABELS = {
    "PAR-I": "PAR-I",
    "5069": "AP05069",
    "1339": "AP01339",
    "3627": "AP03627",
    "2599": "AP02599",
    "736":  "AP00736"
}

MEMBRANES = ["COV", "POPC"]
TITLE_MAP = {
    "COV": "",
    "POPC": ""
}

X_MIN, X_MAX = 1.0, 7.0
Y_MIN, Y_MAX = 0.0, 160.0

COLOR_MIN_X     = "#860203"   # rojo
COLOR_PLATEAU_X = "#2B8092"   # naranja
COLOR_PLATEAU_Y = "#959800"   # verde

# curva: azul fijo = el más oscuro del cmap Blues
CMAP = plt.get_cmap("Blues")
CURVE_COLOR = CMAP(1.0)
LINE_MAIN_WIDTH = 2.2

# tamaño de letra de las anotaciones (±)
ANNOT_FS = 16

# etiqueta del péptido (sim_id) en columna izq
PEPTIDE_LABEL_FS = 18
PEPTIDE_LABEL_X = 0.97   # coords del eje (0..1), alineada a la derecha
PEPTIDE_LABEL_Y = 0.18

# ============================================================
# ================= LECTOR DEL CSV ÚNICO =====================
# ============================================================

def load_fes_big_csv(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    # --- summary block ---
    header_idx = None
    blank_after = None
    for i, line in enumerate(lines):
        if line.startswith("sim_id,system"):
            header_idx = i
            continue
        if header_idx is not None and i > header_idx and line.strip() == "":
            blank_after = i
            break
    if header_idx is None or blank_after is None:
        raise ValueError("No pude localizar el bloque de resumen (sim_id,system,...) en el CSV.")

    summary_csv = "\n".join(lines[header_idx:blank_after])
    summary_df = pd.read_csv(io.StringIO(summary_csv))
    summary_df["sim_id"] = summary_df["sim_id"].astype(str)
    summary_df["system"] = summary_df["system"].astype(str)

    # --- profiles sections ---
    profiles = {}
    section_re = re.compile(r"##\s*(.+?)\s*-\s*(COV|POPC)\s*##")

    i = 0
    while i < len(lines):
        m = section_re.match(lines[i])
        if not m:
            i += 1
            continue

        sim = m.group(1).strip()
        mem = m.group(2).strip()

        i += 1
        if i >= len(lines) or not lines[i].startswith("Dz_nm"):
            raise ValueError(f"Sección {sim}-{mem} no tiene header Dz_nm,FreeEnergy_kJ_mol donde esperaba.")
        i += 1

        data = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("##"):
            parts = lines[i].split(",")
            if len(parts) >= 2:
                try:
                    dz = float(parts[0])
                    fe = float(parts[1])
                    data.append((dz, fe))
                except ValueError:
                    pass
            i += 1

        profiles[(sim, mem)] = pd.DataFrame(data, columns=["Dz_nm", "FreeEnergy_kJ_mol"])

    return summary_df, profiles

# ============================================================
# ================= PLOT UTILITIES ===========================
# ============================================================

def format_pm(mean, std, decimals=2):
    return f"{mean:.{decimals}f}\u00B1{std:.{decimals}f}"

def plot_single_fes(ax, sim_id, membrane, summary_df, profiles,
                    *,
                    is_right_col=False,
                    is_bottom_row=False,
                    is_left_col=False,
                    FP_TICKS=None,
                    x_min=X_MIN, x_max=X_MAX,
                    y_min=Y_MIN, y_max=Y_MAX,
                    label_x=PEPTIDE_LABEL_X,
                    label_y=PEPTIDE_LABEL_Y
):

    key = (str(sim_id), str(membrane))
    if key not in profiles:
        ax.text(0.5, 0.5, f"Missing {sim_id}-{membrane}", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return

    df = profiles[key].copy().sort_values("Dz_nm")
    df = df[(df["Dz_nm"] >= x_min) & (df["Dz_nm"] <= x_max)]

    x = df["Dz_nm"].to_numpy()
    y = df["FreeEnergy_kJ_mol"].to_numpy()

    row = summary_df[(summary_df["sim_id"] == str(sim_id)) & (summary_df["system"] == str(membrane))]
    if len(row) == 1:
        r = row.iloc[0]
        min_x_mean, min_x_std = float(r["min_x_mean"]), float(r["min_x_std"])
        plat_x_mean, plat_x_std = float(r["plateau_x_mean"]), float(r["plateau_x_std"])
        plat_y_mean, plat_y_std = float(r["plateau_y_mean"]), float(r["plateau_y_std"])

        # >>> NUEVO: shift energético (plateau a 0)
        y_shift = y - plat_y_mean
        min_y_shift = -plat_y_mean

        # === Inset (zoom) alrededor del mínimo: x en [min_x_mean-1, min_x_mean+1], y en [-20, 20]
        y_plot = y_shift
        x_center_inset = min_x_mean

        # Sombrear región entre 0 y la curva donde esté por debajo de 0
        ax.fill_between(
            x,
            min_y_shift,
            0,
            #where=(y_shift < 0),
            # interpolate=True,
            color=COLOR_PLATEAU_Y,
            alpha=0.17,
            zorder=0
        )



        # líneas verticales igual
        ax.axvline(min_x_mean, color=COLOR_MIN_X, linestyle="--", linewidth=1.2, alpha=0.7)
        ax.axvline(plat_x_mean, color=COLOR_PLATEAU_X, linestyle="--", linewidth=1.2, alpha=0.7)

        # >>> NUEVO: plateau horizontal en y=0
        ax.axhline(0.0, color="black", linestyle="--", linewidth=1, alpha=0.8)

        # >>> NUEVO: línea horizontal en el mínimo con valor = -plat_y_mean
        
        ax.axhline(min_y_shift, color=COLOR_PLATEAU_Y, linestyle=":", linewidth=1.3, alpha=0.8)
        
        # curva
        ax.plot(x, y_shift, color=CURVE_COLOR, linewidth=LINE_MAIN_WIDTH)
        
        # anotaciones
        txt_bbox = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.75)

        ax.text(min_x_mean, y_max * 0.97,
                format_pm(min_x_mean, min_x_std, 2),
                color=COLOR_MIN_X, ha="center", va="top",
                fontsize=ANNOT_FS, bbox=txt_bbox)

        ax.text(plat_x_mean, y_max * 0.89,
                format_pm(plat_x_mean, plat_x_std, 2),
                color=COLOR_PLATEAU_X, ha="center", va="center",
                fontsize=ANNOT_FS, bbox=txt_bbox)

        # >>> NUEVO: etiqueta en el mínimo con el plateau cambiado de signo
        ax.text(x_min + 0.05 * (x_max - x_min), min_y_shift - 38,
                format_pm(min_y_shift, plat_y_std, 2),   # mean=-plat_y_mean, std=plat_y_std
                color=COLOR_PLATEAU_Y, ha="left", va="bottom",
                fontsize=ANNOT_FS, bbox=txt_bbox)

    else:
        # si no hay fila resumen, plotea sin shift como antes
        ax.plot(x, y, color=CURVE_COLOR, linewidth=LINE_MAIN_WIDTH)

        y_plot = y
        # si no hay resumen, usa el mínimo de la curva como centro del inset
        try:
            x_center_inset = float(x[int(np.nanargmin(y_plot))])
        except Exception:
            x_center_inset = float(x[0]) if len(x) else x_min

    
    # --- Inset: zoom en la región del mínimo (x: min±1, y: [-20, 20]) ---
    try:
        x1_inset, x2_inset = x_center_inset - 1.0, x_center_inset + 1.0
        y1_inset = float(np.nanmin(y_plot)-10)
        y2_inset = 20.0
        if y1_inset >= y2_inset:
            # Evitar límites invertidos si toda la curva está por encima de 20
            y2_inset = y1_inset + 1e-3

        # Colocar a la derecha dentro del área de ploteo (aprox. desde x~4.5 en adelante)
        if (x_max - x_min) != 0:
            xfrac_45 = (5 - x_min) / (x_max - x_min)
        else:
            xfrac_45 = 0.60

        inset_w, inset_h = 0.34, 0.34
        inset_left = min(max(xfrac_45, 0.60), 1.0 - inset_w - 0.02)
        inset_bottom = 0.50  # zona superior derecha

        axins = ax.inset_axes([inset_left, inset_bottom, inset_w, inset_h], transform=ax.transAxes)

        axins.plot(x, y_plot, color=CURVE_COLOR, linewidth=max(LINE_MAIN_WIDTH * 0.9, 1.0))

        # Referencias visuales coherentes con el plot principal cuando hay shift
        if len(row) == 1:
            axins.axhline(0.0, color="black", linestyle="--", linewidth=0.8, alpha=0.8)
            axins.axvline(x_center_inset, color=COLOR_MIN_X, linestyle="--", linewidth=0.9, alpha=0.7)

        axins.set_xlim(x1_inset, x2_inset)
        axins.set_ylim(y1_inset, y2_inset)
        axins.grid(True, alpha=0.20)

        # Ticks pequeños y pocos
        axins.xaxis.set_major_locator(MaxNLocator(nbins=3))
        axins.yaxis.set_major_locator(MaxNLocator(nbins=3))
        axins.tick_params(axis="both", which="major",
                          labelsize=max(7, int(ANNOT_FS * 0.75)))

        # Marco + líneas de conexión (si está disponible en tu versión de Matplotlib)
        try:
            rect = Rectangle(
                (x1_inset, y1_inset),
                x2_inset - x1_inset,
                y2_inset - y1_inset,
                linewidth=1,
                edgecolor="black",
                facecolor="none",
                alpha=0.6
            )
            ax.add_patch(rect)
        except Exception:
            pass
    except Exception:
        pass

# etiqueta sim_id SOLO en columna izquierda, alineada a la derecha
    if is_left_col:
        display_label = SYSTEM_LABELS.get(str(sim_id), str(sim_id))
        ax.text(
            label_x, label_y, display_label,
            transform=ax.transAxes,
            ha="right", va="top",
            fontsize=PEPTIDE_LABEL_FS,
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                edgecolor="#15347CA1",
                alpha=0.8
            )
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(-95, 160)#y_max)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5), )
    ax.grid(True, alpha=0.25)

    # ocultar y ticks/labels en columna derecha
    if is_right_col:
        ax.tick_params(axis="y", left=False, labelleft=False)
    else:
        apply_tick_font(ax, FP_TICKS)

    # solo x labels abajo
    if is_bottom_row:
        apply_tick_font(ax, FP_TICKS)
    else:
        ax.tick_params(axis="x", bottom=True, labelbottom=False, direction="out")

# ============================================================
# ========================= MAIN =============================
# ============================================================

def main():
    FPS = setup_plot_style(USE_CUSTOM_FONT)
    FP_TITLE = FPS["fp_title"]
    FP_AXIS  = FPS["fp_axis"]
    FP_TICKS = FPS["fp_ticks"]

    summary_df, profiles = load_fes_big_csv(FES_CSV_PATH)

    fig, axes = plt.subplots(len(SYSTEM_ORDER), 2, figsize=FIGSIZE, sharex=True, sharey=True)

    for i, sim_id in enumerate(SYSTEM_ORDER):
        for j, membrane in enumerate(MEMBRANES):
            ax = axes[i, j]

            plot_single_fes(
                ax,
                sim_id,
                membrane,
                summary_df,
                profiles,
                is_right_col=(j == 1),
                is_left_col=(j == 0),
                is_bottom_row=(i == len(SYSTEM_ORDER) - 1),
                FP_TICKS=FP_TICKS,
            )

            # if i == 0:
            #     ax.set_title(TITLE_MAP[membrane], fontproperties=FP_TITLE)

    # etiquetas globales
    fig.text(0.04, 0.5, r"Free Energy (kJ/mol)",
             rotation=90, ha="center", va="center", fontproperties=FP_AXIS)
    fig.text(0.53, 0.03, r"Dz (nm)",
             rotation=0, ha="center", va="center", fontproperties=FP_AXIS)

    # ============================================================
    # =================== LEYENDA GLOBAL =========================
    # ============================================================
    line_min_energy = Line2D(
        [0], [0],
        color=COLOR_PLATEAU_Y,
        lw=3,
        linestyle=":"
    )
    patch_dg = Patch(
        facecolor=COLOR_PLATEAU_Y,
        alpha=0.25
    )    

    legend_elements = [
        Line2D([0], [0], color=CURVE_COLOR, lw=LINE_MAIN_WIDTH),#, label="PMF"),
        Line2D([0], [0], color=COLOR_MIN_X, lw=2, linestyle="--"),# label=f"Minimum (nm)"),
        Line2D([0], [0], color=COLOR_PLATEAU_X, lw=2, linestyle="--", label=f"Plateau pos. (nm)"),
        Line2D([0], [0], color='black', lw=2, linestyle="--"),# label=f"Plateau energy (kJ/mol)"),
        (line_min_energy, patch_dg)
    ]

    labels = [
        "PMF",
        "Minimum position (nm)",
        "Plateau position (nm)",
        "Plateau (y=0)",
        f"ΔG region\n (kJ/mol)"
    ]

    leg = fig.legend(
        handles=legend_elements,
        labels=labels,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 0.99),
        frameon=True,
        fancybox=True,
        borderaxespad=0.2,
        prop=FPS["fp_legend"]
    )

    # Estilo de la caja de la leyenda (fondo blanco + borde tenue)
    frame = leg.get_frame()
    frame.set_facecolor("white")
    frame.set_alpha(0.2)
    frame.set_edgecolor("#00000057")
    frame.set_linewidth(1.0)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.subplots_adjust(hspace=0.15, left=0.12, right=0.93, bottom=0.07, top=0.92)

    plt.savefig("SHIFT_PLATEAU_INSET/fes_6x2_no_cbar_arreglado_SHIFT_PLATEAU.png", dpi=600, transparent=False)
    plt.savefig("SHIFT_PLATEAU_INSET/fes_6x2_no_cbar_transparent_arreglado_SHIFT_PLATEAU.png", dpi=600, transparent=True)
    plt.close()

    save_individual_plots(summary_df, profiles, FPS)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helical wheel estilo HeliQuest con vector de momento hidrofóbico.

Modificaciones:
- Flecha de μH con orientación física.
- Secuencias permitidas hasta 40 aa.

Modifications made Alejandro Seco Gonzalez, 2025
"""

import argparse
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as col
import numpy as np

try:
    from .hydrophobic_moment import assign_hydrophobicity
except ImportError:
    from hydrophobic_moment import assign_hydrophobicity


cmap = plt.get_cmap('gist_gray')
custom = col.LinearSegmentedColormap.from_list("custom", ["black", "grey", "silver"])


def get_seq2hw_hworder():
    """
    Provides the positions and the order of the residue ids
    along the helical wheels for first and second round.
    """
    seq2hw = {
        'first_round': {
            1: 1,
            12: 2,
            5: 3,
            16: 4,
            9: 5,
            2: 6,
            13: 7,
            6: 8,
            17: 9,
            10: 10,
            3: 11,
            14: 12,
            7: 13,
            18: 14,
            11: 15,
            4: 16,
            15: 17,
            8: 18,
        },
        'second_round': {
            19: 19,
            30: 20,
            23: 21,
            34: 22,
            27: 23,
            20: 24,
            31: 25,
            24: 26,
            35: 27,
            28: 28,
            21: 29,
            32: 30,
            25: 31,
            36: 32,
            29: 33,
            22: 34,
            33: 35,
            26: 36,
        },
        'third_round': {
            37: 37,
            48: 38,
            41: 39,
            52: 40,
            45: 41,
            38: 42,
            49: 43,
            42: 44,
            53: 45,
            46: 46,
            39: 47,
            50: 48,
            43: 49,
            54: 50,
            47: 51,
            40: 52,
            51: 53,
            44: 54,
            55: 55,
        },
    }
    hworder = [1, 6, 11, 16, 3, 8, 13, 18, 5, 10, 15, 2, 7, 12, 17, 4, 9, 14]
    return seq2hw, hworder


def get_residue_colors():
    """
    Colores estilo HeliQuest.
    """
    residue_colors = {
        "A": "lawngreen",
        "C": "gold",
        "D": "tomato",
        "E": "tomato",
        "F": "lawngreen",
        "G": "lawngreen",
        "H": "steelblue",
        "I": "lawngreen",
        "K": "steelblue",
        "L": "lawngreen",
        "M": "lawngreen",
        "N": "gold",
        "P": "lawngreen",
        "Q": "gold",
        "R": "steelblue",
        "S": "gold",
        "T": "gold",
        "V": "lawngreen",
        "W": "lawngreen",
        "Y": "lawngreen",
        "X": "white",
    }
    return residue_colors


def test_residue_colors(residue_colors, sequence):
    """
    Comprueba que la secuencia solo use los 20 aa estándar o X.
    """
    residues = residue_colors.keys()
    bad = [r for r in sequence if r not in residues]
    if not bad:
        return True
    msg = "No color is specified for residue(s) {}.".format(" & ".join(set(bad)))
    raise RuntimeError(msg)


def test_sequence_length(sequence):
    """
    Comprueba que la longitud de la secuencia no supere 40 aa.
    """
    if len(sequence) <= 40:
        return True
    msg = (
        "Please provide a sequence with a maximum of 40 residues. "
        f"The provided sequence length is {len(sequence)}."
    )
    raise RuntimeError(msg)


def visualize_HW(sequence, fn_hw="hw.png", legend=True):
    """
    Visualiza la helical wheel y dibuja el vector de momento hidrofóbico.
    """
    sequence = sequence.strip().upper()
    seq2hw, hworder = get_seq2hw_hworder()
    residue_colors = get_residue_colors()
    test_residue_colors(residue_colors, sequence)
    test_sequence_length(sequence)

    fig = plt.figure(figsize=[10, 10])
    ax = fig.add_subplot(111)

    # Genera posiciones (3 anillos, 18 posiciones cada uno)
    positions = []
    angle = (2.0 * np.pi) / 18.0
    # NOTA: Aquí defines x=sin(a), y=cos(a). Sistema horario desde el Norte.
    for a in np.arange(0.0, 2 * np.pi, angle):
        positions.append([np.sin(a) * 10.0, np.cos(a) * 10.0])
    for a in np.arange(0.0, 2 * np.pi, angle):
        positions.append([np.sin(a) * 13.2, np.cos(a) * 13.2])
    for a in np.arange(0.0, 2 * np.pi, angle):
        positions.append([np.sin(a) * 16.2, np.cos(a) * 16.2])

    # Líneas de conexión
    hw_lines = []
    for residue_position in hworder:
        position = positions[residue_position - 1]
        hw_lines.append([position[0], position[1]])

    alphas = len(sequence)
    for i in range(len(hw_lines) - 1):
        hw_line = np.array([hw_lines[i], hw_lines[i + 1]])
        if i < np.min([len(sequence) - 1, 18]):
            line_color = custom(i / (len(hw_lines) - 1))
            ax.plot(
                hw_line[:, 0],
                hw_line[:, 1],
                color=line_color,
                zorder=alphas - i,
                linewidth=3,
            )

    # Círculos y letras
    for resid, residue in enumerate(sequence, start=1):
        if resid <= 18:
            seq2hw_part = seq2hw["first_round"]
        elif 18 < resid < 37:
            seq2hw_part = seq2hw["second_round"]
        else:
            seq2hw_part = seq2hw["third_round"]

        position = positions[seq2hw_part[resid] - 1]
        circle = plt.Circle(
            (position[0], position[1]),
            radius=1.4,
            color=residue_colors[residue],
            alpha=1,
            zorder=2 * alphas,
        )
        ax.add_patch(circle)

        ax.annotate(
            residue,
            xy=(position[0], position[1] + 0.15),
            fontsize=30,
            ha="center", 
            va="center",
            zorder=2 * alphas,
        )
        ax.annotate(
            resid,
            xy=(position[0], position[1] - 0.9),
            fontsize=12,
            ha="center",
            va="center",
            zorder=2 * alphas,
        )

    # ---------------------- Momento hidrofóbico (CORREGIDO) --------------------------
    try:
        # 1) Hidrofobicidades
        hvalues = assign_hydrophobicity(sequence, scale="Fauchere-Pliska")

        # 2) Componentes del vector
        # Usamos el mismo sistema de coordenadas que el gráfico:
        # X = sin(angle), Y = cos(angle)
        # Esto asegura que la flecha apunte en la dirección visual correcta (Horaria desde Norte)
        
        delta = 100.0
        vec_x, vec_y = 0.0, 0.0
        
        for i, hv in enumerate(hvalues):
            rad_inc = math.radians(i * delta)
            # Proyección directa sobre los ejes visuales
            vec_x += hv * math.sin(rad_inc)
            vec_y += hv * math.cos(rad_inc)

        # Normalizamos por longitud para obtener el momento medio
        mean_vec_x = vec_x / len(hvalues)
        mean_vec_y = vec_y / len(hvalues)
        
        # Magnitud escalar (µH)
        moment = math.sqrt(mean_vec_x**2 + mean_vec_y**2)

        # Escalado visual para la flecha (factor arbitrario para que se vea bien)
        arrow_scale = 8.0 
        
        # Dibujamos usando directamente las componentes calculadas
        ax.arrow(
            0.0,
            0.0,
            mean_vec_x * arrow_scale,
            mean_vec_y * arrow_scale,
            head_width=0.8,
            head_length=1.2,
            fc="black",
            ec="black",
            linewidth=2,
            zorder=2 * alphas + 1,
        )

        ax.text(
            0.0,
            -17.0,
            r"$\mu_H$ = {:.2f}".format(moment),
            ha="center",
            va="center",
            fontsize=16,
        )
    except Exception as e:
        print(f"Error calculating moment: {e}")
        pass

    # Leyenda
    if legend:
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label='Hydrophobic',
                   markerfacecolor='lawngreen', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Polar',
                   markerfacecolor='gold', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Positive',
                   markerfacecolor='steelblue', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Negative',
                   markerfacecolor='tomato', markersize=10),
            Line2D([0], [0], marker='o', color='w', label='Mismatch',
                   markerfacecolor='white', markersize=10)
        ]
        ax.legend(handles=legend_elements,
                  loc='upper right',
                  bbox_to_anchor=(1.3, 1.0),
                  frameon=False)

    plt.axis("scaled")
    plt.axis("off")
    ax.set_xlim(-18, 18)
    ax.set_ylim(-18, 18)

    plt.savefig(fn_hw, dpi=300, bbox_inches="tight")
    plt.tight_layout()
    # plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate helical wheel based on provided sequence."
    )
    parser.add_argument(
        "-s",
        dest="sequence",
        type=str,
        required=True,
        help="Sequence to be visualized in a HW.",
    )
    parser.add_argument(
        "-o",
        dest="fn_hw",
        type=str,
        default="hw.png",
        help="File name of the image.",
    )
    args = parser.parse_args()

    visualize_HW(args.sequence, args.fn_hw)

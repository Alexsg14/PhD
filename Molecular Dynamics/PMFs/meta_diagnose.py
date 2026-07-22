#!/usr/bin/env python3
import sys
import os
import argparse
import numpy as np

# ---------------------------------------------------------
# Utilidades
# ---------------------------------------------------------

def read_fields(filename):
    """
    Lee la línea '#! FIELDS' de un archivo PLUMED (COLVAR, HILLS, etc.)
    y devuelve la lista de nombres de columnas.
    """
    fields = None
    with open(filename) as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                fields = line.split()[2:]
                break
    if fields is None:
        raise RuntimeError(f"No se encontró '#! FIELDS' en {filename}")
    return fields


def load_colvar(colvar_file, cv_name):
    """
    Carga COLVAR, devuelve:
    - time (ps)
    - cv (array)
    - bias (array o None)
    """
    if not os.path.isfile(colvar_file):
        raise FileNotFoundError(f"No existe COLVAR: {colvar_file}")

    fields = read_fields(colvar_file)
    data = np.loadtxt(colvar_file)

    if "time" not in fields:
        raise RuntimeError("El COLVAR no tiene columna 'time' en '#! FIELDS'.")

    if cv_name not in fields:
        raise RuntimeError(f"El COLVAR no tiene la columna '{cv_name}' en '#! FIELDS'.")

    idx_time = fields.index("time")
    idx_cv = fields.index(cv_name)

    time_ps = data[:, idx_time]
    cv = data[:, idx_cv]

    bias = None
    if "metad.bias" in fields:
        idx_bias = fields.index("metad.bias")
        bias = data[:, idx_bias]

    return time_ps, cv, bias


# ---------------------------------------------------------
# Análisis
# ---------------------------------------------------------

def analyze_exploration(time_ps, cv, roi_min, roi_max,
                        lower_wall, upper_wall, wall_margin):
    """
    Analiza la exploración de la CV y calcula varias métricas útiles.
    """

    # -------------------------------------------------------------------------
    # NOTA SOBRE EL TIEMPO TOTAL
    # -------------------------------------------------------------------------
    # Los archivos COLVAR guardan "time" en ps como tiempo ABSOLUTO del sistema.
    #
    # Si la simulación viene de un RESTART=YES, la primera línea del COLVAR
    # NO tiene time = 0, sino el tiempo donde se quedó la simulación previa.
    #
    # Ejemplo:
    #   Primera línea: time = 3020 ps  (3.02 ns)
    #   Última línea:  time = 8000 ps  (8.00 ns)
    #
    # Este script calcula:
    #   tiempo_segmento = time_ns[-1] - time_ns[0]
    #
    # Resultado:
    #   8.00 ns - 3.02 ns = 4.98 ns
    #
    # Esto es *correcto*, porque este cálculo refleja SOLAMENTE la duración del
    # segmento de simulación representado por este COLVAR.
    #
    # Adicionalmente calculamos:
    #   tiempo_absoluto = time_ns[-1]
    #
    # que es el tiempo total acumulado desde el nanosegundo cero de la primera
    # simulación completa.
    # -------------------------------------------------------------------------

    time_ns = time_ps / 1000.0

    # Duración real de este tramo del COLVAR
    total_time_ns = time_ns[-1] - time_ns[0]

    # Tiempo absoluto acumulado (último time)
    abs_time_ns = time_ns[-1]

    # Paso de tiempo promedio
    dt_ns = np.median(np.diff(time_ns)) if len(time_ns) > 1 else np.nan

    cv_min = cv.min()
    cv_max = cv.max()

    # Fracción de frames cerca de los muros
    near_lower = np.abs(cv - lower_wall) < wall_margin
    near_upper = np.abs(cv - upper_wall) < wall_margin
    frac_lower = near_lower.mean()
    frac_upper = near_upper.mean()

    # Exploración dentro del ROI
    mask_roi = (cv >= roi_min) & (cv <= roi_max)
    frac_en_roi = mask_roi.mean()

    # Cobertura de bins dentro del ROI
    n_bins = 40
    if frac_en_roi > 0:
        cv_roi = cv[mask_roi]
        hist, edges = np.histogram(cv_roi, bins=n_bins, range=(roi_min, roi_max))
        cobertura_bins = (hist > 0).mean()
    else:
        cobertura_bins = 0.0

    # Transiciones entre dos regiones del ROI
    mid = 0.5 * (roi_min + roi_max)
    left_region = (cv < mid) & mask_roi
    right_region = (cv >= mid) & mask_roi

    state = np.zeros_like(cv, dtype=int)
    state[left_region] = 1
    state[right_region] = 2

    transitions = np.sum(
        (state[1:] != state[:-1]) &
        ((state[1:] + state[:-1]) == 3)  # 1↔2
    )

    return {
        "time_ns": time_ns,
        "dt_ns": dt_ns,
        "total_time_ns": total_time_ns,
        "abs_time_ns": abs_time_ns,      # ← ESTA CLAVE ES LA NUEVA
        "cv_min": cv_min,
        "cv_max": cv_max,
        "frac_lower_wall": frac_lower,
        "frac_upper_wall": frac_upper,
        "frac_en_roi": frac_en_roi,
        "cobertura_bins_roi": cobertura_bins,
        "transitions_left_right": transitions,
        "roi_min": roi_min,
        "roi_max": roi_max,
        "lower_wall": lower_wall,
        "upper_wall": upper_wall,
        "wall_margin": wall_margin,
    }


def analyze_bias(time_ps, bias):
    """
    Analiza metad.bias vs tiempo:
    - bias final
    - pendiente media global
    - pendiente en último 20% del tiempo
    """
    if bias is None or len(bias) < 2:
        return None

    time_ns = time_ps / 1000.0
    total_time_ns = time_ns[-1] - time_ns[0]
    if total_time_ns <= 0:
        return None

    # Ajuste lineal global
    coeffs_global = np.polyfit(time_ns, bias, 1)
    slope_global = coeffs_global[0]  # kJ/mol por ns

    # Último 20% del tiempo
    t_cut = time_ns[0] + 0.8 * total_time_ns
    mask_last = time_ns >= t_cut
    if mask_last.sum() >= 2:
        coeffs_last = np.polyfit(time_ns[mask_last], bias[mask_last], 1)
        slope_last = coeffs_last[0]
    else:
        slope_last = np.nan

    bias_final = bias[-1]

    return {
        "bias_final": bias_final,
        "slope_global": slope_global,
        "slope_last": slope_last,
        "total_time_ns": total_time_ns,
    }

def suggest_height_adjustment(expl, bias_info):
    """
    Da una recomendación cualitativa sobre si convendría subir, bajar
    o mantener la altura (HEIGHT) de las colinas, basándose en:
      - cobertura del ROI
      - transiciones entre cuencas
      - tiempo cerca de muros
      - crecimiento del metad.bias al final
    """

    cobertura = expl["cobertura_bins_roi"]          # 0–1
    trans = expl["transitions_left_right"]
    frac_wall = max(expl["frac_lower_wall"], expl["frac_upper_wall"])

    # Por si no hay metad.bias (RESTRAINT u otras)
    slope_last = None
    bias_final = None
    if bias_info is not None:
        slope_last = bias_info["slope_last"]
        bias_final = bias_info["bias_final"]

    print("\n--- Sugerencia orientativa sobre HEIGHT ---")

    # 1) Caso claro de HEIGHT demasiado bajo: casi no exploras el ROI,
    #    pocas transiciones y el bias ni crece al final.
    if cobertura < 0.3 and trans < 2 and frac_wall < 0.1 and \
       (slope_last is None or abs(slope_last) < 0.2):
        print("* La exploración en el ROI es pobre y casi no hay transiciones entre cuencas.")
        if slope_last is not None:
            print(f"  Pendiente final del bias baja (≈ {slope_last:.3f} kJ/mol/ns).")
        print("  → Sugerencia: HEIGHT probablemente demasiado bajo.")
        print("    Prueba a aumentarlo moderadamente (por ejemplo +20–50%) "
              "o a combinarlo con una ligera bajada de BIASFACTOR.")
        return

    # 2) Caso claro de HEIGHT demasiado alto: mucho tiempo pegado a muros
    #    y bias muy grande creciendo fuerte.
    if frac_wall > 0.1 and bias_final is not None and bias_final > 300 and \
       slope_last is not None and slope_last > 0.5:
        print("* El sistema pasa bastante tiempo cerca de los muros y el bias total es muy alto.")
        print(f"  Bias final ≈ {bias_final:.1f} kJ/mol, pendiente final ≈ {slope_last:.3f} kJ/mol/ns.")
        print("  → Sugerencia: HEIGHT probablemente demasiado alto.")
        print("    Considera reducir HEIGHT y/o aumentar BIASFACTOR o PACE para templar la metadinámica.")
        return

    # 3) Caso razonable: buena cobertura y transiciones, sin excesivo apego a muros.
    if cobertura >= 0.5 and trans >= 3 and frac_wall < 0.1:
        print("* La cobertura del ROI y el número de transiciones parecen razonables,")
        print("  y no hay señales claras de sesgo excesivo hacia los muros.")
        print("  → Sugerencia: HEIGHT parece razonable. Prioriza alargar el muestreo "
              "antes de cambiarlo.")
        return

    # 4) Caso intermedio/mixto: no se ve un problema dramático, pero
    #    la exploración no es perfecta.
    print("* No hay una señal inequívoca de que HEIGHT sea claramente demasiado alto o demasiado bajo.")
    print("  → Sugerencia: revisa manualmente D.z vs tiempo y metad.bias; si la CV explora poco,")
    print("    prueba a subir ligeramente HEIGHT o bajar un poco BIASFACTOR.")


def print_diagnosis(expl, bias_info):
    print("\n================= DIAGNÓSTICO METAD =================\n")

    print(f"Tiempo en este COLVAR (segmento): {expl['total_time_ns']:.2f} ns "
          f"(dt ≈ {expl['dt_ns']:.4f} ns)")
    print(f"Tiempo absoluto acumulado (último time del COLVAR): {expl['abs_time_ns']:.2f} ns")

    print(f"{'CV min/max:':15s} {expl['cv_min']:.3f}  /  {expl['cv_max']:.3f}")
    print(f"{'ROI (nm):':15s} [{expl['roi_min']:.2f}, {expl['roi_max']:.2f}]")
    print(f"{'Muros:':15s} lower={expl['lower_wall']:.2f}, upper={expl['upper_wall']:.2f}")
    print(f"Fracción de tiempo cerca muro inferior (±{expl['wall_margin']:.2f} nm): "
          f"{100*expl['frac_lower_wall']:.1f}%")
    print(f"Fracción de tiempo cerca muro superior (±{expl['wall_margin']:.2f} nm): "
          f"{100*expl['frac_upper_wall']:.1f}%")

    print(f"\nCobertura del ROI [{expl['roi_min']:.2f}, {expl['roi_max']:.2f}]")
    print(f"  - Fracción de frames dentro del ROI: {100*expl['frac_en_roi']:.1f}%")
    print(f"  - Cobertura de bins (ocupados / total): {100*expl['cobertura_bins_roi']:.1f}%")
    print(f"  - Transiciones izquierda↔derecha dentro del ROI: {expl['transitions_left_right']}")

    print("\n--- Evaluación cualitativa de la exploración ---")

    if expl["cobertura_bins_roi"] < 0.3:
        print("* Exploración POCA: la CV visita menos del 30% de los bins en el ROI.")
        print("  → Sugerencia: subir HEIGHT y/o bajar BIASFACTOR, o alargar la simulación.")
    elif expl["cobertura_bins_roi"] < 0.6:
        print("* Exploración MODERADA: la CV cubre parte del ROI, pero no todo.")
        print("  → Sugerencia: quizá subir ligero HEIGHT o alargar el tiempo WT.")
    else:
        print("* Exploración BUENA: la CV cubre bien el ROI.")

    if expl["transitions_left_right"] < 2:
        print("* Pocas transiciones entre cuencas (izquierda/derecha en ROI).")
        print("  → Podría faltar sampling entre estados; revisa barreras en FES.")
    elif expl["transitions_left_right"] < 6:
        print("* Número razonable de transiciones entre cuencas.")
    else:
        print("* Muchas transiciones entre cuencas: buen intercambio entre estados.")

    if expl["frac_lower_wall"] > 0.1 or expl["frac_upper_wall"] > 0.1:
        print("* OJO: más del 10% del tiempo se pasa cerca de un muro.")
        print("  → Sesgo fuerte hacia el borde del rango; revisa HEIGHT/BIASFACTOR y posición de muros.")

    print("\n--- Análisis de metad.bias ---")
    if bias_info is None:
        print("No hay columna 'metad.bias' o datos insuficientes para analizar bias.")
    else:
        print(f"Bias final: {bias_info['bias_final']:.1f} kJ/mol")
        print(f"Pendiente media global (d bias / d t): {bias_info['slope_global']:.3f} kJ/mol/ns")
        print(f"Pendiente en último 20% del tiempo: {bias_info['slope_last']:.3f} kJ/mol/ns")

        if abs(bias_info["slope_last"]) < 0.5:
            print("* Bias casi plano en el tramo final → posible indicio de convergencia WT en esa región.")
        else:
            print("* Bias sigue creciendo de forma apreciable en el tramo final.")
            print("  → Aún se está rellenando la FES; alargar simulación o revisar parámetros.")

        if bias_info["bias_final"] > 300:
            print("* Bias total muy alto (>300 kJ/mol).")
            print("  → Podría indicar hills demasiado altos o sampling muy amplio (revisar FES).")

    print("\n================= FIN DEL DIAGNÓSTICO =================\n")

        # Recomendación extra sobre HEIGHT
    suggest_height_adjustment(expl, bias_info)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Diagnóstico automático de una simulación metadinámica a partir de un COLVAR."
    )
    parser.add_argument("colvar", help="Archivo COLVAR de PLUMED")
    parser.add_argument("--cv-name", default="D.z",
                        help="Nombre de la columna de la CV (por defecto: D.z)")
    parser.add_argument("--roi-min", type=float, default=0.0,
                        help="Límite inferior del rango de interés (ROI) de la CV (nm)")
    parser.add_argument("--roi-max", type=float, default=7.0,
                        help="Límite superior del ROI (nm)")
    parser.add_argument("--lower-wall", type=float, default=-1.0,
                        help="Posición del muro inferior (nm)")
    parser.add_argument("--upper-wall", type=float, default=9.0,
                        help="Posición del muro superior (nm)")
    parser.add_argument("--wall-margin", type=float, default=0.2,
                        help="Margen alrededor de los muros para considerar 'cerca del muro' (nm)")

    args = parser.parse_args()

    try:
        time_ps, cv, bias = load_colvar(args.colvar, args.cv_name)
    except Exception as e:
        print(f"ERROR al leer COLVAR: {e}")
        sys.exit(1)

    expl = analyze_exploration(
        time_ps=time_ps,
        cv=cv,
        roi_min=args.roi_min,
        roi_max=args.roi_max,
        lower_wall=args.lower_wall,
        upper_wall=args.upper_wall,
        wall_margin=args.wall_margin,
    )

    bias_info = analyze_bias(time_ps, bias)
    print_diagnosis(expl, bias_info)


if __name__ == "__main__":
    main()


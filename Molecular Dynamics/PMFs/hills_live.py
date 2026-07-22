#!/usr/bin/env python3
import sys
import os
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")   # seguimos con Agg, todo en modo archivo
import matplotlib.pyplot as plt

D = "D.z"   # misma CV que en tu script grande


# ---------- UTILIDADES REUTILIZADAS DEL SCRIPT GRANDE ----------

def read_fields(hills_file):
    fields = None
    with open(hills_file) as f:
        for line in f:
            if line.startswith("#! FIELDS"):
                fields = line.split()[2:]
                break
    if fields is None:
        raise RuntimeError("No se encontró la línea '#! FIELDS' en el archivo")
    return fields


def compute_fes_profile(grid, D0, sigma, h, n_hills=None):
    """
    MISMA convención que tu script:
      - suma de gaussianas
      - signo cambiado
      - mínimo a 0 y máximo también referenciado
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


# ---------- FES EN PNG “EN VIVO” DESDE HILLS ----------

def live_fes_from_hills(hills_file, out_dir, interval=10.0):
    import matplotlib.cm as cm
    
    if not os.path.isfile(hills_file):
        print(f"ERROR: no existe HILLS: {hills_file}")
        return

    os.makedirs(out_dir, exist_ok=True)

    fields = read_fields(hills_file)
    try:
        idx_D = fields.index(D)
        idx_sigma = fields.index(f"sigma_{D}")
        idx_h = fields.index("height")
    except ValueError as e:
        raise RuntimeError(f"Faltan columnas necesarias en HILLS: {e}")

    print(f"[LIVE FES] Guardando PNG en: {out_dir}/fes_live.png\n")

    last_mtime = None
    historial = []      # <=== AQUÍ GUARDAREMOS TODOS LOS FES

    while True:
        try:
            mtime = os.path.getmtime(hills_file)
        except FileNotFoundError:
            print("HILLS ha desaparecido, salgo.")
            break

        if last_mtime is None or mtime != last_mtime:
            last_mtime = mtime

            data = np.loadtxt(hills_file)
            if data.ndim == 1:
                data = data.reshape(1, -1)

            D0 = data[:, idx_D]
            sigma = data[:, idx_sigma]
            h = data[:, idx_h]

            Dmin = D0.min() - 2 * sigma.max()
            Dmax = D0.max() + 2 * sigma.max()
            grid = np.linspace(Dmin, Dmax, 400)

            F = compute_fes_profile(grid, D0, sigma, h)

            # añadir FES actual al historial
            historial.append(F.copy())

            # --- PLOT MULTICOLOR EVOLUTIVO ---
            plt.figure(figsize=(6, 5))
            cmap = cm.get_cmap("Blues", len(historial))

            for i, Fi in enumerate(historial):
                frac = i / max(1, (len(historial)-1))
                color = cmap(frac)
                alpha = 0.2 + 0.8 * frac
                rgba = list(color)
                rgba[-1] = alpha
                plt.plot(grid, Fi, color=rgba, lw=1)

            plt.xlabel(D)
            plt.ylabel("Energy (kJ/mol)")
            plt.title("FES (live, evolución)")
            plt.ylim(F.min() * 1.05, F.max() * 1.05)
            plt.tight_layout()

            out_png = os.path.join(out_dir, "fes_live.png")
            plt.savefig(out_png, dpi=200)
            plt.close()

            print(f"[LIVE FES] Actualizado: {out_png}  (hills={len(D0)}, curvas={len(historial)})")

        time.sleep(interval)



# ---------- COLVAR EN PNG “EN VIVO” ----------

def live_colvar(colvar_file, out_dir, interval=10.0, cv_name=D):
    """
    Cada 'interval' segundos:
      - lee TODO el COLVAR
      - plotea time(ns) vs cv_name
      - guarda out_dir/colvar_live.png
    """
    if not os.path.isfile(colvar_file):
        print(f"ERROR: no existe COLVAR: {colvar_file}")
        return

    os.makedirs(out_dir, exist_ok=True)

    fields = read_fields(colvar_file)
    try:
        idx_time = fields.index("time")
    except ValueError:
        raise RuntimeError("El COLVAR no tiene columna 'time' en #! FIELDS.")
    try:
        idx_cv = fields.index(cv_name)
    except ValueError:
        raise RuntimeError(f"El COLVAR no tiene la columna '{cv_name}' en #! FIELDS.")

    print(f"[LIVE COLVAR] Leyendo COLVAR cada {interval}s: {colvar_file}")
    print(f"[LIVE COLVAR] Guardando PNG en: {out_dir}/colvar_live.png\n")

    last_mtime = None

    while True:
        try:
            mtime = os.path.getmtime(colvar_file)
        except FileNotFoundError:
            print("COLVAR ha desaparecido, salgo.")
            break

        if last_mtime is None or mtime != last_mtime:
            last_mtime = mtime

            data = np.loadtxt(colvar_file)
            if data.ndim == 1:
                data = data.reshape(1, -1)

            time_ps = data[:, idx_time]
            cv = data[:, idx_cv]
            time_ns = time_ps / 1000.0

            plt.figure(figsize=(8, 5))
            plt.plot(time_ns, cv, lw=1)
            plt.xlabel("Time (ns)")
            plt.ylabel(cv_name)
            plt.title("COLVAR (live)")
            plt.tight_layout()

            out_png = os.path.join(out_dir, "colvar_live.png")
            plt.savefig(out_png, dpi=200)
            plt.close()
            print(f"[LIVE COLVAR] Actualizado: {out_png}  (frames = {len(time_ns)})")

        time.sleep(interval)


# ---------- MAIN: INTERFAZ ESTILO TU .sh ----------

def main():
    if len(sys.argv) < 4:
        print("Uso:")
        print("  python hills_live_png.py HILLS OUTDIR --fes [--interval SEG]")
        print("  python hills_live_png.py COLVAR OUTDIR --colvar [--interval SEG]")
        print("")
        print("Ejemplos:")
        print("  python hills_live_png.py /ruta/HILLS /ruta/OUTDIR --fes --interval 30")
        print("  python hills_live_png.py /ruta/COLVAR_WT /ruta/OUTDIR --colvar --interval 10")
        sys.exit(1)

    input_file = sys.argv[1]
    out_dir = sys.argv[2]
    args = sys.argv[3:]

    do_fes = False
    do_colvar = False
    interval = 10.0

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--fes":
            do_fes = True
            i += 1
        elif arg == "--colvar":
            do_colvar = True
            i += 1
        elif arg == "--interval":
            if i + 1 >= len(args):
                print("ERROR: --interval necesita un número.")
                sys.exit(1)
            interval = float(args[i+1])
            i += 2
        else:
            print(f"Argumento no reconocido: {arg}")
            sys.exit(1)

    if do_fes:
        live_fes_from_hills(input_file, out_dir, interval=interval)
    elif do_colvar:
        live_colvar(input_file, out_dir, interval=interval)
    else:
        print("ERROR: debes usar --fes o --colvar.")
        sys.exit(1)


if __name__ == "__main__":
    main()

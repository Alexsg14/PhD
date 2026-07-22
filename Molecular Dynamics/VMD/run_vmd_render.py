#!/usr/bin/env python3
import argparse
import subprocess
import tempfile
import os
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(
        description="Ejecuta VMD en modo texto con un PDB y un script Tcl de estilo, guardando los resultados en una carpeta."
    )
    ap.add_argument("--render-tcl", default="RENDER_VMD.tcl", help="Ruta a RENDER_VMD.tcl")
    ap.add_argument("--pdb", help="Ruta al archivo PDB (p.ej., MIN_FRAME2.pdb)", default="MIN_FRAME2.pdb")
    ap.add_argument("--out-name", help="Nombre base de salida (sin extensión o como lo use tu Tcl)", default="image")
    ap.add_argument("--out-dir", help="Carpeta donde guardar resultados (se crea si no existe)", default="_RENDERS")
    ap.add_argument("--vmd-bin", default="vmd", help="Ruta al binario de VMD (por defecto 'vmd')")
    # Opcionales por si quieres afinarlos desde CLI:
    ap.add_argument("--fps", type=int, default=24, help="Frames por segundo para make_movie (por defecto 24)")
    ap.add_argument("--degrees", type=int, default=360, help="Grados de giro para make_movie (por defecto 360)")
    ap.add_argument("--smooth-a", type=int, default=0, help="Primer parámetro de smooth (por defecto 1), la molecula que se carga")
    ap.add_argument("--smooth-b", type=int, default=0, help="Segundo parámetro de smooth (por defecto 0), la cantidad de smooth")
    ap.add_argument(
    "--do",
    choices=["pic", "movie"],               # <- fuerza a que sea uno de estos
    default="pic",
    help="Qué ejecutar en VMD: 'pic' o 'movie' (por defecto: pic)"
)
    args = ap.parse_args()

    render_tcl = Path(args.render_tcl).expanduser().resolve()
    pdb_path = Path(args.pdb).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_name = args.out_name

    # Validaciones rápidas
    if not render_tcl.is_file():
        raise FileNotFoundError(f"No existe RENDER_TCL: {render_tcl}")
    if not pdb_path.is_file():
        raise FileNotFoundError(f"No existe PDB: {pdb_path}")

    # Crear carpeta de salida
    out_dir.mkdir(parents=True, exist_ok=True)

    # Script Tcl que ejecutará VMD
    # - cd a la carpeta de salida para que todo lo que escriba VMD/tu Tcl quede allí
    # - carga el PDB
    # - source del script de estilo
    # - aplica smooth y make_movie con los parámetros que pasaste
    movie = f'''
# Cambiar a la carpeta de salida
cd "{out_dir}"

# Cargar el PDB (ruta absoluta para evitar problemas)
mol new "{pdb_path}" type pdb waitfor all

# Cargar script de estilo
source "{render_tcl}"

# Aplicar estilo y generar película
style_alex 0
smooth {args.smooth_a} {args.smooth_b}
make_movie {args.fps} {args.degrees} y "{out_name}"

# Salir
quit
'''.lstrip()

    pic = f'''
cd "{out_dir}"

# Cargar el PDB (ruta absoluta para evitar problemas)
mol new "{pdb_path}" type pdb waitfor all

# Cargar script de estilo
source "{render_tcl}"

# Aplicar estilo y generar película
style_alex 0
smooth {args.smooth_a} {args.smooth_b}
pic "{out_name}" 0

# Salir
quit
'''.lstrip()


    scripts = {
        "pic": pic,
        "movie": movie,
    }
    script_text = scripts.get(args.do)
    if script_text is None:
        raise ValueError(f"Opción --do inválida: {args.do}")  # por si acaso




    # Crear archivo temporal Tcl (no se borra automáticamente para que VMD pueda leerlo)
    tf = tempfile.NamedTemporaryFile("w", suffix=".tcl", delete=False)
    try:
        tf.write(script_text)
        tf.flush()
        tcl_path = tf.name
    finally:
        tf.close()

    cmd = [args.vmd_bin, "-dispdev", "text", "-e", tcl_path, "-eofexit"]
    print(">> Ejecutando:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    finally:
        # Limpieza del archivo temporal Tcl
        try:
            os.remove(tcl_path)
            print(f">> Limpieza: eliminado temporal {tcl_path}")
        except Exception as e:
            print(f">> Aviso: no se pudo borrar el temporal {tcl_path}: {e}")

if __name__ == "__main__":
    main()

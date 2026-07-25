import subprocess
import re
import numpy as np
import argparse
import shutil
from Bio.PDB import PDBParser, PDBIO, NeighborSearch
from pathlib import Path
import os

# =====================================
# Script para atribuir B-factors según rankings de energía de acoplamiento (docking)
# y organizar archivos para la visualización en Realidad Virtual (VR).
# =====================================

def main():
    parser = argparse.ArgumentParser(description='Procesa resultados de docking y simulación para VR.')
    
    # Argumentos de Docking (inputs)
    parser.add_argument('--pdbqt_ligs', default='../../Output/all.pdbqt', help='Archivo de entrada con poses (all.pdbqt)')
    parser.add_argument('--ligand_pdbqt', default='../../Output/ligand.pdbqt', help='Estructura del ligando solo (ligand.pdbqt)')
    parser.add_argument('--receptor_in', default='../../Output/receptor_clean.pdb', help='Archivo pdb del receptor original')
    
    # Argumentos de Simulación (inputs)
    parser.add_argument('--sim_xtc', default='../../Output/preview_mol.xtc', help='Trayectoria de la simulación (.xtc)')
    parser.add_argument('--sim_gro', default='../../Output/preview_mol.gro', help='Estructura de la simulación (.gro)')
    
    # Configuración de procesamiento
    parser.add_argument('--dir_models', default='./modelos_pdb', help='Directorio temporal para modelos pdb individuales')
    parser.add_argument('--cutoff', type=float, default=5.0, help='Radio para considerar cercanía entre átomos (Å)')
    
    # Carpeta de salida VR
    parser.add_argument('--vr_folder', default='../../Output/VR', help='Directorio de salida para archivos de VR')

    args = parser.parse_args()

    # Prepara rutas
    vr_path = Path(args.vr_folder)
    vr_path.mkdir(parents=True, exist_ok=True)
    Path(args.dir_models).mkdir(parents=True, exist_ok=True)

    print("🚀 Iniciando procesamiento para VR...")

    # 1. Generar all.pdb (todas las poses del docking)
    print(f"📦 Generando all.pdb desde {args.pdbqt_ligs}...")
    all_pdb_path = vr_path / 'all.pdb'
    subprocess.run(f'obabel -ipdbqt {args.pdbqt_ligs} -opdb -O {all_pdb_path}', shell=True, check=True)

    # 2. Generar ligand.pdb (estructura inicial del ligando sola)
    print(f"🧪 Generando ligand.pdb desde {args.ligand_pdbqt}...")
    subprocess.run(f'obabel -ipdbqt {args.ligand_pdbqt} -opdb -O {vr_path}/ligand.pdb', shell=True, check=True)

    # 3. Procesar Energía y B-factors para receptor.pdb
    print("🔋 Procesando energías y atribuyendo B-factors...")
    with open(all_pdb_path, 'r') as file:
        lines = file.readlines()

    energias = {}
    modelo_actual = []
    indice_modelo_actual = None

    for linea in lines:
        if linea.startswith('MODEL'):
            match = re.match(r'MODEL\s+(\d+)', linea)
            if match:
                if modelo_actual and indice_modelo_actual:
                    archivo_modelo = Path(args.dir_models) / f'modelo_{indice_modelo_actual}.pdb'
                    with open(archivo_modelo, 'w') as f:
                        f.writelines(modelo_actual)
                    modelo_actual = []
                indice_modelo_actual = int(match.group(1))
                modelo_actual.append(linea)
        elif linea.startswith('REMARK VINA RESULT'):
            energia = float(linea.split()[3])
            energias[indice_modelo_actual] = energia
            modelo_actual.append(linea)
        elif linea.startswith('ENDMDL'):
            modelo_actual.append(linea)
            if modelo_actual and indice_modelo_actual:
                archivo_modelo = Path(args.dir_models) / f'modelo_{indice_modelo_actual}.pdb'
                with open(archivo_modelo, 'w') as f:
                    f.writelines(modelo_actual)
                modelo_actual = []
                indice_modelo_actual = None
        elif indice_modelo_actual is not None:
            modelo_actual.append(linea)

    # Ordenar modelos según energía descendente para ranking
    modelos_ordenados = sorted(energias.items(), key=lambda x: x[1], reverse=True)
    modelo_rank = {modelo: rank+1 for rank, (modelo, _) in enumerate(modelos_ordenados)}

    # Asignar B-factors al receptor según cercanía al ligando en cada pose
    parser_pdb = PDBParser(QUIET=True)
    estructura_receptor = parser_pdb.get_structure('receptor', args.receptor_in)
    atomos_receptor = list(estructura_receptor.get_atoms())
    bfactor_receptor_residue = {residuo: 0 for residuo in estructura_receptor.get_residues()}

    for num_modelo, rank in modelo_rank.items():
        modelo_file = Path(args.dir_models) / f'modelo_{num_modelo}.pdb'
        if not modelo_file.exists(): continue
        
        estructura_ligando = parser_pdb.get_structure('lig', str(modelo_file))
        atomos_ligando = list(estructura_ligando.get_atoms())
        busqueda_cercania = NeighborSearch(atomos_ligando)

        for atomo_rec in atomos_receptor:
            cercanos = busqueda_cercania.search(atomo_rec.coord, args.cutoff, level='A')
            if cercanos:
                parent_res = atomo_rec.get_parent()
                if rank > bfactor_receptor_residue[parent_res]:
                    bfactor_receptor_residue[parent_res] = rank

    # Aplicar B-factors por residuo a todos sus átomos
    for residuo, rank in bfactor_receptor_residue.items():
        for atomo in residuo:
            atomo.set_bfactor(float(rank))

    # Guardar receptor.pdb (la proteína sola con b-factors para VR)
    print(f"🏛️ Guardando receptor.pdb en folder VR...")
    io = PDBIO()
    io.set_structure(estructura_receptor)
    io.save(str(vr_path / 'receptor.pdb'))

    # 4. Preparar archivos de Simulación (center.xtc y center.pdb)
    print(f"🏃 Preparando archivos de trayectoria simulación (center)...")
    
    # center.xtc: Copia directa de la trayectoria de simulación
    if Path(args.sim_xtc).exists():
        shutil.copy(args.sim_xtc, vr_path / 'center.xtc')
    else:
        print(f"⚠️ Trayectoria {args.sim_xtc} no encontrada.")

    # center.pdb: Conversión del archivo estructural (.gro) a .pdb
    if Path(args.sim_gro).exists():
        subprocess.run(f'obabel -igro {args.sim_gro} -opdb -O {vr_path}/center.pdb', shell=True, check=True)
    else:
        print(f"⚠️ Estructura {args.sim_gro} no encontrada.")

    print(f"\n✅ Proceso completado con éxito.")
    print(f"📁 Los archivos para VR están listos en: {vr_path.resolve()}")
    print(f"- center.xtc: Trayectoria de simulación")
    print(f"- center.pdb: Estructura de simulación")
    print(f"- receptor.pdb: Proteína inicial con atribución de energía (B-factor)")
    print(f"- ligand.pdb: Ligando original")
    print(f"- all.pdb: Todas las poses de docking")

    # Limpieza temporal
    shutil.rmtree(args.dir_models)

if __name__ == "__main__":
    main()

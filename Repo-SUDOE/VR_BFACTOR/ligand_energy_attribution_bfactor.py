import subprocess
import re
import numpy as np
import argparse
from Bio.PDB import PDBParser, PDBIO, NeighborSearch
from pathlib import Path

# Argumentos desde la terminal
parser = argparse.ArgumentParser(description='Procesa archivos pdbqt para asignar B-factors al receptor.')
parser.add_argument('--pdbqt_ligs', default='all.pdbqt', help='Archivo de entrada en formato pdbqt (ligandos)')
parser.add_argument('--output_pdb', default='all.pdb', help='Archivo temporal pdb de salida generado desde pdbqt')
parser.add_argument('--receptor', default='receptor.pdb', help='Archivo pdb del receptor')
parser.add_argument('--dir_models', default='./modelos_pdb', help='Directorio para modelos pdb individuales')
parser.add_argument('--dir_output', default='./resultado_final', help='Directorio para guardar resultados')
parser.add_argument('--cutoff', type=float, default=5.0, help='Radio para considerar cercanía entre átomos')

args = parser.parse_args()

# Crear directorios
Path(args.dir_models).mkdir(exist_ok=True)
Path(args.dir_output).mkdir(exist_ok=True)

# Paso 1: Convertir pdbqt a pdb
subprocess.run(f'obabel -ipdbqt {args.pdbqt_ligs} -opdb -O {args.output_pdb}', shell=True, check=True)

# Paso 2: Leer archivo pdb y extraer energías
with open(args.output_pdb, 'r') as file:
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

# Ordenar modelos según energía descendente
modelos_ordenados = sorted(energias.items(), key=lambda x: x[1], reverse=True)
modelo_rank = {modelo: rank+1 for rank, (modelo, _) in enumerate(modelos_ordenados)}

# Paso 3: Asignar B-factors según número de modelo descendente
parser_pdb = PDBParser(QUIET=True)
estructura_receptor = parser_pdb.get_structure('receptor', args.receptor)
atomos_receptor = list(estructura_receptor.get_atoms())
bfactor_receptor_atom = {atomo: 0 for atomo in atomos_receptor}
bfactor_receptor_residue = {residuo: 0 for residuo in estructura_receptor.get_residues()}

for num_modelo, rank in modelo_rank.items():
    modelo_file = Path(args.dir_models) / f'modelo_{num_modelo}.pdb'
    estructura_ligando = parser_pdb.get_structure('lig', modelo_file)
    atomos_ligando = list(estructura_ligando.get_atoms())
    busqueda_cercania = NeighborSearch(atomos_ligando)

    for atomo_rec in atomos_receptor:
        cercanos = busqueda_cercania.search(atomo_rec.coord, args.cutoff, level='A')
        if cercanos:
            if rank > bfactor_receptor_atom[atomo_rec]:
                bfactor_receptor_atom[atomo_rec] = rank
                bfactor_receptor_residue[atomo_rec.get_parent()] = rank

# Actualizar B-factors por átomo
for atomo_rec in atomos_receptor:
    atomo_rec.set_bfactor(float(bfactor_receptor_atom[atomo_rec]))

# Guardar resultado por átomo
io = PDBIO()
io.set_structure(estructura_receptor)
io.save(str(Path(args.dir_output) / 'receptor_final_bfactor_atom.pdb'))

# Actualizar B-factors por residuo
for residuo, rank in bfactor_receptor_residue.items():
    for atomo in residuo:
        atomo.set_bfactor(float(rank))

# Guardar resultado por residuo
io.set_structure(estructura_receptor)
io.save(str(Path(args.dir_output) / 'receptor_final_bfactor_residue.pdb'))

print(f"✅ Proceso completado correctamente. Archivos guardados en: {args.dir_output}/receptor_final_bfactor_atom.pdb y {args.dir_output}/receptor_final_bfactor_residue.pdb")

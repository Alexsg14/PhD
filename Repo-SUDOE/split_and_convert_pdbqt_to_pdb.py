import subprocess
from pathlib import Path

# Rutas del archivo original y de los directorios de salida
input_pdbqt = 'all.pdbqt'
output_pdb = 'all.pdb'
output_dir_models_pdb = Path('./modelos_pdb')

# Crear carpeta de modelos individuales
output_dir_models_pdb.mkdir(exist_ok=True)

# Convertir directamente all.pdbqt a all.pdb
subprocess.run(f'obabel -ipdbqt {input_pdbqt} -opdb -O {output_pdb}', shell=True, check=True)

# Ahora, leer all.pdb y dividir en modelos individuales
with open(output_pdb, 'r') as file:
    lines = file.readlines()

modelo_actual = []
idx_modelo = 0
grabando = False

for linea in lines:
    if linea.startswith('MODEL'):
        modelo_actual = [linea]
        grabando = True
        idx_modelo += 1
    elif linea.startswith('ENDMDL'):
        modelo_actual.append(linea)
        grabando = False
        # Guardar modelo individual
        with open(output_dir_models_pdb / f'modelo_{idx_modelo}.pdb', 'w') as out_file:
            out_file.writelines(modelo_actual)
    elif grabando:
        modelo_actual.append(linea)

print(f"Conversión y separación completadas exitosamente.\nArchivos guardados en: {output_dir_models_pdb.resolve()}")

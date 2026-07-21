import os
import matplotlib as mpl
import MDAnalysis as mda
import numpy as np
import matplotlib.pyplot as plt
from MDAnalysis.analysis import distances
from MDAnalysis.lib.distances import distance_array, apply_PBC
import csv
import argparse
from tqdm import tqdm
import pandas as pd

mpl.use('Agg')

# Configurar el parser de argumentos
parser = argparse.ArgumentParser(
    description="Script para análisis y graficado basado en archivos .pdb y .xtc o a partir de CSV"
)
parser.add_argument("-pdb_file", help="Nombre del archivo .pdb")
parser.add_argument("-xtc_file", help="Nombre del archivo .xtc")
parser.add_argument("-skip", help="Número de frames a saltar", type=int, default=10)
parser.add_argument("-folder", help="Nombre de la carpeta de salida", default="Resultados_finales")
parser.add_argument("-plot", action="store_true", help="Solo generar gráficos a partir de CSV, sin leer trayectorias")
parser.add_argument("-csv", help="Nombre de la carpeta de lectura de csv", default="Resultados_finales")
args = parser.parse_args()

path = os.getcwd()
result_dir = os.path.join(path, args.folder)
csv_plot = os.path.join(path, args.csv)
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

window_size = 10

# Si se activa la flag -plot, leer los CSV y generar los gráficos
if args.plot:
    contacts_csv_filename = os.path.join(result_dir, "contactos_totales.csv")
    z_csv_filename = os.path.join(result_dir, "posiciones_z.csv")
    contacts_csv_filename = os.path.join(csv_plot, "contactos_totales.csv")
    z_csv_filename = os.path.join(csv_plot, "posiciones_z.csv")
    if not os.path.exists(contacts_csv_filename) or not os.path.exists(z_csv_filename):
        print("No se encontraron los archivos CSV requeridos en la carpeta especificada.")
        exit(1)
    
    # Leer CSV usando pandas
    contacts_df = pd.read_csv(contacts_csv_filename)
    z_df = pd.read_csv(z_csv_filename)
    
    # Extraer la columna de tiempo
    time_values = contacts_df.iloc[:, 0].values

    # Definir los grupos de contactos a graficar
    grouped_contacts = {
       "Peptides-Water": "peptides_water",
       "Peptides-Mem Heads": "peptides_mem_heads",
       "Peptides-Micelle Heads": "peptides_micelle_heads",
       "Micelle Heads-Mem Heads": "micelle_heads_mem_heads",
       "Peptides-Peptides": "peptides_peptide"
    }
    
    # Graficar cada conjunto de contactos por separado
    for label, col in grouped_contacts.items():
        plt.figure(figsize=(10, 6))
        data = contacts_df[col].values
        smoothed_counts = moving_average(data, window_size)
        plt.plot(time_values[:len(smoothed_counts)], smoothed_counts, label=label, linestyle='-', marker='')
        plt.title(f"{label} Contactos a lo largo de la trayectoria")
        plt.xlabel("Time ($\mu$S)")
        plt.ylabel("Número de contactos")
        plt.ylim(-1, None)
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(result_dir, f"{label.replace(' ', '_').lower()}_smoothed_plot.png"))
    
    # Graficar todos los contactos juntos
    plt.figure(figsize=(10, 6))
    for label, col in grouped_contacts.items():
        data = contacts_df[col].values
        smoothed_counts = moving_average(data, window_size)
        plt.plot(time_values[:len(smoothed_counts)], smoothed_counts, label=label)
    plt.title("Contactos a lo largo de la trayectoria (Todos)")
    plt.xlabel("Time ($\mu$S)")
    plt.ylabel("Número de contactos")
    plt.ylim(-1, None)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(result_dir, "contactos_grupos_smoothed_plot.png"))
    
    # Graficar evolución de posiciones en Z
    time_values = z_df.iloc[:, 0].values
    plt.figure(figsize=(10, 6))
    # Se asume que la primera columna es el tiempo
    for col in z_df.columns[1:]:
        if col == "Membrane_Lower_Heads":
            continue
        data = z_df[col].values
        smoothed_data = moving_average(data, window_size)
        plt.plot(time_values[:len(smoothed_data)], smoothed_data, label=col)
    plt.title("Evolución de la posición en Z")
    plt.xlabel("Time ($\mu$S)")
    plt.ylabel("Posición en Z (Å)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(result_dir, "posiciones_z_plot.png"))
    
    print("Gráficos generados a partir de los archivos CSV.")
    exit(0)

# -------------------------
# Si no se activa -plot, se procesa la trayectoria y se generan CSV y gráficos
# -------------------------

# Verificar que se hayan pasado los archivos pdb y xtc
if not args.pdb_file or not args.xtc_file:
    print("Debe especificar los archivos -pdb_file y -xtc_file")
    exit(1)

topology = os.path.join(path, args.pdb_file)
trajectory = os.path.join(path, args.xtc_file)
u = mda.Universe(topology, trajectory, in_memory=False)
skip = args.skip
total_frames = (u.trajectory.n_frames + skip - 1) // skip

# Desenrollar (unwrap) las coordenadas para cada residuo (Martini-specific)
for ts in u.trajectory[::skip]:
    for res in u.residues:
        res.atoms.positions = apply_PBC(res.atoms.positions, u.dimensions)

# Selecciones de átomos
micelle_tails = u.select_atoms("resname LPA and name C4A")
micelle_heads = u.select_atoms("resname LPA and name PO4")
mem_heads = u.select_atoms("not resname LPA and name PO4")
membrane = u.select_atoms("resname POPC or resname POPS")
water = u.select_atoms("resname W")
peptides = u.select_atoms("protein and name BB")

# Dividir péptidos en cuatro grupos
PEPTIDE_1 = u.select_atoms("protein and name BB and segid A")
PEPTIDE_2 = u.select_atoms("protein and name BB and segid B")
PEPTIDE_3 = u.select_atoms("protein and name BB and segid C")
PEPTIDE_4 = u.select_atoms("protein and name BB and segid D")

# Función para calcular contactos entre péptidos (excluye intra-péptido)
def calcular_contactos_peptido_peptido(peptide_groups, box, cutoff):
    total_contacts = 0
    for i in range(len(peptide_groups)):
        for j in range(i + 1, len(peptide_groups)):
            coords1 = peptide_groups[i].positions
            coords2 = peptide_groups[j].positions
            dmat = distance_array(coords1, coords2, box=box)
            total_contacts += np.sum(dmat < cutoff)
    return total_contacts

cutoff = 6.0

# Preparar listas para almacenar resultados de contactos
contact_types = {
    "lipid_lipid": (micelle_tails, micelle_tails),
    "lipid_water": (micelle_tails, water),
    "peptides_water": (peptides, water),
    "peptides_mem_heads": (peptides, mem_heads),
    "peptides_micelle_heads": (peptides, micelle_heads),
    "micelle_heads_mem_heads": (micelle_heads, mem_heads),
    "peptides_peptide": None  # Se calculará aparte
}
contacts_data = {key: [] for key in contact_types}

# Preparar listas para almacenar posiciones en Z
z_data = {
    "PEPTIDE_1": [], "PEPTIDE_2": [], "PEPTIDE_3": [], "PEPTIDE_4": [],
    "Micelle": [], "Membrane_Center": [],
    "Membrane_Upper_Heads": [], "Membrane_Lower_Heads": []
}
time_values = []

print("Calculando contactos y posiciones en Z para cada frame...")
for ts in tqdm(u.trajectory[::skip], total=total_frames, desc="Procesando frames"):
    dt = u.trajectory.dt
    time = (ts.frame * dt) / 1e6  # Convertir a microsegundos
    time_values.append(time)
    
    # Centrar la membrana en el eje Z
    membrane_com = membrane.center_of_mass()
    shift = u.dimensions[2] / 2 - membrane_com[2]
    u.atoms.positions[:, 2] += shift

    # Calcular contactos para cada tipo definido
    for key, groups in contact_types.items():
        if groups is not None:
            group1, group2 = groups
            coords1, coords2 = group1.positions, group2.positions
            dmat = distance_array(coords1, coords2, box=u.dimensions)
            num_contacts = np.sum(dmat < cutoff)
            contacts_data[key].append(num_contacts)
        else:
            # Calcular contactos entre péptidos
            pep_groups = [PEPTIDE_1, PEPTIDE_2, PEPTIDE_3, PEPTIDE_4]
            pep_pep_contacts = calcular_contactos_peptido_peptido(pep_groups, u.dimensions, cutoff)
            contacts_data[key].append(pep_pep_contacts)
    
    # Cálculo de posiciones en Z (Minimum Image Convention)
    box_z = u.dimensions[2]
    membrane_com_z = membrane.center_of_mass()[2]
    for label, group in zip(
        ["PEPTIDE_1", "PEPTIDE_2", "PEPTIDE_3", "PEPTIDE_4", "Micelle"],
        [PEPTIDE_1, PEPTIDE_2, PEPTIDE_3, PEPTIDE_4, micelle_heads]
    ):
        group_com_z = group.center_of_mass()[2]
        z_diff = group_com_z - membrane_com_z
        z_diff = z_diff - box_z * np.round(z_diff / box_z)
        z_data[label].append(np.abs(z_diff))
    
    # Almacenar datos del centro y cabezas de la membrana
    z_data["Membrane_Center"].append(0.0)
    upper_heads = mem_heads.positions[mem_heads.positions[:, 2] > membrane_com_z, 2]
    lower_heads = mem_heads.positions[mem_heads.positions[:, 2] < membrane_com_z, 2]
    z_data["Membrane_Upper_Heads"].append(np.mean(upper_heads) - membrane_com_z if len(upper_heads) > 0 else 0.0)
    z_data["Membrane_Lower_Heads"].append(np.mean(lower_heads) - membrane_com_z if len(lower_heads) > 0 else 0.0)

# Guardar resultados de contactos en un CSV
csv_filename = os.path.join(result_dir, "contactos_totales.csv")
with open(csv_filename, "w", newline='') as f:
    writer = csv.writer(f)
    header = ["Time (µs)"] + list(contact_types.keys())
    writer.writerow(header)
    for i in range(len(time_values)):
        writer.writerow([time_values[i]] + [contacts_data[key][i] for key in contact_types])

# Guardar posiciones en Z en otro CSV
z_csv_filename = os.path.join(result_dir, "posiciones_z.csv")
with open(z_csv_filename, "w", newline='') as f:
    writer = csv.writer(f)
    header = ["Time (µs)"] + list(z_data.keys())
    writer.writerow(header)
    for i in range(len(time_values)):
        writer.writerow([time_values[i]] + [z_data[key][i] for key in z_data])

print(f"Resultados guardados en {csv_filename} y {z_csv_filename}")

# Generar gráficos
grouped_contacts = {
    "Peptides-Water": "peptides_water",
    "Peptides-Mem Heads": "peptides_mem_heads",
    "Peptides-Micelle Heads": "peptides_micelle_heads",
    "Micelle Heads-Mem Heads": "micelle_heads_mem_heads",
    "Peptides-Peptides": "peptides_peptide"
}

# Graficar cada conjunto de contactos por separado
for label, key in grouped_contacts.items():
    plt.figure(figsize=(10, 6))
    smoothed_counts = moving_average(contacts_data[key], window_size)
    plt.plot(time_values[:len(smoothed_counts)], smoothed_counts, label=label, linestyle='-', marker='')
    plt.title(f"{label} Contactos a lo largo de la trayectoria")
    plt.xlabel("Time ($\mu$S)")
    plt.ylabel("Número de contactos")
    plt.ylim(-1, None)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(result_dir, f"{label.replace(' ', '_').lower()}_smoothed_plot.png"))

# Graficar todos los contactos juntos
plt.figure(figsize=(10, 6))
for label, key in grouped_contacts.items():
    smoothed_counts = moving_average(contacts_data[key], window_size)
    plt.plot(time_values[:len(smoothed_counts)], smoothed_counts, label=label)
plt.title("Contactos a lo largo de la trayectoria (Todos)")
plt.xlabel("Time ($\mu$S)")
plt.ylabel("Número de contactos")
plt.ylim(-1, None)
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(result_dir, "contactos_grupos_smoothed_plot.png"))

# Graficar evolución de posiciones en Z
# Graficar evolución de posiciones en Z
time_values = z_df.iloc[:, 0].values
plt.figure(figsize=(10, 6))
# Se asume que la primera columna es el tiempo
for col in z_df.columns[1:]:
    if col == "Membrane_Lower_Heads":
        continue
    data = z_df[col].values
    smoothed_data = moving_average(data, window_size)
    plt.plot(time_values[:len(smoothed_data)], smoothed_data, label=col)
plt.title("Evolución de la posición en Z")
plt.xlabel("Time ($\mu$S)")
plt.ylabel("Posición en Z (Å)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(result_dir, "posiciones_z_plot.png"))

print("Análisis y graficado completados.")

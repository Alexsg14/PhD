import os
import matplotlib as mpl
import MDAnalysis as mda
import numpy as np
import matplotlib.pyplot as plt
from MDAnalysis.analysis import distances
from MDAnalysis.lib.distances import distance_array, apply_PBC
import csv
import argparse

mpl.use('Agg')

# Configurar el parser de argumentos
parser = argparse.ArgumentParser(description="Especificar archivos .pdb y .xtc")
parser.add_argument("-pdb_file", help="Nombre del archivo .pdb")
parser.add_argument("-xtc_file", help="Nombre del archivo .xtc")

# Leer argumentos
args = parser.parse_args()

path = os.getcwd()
result_dir = os.path.join(path, "Resultados_DeepSeek")
if not os.path.exists(result_dir):
    os.makedirs(result_dir)

topology = os.path.join(path, args.pdb_file) 
trajectory = os.path.join(path, args.xtc_file)
skip = 10
u = mda.Universe(topology, trajectory, in_memory=False)

# Unwrap coordinates for each residue (Martini-specific)
for ts in u.trajectory[::skip]:
    for res in u.residues:
        res.atoms.positions = apply_PBC(res.atoms.positions, u.dimensions)

micelle_tails = u.select_atoms("resname LPA and name C4A")
micelle_heads = u.select_atoms("resname LPA and name PO4")
mem_heads = u.select_atoms("not resname LPA and name PO4")
membrane = u.select_atoms("resname POPC or resname POPS")
water = u.select_atoms("resname W")
peptides = u.select_atoms("protein and name BB")

# Dividir peptides en cuatro grupos
PEPTIDE_1 = u.select_atoms("protein and name BB and segid A")
PEPTIDE_2 = u.select_atoms("protein and name BB and segid B") 
PEPTIDE_3 = u.select_atoms("protein and name BB and segid C") 
PEPTIDE_4 = u.select_atoms("protein and name BB and segid D")


def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

cutoff = 6.0

# Preparar listas para almacenar resultados
contact_types = {
    "lipid_lipid": (micelle_tails, micelle_tails),
    "lipid_water": (micelle_tails, water),
    "peptides_water": (peptides, water),
    "peptides_mem_heads": (peptides, mem_heads),
    "peptides_micelle_heads": (peptides, micelle_heads),
    "micelle_heads_mem_heads": (micelle_heads, mem_heads),
}
contacts_data = {key: [] for key in contact_types}

# Para análisis de posiciones en el eje Z
z_data = {
    "PEPTIDE_1": [], "PEPTIDE_2": [], "PEPTIDE_3": [], "PEPTIDE_4": [],
    "Micelle": [], "Membrane_Center": [],
    "Membrane_Upper_Heads": [], "Membrane_Lower_Heads": []
}
time_values = []

print("Calculando contactos y posiciones en Z para cada frame...")
for ts in u.trajectory[::skip]:
    dt = u.trajectory.dt
    time = (ts.frame * dt) / 1e6  # Convertir a microsegundos
    time_values.append(time)
    
    # Center the membrane in the z-axis
    membrane_com = membrane.center_of_mass()
    shift = u.dimensions[2] / 2 - membrane_com[2]
    u.atoms.positions[:, 2] += shift

    # Calculate contacts
    for key, (group1, group2) in contact_types.items():
        coords1, coords2 = group1.positions, group2.positions
        distances_matrix = distance_array(coords1, coords2, box=u.dimensions)
        num_contacts = np.sum(distances_matrix < cutoff)
        contacts_data[key].append(num_contacts)
    
    # Cálculo de posiciones en Z usando Minimum Image Convention
    box_z = u.dimensions[2]  # Z-dimension of the simulation box
    membrane_com_z = membrane.center_of_mass()[2]

    # Calculate z-positions relative to the membrane center
    for label, group in zip(["PEPTIDE_1", "PEPTIDE_2", "PEPTIDE_3", "PEPTIDE_4", "Micelle"], 
                            [PEPTIDE_1, PEPTIDE_2, PEPTIDE_3, PEPTIDE_4, micelle_heads]):
        group_com_z = group.center_of_mass()[2]
        # Apply minimum image convention
        z_diff = group_com_z - membrane_com_z
        z_diff = z_diff - box_z * np.round(z_diff / box_z)
        z_data[label].append(np.abs(z_diff))  # Absolute value relative to membrane center

    # Store membrane center and upper/lower heads
    z_data["Membrane_Center"].append(0.0)  # Membrane center is now at zero
    upper_heads = mem_heads.positions[mem_heads.positions[:, 2] > membrane_com_z, 2]
    lower_heads = mem_heads.positions[mem_heads.positions[:, 2] < membrane_com_z, 2]
    z_data["Membrane_Upper_Heads"].append(np.mean(upper_heads) - membrane_com_z if len(upper_heads) > 0 else 0.0)
    z_data["Membrane_Lower_Heads"].append(np.mean(lower_heads) - membrane_com_z if len(lower_heads) > 0 else 0.0)

# Guardar resultados en un único CSV
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
window_size = 10
grouped_contacts = {
    "Peptides-Water": "peptides_water",
    "Peptides-Mem Heads": "peptides_mem_heads",
    "Peptides-Micelle Heads": "peptides_micelle_heads",
    "Micelle Heads-Mem Heads": "micelle_heads_mem_heads"
}

# Graficar cada conjunto de contactos por separado
for label, key in grouped_contacts.items():
    plt.figure(figsize=(10, 6))
    smoothed_counts = moving_average(contacts_data[key], window_size)
    smoothed_frames = time_values[:len(smoothed_counts)]
    plt.plot(smoothed_frames, smoothed_counts, label=label, linestyle='-', marker='')
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
    smoothed_frames = time_values[:len(smoothed_counts)]
    plt.plot(smoothed_frames, smoothed_counts, label=label)

plt.title("Contactos a lo largo de la trayectoria (Todos)")
plt.xlabel("Time ($\mu$S)")
plt.ylabel("Número de contactos")
plt.ylim(-1, None)
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(result_dir, "contactos_grupos_smoothed_plot.png"))

# Graficar evolución de posiciones en Z
plt.figure(figsize=(10, 6))
for label, values in z_data.items():
    if label == "Membrane_Lower_Heads":
        continue
    plt.plot(time_values, values, label=label)
plt.title("Evolución de la posición en Z")
plt.xlabel("Time ($\mu$S)")
plt.ylabel("Posición en Z (Å)")
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(result_dir, "posiciones_z_plot.png"))

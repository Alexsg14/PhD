import prolif as plf
import MDAnalysis as mda
import json
import re
import argparse
import os

# --- Argumentos por línea de comandos ---
parser = argparse.ArgumentParser(description="Processes protein-ligand interactions with ProLIF.")
parser.add_argument('--file', required=True, help='Base path of the project (without trailing slash)')
parser.add_argument('--pdb_path', help='Path to the receptor PDB file')
parser.add_argument('--sdf_path', help='Path to the ligand poses SDF file')
parser.add_argument('--output_path', help='Path to save the output JSON file')

args = parser.parse_args()

# --- Resolución de rutas ---
file = args.file
pdb_path = args.pdb_path if args.pdb_path else f"{file}/receptor.pdb"
sdf_path = args.sdf_path if args.sdf_path else f"{file}/all.sdf"
output_path = args.output_path if args.output_path else f"{file}/aa_interactions_arx.json"

# --- Carga de la proteína ---
protein = mda.Universe(pdb_path)
for residuo in protein.select_atoms("protein").residues:
    residuo.resid += 0  # Ajuste opcional de numeración

# --- Crear objetos ProLIF ---
protein_plf = plf.Molecule.from_mda(protein)
poses_plf = plf.sdf_supplier(sdf_path)

# --- Calcular fingerprint ---
fp = plf.Fingerprint(count=True, vicinity_cutoff=6.0)
fp.run_from_iterable(poses_plf, protein_plf)

# --- Regex para parseo de residuos ---
pattern = re.compile(r"^([A-Z]{3})(\d+)\.([A-Za-z0-9])$")

# --- Leer energías VINA del archivo SDF ---
vina_re = re.compile(r"VINA RESULT:\s*([-+]?\d*\.\d+|\d+)")
energies = []
with open(sdf_path, 'r') as f:
    for line in f:
        m = vina_re.search(line)
        if m:
            energies.append(float(m.group(1)))

# --- Convertir fingerprint a DataFrame ---
df_full = fp.to_dataframe().reset_index()

# --- Procesar cada pose ---
results = []
N_poses = len(poses_plf)
for pose_index in range(N_poses):
    energy = energies[pose_index] if pose_index < len(energies) else None
    df_pose = df_full[df_full["Frame"] == pose_index]
    row = df_pose.iloc[0]

    interacting = {
        col[1]
        for col, val in row.items()
        if isinstance(col, tuple) and val > 0
    }

    residues = []
    for entry in sorted(interacting):
        m = pattern.match(entry)
        if not m:
            continue
        resname, resid, chain = m.groups()
        residues.append({
            "resname": resname,
            "resid": int(resid),
            "chain": chain
        })

    for res in residues:
        sel = (f"resname {res['resname']} "
               f"and resid {res['resid']} "
               f"and segid {res['chain']}")
        atom_indices = protein.select_atoms(sel).indices.tolist()
        res["atoms"] = [int(i) for i in atom_indices]

    results.append({
        "model": int(pose_index) + 1,
        "energy": energy,
        "residues": residues
    })

# --- Guardar JSON ---
with open(output_path, 'w') as json_file:
    json.dump(results, json_file, indent=2)

print(f"JSON with the interactions saved at: {output_path}")

# --- Imprimir JSON final ---
#print(json.dumps(results, indent=2))

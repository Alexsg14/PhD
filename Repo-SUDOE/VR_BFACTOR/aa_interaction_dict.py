import argparse
import json
import re
import MDAnalysis as mda
from MDAnalysis.topology import guessers
import prolif as plf
from rdkit import Chem
from rdkit.Chem import SDMolSupplier

def main():
    parser = argparse.ArgumentParser(description="Genera info VR de interacciones")
    parser.add_argument("--file", required=True, help="Directorio base de output")
    parser.add_argument("--pdb_path", required=True, help="Ruta al receptor (pdb)")
    parser.add_argument("--sdf_path", required=True, help="Ruta al sdf de poses")
    parser.add_argument("--output_path", required=True, help="Ruta de salida JSON")
    args = parser.parse_args()

    # 1. Cargar proteína
    print(f"🔄 Cargando receptor: {args.pdb_path}")
    protein = mda.Universe(args.pdb_path)
    elements = guessers.guess_types(protein.atoms.names)
    protein.add_TopologyAttr("elements", elements)
    protein_atoms = protein.select_atoms("protein")
    try:
        protein_atoms.guess_bonds()
    except ValueError as e:
        if "vdw radii for types: CO" in str(e):
            protein.atoms.guess_bonds(vdwradii={"CO": 1.8})
        else:
            raise
    
    protein_plf = plf.Molecule.from_mda(protein, NoImplicit=False)

    # 2. Cargar ligando (usando sdf_supplier como fallback seguro para coords 3D)
    print(f"🔄 Cargando poses: {args.sdf_path}")
    poses_plf = plf.sdf_supplier(args.sdf_path)

    # 3. Extraer energías VINA RESULT del SDF
    vina_re = re.compile(r"VINA RESULT:\s*([-+]?\d*\.\d+|\d+)")
    energies = []
    with open(args.sdf_path, 'r') as f:
        for line in f:
            m = vina_re.search(line)
            if m:
                energies.append(float(m.group(1)))

    # 4. Calcular fingerprint
    print("🔄 Sprinting ProLIF fingerprint...")
    fp = plf.Fingerprint(count=True, vicinity_cutoff=6.0)
    fp.run_from_iterable(poses_plf, protein_plf)

    # Convertir a DataFrame completo
    df_full = fp.to_dataframe().reset_index()

    # 5. Armar JSON para VR
    results = []
    N_poses = len(poses_plf)
    print(f"📊 Procesando {N_poses} poses para VR...")

    for pose_index in range(N_poses):
        energy = energies[pose_index] if pose_index < len(energies) else None

        df_pose = df_full[df_full["Frame"] == pose_index]
        if df_pose.empty:
            continue
            
        row = df_pose.iloc[0]

        # Encontrar residuos interactuantes (>0)
        interacting_res_keys = set()
        for col, val in row.items():
            if isinstance(col, tuple) and len(col) == 3:
                _, res_key, _ = col
                if val > 0:
                    interacting_res_keys.add(str(res_key))

        residues_info = []
        for entry in sorted(interacting_res_keys):
            # ProLIF format: "ALA1148.A" or just "ALA1148"
            res_name = ''.join(filter(str.isalpha, entry)).split('.')[0] if '.' in entry else ''.join(filter(str.isalpha, entry))
            res_num  = ''.join(filter(str.isdigit, entry))
            chain    = entry.split('.')[1] if '.' in entry else ""

            if not res_num:
                continue

            # Buscar átomos en MDAnalysis para este residuo
            # Dependiendo de si la proteína tiene chain ID ou no en MDAnalysis
            if chain:
                sel = f"resname {res_name} and resid {res_num} and segid {chain}"
            else:
                sel = f"resname {res_name} and resid {res_num}"
                
            atom_indices = protein.select_atoms(sel).indices.tolist()

            residues_info.append({
                "resname": res_name,
                "resid": int(res_num),
                "chain": chain,
                "atoms": atom_indices
            })

        results.append({
            "model": float(pose_index) + 1,
            "energy": energy,
            "residues": residues_info
        })

    # 6. Guardar JSON
    with open(args.output_path, 'w') as json_file:
        json.dump(results, json_file, indent=2)

    print(f"✅ JSON de interacciones guardado en: {args.output_path}")

if __name__ == "__main__":
    main()

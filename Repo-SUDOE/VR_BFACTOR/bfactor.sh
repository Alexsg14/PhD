#!/bin/bash

# ================================
# Parse command-line arguments
# ================================

# Load gromacs at 2024.3 version

source $HOME/gromacs/2024.3/bin/GMXRC

while getopts p:v:l: flag
do
    case "${flag}" in
        p) path=${OPTARG};;
        v) vr_folder=${OPTARG};;
        l) ligand=${OPTARG};;
        *) echo "Usage: $0 -p <path> -v <vr_folder> -l <ligand>"
           exit 1;;
    esac
done

if [ -z "$path" ] || [ -z "$vr_folder" ] || [ -z "$ligand" ]; then
    echo "Missing required arguments."
    echo "Usage: $0 -p <path> -v <vr_folder> -l <ligand>"
    exit 1
fi



# ================================
# Activate Conda environment
# ================================


# Create output folder
mkdir -p "$vr_folder"

# Convert and concatenate trajectories
gmx convert-trj -f "$path/min_fep1.trr" -o "$path/min_fep1_c.xtc"
gmx convert-trj -f "$path/min_fep2.trr" -o "$path/min_fep2_c.xtc"

gmx trjcat -f "$path/min_fep1_c.xtc" "$path/eq_fep.xtc" "$path/min_fep2_c.xtc" "$path/eq_nvt_fep.xtc" "$path/eq_npt_fep_1.xtc" "$path/eq_npt_fep_2.xtc" "$path/prod_fep.xtc" -o "$path/traj.xtc"

echo -e "Protein\nOther_Protein\nq" | gmx trjconv -s "$path/prod_fep.tpr" -f "$path/traj.xtc" -pbc mol -center -n "$path/index.ndx" -o "$path/center_complete.pdb" -e 0

echo -e "Protein\nOther_Protein\nq" | gmx trjconv -s "$path/prod_fep.tpr" -f "$path/traj.xtc" -pbc mol -center -n "$path/index.ndx" -o "$path/center_complete.xtc" -b 0 -e 2500

# Execute the Python script
# before --receptor center_completo.pdb
python ligand_energy_attribution.py \
    --pdbqt_ligs  "$path/all.pdbqt" \
    --output_pdb "$path/all.pdb" \
    --receptor "$path/receptor.pdb" \
    --dir_models "$path/models_center_pdb" \
    --dir_output "$path/bfactor_receptor_center" \
    --cutoff 5.0

# Copy and rename output files
cp "$path/all.pdb" "$vr_folder"
cp "$path/bfactor_receptor_center/receptor_final_bfactor_residue.pdb" "$vr_folder"
cp "$path/center_complete.xtc" "$vr_folder/center.xtc"
cp "$path/center_complete.pdb" "$vr_folder/center.pdb"
mv "$vr_folder/receptor_final_bfactor_residue.pdb" "$vr_folder/receptor.pdb"

# Copy ligand pdb file
cp $ligand "$vr_folder/ligand.pdb"


# Execute aminoacid displaying script
python aa_interaction_flags.py \
    --file "$path"\
    --pdb_path "$path/receptor.pdb" \
    --sdf_path "$path/all.sdf" \
    --output_path "$vr_folder/aa_interactions_arx.json"

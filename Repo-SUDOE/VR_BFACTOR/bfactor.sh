#!/bin/bash

# Activa el entorno de Conda
. /home/alejandroseco/anaconda3/etc/profile.d/conda.sh
conda activate obabel_env

# Ejecuta tu script de Python
python ligand_energy_attribution_bfactor.py --pdbqt_ligs  /home/alejandroseco/Desktop/MMDR-main/Code/Output/all.pdbqt --output_pdb /home/alejandroseco/Desktop/MMDR-main/Code/Output/all.pdb --receptor /home/alejandroseco/Desktop/MMDR-main/Code/Output/receptor.pdb --dir_models /home/alejandroseco/Desktop/MMDR-main/Code/Output/models_pdb --dir_output /home/alejandroseco/Desktop/MMDR-main/Code/Output/bfactor_receptor --cutoff 5.0  


# ligand_energy_attribution_bfactor.py

# Opcional: desactivar entorno al terminar
# conda init bash
conda deactivate


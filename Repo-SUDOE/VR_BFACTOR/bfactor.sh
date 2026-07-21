#!/bin/bash
# ==============================================================================
# Script for B-factor Attribution on Receptor Atoms/Residues from Vina Results
# ==============================================================================

# Activate Conda environment if available
CONDA_BASE="${CONDA_BASE:-$HOME/anaconda3}"
if [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    conda activate obabel_env 2>/dev/null || true
fi

# Define input/output paths (defaults to local directory or environment overrides)
DATA_DIR="${DATA_DIR:-./data}"
PDBQT_LIGS="${PDBQT_LIGS:-$DATA_DIR/all.pdbqt}"
OUTPUT_PDB="${OUTPUT_PDB:-$DATA_DIR/all.pdb}"
RECEPTOR="${RECEPTOR:-$DATA_DIR/receptor.pdb}"
DIR_MODELS="${DIR_MODELS:-$DATA_DIR/models_pdb}"
DIR_OUTPUT="${DIR_OUTPUT:-$DATA_DIR/bfactor_receptor}"
CUTOFF="${CUTOFF:-5.0}"

# Run Python script
python ligand_energy_attribution_bfactor.py \
    --pdbqt_ligs "$PDBQT_LIGS" \
    --output_pdb "$OUTPUT_PDB" \
    --receptor "$RECEPTOR" \
    --dir_models "$DIR_MODELS" \
    --dir_output "$DIR_OUTPUT" \
    --cutoff "$CUTOFF"

# Deactivate environment
conda deactivate 2>/dev/null || true

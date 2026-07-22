#!/usr/bin/env bash
# ===============================================================================
#  Conda Environment Builder for CESGA (v0.1)
# ===============================================================================
#  Author: F. Suárez Lestón
#
#  This script builds a Python environment suitable for the trajectory analysis
#  of the SuPepMem Database.
#
#  Usage:
#    ./create_conda.sh <environment_name>
#
#  Activation:
#    conda activate <environment_name>
# ===============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Error: Environment name argument is required."
    echo "Usage: $0 <environment_name>"
    exit 1
fi

ENVIRONMENT="$1"

# Go to the user's HOME directory
cd ~

# Create directory in the STORE partition to contain the environment files
mkdir -p "${STORE}/conda_python_envs"

# Configure .condarc to direct environments and package downloads to STORE partition
cat <<EOF > .condarc
channels:
  - conda-forge
  - bioconda
  - defaults
envs_dirs:
  - ${STORE}/conda_python_envs/py_envs
pkgs_dirs:
  - ${STORE}/conda_python_envs/py_envs/pkgs
EOF

# Load Miniconda3 module on the CESGA cluster
if command -v module &>/dev/null; then
    module load miniconda3 || true
fi

echo "Creating conda environment: ${ENVIRONMENT}..."
conda create -y -n "${ENVIRONMENT}" python=3.9

echo "Activating environment..."
# Try different ways to activate conda environment in a bash script
eval "$(conda shell.bash hook)"
conda activate "${ENVIRONMENT}"

echo "Installing MDAnalysis and dependencies..."
conda install -y -c conda-forge MDAnalysis
pip install statsmodels tqdm pandas numpy matplotlib scipy

echo "Deactivating environment..."
conda deactivate

echo "Conda environment '${ENVIRONMENT}' successfully created!"
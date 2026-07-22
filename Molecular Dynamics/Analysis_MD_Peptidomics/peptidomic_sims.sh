#!/bin/bash
#SBATCH -t 2:00:00 # execution time. Ex: 1 hour
#SBATCH --mem=16GB
#SBATCH -c 16 # number of tasks, number of cores

set -euo pipefail

# ===============================================================================
#  Peptidomic Simulations Post-Analysis Runner (CESGA SBATCH Script)
# ===============================================================================
#
# This script runs modular_analysis.py to execute the analysis and generate
# plots for peptidomics trajectories.
#
# Environment Variables:
#   PEPTIDOMICA_BASE_PATH : Base directory where peptidomics simulation folders are located.
#                           (Default: /mnt/lustre/scratch/nlsas/home/usc/cq/asg/_PEPTIDOMICA)
# ===============================================================================

# Load environment modules (cluster specific)
if command -v module &>/dev/null; then
    module load cesga/system miniconda3/22.11.1-1 || true
fi

# Activate Conda environment
source activate peptidomica_spm || conda activate peptidomica_spm || true

# Resolve script directory to keep execution path-independent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
path_py="${SCRIPT_DIR}"

# Define paths (with environment variable override support)
BASE_PATH="${PEPTIDOMICA_BASE_PATH:-/mnt/lustre/scratch/nlsas/home/usc/cq/asg/_PEPTIDOMICA}"
folder="TEST_COV_ParI"

top="${BASE_PATH}/${folder}/md_20_d.tpr"
traj="${BASE_PATH}/${folder}/traj_skip100.xtc"
csv_dir="${BASE_PATH}/${folder}/_RESULTS"
out="${BASE_PATH}/${folder}/_density"

analyses="tilt zcontacts rolling"
rolling_skip=10
time=5000

echo "=================================================="
echo " Starting Peptidomic Simulations Post-Analysis"
echo "--------------------------------------------------"
echo " Base Path   : $BASE_PATH"
echo " Folder      : $folder"
echo " Topology    : $top"
echo " Trajectory  : $traj"
echo " CSV Dir     : $csv_dir"
echo " Output Dir  : $out"
echo "=================================================="

# Standard Plotting/Analysis Usage
python "${path_py}/modular_analysis.py" \
     -plot \
     --analyses zcontacts \
     -csv_dir "${csv_dir}" \
     -out "${out}" \
     --time "${time}" \
     --do_all_plots

echo "=================================================="
echo " Analysis and Plotting Completed Successfully!"
echo "=================================================="

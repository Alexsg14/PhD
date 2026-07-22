#!/bin/bash
#SBATCH -t 6:00:00 # execution time. Ex: 1 hour
#SBATCH --mem=16GB
#SBATCH -c 16 # number of tasks, number of cores

set -euo pipefail

# ===============================================================================
#  Conda SPM Analysis Runner (CESGA SBATCH Script)
# ===============================================================================
#
# This script runs the SPM_Analysis.py tool under a Conda environment.
# It resolves python script and style paths dynamically and supports overrides
# via environment variables.
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
path_spm="${SCRIPT_DIR}"

# Define paths (with environment variable override support)
BASE_PATH="${PEPTIDOMICA_BASE_PATH:-/mnt/lustre/scratch/nlsas/home/usc/cq/asg/_PEPTIDOMICA}"
f="${BASE_PATH}/TEST_COV_5069"
o="${f}/_Analisis_SPM4"
style="${path_spm}/style_SPM/SuPepMem.mplstyle"
font="${path_spm}/style_SPM/"
tpr="${f}/md_20_d.tpr"
xtc="${f}/traj.xtc"
mdp="${BASE_PATH}/TEST_COV_485/martini_md.mdp"

ff="martini22"
i=0
l=5000000
av=4000000

echo "=================================================="
echo " Starting Conda SPM Analysis"
echo "--------------------------------------------------"
echo " Base Path   : $BASE_PATH"
echo " Folder      : $f"
echo " Output Dir  : $o"
echo " Forcefield  : $ff"
echo "=================================================="

python "${path_spm}/SPM_Analysis.py" \
    -f "${f}" \
    -o "${o}" \
    -style "${style}" \
    -font "${font}" \
    -tpr "${tpr}" \
    -xtc "${xtc}" \
    -mdp "${mdp}" \
    -ff "${ff}" \
    -A -i "${i}" -l "${l}" -av "${av}"

echo "=================================================="
echo " SPM Analysis Completed Successfully!"
echo "=================================================="

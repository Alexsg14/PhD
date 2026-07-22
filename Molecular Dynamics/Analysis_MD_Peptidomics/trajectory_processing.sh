#!/bin/bash
#SBATCH -t 20:00:00 # execution time. Ex: 1 hour
#SBATCH --mem=16GB
#SBATCH -c 16 # number of tasks, number of cores
##SBATCH --ntasks-per-node=1
##SBATCH -C clk

set -euo pipefail

# ===============================================================================
#  Trajectory Pre-processing & Analysis (CESGA SBATCH Script)
# ===============================================================================
#
# This script handles GROMACS trajectory manipulation (concatenation, frame
# skipping, PBC cluster treatment, and nojump corrections) and then runs the
# modular analysis script to estimate contacts and Z-positions.
#
# Environment Variables:
#   TRAJ_PATH : Path containing the raw trajectory parts and production files.
#               (Default: /mnt/lustre/scratch/nlsas/home/usc/cq/ama/Alicia_LPA_replicas/MLT/libres_R)
# ===============================================================================

# Load environment modules (cluster specific)
if command -v module &>/dev/null; then
    module load cesga/2020 gcc/system openmpi/4.0.5_ft3_cuda gromacs/2022.1 || true
    module load mdanalysis/2.1.0 || true
fi

# Resolve script directory to keep execution path-independent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

path="${TRAJ_PATH:-/mnt/lustre/scratch/nlsas/home/usc/cq/ama/Alicia_LPA_replicas/MLT/libres_R}"

## Concatenacion inicial
echo "Concatenando..."
gmx trjcat -f "$path"/traj_comp.part00* -o traj.xtc

## Skipeamos trayectoria
echo "Skippeando..."
echo -e "0" | gmx trjconv -f traj.xtc -skip 100 -o traj_skip100.xtc -s "$path"/prod.tpr
cp traj_skip100.xtc "$path"

## Sacamos el primer frame y lo tratamos con cluster y nojump
echo "Sacando primer frame..."
echo -e "Protein\nSystem\nq" | gmx trjconv -f traj_skip100.xtc -b 0 -e 0 -pbc cluster -o traj_cluster_peptides.pdb -s "$path"/prod.tpr
cp traj_cluster_peptides.pdb "$path"
echo -e "LPA\nSystem\nq" | gmx trjconv -f traj_cluster_peptides.pdb -pbc cluster -o traj_cluster_peptides_LPA.pdb -s "$path"/prod.tpr
cp traj_cluster_peptides_LPA.pdb "$path"
echo -e "System" | gmx trjconv -f traj_cluster_peptides_LPA.pdb -pbc nojump -o traj_cluster_peptides_LPA_nojump.pdb -s "$path"/prod.tpr
cp traj_cluster_peptides_LPA_nojump.pdb "$path"

## Tratamos la trayectoria igual que el frame 0 (cluster a peptido y LPA; posterior nojump)
echo "Sacando trayectoria para analizar..."
echo -e "Protein\nSystem\nq" | gmx trjconv -f traj_skip100.xtc -pbc cluster -o traj_skip100_cluster_peptides.xtc -s "$path"/prod.tpr
cp traj_skip100_cluster_peptides.xtc "$path"
echo -e "LPA\nSystem\nq" | gmx trjconv -f traj_skip100_cluster_peptides.xtc -pbc cluster -o traj_skip100_cluster_peptides_LPA.xtc -s "$path"/prod.tpr
cp traj_skip100_cluster_peptides_LPA.xtc "$path"
echo -e "System" | gmx trjconv -f traj_skip100_cluster_peptides_LPA.xtc -pbc nojump -o traj_skip100_cluster_peptides_LPA_nojump.xtc -s "$path"/prod.tpr
cp traj_skip100_cluster_peptides_LPA_nojump.xtc "$path"

# Con skip = 1, son 4000 frames
echo "Analizando..."
python "${SCRIPT_DIR}/modular_analysis.py" \
    -top traj_cluster_peptides_LPA_nojump.pdb \
    -traj traj_skip100_cluster_peptides_LPA.xtc \
    --analyses zcontacts \
    --zc_skip 10 \
    -out Resultados_Cluster_NoJump

cp -r Resultados* "$path"

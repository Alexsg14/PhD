#!/usr/bin/env bash
set -euo pipefail

# ===============================================================================
#  Master Script for HILLS / FES / PMF Analysis
# ===============================================================================
#
# This script wraps the Python analysis tool to compute FES curves, create
# movies, apply restricted plotting limits, and perform PMF analysis including
# plateau detection and ΔG estimation by integration.
#
# Environment Variables:
#   PMF_BASE_PATH : Base directory where simulation folders are located.
#                   (Default: /mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica)
#
# Basic Usage:
#   ./master_hills.sh <folder_name> <hills_file_name> <output_subdir> [additional_flags...]
#
# Examples of Use:
#   # 1. Standard FES profile generation:
#   ./master_hills.sh kappa2000_COV HILLS_WT TODO_PMF
#
#   # 2. FES profile generation with movie/video creation:
#   ./master_hills.sh kappa2000_COV HILLS_WT TODO_PMF --movie
#
#   # 3. FES profile with ROI limits fitting and PMF ΔG integration:
#   ./master_hills.sh kappa2000_COV HILLS_WT TODO_PMF --limits --pmf
#
#   # 4. Analyzing from a specific COLVAR file (no hills reconstruction):
#   ./master_hills.sh kappa2000_COV HILLS_WT TODO_PMF --colvar COLVAR_WT --no-hills
#
# ===============================================================================

# --- Arguments check ---
if [ "$#" -lt 3 ]; then
    echo "Error: Missing arguments."
    echo "Usage: $0 <folder_name> <hills_file_name> <output_subdir> [additional_flags...]"
    exit 1
fi

FOLDER="$1"
HILLS_NAME="$2"
OUT_SUBDIR="$3"
shift 3

# --- Path resolution ---
BASE_PATH="${PMF_BASE_PATH:-/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica}"
f="${BASE_PATH}/${FOLDER}"
h="${f}/${HILLS_NAME}"
output="${f}/${OUT_SUBDIR}"

mkdir -p "$output"

echo "=================================================="
echo " Starting HILLS / FES / PMF Analysis"
echo "--------------------------------------------------"
echo " Base Path   : $BASE_PATH"
echo " Folder      : $FOLDER"
echo " HILLS File  : $h"
echo " Output Dir  : $output"
echo " Extra Flags : $*"
echo "=================================================="

# --- Execute python analysis script ---
python hills_analysis.py "$h" "$output" "$@"

echo "--------------------------------------------------"
echo " Analysis Completed Successfully!"
echo " Results saved in: $output"
echo "=================================================="

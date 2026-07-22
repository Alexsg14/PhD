#!/usr/bin/env bash
set -euo pipefail

# ======================
# USO:
# ./run_compare_block_analysis.sh BASE_PATH FOLDER OUTPUT_SUBDIR \
#   A_LO A_HI B_LO B_HI \
#   [ "N1 N2 N3 ..." ]
#
# EJEMPLO:
# ./run_compare_block_analysis.sh \
#   /mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica \
#   kappa2000_COV \
#   TODO_BLOCKS_COMPARE \
#   2.3 2.9 5.0 7.0 \
#   "10000 20000 40000 80000"
# ======================

# --- argumentos obligatorios ---
BASE_PATH="$1"
FOLDER="$2"
OUT_SUBDIR="$3"

A_LO="$4"
A_HI="$5"
B_LO="$6"
B_HI="$7"

# --- opcional: lista de últimos HILLS, como string ---
LAST_HILLS_LIST="${8:-"10000 20000 40000 80000"}"

# --- configuración fija ---
PY_COMPARE="compare_last_hills.py"      # nuevo driver
PY_BLOCK="block_analysis_hills.py"      # el que ya tenías
CV_NAME="D.z"

HILLS_NAME="HILLS_WT"
COLVAR_NAME="COLVAR_WT"

ROI_LO="0.0"
ROI_HI="7.0"

MIN_BLOCKS="15"

# ======================

f="${BASE_PATH}/${FOLDER}"
h="${f}/${HILLS_NAME}"
c="${f}/${COLVAR_NAME}"
output="${f}/${OUT_SUBDIR}"

mkdir -p "$output"

echo "===================================="
echo " Compare block analysis (metadynamics)"
echo "------------------------------------"
echo " Base path : $BASE_PATH"
echo " Folder    : $FOLDER"
echo " HILLS     : $h"
echo " COLVAR    : $c"
echo " Output    : $output"
echo " CV        : $CV_NAME"
echo " A         : [$A_LO, $A_HI]"
echo " B         : [$B_LO, $B_HI]"
echo " ROI       : [$ROI_LO, $ROI_HI]"
echo " lastHILLS : $LAST_HILLS_LIST"
echo " minBlocks : $MIN_BLOCKS"
echo "===================================="
echo

# Convierte la string en array
read -r -a LAST_ARR <<< "$LAST_HILLS_LIST"

# --- construye comando ---
cmd=(
  python "$PY_COMPARE"
  --py-script "$PY_BLOCK"
  --hills "$h"
  --outdir "$output"
  --cv "$CV_NAME"
  --A "$A_LO" "$A_HI"
  --B "$B_LO" "$B_HI"
  --roi "$ROI_LO" "$ROI_HI"
  --min-blocks "$MIN_BLOCKS"
  --last-hills
)

# añade Ns
for N in "${LAST_ARR[@]}"; do
  cmd+=("$N")
done

# --- ejecución ---
echo ">>> Ejecutando:"
echo "${cmd[@]}"
echo

"${cmd[@]}" | tee "$output/compare_block_analysis.log"

echo
echo ">>> Comparativa terminada"
echo "    Resultados en: $output"
echo "    Figura: $output/compare_sem_vs_blocksize.png"
echo "    Resumen: $output/compare_summary.csv"

# ./block_analysis.sh \
#   /mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica \
#   kappa2000_COV \
#   TODO_BLOCKS_COMPARE \
#   2.3 2.9 5.0 7.0 \
#   "10000 20000 40000 80000"

#!/bin/bash
set -euo pipefail

# ===============================================================================
#  Peptidomic Analysis Runner
# ===============================================================================
#
# This script loads MDAnalysis and executes the modular analysis tool on the
# local GROMACS topology (md.tpr) and trajectory (traj_skip100.xtc) files.
#
# Usage:
#   ./peptidomic_analysis.sh
# ===============================================================================

# Load environment modules (cluster specific)
if command -v module &>/dev/null; then
    module load mdanalysis/2.1.0 || true
fi

# Resolve script directory to keep execution path-independent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

python "${SCRIPT_DIR}/modular_analysis.py" \
    -top md.tpr \
    -traj traj_skip100.xtc \
    --analyses tilt zcontacts rolling \
    --rolling_skip 10 \
    -out _RESULTS \
    --time 5000

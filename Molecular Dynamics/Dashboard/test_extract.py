import os
import MDAnalysis as mda
import subprocess
from realtime_analysis import VIEWER_DIR

def test(pdb_path, xtc_path):
    print(f"Checking {xtc_path}")
    if not os.path.exists(xtc_path): return "XTC missing"
    u = mda.Universe(pdb_path, xtc_path)
    if len(u.trajectory) == 0: return "Empty traj"
    start_idx = max(0, len(u.trajectory) - 20)
    start_time = u.trajectory[start_idx].time
    tpr_path = xtc_path.replace(".xtc", ".tpr")
    s_path = tpr_path if os.path.exists(tpr_path) else pdb_path
    
    cmd = ["gmx", "trjconv", "-s", s_path, "-f", xtc_path, "-b", str(start_time), "-pbc", "whole"]
    print("Running", " ".join(cmd))
    p = subprocess.run(cmd, input="0\n", capture_output=True, text=True)
    if p.returncode != 0: return f"Failed: {p.stderr}"
    return "Success"

# Run test using dynamic path based on BASE_DIR env var or original fallback
base_dir = os.environ.get("MD_DASHBOARD_BASE_DIR", "/home/ciqus/aliciaft3/YAP_TEAD_Junio26")
test_pdb = os.path.join(base_dir, "TEAD_ALA48/complex_with_ligand.pdb")
test_xtc = os.path.join(base_dir, "TEAD_ALA48/replica_1/r1_tray.xtc")

if os.path.exists(test_pdb) and os.path.exists(test_xtc):
    print(test(test_pdb, test_xtc))
else:
    print(f"⚠️ Test files not found. Base directory: {base_dir}")


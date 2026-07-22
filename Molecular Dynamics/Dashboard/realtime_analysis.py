"""
realtime_analysis.py
MDAnalysis-based trajectory analysis for real-time monitoring.
READ-ONLY on simulation files. Only writes PDB to Dashboard/static/viewer/.
"""

import os
import numpy as np
import traceback
import subprocess
import warnings

# Suppress warnings from MDAnalysis about reloading offsets (which happens normally on actively written XTC files)
warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis")

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis import rms, align
    from MDAnalysis.analysis.distances import distance_array
    MDA_AVAILABLE = True
except ImportError:
    MDA_AVAILABLE = False
    print("⚠️  MDAnalysis not installed — trajectory analyses disabled.")

# Output directory for viewer PDBs
VIEWER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "viewer")
os.makedirs(VIEWER_DIR, exist_ok=True)


def _safe_select(u, sel):
    try:
        ag = u.select_atoms(sel)
        return ag if len(ag) > 0 else None
    except Exception:
        return None


def _get_chain_a(u):
    for sel in [
        "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A) and name CA",
        "protein and (chainID A or chainID 0) and name CA",
        "protein and name CA",
    ]:
        ag = _safe_select(u, sel)
        if ag and len(ag) > 0:
            return ag
    return None


def _get_chain_b(u):
    for sel in [
        "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B) and name CA",
        "protein and (chainID B or chainID 1) and name CA",
        "resname MOL or resname LIG or resname UNL",
    ]:
        ag = _safe_select(u, sel)
        if ag and len(ag) > 0:
            return ag
    return None


def compute_analyses(pdb_path, xtc_path, frame_step=1, apply_pbc=True, is_cancelled=None):
    """
    Compute RMSD, Rg, CoM distance, and contacts from trajectory.
    Uses frame_step=1 to process all frames.
    Returns dict with time series data, or None on failure.
    """
    if not MDA_AVAILABLE:
        return None
    if not pdb_path or not xtc_path:
        return None
        
    if not os.path.exists(pdb_path):
        return None

    if isinstance(xtc_path, list):
        for path in xtc_path:
            if not os.path.exists(path):
                return None
    else:
        if not os.path.exists(xtc_path):
            return None

    try:
        u = mda.Universe(pdb_path, xtc_path)
    except Exception as e:
        print(f"⚠️  Failed to load trajectory: {e}")
        return None

    n_frames = len(u.trajectory)
    if n_frames == 0:
        return None

    result = {
        "times": [], 
        "rmsd_complex": [], "rmsd_chain_a": [], "rmsd_chain_b": [], "rmsd_ligand": [],
        "rg": [], "rg_chain_a": [], "rg_chain_b": [],
        "com_lig_prot": [], "com_lig_a": [], "com_lig_b": [], "com_a_b": [],
        "cont_lig_prot": [], "cont_lig_a": [], "cont_lig_b": [], "cont_a_b": [],
        "n_frames": n_frames,
        "n_atoms": u.atoms.n_atoms,
    }

    try:
        # Setup selections
        protein = _safe_select(u, "protein")
        ca_protein = _safe_select(u, "protein and name CA")
        backbone = _safe_select(u, "protein and backbone")
        
        ref = mda.Universe(pdb_path, xtc_path)
        ref.trajectory[0]
        
        ca_a_u = _safe_select(u, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A) and name CA")
        if not ca_a_u: ca_a_u = _safe_select(u, "protein and (chainID A or chainID 0) and name CA")
        ca_a_ref = _safe_select(ref, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A) and name CA") if ca_a_u else None
        if not ca_a_ref and ca_a_u: ca_a_ref = _safe_select(ref, "protein and (chainID A or chainID 0) and name CA")

        ca_b_u = _safe_select(u, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B) and name CA")
        if not ca_b_u: ca_b_u = _safe_select(u, "protein and (chainID B or chainID 1) and name CA")
        ca_b_ref = _safe_select(ref, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B) and name CA") if ca_b_u else None
        if not ca_b_ref and ca_b_u: ca_b_ref = _safe_select(ref, "protein and (chainID B or chainID 1) and name CA")

        # Full protein selections for Chain A and B (for radius of gyration)
        protein_a = _safe_select(u, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A or chainID A or chainID 0)")
        protein_b = _safe_select(u, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B or chainID B or chainID 1)")

        lig_u = _safe_select(u, "resname MOL or resname LIG or resname UNL")
        lig_ref = _safe_select(ref, "resname MOL or resname LIG or resname UNL")

        bb_u = backbone
        bb_ref = _safe_select(ref, "protein and backbone")

        if not bb_u or not protein:
            print("⚠️  No protein atoms found.")
            return None

        # --- PBC CORRECTION (ON-THE-FLY) ---
        if apply_pbc:
            try:
                from MDAnalysis import transformations as trans

                # Apply to main universe (all frames)
                protein_for_pbc = _safe_select(u, "protein") or u.select_atoms("all")
                transform = [
                    trans.unwrap(protein_for_pbc),
                    trans.center_in_box(protein_for_pbc, center='geometry'),
                    trans.wrap(u.atoms, compound='fragments')
                ]
                u.trajectory.add_transformations(*transform)

                # Apply same correction to ref universe (frame 0 reference)
                # so both are in the same coordinate system before alignment
                ref_protein = _safe_select(ref, "protein") or ref.select_atoms("all")
                ref_transform = [
                    trans.unwrap(ref_protein),
                    trans.center_in_box(ref_protein, center='geometry'),
                    trans.wrap(ref.atoms, compound='fragments')
                ]
                ref.trajectory.add_transformations(*ref_transform)
                ref.trajectory[0]  # re-read frame 0 with corrections applied

            except Exception as e:
                print(f"⚠️  PBC correction failed: {e}")
        # -----------------------------------

        # Iterate frames
        for ts in u.trajectory[::frame_step]:
            if is_cancelled and is_cancelled():
                print("🛑 [Analysis] Task cancelled by user request.")
                return None
                
            result["times"].append(float(ts.time))  # ps
            
            # Align complex to reference (Frame 0) based on backbone
            if bb_u and bb_ref:
                align.alignto(u, ref, select="protein and backbone")
            
            # RMSD Complex
            if bb_u and bb_ref:
                diff = bb_u.positions - bb_ref.positions
                rmsd_val = np.sqrt(np.mean(np.sum(diff**2, axis=1)))
                result["rmsd_complex"].append(round(float(rmsd_val), 3))
            else:
                result["rmsd_complex"].append(0.0)
                
            # RMSD Chain A — local superposition on Chain A Cα only
            if ca_a_u and ca_a_ref and len(ca_a_u) == len(ca_a_ref):
                try:
                    rmsd_val = rms.rmsd(ca_a_u.positions, ca_a_ref.positions, superposition=True)
                    result["rmsd_chain_a"].append(round(float(rmsd_val), 3))
                except Exception:
                    result["rmsd_chain_a"].append(0.0)
            else:
                result["rmsd_chain_a"].append(0.0)

            # RMSD Chain B — local superposition on Chain B Cα only
            if ca_b_u and ca_b_ref and len(ca_b_u) == len(ca_b_ref):
                try:
                    rmsd_val = rms.rmsd(ca_b_u.positions, ca_b_ref.positions, superposition=True)
                    result["rmsd_chain_b"].append(round(float(rmsd_val), 3))
                except Exception:
                    result["rmsd_chain_b"].append(0.0)
            else:
                result["rmsd_chain_b"].append(0.0)

            # RMSD Ligand — local superposition on ligand heavy atoms
            if lig_u and lig_ref and len(lig_u) == len(lig_ref):
                try:
                    rmsd_val = rms.rmsd(lig_u.positions, lig_ref.positions, superposition=True)
                    result["rmsd_ligand"].append(round(float(rmsd_val), 3))
                except Exception:
                    result["rmsd_ligand"].append(0.0)
            else:
                result["rmsd_ligand"].append(0.0)

            # Radius of gyration
            try:
                rg_val = protein.radius_of_gyration()
                result["rg"].append(round(float(rg_val), 3))
            except Exception:
                result["rg"].append(0.0)

            try:
                if protein_a is not None and len(protein_a) > 0:
                    rg_val = protein_a.radius_of_gyration()
                    result["rg_chain_a"].append(round(float(rg_val), 3))
                else:
                    result["rg_chain_a"].append(0.0)
            except Exception:
                result["rg_chain_a"].append(0.0)

            try:
                if protein_b is not None and len(protein_b) > 0:
                    rg_val = protein_b.radius_of_gyration()
                    result["rg_chain_b"].append(round(float(rg_val), 3))
                else:
                    result["rg_chain_b"].append(0.0)
            except Exception:
                result["rg_chain_b"].append(0.0)

            # Distances & Contacts
            def get_com(sel): return sel.center_of_mass() if sel is not None else None
            def get_contacts(target_sel, ref_sel, cutoff=5.0): 
                if target_sel is None or ref_sel is None or len(target_sel) == 0 or len(ref_sel) == 0: return 0
                dists = distance_array(target_sel.positions, ref_sel.positions)
                return int((dists < cutoff).any(axis=1).sum())

            com_p = get_com(protein)
            com_a = get_com(ca_a_u)
            com_b = get_com(ca_b_u)
            com_l = get_com(lig_u)

            if com_l is not None and com_p is not None:
                result["com_lig_prot"].append(round(float(np.linalg.norm(com_l - com_p)), 3))
                result["cont_lig_prot"].append(get_contacts(ca_protein, lig_u))
            else:
                result["com_lig_prot"].append(0.0)
                result["cont_lig_prot"].append(0)

            if com_l is not None and com_a is not None:
                result["com_lig_a"].append(round(float(np.linalg.norm(com_l - com_a)), 3))
                result["cont_lig_a"].append(get_contacts(ca_a_u, lig_u))
            else:
                result["com_lig_a"].append(0.0)
                result["cont_lig_a"].append(0)

            if com_l is not None and com_b is not None:
                result["com_lig_b"].append(round(float(np.linalg.norm(com_l - com_b)), 3))
                result["cont_lig_b"].append(get_contacts(ca_b_u, lig_u))
            else:
                result["com_lig_b"].append(0.0)
                result["cont_lig_b"].append(0)

            if com_a is not None and com_b is not None:
                result["com_a_b"].append(round(float(np.linalg.norm(com_a - com_b)), 3))
                result["cont_a_b"].append(get_contacts(ca_a_u, ca_b_u))
            else:
                result["com_a_b"].append(0.0)
                result["cont_a_b"].append(0)

    except Exception as e:
        print(f"⚠️  Analysis error: {e}")
        traceback.print_exc()
        if not result["times"]:
            return None
    try:
        fel = compute_fel_landscape(result["rmsd_complex"], result["rg"])
        if fel:
            result["fel"] = fel
    except Exception as e:
        print(f"⚠️  FEL computation failed: {e}")

    return result


def compute_fel_landscape(rmsd_values, rg_values, bins=25):
    """
    Build a 2D Boltzmann-weighted conformational landscape from already-computed
    RMSD and Rg arrays (no trajectory re-reading needed).

    Returns a dict suitable for JSON serialisation:
      - energy:   2D list [bins × bins] of ΔE values (kcal/mol)
                  0.0 → unvisited bins (rendered as transparent)
      - xmid:     bin centres for RMSD axis (Å)
      - ymid:     bin centres for Rg axis (Å)
      - min_rmsd: RMSD of global minimum bin centre (Å)
      - min_rg:   Rg  of global minimum bin centre (Å)
      - n_frames: number of frames used
    Returns None if there are too few valid data points.
    """
    # ── Gaussian smoothing ──────────────────────────────────────
    # Set SMOOTH_SIGMA > 0 to smooth the histogram before computing energies.
    # This interpolates counts across neighbouring bins, giving a continuous-
    # looking landscape even with few frames (similar to g_sham in GROMACS).
    # Set to 0 to disable smoothing entirely. 1 to able it

    SMOOTH_SIGMA = 1.0
    # ───────────────────────────────────────────────────────────

    if not rmsd_values or not rg_values:
        return None

    rmsd = np.array(rmsd_values, dtype=float)
    rg   = np.array(rg_values,   dtype=float)

    # Exclude frame 0 (RMSD=0 is the reference frame, not a sampled state)
    # and any failed frames (rg=0 or non-finite values)
    valid = (rmsd > 0) & (rg > 0) & np.isfinite(rmsd) & np.isfinite(rg)
    rmsd  = rmsd[valid]
    rg    = rg[valid]

    if len(rmsd) < 5:
        return None

    kT   = 0.596   # kcal/mol  (k_B · 300 K)
    H, xedges, yedges = np.histogram2d(rmsd, rg, bins=bins)
    H    = H.T                   # rows = Rg, cols = RMSD

    # Capture which bins have real frames BEFORE smoothing
    mask_real = (H > 0).astype(int).tolist()

    # Optional Gaussian smoothing
    if SMOOTH_SIGMA > 0:
        from scipy.ndimage import gaussian_filter
        H = gaussian_filter(H, sigma=SMOOTH_SIGMA)

    prob = H / H.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        energy = -kT * np.log(np.where(prob > 0, prob / prob[prob > 0].max(), np.nan))

    # Global minimum
    flat_min = np.nanargmin(energy)
    iy, ix   = np.unravel_index(flat_min, energy.shape)
    min_rmsd = float(0.5 * (xedges[ix] + xedges[ix + 1]))
    min_rg   = float(0.5 * (yedges[iy] + yedges[iy + 1]))

    xmid = [float(0.5 * (xedges[i] + xedges[i+1])) for i in range(bins)]
    ymid = [float(0.5 * (yedges[i] + yedges[i+1])) for i in range(bins)]

    # Serialise: NaN (unvisited) → JSON null so frontend can distinguish
    # them from ΔE=0.0 (the global minimum bin).
    energy_list = [[None if np.isnan(v) else float(v) for v in row] for row in energy.tolist()]

    return {
        "energy":    energy_list,   # [bins_rg][bins_rmsd]
        "mask_real": mask_real,     # 1=bin with real frames, 0=interpolated
        "xmid":      xmid,          # RMSD axis
        "ymid":      ymid,          # Rg axis
        "min_rmsd":  min_rmsd,
        "min_rg":    min_rg,
        "n_frames":  int(len(rmsd)),
    }




import subprocess

def extract_last_frame_pdb(pdb_path, xtc_path, system_name, replica_num):
    """
    Extract the last frame from the trajectory as a PDB file using GROMACS.
    Only includes protein + ligand (strips water/ions).
    Writes to VIEWER_DIR/current_frame.pdb (overwrites).
    Returns the output path or None on failure.
    """
    if not MDA_AVAILABLE:
        return None
    if not pdb_path or not xtc_path:
        return None
    if not os.path.exists(pdb_path) or not os.path.exists(xtc_path):
        return None

    output_path = os.path.join(VIEWER_DIR, f"{system_name}_r{replica_num}.pdb")
    
    # Clear old PDBs in viewer directory to prevent accumulation
    try:
        for f in os.listdir(VIEWER_DIR):
            if f.endswith(".pdb"):
                os.remove(os.path.join(VIEWER_DIR, f))
    except Exception as e:
        print(f"⚠️  Cleanup error: {e}")

    tpr_path = xtc_path.replace(".xtc", ".tpr")
    s_path = tpr_path if os.path.exists(tpr_path) else pdb_path

    try:
        u = mda.Universe(pdb_path, xtc_path)
        if len(u.trajectory) == 0:
            return None

        last_time = u.trajectory[-1].time

        # Run GROMACS trjconv
        cmd = [
            "gmx", "trjconv",
            "-s", s_path,
            "-f", xtc_path,
            "-o", output_path,
            "-dump", str(last_time),
            "-pbc", "whole"
        ]
        
        # Disable GROMACS backups to prevent #file.pdb.1# clutter
        env = os.environ.copy()
        env["GMX_MAXBACKUP"] = "-1"
        
        process = subprocess.run(
            cmd, 
            input="0\n", 
            capture_output=True, 
            text=True, 
            check=False,
            env=env
        )

        if process.returncode != 0:
            print(f"⚠️  trjconv failed: {process.stderr}")
            # Fallback to pure MDAnalysis
            sel = _safe_select(u, "protein or resname MOL or resname LIG or resname UNL")
            if sel is None or len(sel) == 0:
                sel = _safe_select(u, "not (resname SOL or resname WAT or resname HOH or resname NA or resname CL)")
            if sel is not None and len(sel) > 0:
                sel.write(output_path)
            return output_path

        # Strip water and ions from the generated PDB
        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                lines = f.readlines()
            
            with open(output_path, "w") as f:
                for line in lines:
                    if line.startswith(("ATOM", "HETATM")):
                        resname = line[17:21].strip()
                        if resname in ["SOL", "WAT", "HOH", "NA", "CL", "K", "MG", "CA", "ZN"]:
                            continue
                    f.write(line)
                    
        return output_path

    except Exception as e:
        print(f"⚠️  PDB extraction error: {e}")
        return None
def extract_trajectory_pdb(pdb_path, xtc_path, system_name, replica_num, n_frames=20):
    """
    Extract the last n_frames from the trajectory as a multi-model PDB using GROMACS.
    Only includes protein + ligand.
    """
    if not MDA_AVAILABLE: return None
    if not pdb_path or not xtc_path: return None
    if not os.path.exists(xtc_path): return None

    output_path = os.path.join(VIEWER_DIR, f"{system_name}_r{replica_num}_traj.pdb")
    
    # Cleanup old trajectory pdbs
    try:
        for f in os.listdir(VIEWER_DIR):
            if f.endswith("_traj.pdb"):
                os.remove(os.path.join(VIEWER_DIR, f))
    except Exception:
        pass

    tpr_path = xtc_path.replace(".xtc", ".tpr")
    s_path = tpr_path if os.path.exists(tpr_path) else pdb_path

    try:
        u = mda.Universe(pdb_path, xtc_path)
        if len(u.trajectory) == 0: return None

        start_idx = max(0, len(u.trajectory) - n_frames)
        start_time = u.trajectory[start_idx].time

        cmd = [
            "gmx", "trjconv",
            "-s", s_path,
            "-f", xtc_path,
            "-o", output_path,
            "-b", str(start_time),
            "-pbc", "whole"
        ]
        
        env = os.environ.copy()
        env["GMX_MAXBACKUP"] = "-1"
        
        process = subprocess.run(cmd, input="0\n", capture_output=True, text=True, check=False, env=env)

        if process.returncode != 0:
            print(f"⚠️ trjconv traj failed: {process.stderr}")
            return None

        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                lines = f.readlines()
            with open(output_path, "w") as f:
                for line in lines:
                    if line.startswith(("ATOM", "HETATM")):
                        resname = line[17:21].strip()
                        if resname in ["SOL", "WAT", "HOH", "NA", "CL", "K", "MG", "CA", "ZN"]:
                            continue
                    f.write(line)
        return output_path

    except Exception as e:
        print(f"⚠️ Traj extraction error: {e}")
        return None

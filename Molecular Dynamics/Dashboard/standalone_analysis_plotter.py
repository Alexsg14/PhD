import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import warnings

# Suppress warnings from MDAnalysis
warnings.filterwarnings("ignore", category=UserWarning, module="MDAnalysis")

try:
    import MDAnalysis as mda
    from MDAnalysis.analysis import rms, align
    from MDAnalysis.analysis.distances import distance_array
    import MDAnalysis.transformations as trans
    MDA_AVAILABLE = True
except ImportError:
    MDA_AVAILABLE = False
    print("MDAnalysis is not installed.")

BASE_DIR = os.environ.get("MD_DASHBOARD_BASE_DIR", "/home/ciqus/aliciaft3/YAP_TEAD_Junio26")
OUTPUT_DIR = "./analysis_plots"

def _safe_select(u, sel):
    try:
        ag = u.select_atoms(sel)
        return ag if len(ag) > 0 else None
    except Exception:
        return None

def compute_analyses(pdb_path, xtc_paths, frame_step=1):
    """
    Compute RMSD, Rg, CoM distance, and contacts from trajectory.
    Applies PBC corrections and alignment.
    """
    if not MDA_AVAILABLE:
        return None
    
    print(f"  Loading {os.path.basename(pdb_path)} and {len(xtc_paths)} trajectory files...")
    try:
        # Load Universe with multiple trajectories sequentially
        u = mda.Universe(pdb_path, *xtc_paths)
    except Exception as e:
        print(f"  Error loading trajectory: {e}")
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
    }

    protein = _safe_select(u, "protein")
    ca_protein = _safe_select(u, "protein and name CA")
    backbone = _safe_select(u, "protein and backbone")
    
    ref = mda.Universe(pdb_path, xtc_paths[0])
    ref.trajectory[0]
    
    ca_a_u = _safe_select(u, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A) and name CA")
    if not ca_a_u: ca_a_u = _safe_select(u, "protein and (chainID A or chainID 0) and name CA")
    ca_a_ref = _safe_select(ref, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A) and name CA") if ca_a_u else None
    if not ca_a_ref and ca_a_u: ca_a_ref = _safe_select(ref, "protein and (chainID A or chainID 0) and name CA")

    ca_b_u = _safe_select(u, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B) and name CA")
    if not ca_b_u: ca_b_u = _safe_select(u, "protein and (chainID B or chainID 1) and name CA")
    ca_b_ref = _safe_select(ref, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B) and name CA") if ca_b_u else None
    if not ca_b_ref and ca_b_u: ca_b_ref = _safe_select(ref, "protein and (chainID B or chainID 1) and name CA")

    protein_a = _safe_select(u, "protein and (segid A or segid seg_0 or segid seg_0_Protein_chain_A or segid Protein_chain_A or chainID A or chainID 0)")
    protein_b = _safe_select(u, "protein and (segid B or segid seg_1 or segid seg_1_Protein_chain_B or segid Protein_chain_B or chainID B or chainID 1)")

    lig_u = _safe_select(u, "resname MOL or resname LIG or resname UNL")
    lig_ref = _safe_select(ref, "resname MOL or resname LIG or resname UNL")

    bb_u = backbone
    bb_ref = _safe_select(ref, "protein and backbone")

    if not bb_u or not protein:
        print("  No protein atoms found.")
        return None

    # Apply PBC correction
    print("  Applying PBC corrections...")
    try:
        protein_for_pbc = _safe_select(u, "protein") or u.select_atoms("all")
        transform = [
            trans.unwrap(protein_for_pbc),
            trans.center_in_box(protein_for_pbc, center='geometry'),
            trans.wrap(u.atoms, compound='fragments')
        ]
        u.trajectory.add_transformations(*transform)

        ref_protein = _safe_select(ref, "protein") or ref.select_atoms("all")
        ref_transform = [
            trans.unwrap(ref_protein),
            trans.center_in_box(ref_protein, center='geometry'),
            trans.wrap(ref.atoms, compound='fragments')
        ]
        ref.trajectory.add_transformations(*ref_transform)
        ref.trajectory[0] 
    except Exception as e:
        print(f"  PBC correction failed: {e}")

    print(f"  Processing {n_frames} frames...")
    
    def get_com(sel): return sel.center_of_mass() if sel is not None else None
    def get_contacts(target_sel, ref_sel, cutoff=5.0): 
        if target_sel is None or ref_sel is None or len(target_sel) == 0 or len(ref_sel) == 0: return 0
        dists = distance_array(target_sel.positions, ref_sel.positions)
        return int((dists < cutoff).any(axis=1).sum())

    base_time = 0.0
    last_ts_time = 0.0

    for i, ts in enumerate(u.trajectory[::frame_step]):
        # Keep time strictly monotonic when spanning multiple xtc files
        if ts.time < last_ts_time:
            base_time += last_ts_time
        
        current_time_ns = (base_time + ts.time) / 1000.0
        result["times"].append(current_time_ns)
        last_ts_time = ts.time
        
        if bb_u and bb_ref:
            align.alignto(u, ref, select="protein and backbone")
        
        if bb_u and bb_ref:
            diff = bb_u.positions - bb_ref.positions
            result["rmsd_complex"].append(np.sqrt(np.mean(np.sum(diff**2, axis=1))))
        else:
            result["rmsd_complex"].append(0.0)
            
        if ca_a_u and ca_a_ref and len(ca_a_u) == len(ca_a_ref):
            try: result["rmsd_chain_a"].append(rms.rmsd(ca_a_u.positions, ca_a_ref.positions, superposition=True))
            except: result["rmsd_chain_a"].append(0.0)
        else: result["rmsd_chain_a"].append(0.0)

        if ca_b_u and ca_b_ref and len(ca_b_u) == len(ca_b_ref):
            try: result["rmsd_chain_b"].append(rms.rmsd(ca_b_u.positions, ca_b_ref.positions, superposition=True))
            except: result["rmsd_chain_b"].append(0.0)
        else: result["rmsd_chain_b"].append(0.0)

        if lig_u and lig_ref and len(lig_u) == len(lig_ref):
            try: result["rmsd_ligand"].append(rms.rmsd(lig_u.positions, lig_ref.positions, superposition=True))
            except: result["rmsd_ligand"].append(0.0)
        else: result["rmsd_ligand"].append(0.0)

        try: result["rg"].append(protein.radius_of_gyration())
        except: result["rg"].append(0.0)

        if protein_a is not None and len(protein_a) > 0:
            result["rg_chain_a"].append(protein_a.radius_of_gyration())
        else: result["rg_chain_a"].append(0.0)

        if protein_b is not None and len(protein_b) > 0:
            result["rg_chain_b"].append(protein_b.radius_of_gyration())
        else: result["rg_chain_b"].append(0.0)

        com_p = get_com(protein)
        com_a = get_com(ca_a_u)
        com_b = get_com(ca_b_u)
        com_l = get_com(lig_u)

        if com_l is not None and com_p is not None:
            result["com_lig_prot"].append(np.linalg.norm(com_l - com_p))
            result["cont_lig_prot"].append(get_contacts(ca_protein, lig_u))
        else:
            result["com_lig_prot"].append(0.0)
            result["cont_lig_prot"].append(0)

        if com_l is not None and com_a is not None:
            result["com_lig_a"].append(np.linalg.norm(com_l - com_a))
            result["cont_lig_a"].append(get_contacts(ca_a_u, lig_u))
        else:
            result["com_lig_a"].append(0.0)
            result["cont_lig_a"].append(0)

        if com_l is not None and com_b is not None:
            result["com_lig_b"].append(np.linalg.norm(com_l - com_b))
            result["cont_lig_b"].append(get_contacts(ca_b_u, lig_u))
        else:
            result["com_lig_b"].append(0.0)
            result["cont_lig_b"].append(0)

        if com_a is not None and com_b is not None:
            result["com_a_b"].append(np.linalg.norm(com_a - com_b))
            result["cont_a_b"].append(get_contacts(ca_a_u, ca_b_u))
        else:
            result["com_a_b"].append(0.0)
            result["cont_a_b"].append(0)
            
        if (i+1) % 100 == 0:
            print(f"  Processed {i+1}/{n_frames} frames", end="\r")
            
    print(f"  Processed {n_frames}/{n_frames} frames. Done.")
    return result

def plot_time_series(times, data_dict, title, ylabel, out_path):
    plt.figure(figsize=(10, 6))
    for label, values in data_dict.items():
        if any(v > 0 for v in values): # only plot if there is data
            plt.plot(times, values, label=label, alpha=0.8, linewidth=1.5)
    plt.xlabel("Time (ns)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

def plot_fel(rmsd_values, rg_values, out_path, bins=50, smooth_sigma=1.0):
    if not rmsd_values or not rg_values:
        return
        
    rmsd = np.array(rmsd_values, dtype=float)
    rg = np.array(rg_values, dtype=float)
    
    # Exclude frame 0 (RMSD=0) and failed frames
    valid = (rmsd > 0) & (rg > 0) & np.isfinite(rmsd) & np.isfinite(rg)
    rmsd = rmsd[valid]
    rg = rg[valid]
    
    if len(rmsd) < 5:
        return

    kT = 0.596 
    H, xedges, yedges = np.histogram2d(rmsd, rg, bins=bins)
    H = H.T

    if smooth_sigma > 0:
        from scipy.ndimage import gaussian_filter
        H = gaussian_filter(H, sigma=smooth_sigma)

    prob = H / H.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        energy = -kT * np.log(np.where(prob > 0, prob / prob[prob > 0].max(), np.nan))
    
    X, Y = np.meshgrid(xedges[:-1] + np.diff(xedges)/2, yedges[:-1] + np.diff(yedges)/2)

    plt.figure(figsize=(8, 6))
    cmap = plt.cm.jet
    cmap.set_bad(color='white')
    
    contour = plt.contourf(X, Y, energy, levels=20, cmap=cmap)
    plt.colorbar(contour, label="Free Energy (kcal/mol)")
    plt.xlabel("RMSD (Å)")
    plt.ylabel("Radius of Gyration (Å)")
    plt.title("Free Energy Landscape")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

def find_system_trajectories(replica_dir, replica_num):
    xtc_paths = []
    prefix = f"r{replica_num}_"
    # Append equilibration steps first
    for i in range(1, 14):
        p = os.path.join(replica_dir, f"{prefix}step{i}_eq.xtc")
        if os.path.exists(p):
            xtc_paths.append(p)
    # Then production
    p_tray = os.path.join(replica_dir, f"{prefix}tray.xtc")
    if os.path.exists(p_tray):
        xtc_paths.append(p_tray)
    return xtc_paths

def analyze_single_replica(rep_dir, sys_name, rep_num):
    pdb_path = os.path.join(rep_dir, "complex_with_ligand.pdb")
    if not os.path.exists(pdb_path):
        # Fallback to system dir
        sys_dir = os.path.dirname(rep_dir)
        pdb_path = os.path.join(sys_dir, "complex_with_ligand.pdb")
        
    if not os.path.exists(pdb_path):
        print(f"  Skipping replica {rep_num} (no PDB found)")
        return
        
    xtc_paths = find_system_trajectories(rep_dir, rep_num)
    if not xtc_paths:
        print(f"  Skipping replica {rep_num} (no trajectories found)")
        return
        
    print(f"\n--- Replica {rep_num} ---")
    results = compute_analyses(pdb_path, xtc_paths, frame_step=1)
    if not results:
        print("  Analysis yielded no results.")
        return
        
    out_rep_dir = os.path.join(OUTPUT_DIR, sys_name, f"replica_{rep_num}")
    os.makedirs(out_rep_dir, exist_ok=True)
    
    times = results["times"]
    
    # Plot RMSD
    plot_time_series(times, {
        "Complex": results["rmsd_complex"],
        "Chain A": results["rmsd_chain_a"],
        "Chain B": results["rmsd_chain_b"],
        "Ligand": results["rmsd_ligand"]
    }, "RMSD over time", "RMSD (Å)", os.path.join(out_rep_dir, "rmsd.png"))
    
    # Plot Rg
    plot_time_series(times, {
        "Complex": results["rg"],
        "Chain A": results["rg_chain_a"],
        "Chain B": results["rg_chain_b"]
    }, "Radius of Gyration over time", "Rg (Å)", os.path.join(out_rep_dir, "rg.png"))
    
    # Plot Distances (CoM)
    plot_time_series(times, {
        "Ligand - Complex": results["com_lig_prot"],
        "Ligand - Chain A": results["com_lig_a"],
        "Ligand - Chain B": results["com_lig_b"],
        "Chain A - Chain B": results["com_a_b"]
    }, "Center of Mass Distances", "Distance (Å)", os.path.join(out_rep_dir, "com_distances.png"))
    
    # Plot Contacts
    plot_time_series(times, {
        "Ligand - Complex": results["cont_lig_prot"],
        "Ligand - Chain A": results["cont_lig_a"],
        "Ligand - Chain B": results["cont_lig_b"],
        "Chain A - Chain B": results["cont_a_b"]
    }, "Number of Contacts (< 5Å)", "Contacts", os.path.join(out_rep_dir, "contacts.png"))
    
    # Plot FEL
    plot_fel(results["rmsd_complex"], results["rg"], os.path.join(out_rep_dir, "fel_rmsd_rg.png"), bins=50, smooth_sigma=1.0)
    
    print(f"  Plots saved to {out_rep_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Standalone Analysis Plotter")
    parser.add_argument("--replica_dir", type=str, help="Path to a specific replica directory to analyze (e.g., /path/to/TEAD_ALA48/replica_1). If not provided, it scans BASE_DIR.")
    args = parser.parse_args()

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if args.replica_dir:
        # Analyze only this single replica
        rep_dir = os.path.abspath(args.replica_dir)
        if not os.path.isdir(rep_dir):
            print(f"Error: Directory {rep_dir} does not exist.")
            return
            
        sys_name = os.path.basename(os.path.dirname(rep_dir))
        rep_name = os.path.basename(rep_dir)
        try:
            rep_num = int(rep_name.split("_")[-1])
        except ValueError:
            print(f"Warning: Could not parse replica number from {rep_name}. Defaulting to 1.")
            rep_num = 1
            
        print(f"\n==============================================")
        print(f"Analyzing specific replica: {sys_name} / {rep_name}")
        print(f"==============================================")
        analyze_single_replica(rep_dir, sys_name, rep_num)

    else:
        # Mass scan logic
        system_dirs = sorted(glob.glob(os.path.join(BASE_DIR, "TEAD_*")) + 
                             glob.glob(os.path.join(BASE_DIR, "YAP_*")))
                             
        for sys_dir in system_dirs:
            sys_name = os.path.basename(sys_dir)
            print(f"\n==============================================")
            print(f"Analyzing system: {sys_name}")
            print(f"==============================================")
            
            for rep_num in [1, 2, 3]:
                rep_dir = os.path.join(sys_dir, f"replica_{rep_num}")
                if not os.path.exists(rep_dir):
                    continue
                analyze_single_replica(rep_dir, sys_name, rep_num)

if __name__ == "__main__":
    main()

# Peptidomics MD Trajectory Analysis Suite

This folder contains a collection of analysis engines and processing workflows designed to evaluate coarse-grained (Martini 2 and Martini 3) Molecular Dynamics (MD) trajectories of peptide-lipid bilayer systems. It includes tools for calculating peptide orientation (tilt/roll), membrane contacts, center-of-mass positions, area-per-lipid, density maps, and dipole/hydrophobic moments.

---

## 📂 Directory Contents

### 1. Analysis & Plotting Engines (Python)
*   **[`modular_analysis.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/modular_analysis.py)**: A comprehensive modular tool for calculating:
    *   **Tilt & Azimuth Angles**: Peptide orientation relative to the membrane normal.
    *   **Rolling Angle**: Rotation of the peptide around its principal axis.
    *   **Z-Positions & Contacts**: Monomer/bead coordinates relative to the bilayer center, and contact statistics (peptide-water, peptide-headgroups, peptide-tails).
*   **[`SPM_Analysis.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/SPM_Analysis.py)**: Performs global physical characterization of the peptide-membrane system:
    *   Leaflet division (upper/lower) and Voronoi area-per-lipid calculation.
    *   Electrostatic and hydrophobic dipole moments.
    *   2D lipid density maps around the peptide.
*   **[`SuPepDex.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/SuPepDex.py)**: Utility database wrapper containing constants, amino acid hydrophobicity coefficients, and topology-specific lipid definitions.

### 2. Workflow & Processing Scripts (Bash)
*   **[`peptidomic_analysis.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/peptidomic_analysis.sh)**: A simple runner script to execute the `modular_analysis.py` pipeline.
*   **[`conda_analysis_spm.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/conda_analysis_spm.sh)**: Cluster batch submission script (`sbatch`) designed to run the full `SPM_Analysis.py` suite.
*   **[`trajectory_processing.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/trajectory_processing.sh)**: GROMACS pre-processing pipeline. It automates trajectory concatenation (`trjcat`), frame skipping (`trjconv`), PBC cluster reconstruction, and `nojump` corrections before analyzing.
*   **[`simulation_setup.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/Analysis_MD_Peptidomics/simulation_setup.sh)**: A step-by-step interactive command-line walkthrough to prepare and run Martini simulations for peptides in water and lipid membranes.

### 3. Plotting Styles & Assets
*   **`style_SPM/`**: Style directory containing:
    *   `SuPepMem.mplstyle`: Custom Matplotlib theme for publication-quality figures.
    *   `DIN_Condensed.ttf` / `avenir-next-*.ttf`: TTF fonts used in the plots.

---

## ⚙️ Environment Configuration

These scripts are optimized for compute clusters (like CESGA) but support local path customization. Use the environment variable `PEPTIDOMICA_BASE_PATH` to point to your simulation folders without editing the scripts:

```bash
export PEPTIDOMICA_BASE_PATH="/path/to/your/simulations"
./peptidomic_analysis.sh
```

---

## 🚀 Usage Examples

### 1. Run Complete Modular Analysis (Tilt, Roll, Contacts)
```bash
python modular_analysis.py \
    -top md.tpr \
    -traj traj_skip100.xtc \
    --analyses tilt rolling zcontacts \
    --rolling_skip 10 \
    -out _RESULTS
```

### 2. Plot Pre-Computed Data from CSVs (No Recalculation)
```bash
python modular_analysis.py \
    -plot \
    -csv_dir _RESULTS \
    -out _RESULTS \
    --do_all_plots
```

### 3. Run Physical Characterization Suite (Area, Dipoles, Density Maps)
Submit a cluster job using the provided batch script:
```bash
sbatch conda_analysis_spm.sh
```
Or run directly:
```bash
python SPM_Analysis.py \
    -f /path/to/simulation \
    -o /path/to/output \
    -tpr md.tpr \
    -xtc traj.xtc \
    -mdp prod.mdp \
    -ff martini22 \
    -A
```

# Molecular Dynamics Analysis & Processing Tools

This directory contains analytical scripts, trajectory manipulation utilities, and post-processing tools for Molecular Dynamics (MD) simulations, specifically tailored for lipid-protein systems, Martini coarse-grained models, and Metadynamics free energy surfaces.

---

## 📂 Subdirectory Structure

```
Molecular Dynamics/
├── Analysis_MD_Peptidomics/                  # Coarse-grained peptide-membrane analysis tools
│   ├── modular_analysis.py                   # Calculates tilt, azimuth, roll, contacts, and Z positions
│   ├── SPM_Analysis.py                       # Physical properties (leaflet area, dipoles, density maps)
│   ├── trajectory_processing.sh              # GROMACS trajectory pre-processing pipeline
│   └── peptidomic_analysis.sh                # Script wrapper for modular_analysis.py
├── Spin_scripts/
│   ├── block_average.py                      # Block average statistical uncertainty tool
│   ├── pmf_analysis.py                       # 2D Potential of Mean Force (PMF) visualizer
│   └── afinador_minimos.sh                   # Minima finder shell script
├── PMFs/                                     # Output directory for PMF plots and dat files
└── VMD/                                      # Tcl & Python scripts for VMD rendering
```

---

## 🛠️ Main Tools & Scripts

### 1. Peptidomics Trajectory Analysis (`Analysis_MD_Peptidomics/modular_analysis.py`)
Analyzes coarse-grained (Martini) trajectories and structures to calculate:
- Orientation angles (tilt, azimuth, and rolling angle).
- Z-axis center-of-mass positions of peptide monomers relative to the membrane center.
- Inter-molecular contact counts between peptides, lipid headgroups, and water.

**Usage:**
```bash
# Process trajectory and output CSVs & plots
python Analysis_MD_Peptidomics/modular_analysis.py \
    -top md.tpr \
    -traj traj_skip100.xtc \
    --analyses tilt rolling zcontacts \
    --rolling_skip 10 \
    -out Results_Dir

# Re-generate plots from pre-computed CSV files
python Analysis_MD_Peptidomics/modular_analysis.py \
    -plot \
    -csv_dir Results_Dir \
    -out Results_Dir \
    --do_all_plots
```

---

### 2. Block Averaging Uncertainty Analysis (`Spin_scripts/block_average.py`)
Computes statistical uncertainty for time-correlated time series data (such as metadynamics collective variables or free energy profiles) using the Flyvbjerg-Petersen block averaging algorithm (`doi:10.1063/1.457480`).

---

### 3. Free Energy Surface (PMF) Visualizer (`Spin_scripts/pmf_analysis.py`)
Reads PLUMED 2D `fesd1d2.dat` files alongside 1D block-averaged `CV1_BA.dat` files to build 2D contour maps with projected 1D energy margins and error bands.

---

### 4. Automated Trajectory Pre-processing (`Analysis_MD_Peptidomics/trajectory_processing.sh`)
SLURM job script for pre-processing GROMACS trajectories (concatenation, frame skipping, PBC cluster treatment, and `nojump` correction) before running contact analysis.

---

### 5. Automated VMD Rendering & Custom Styles (`VMD/`)
Automates high-quality image and video rendering using VMD (Visual Molecular Dynamics) and the Tachyon ray tracer.
- **`run_vmd_render.py`**: Python launcher script to execute VMD in text-only mode (`-dispdev text`) with a given structure and render script.
- **`RENDER_VMD.tcl`**: Master Tcl script containing custom rendering routines (`giro`, `video`, `make_movie`, `pic`, `obj`, `double`).
- **Style Scripts**:
  - `materials.tcl`: Adds custom materials like `RealWater` with realistic opacity and shininess.
  - `style_vmd.tcl` / `Alex_style.tcl` / `style_yt.tcl`: Customized cartoon/licorice/surf styles for atom selections.
  - `style_vmd_martini.tcl` / `style_vmd_martini_peptidomica.tcl`: Tailored colors and representations for Martini coarse-grained topologies.
  - `style_vmd_docking.tcl`: Colors chains and poses to visualize docking orientations.
  - `style_vmd_RMSD.tcl`: Maps RMSD fluctuations to color scales.

**Usage:**
```bash
python VMD/run_vmd_render.py \
    --render-tcl VMD/RENDER_VMD.tcl \
    --pdb MIN_FRAME2.pdb \
    --do pic \
    --out-dir _RENDERS
```

# PMF & FES Analysis Toolkit

This folder contains a suite of Bash and Python scripts designed to analyze, monitor, and visualize Free Energy Surfaces (FES) and Potentials of Mean Force (PMF) from Metadynamics simulations (both standard and Well-Tempered). The scripts process PLUMED outputs like `HILLS` and `COLVAR` files.

---

## 📂 Folder Contents

### 1. Bash Master Scripts (Command-Line Entrypoints)
*   **[`master_hills.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/master_hills.sh)**: The primary master script for 1D FES/PMF workflows. It wraps python execution to generate FES curve evolution plots, restricted Region of Interest (ROI) fits, PMF profiles, and integrates areas to calculate $\Delta G$.
*   **[`master_hills_2D.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/master_hills_2D.sh)**: Staging master script adjusted for 2D Metadynamics reconstructions.
*   **[`blocks_analysis.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/blocks_analysis.sh)**: Automates the execution of comparative block analysis over multiple segments of your trajectory.
*   **[`manual_hills.sh`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/manual_hills.sh)**: A simple runner script for quick testing and manual debugging of specific systems.

### 2. Processing & Plotting Engines (Python)
*   **[`hills_analysis.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills_analysis.py)**: The core 1D rendering engine. It handles:
    *   FES curve reconstruction from cumulative hills.
    *   Outputting static FES images (`fes.png`, `fes_trail_.png`).
    *   Compiling trajectory videos/animations (e.g. `fes_movie.mp4` or gradient-style evolutions) using `ffmpeg`.
    *   $\Delta G$ calculation via relative probability area integration under the curves.
*   **[`2D_hills.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/2D_hills.py)**: Reconstructs and plots 2D free energy landscape contour maps from two Collective Variables.
*   **[`block_analysis_hills.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/block_analysis_hills.py)**: Standard error estimation script. It splits the $\Delta F(t)$ time series into varying block sizes to compute the standard error of the mean (SEM), outputting both CSV logs and plotting graphs.
*   **[`compare_last_hills.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/compare_last_hills.py)**: Runs multiple block analyses for different segments of the simulation (e.g. last 10k, 20k, 40k, 80k hills) and plots them together for a direct convergence comparison.
*   **[`meta_diagnose.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/meta_diagnose.py)**: A diagnostic tool that parses `COLVAR` files. It evaluates the exploration of the collective variables, reports bin coverage inside the ROI, counts transitions, checks wall collisions, and suggests if WT metadynamics parameters (such as `HEIGHT`) should be adjusted.
*   **[`hills_live.py`](file:///home/ciqus/GIT/Github_Personal/PhD/Molecular%20Dynamics/PMFs/hills_live.py)**: A utility script to monitor the active simulation's FES profile in real-time.

### 3. Legacy / Archival
*   **`hills_alicia.py`**: An older predecessor of `hills_analysis.py`, retained only for compatibility and historical reference.

---

## ⚙️ Portability & Configuration

All Bash wrappers are configured to support both local machines and compute clusters without requiring hardcoded absolute paths:

### Base Directory Customization
By default, the scripts point to the cluster storage directory:
`/mnt/netapp1/RES_SuPepMem/ALEX/_PMF_Peptidomica`

To run analyses on a different path (e.g., local folders or another server partition), export the `PMF_BASE_PATH` environment variable in your shell:
```bash
export PMF_BASE_PATH="/home/user/my_simulations"
./master_hills.sh
```

---

## 🚀 Usage Examples

### 1. Generating standard 1D FES profiles and movies
Runs reconstruction over the `HILLS_WT` file, fits plots to the region of interest, and generates animation MP4 files:
```bash
./master_hills.sh HILLS_WT output_folder --movie --limits
```

### 2. Evaluating collective variable convergence
Diagnoses CV exploration and checks for convergence criteria from a `COLVAR` file:
```bash
python meta_diagnose.py COLVAR_WT --cv-name D.z --roi-min 0.0 --roi-max 7.0 --lower-wall -1.0 --upper-wall 9.0
```

### 3. Running statistical block analysis
Runs the comparative block size analysis using defined ranges for state A and B, testing different numbers of final hills:
```bash
./blocks_analysis.sh /path/to/sims system_folder output_subfolder 2.3 2.9 5.0 7.0 "10000 20000 40000 80000"
```

# SUDOE Project: Virtual Reality & Docking B-Factor Analysis (`Repo-SUDOE`)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GROMACS](https://img.shields.io/badge/GROMACS-2024.3-brightgreen.svg)](https://www.gromacs.org/)
[![ProLIF](https://img.shields.io/badge/ProLIF-0.4+-orange.svg)](https://prolif.readthedocs.io/)
[![OpenBabel](https://img.shields.io/badge/OpenBabel-3.1+-blue.svg)](http://openbabel.org/)

Tools for Virtual Reality (VR) 3D molecular visualization, automated GROMACS trajectory processing, protein-ligand interaction fingerprinting, and mapping AutoDock Vina binding energy rankings onto receptor structural B-factors for hot-spot detection in VR.

---

## 📑 Table of Contents

- [Features & Overview](#-features--overview)
- [Directory Architecture](#-directory-architecture)
- [B-Factor Energy Attribution Concept](#-b-factor-energy-attribution-concept)
- [Key Scripts & Pipeline](#-key-scripts--pipeline)
  - [1. Standalone VR B-Factor Processor (`VR_BFACTOR/ligand_energy_attribution_bfactor.py`)](#1-standalone-vr-b-factor-processor-vr_bfactorligand_energy_attribution_bfactorpy)
  - [2. Automated GROMACS & B-Factor Pipeline (`VR_BFACTOR/bfactor.sh`)](#2-automated-gromacs--b-factor-pipeline-vr_bfactorbfactorsh)
  - [3. ProLIF Interaction Fingerprinter (`VR_BFACTOR/aa_interaction_flags.py`)](#3-prolif-interaction-fingerprinter-vr_bfactoraa_interaction_flagspy)
- [Dependencies & Installation](#-dependencies--installation)
- [Visualization Protocol](#-visualization-protocol)

---

## 🎯 Features & Overview

- **B-Factor Energy Mapping:** Translates AutoDock Vina binding affinities (`REMARK VINA RESULT`) into receptor residue B-factors, allowing color-coded 3D structural heatmaps of binding hot spots in VR and molecular visualization tools (VMD, PyMOL).
- **Automated GROMACS Trajectory Assembly:** Concatenates multi-stage free energy perturbation (FEP) or equilibration trajectories (`min`, `eq`, `prod`) and centers system coordinates (`pbc mol`).
- **ProLIF Interaction Fingerprints:** Computes residue-level non-covalent interactions (hydrogen bonds, hydrophobic contacts, $\pi$-stacking, ionic interactions) across docking poses.
- **VR Asset Preparation:** Automated conversion of `.gro`, `.xtc`, `.pdbqt`, and `.sdf` files into VR-ready `.pdb` and `.xtc` outputs.

---

## 📁 Directory Architecture

```
Repo-SUDOE/
├── VR_BFACTOR/
│   ├── ligand_energy_attribution_bfactor.py # Standalone B-factor & VR asset generator
│   ├── bfactor.sh                            # Master Bash pipeline script (GROMACS + VR)
│   ├── ligand_energy_attribution.py          # Core B-factor calculation module for pipeline
│   ├── aa_interaction_flags.py               # ProLIF protein-ligand interaction calculator
│   └── aa_interaction_dict.py                # Interaction type definitions & dictionary mapping
└── README.md                                 # Module documentation
```

---

## 🧮 B-Factor Energy Attribution Concept

Receptor B-factors (temperature factors in PDB structures) are repurposed to visually highlight residues involved in high-affinity ligand interactions:

1. **Energy Ranking:** Docking poses from AutoDock Vina are sorted by binding energy ($\Delta G_{\text{bind}}$ in kcal/mol) in descending order:
   $$\text{Rank}(k) \in \{1, 2, \dots, M\}$$
   where Rank 1 corresponds to the pose with the highest affinity (most negative $\Delta G$).

2. **Distance Cutoff ($\le d_{\text{cutoff}}$):** For each receptor atom $a \in \text{Receptor}$ and residue $R$:
   $$d(a, l) = \| \mathbf{r}_a - \mathbf{r}_l \|_2, \quad \forall l \in \text{Ligand pose } k$$
   If $\min_{l} d(a, l) \le d_{\text{cutoff}}$ (default $5.0$ Å), the residue $R$ is assigned the rank of pose $k$.

3. **Maximum Rank Attribution:**
   $$B(R) = \max_{k \text{ contacting } R} \left( \text{Rank}(k) \right)$$
   Residues contacting top-ranked poses receive high B-factor values, rendering as intense colors in VR color schemes (e.g. Spectrum or B-factor colormaps).

---

## 🛠️ Key Scripts & Pipeline

### 1. Standalone VR B-Factor Processor (`VR_BFACTOR/ligand_energy_attribution_bfactor.py`)

Processes docking poses (`all.pdbqt`), ligand structures, receptor PDBs, and simulation trajectories, outputting a complete VR folder (`Output/VR`).

**Command Syntax:**
```bash
python VR_BFACTOR/ligand_energy_attribution_bfactor.py \
    --pdbqt_ligs all.pdbqt \
    --ligand_pdbqt ligand.pdbqt \
    --receptor_in receptor_clean.pdb \
    --sim_xtc preview_mol.xtc \
    --sim_gro preview_mol.gro \
    --cutoff 5.0 \
    --vr_folder ./Output/VR
```

**Output Files in VR Directory (`./Output/VR`):**
- `receptor.pdb`: Receptor structural file with energy-ranked B-factors assigned per residue.
- `ligand.pdb`: Clean reference ligand PDB.
- `all.pdb`: All converted docking poses.
- `center.pdb`: Centered reference structure from simulation.
- `center.xtc`: Trajectory for animation in VR.

---

### 2. Automated GROMACS & B-Factor Pipeline (`VR_BFACTOR/bfactor.sh`)

Automated bash script for GROMACS simulation workflows. It loads GROMACS, concatenates multi-part trajectories (`min_fep1`, `eq_fep`, `prod_fep`), handles periodic boundary condition centering (`gmx trjconv -pbc mol`), and runs B-factor attribution.

**Usage:**
```bash
bash VR_BFACTOR/bfactor.sh -p /path/to/simulation/dir -v /path/to/vr_output -l /path/to/ligand.pdb
```

**Parameters:**
- `-p`: Base working path containing GROMACS simulation outputs (`prod_fep.tpr`, `all.pdbqt`, etc.).
- `-v`: Destination directory for final VR assets.
- `-l`: Path to reference ligand PDB file.

---

### 3. ProLIF Interaction Fingerprinter (`VR_BFACTOR/aa_interaction_flags.py`)

Calculates detailed protein-ligand interaction fingerprints across all docking poses using [ProLIF](https://prolif.readthedocs.io/) and MDAnalysis.

**Usage:**
```bash
python VR_BFACTOR/aa_interaction_flags.py \
    --file /path/to/project \
    --pdb_path /path/to/receptor.pdb \
    --sdf_path /path/to/all.sdf \
    --output_path /path/to/aa_interactions_arx.json
```

**Output:** Generates a structured JSON file (`aa_interactions_arx.json`) recording interaction types (Hydrophobic, HBond, Pi-Stacking, Cation-Pi, Anionic, Cationic) per residue and per docking pose for VR display.

---

## 📦 Dependencies & Installation

Install required dependencies via Conda or pip:

```bash
# Create dedicated conda environment
conda create -n repo_sudoe -c conda-forge -c openbabel python=3.10 \
    biopython \
    mdanalysis \
    openbabel \
    numpy \
    matplotlib

# Activate environment
conda activate repo_sudoe

# Install ProLIF for interaction fingerprinting
pip install prolif
```

*Note: GROMACS (`gmx`) 2021+ is required for `bfactor.sh` trajectory processing.*

---

## 🥽 Visualization Protocol

To view the generated hot-spot B-factor heatmaps in molecular visualization software (such as VMD or PyMOL):

1. **VMD:** Load `receptor.pdb` and set **Graphics $\rightarrow$ Representations $\rightarrow$ Coloring Method $\rightarrow$ Beta**.
2. **PyMOL:** Load `receptor.pdb` and run `spectrum b, blue_white_red, minimum=1, maximum=80`.

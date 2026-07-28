# PhD Research: Computational Chemistry, Metadynamics, Proteomics & Virtual Reality

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GROMACS](https://img.shields.io/badge/GROMACS-2021+-brightgreen.svg)](https://www.gromacs.org/)
[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)

This repository consolidates computational research tools, enhanced sampling metadynamics web environments, simulation analysis pipelines, interactive Virtual Reality (VR) workflows, SWATH-MS proteomics data processing, and prepress document processing tools developed during PhD research.

---

## 📁 Repository Structure

```
PhD/
├── CESGA_scripts/            # Slurm HPC job monitoring & execution utilities for CESGA supercomputer
│   └── squeue.sh             # Color-coded Slurm queue status & active job summary tool
├── Helix_wheel/              # Helical wheel generator & hydrophobic dipole moment calculator
│   ├── heliquest.py          # Primary wheel renderer & vector plotter
│   ├── hydrophobic_moment.py # Hydrophobicity scales & dipole calculations
│   └── README.md             # Module documentation
├── Molecular Dynamics/       # MD analysis, PMF calculations, block averaging, VMD scripts
│   ├── Analysis/             # Trajectory treatment & contact/Z-position analysis
│   ├── Spin_scripts/         # Block average calculations & 2D PMF plotting
│   ├── PMFs/                 # Free energy surface calculations
│   └── VMD/                  # Visualization scripts
├── Proteomics/               # SWATH-MS proteomics processing, PCA, clustering & clinical severity heatmaps
│   ├── Data_analysis/        # Analysis scripts (analise_Julio26.py, Severity_matrix.py, run_volcano.py, MLR verification)
│   └── README.md             # Module documentation
├── Repo-SUDOE/               # VR B-factor energy mapping & interaction tools
│   ├── VR_BFACTOR/           # Energy attribution to receptor B-factors & ProLIF interaction tools
│   └── README.md             # Module documentation
├── _METADYNAMICS_LABORATORY/ # Interactive Metadynamics, OPES & PLUMED Analysis Suite
│   ├── docs/screenshots/     # Application interface screenshots
│   ├── metadynamics_laboratory/      # React 19 + Vite + Tailwind web application (5 modules: 1D/2D MetaD, 1D OPES, HILLS & OPES Inspectors)
│   ├── metadynamics_laboratory.sh   # Automated project generator script
│   ├── opes_simulator/               # Standalone OPES simulator prototype
│   ├── plot_single_fes_dat.py        # FES profile plotting utility script
│   └── README.md                     # Laboratory specific documentation
├── _PDF_Stamp_/              # Automated dynamic PDF stamping pipeline with PyMuPDF
│   ├── Stamps.py                     # Main Python stamping & preview script
│   └── README.md                     # Stamping tool documentation
├── _Visor_PDF_/              # Web application for PDF book-spread prepress visualization
│   ├── src/                          # React + Vite + Tailwind source code
│   ├── visor-pdf.html                # Standalone single-file HTML version
│   └── README.md                     # Visualizer documentation
├── create_conda.sh           # Environment bootstrap & dependency setup script
└── README.md                 # Main repository documentation & VR setup guide
```

---

## 📑 Table of Contents

- [Repository Structure](#-repository-structure)
- [VR Setup & Installation Protocol](#-vr-setup--installation-protocol)
  - [Smartphone Setup](#smartphone-setup)
    - [Meta Horizon App](#meta-horizon-app)
    - [Duo Mobile Authenticator](#duo-mobile-authenticator)
  - [PC Software Setup](#pc-software-setup)
    - [Meta Quest Link](#meta-quest-link)
    - [SideQuest](#sidequest)
- [NanoVer & OpenMM Interactive VR](#-nanover--openmm-interactive-vr)
  - [Environment Setup](#environment-setup)
  - [Running NanoVer PC-VR](#running-nanover-pc-vr)
  - [Running Standalone APK with JupyterLab](#running-standalone-apk-with-jupyterlab)
- [Modules Overview](#-modules-overview)
  - [Metadynamics & OPES Laboratory](#metadynamics--opes-laboratory)
  - [CESGA Supercomputing Utilities](#cesga-supercomputing-utilities)
  - [Helical Wheel & Hydrophobic Moment Generator](#helical-wheel--hydrophobic-moment-generator)
  - [Molecular Dynamics Analysis](#molecular-dynamics-analysis)
  - [Proteomics Processing](#proteomics-processing)
  - [SUDOE VR B-Factor Pipeline](#sudoe-vr-b-factor-pipeline)
  - [PDF Prepress Book Spread Visualizer](#pdf-prepress-book-spread-visualizer)
  - [Automated PDF Stamping Pipeline](#automated-pdf-stamping-pipeline)

---

## 🥽 VR Setup & Installation Protocol

This protocol guides the installation and configuration of Meta Quest headsets for interactive molecular dynamics visualization on Windows PCs and mobile devices.

### Smartphone Setup

#### **Meta Horizon App**
Used to pair, manage, and configure the Meta Quest headset.

1. **Sign In:** Use your designated lab credentials (`<your_lab_account@domain.com>`).
2. **Two-Factor Authentication:** Enter the verification code sent via SMS or generated by the [Authenticator App](#duo-mobile-authenticator).

> [!NOTE]
> When signing into an existing lab account on a new smartphone, choose **Mobile Number** for the first sign-in if Duo Mobile has not yet been set up on that device.

#### **Duo Mobile Authenticator**
1. In the **Meta Horizon App**, go to **Password & Security** $\rightarrow$ **Two-Step Authentication**.
2. Select **Authentication App** to generate a QR code.
3. Open **Duo Mobile**, scan the QR code, set a local PIN/passcode, and save the token.

---

### PC Software Setup

<a id="meta-quest-link"></a>
#### **Meta Quest Link**
Required for wired or wireless (AirLink) PC-VR streaming to run NanoVer via PC rendering.

1. Download and install **Meta Quest Link** from the [Meta Quest Help Page](https://www.meta.com/help/quest/).
2. Log in using your lab account email credentials.
3. Pair the headset via **AirLink** (over 5GHz Wi-Fi) or a high-speed **USB-C Link Cable**.

> [!IMPORTANT]
> To ensure correct OpenXR rendering in NanoVer, navigate to **Meta Quest Link** $\rightarrow$ **Settings** $\rightarrow$ **General** and set **OpenXR Runtime** to **Meta Quest**.

#### **SideQuest**
Used to sideload third-party APKs (such as *NanoVer*, *Cyclarity*, or *CoronaVRus Coaster*) and tune headset performance.

1. Download and install the **Advanced Installer** from [SideQuest](https://sidequestvr.com/).
2. Connect the Quest headset to the PC via USB-C cable.
3. Put on the headset and accept the **USB Debugging** prompt.
4. Drag and drop `.apk` files into SideQuest using the **Install APK** button (box with down-arrow).

> [!NOTE]
> **Developer Mode** must be turned ON in your Meta Horizon account to allow sideloading and custom app execution under **Unknown Sources**.

---

## 🎮 NanoVer & OpenMM Interactive VR

NanoVer enables interactive molecular dynamics (iMD) simulations where researchers can manipulate molecules in real-time inside Virtual Reality.

- [NanoVer GitHub Repository](https://github.com/IRL2/nanover-server-py)
- [NanoVer Official Documentation](https://irl2.github.io/nanover-docs/)

### Environment Setup

Install [Anaconda / Miniconda](https://www.anaconda.com/download) and create the dedicated environment:

```bash
# Create conda environment with NanoVer server dependencies
conda create -n nanover -c irl -c conda-forge nanover-server=0.1.2768 python=3.10

# Activate environment
conda activate nanover

# Install iMD client interface
conda install -c irl nanover-imd
```

### Running NanoVer PC-VR

1. Ensure the Quest headset is linked to the PC via **Meta Quest Link** (wired or AirLink).
2. Activate your Conda environment:
   ```bash
   conda activate nanover
   ```
3. Start the iMD-VR client application:
   ```bash
   NanoverIMD
   ```
4. Put on the headset to view and interact with the active simulation server.

---

### Running Standalone APK with JupyterLab

#### **Headset Preparation (MQ3):**
1. Turn on the headset and connect to the **same Wi-Fi network** as the host PC.
2. Launch the **NanoVer** app from **Library** $\rightarrow$ **Unknown Sources**.

#### **PC Host Preparation:**
1. Open **Anaconda Powershell Prompt** (or terminal).
2. Run:
   ```bash
   conda activate nanover
   python -m jupyterlab
   ```
3. Open JupyterLab in your simulation directory.
4. Execute the simulation setup cells to spin up an `OmniRunner` server instance.
5. In the Quest VR headset, select **Discover** $\rightarrow$ **Refresh** $\rightarrow$ connect to your PC's IP/port.

---

## 🔬 Modules Overview

### Metadynamics & OPES Laboratory
Located in [`_METADYNAMICS_LABORATORY/`](./_METADYNAMICS_LABORATORY/):
- **`metadynamics_laboratory/`**: React 19 + Vite + Tailwind web application combining 5 interactive simulation and analysis modules:
  1. **🧪 1D Metadynamics Simulator**: Overdamped Langevin dynamics with Box-Muller Gaussian thermal noise $\mathcal{N}(0, 1)$, Standard & Well-Tempered Metadynamics (WT-MetaD), custom math expression parser $V(x)$, PRNG seed lock (`mulberry32`), and session JSON export/restore.
  2. **🌐 2D Metadynamics Simulator**: High-performance HTML5 Canvas 2D heatmap renderer ($V$, $V+V_B$, $V_B$, $F_{\text{est}}$) at 60 FPS with scientific colormaps (Inferno, Viridis, Spectral, Plasma, Coolwarm), interactive walker position clicking, and trajectory path overlay.
  3. **⚡ OPES 1D Simulator**: On-the-Fly Probability Enhanced Sampling simulation, kernel weight/width adaptation, and real-time $P(s)$, $V(s)$, $F(s)$ reconstruction.
  4. **📈 PLUMED HILLS Visualizer & Inspector**: Non-blocking background Web Worker parsing engine, 60 FPS real-time FES timeline animation, drag-and-drop file upload, energy display modes ($F = -V$, relative $F_{\min} = 0$, Plateau Zero), multi-stage convergence analysis, and PLUMED `fes.dat` export.
  5. **🔍 PLUMED OPES Inspector**: Parses PLUMED `KERNELS` and `OPES_STATE` output files, analyzes kernel accumulation over time, and exports FES profiles to `fes.dat`.
- **`metadynamics_laboratory.sh`**: Automated project generator script to bootstrap a new, fully-configured instance of the laboratory application. See [`_METADYNAMICS_LABORATORY/README.md`](./_METADYNAMICS_LABORATORY/README.md) for full documentation.

### CESGA Supercomputing Utilities
Located in [`CESGA_scripts/`](./CESGA_scripts/):
- **`squeue.sh`**: Interactive CLI status monitoring tool for Slurm queues on the CESGA (FinisTerrae) supercomputer. Displays color-coded job status (Running, Pending), resource limits, start times, and active user job counts.

### Helical Wheel & Hydrophobic Moment Generator
Located in [`Helix_wheel/`](./Helix_wheel/):
- **`heliquest.py`**: Programmatic generation of 2D helical wheel diagrams (HeliQuest style) with residue chemical color coding, hydrophobic dipole moment vector ($\vec{\mu}_H$) direction rendering, and high-resolution PNG export.
- **`hydrophobic_moment.py`**: Mathematical module defining amino acid hydrophobicity scales (Fauchère-Pliska, Eisenberg), sequence charge calculation, Keller discrimination factor ($D$), and amino acid composition analysis.
- Accessible as both command-line scripts and as a Python package (`import Helix_wheel`). See [`Helix_wheel/README.md`](./Helix_wheel/README.md) for full module documentation.

### Molecular Dynamics Analysis
Located in [`Molecular Dynamics/`](./Molecular%20Dynamics/):
- **`Analysis/contactos_posz_analysis.py`**: Trajectory analysis script for calculating inter-component contacts (peptides, lipid heads, water) and Z-position trajectories relative to membrane centers.
- **`Spin_scripts/block_average.py`**: Implementation of Flyvbjerg-Petersen block averaging to estimate standard errors on time-correlated MD data.
- **`Spin_scripts/pmf_analysis.py`**: 2D Free Energy Surface (FES) & Potential of Mean Force (PMF) contour map visualizer.
- **`Spin_scripts/afinador_minimos.sh`**: Automated extraction of energy minima structures from COLVAR trajectories.
- **`VMD/`**: Automated script (`run_vmd_render.py`), master TCL controller (`RENDER_VMD.tcl`), and custom visualization styles (Martini coarse-grained membranes, docking poses, water opacity) to render high-quality graphics and videos in VMD using Tachyon.

### Proteomics Processing
Located in [`Proteomics/`](./Proteomics/):
- **`Data_analysis/analise_Julio26.py`**: Full SWATH-MS proteomics data processing pipeline (PCA, PowerTransformer feature scaling, K-Means clustering, silhouette scores, clinical data association).
- **`Data_analysis/Severity_matrix.py`**: Processes clinical patient data and binary biomarker tables to generate patient severity heatmaps using Seaborn.
- **`Data_analysis/run_volcano.py`**: Standalone differential expression analysis and Volcano Plot generator ($\log_2(\text{FC})$ vs $-\log_{10}(p)$). See [`Proteomics/README.md`](./Proteomics/README.md) for full module documentation.

### SUDOE VR B-Factor Pipeline
Located in [`Repo-SUDOE/`](./Repo-SUDOE/):
- **`VR_BFACTOR/ligand_energy_attribution_bfactor.py`**: Standalone processor mapping AutoDock Vina binding energy ranks onto receptor B-factor fields in PDB files for 3D visual analysis in VR.
- **`VR_BFACTOR/bfactor.sh`**: Automated GROMACS trajectory assembly and B-factor mapping pipeline script.
- **`VR_BFACTOR/aa_interaction_flags.py`**: ProLIF interaction fingerprint calculator exporting residue-level contact metadata. See [`Repo-SUDOE/README.md`](./Repo-SUDOE/README.md) for full module documentation.

### PDF Prepress Book Spread Visualizer
Located in [`_Visor_PDF_/`](./_Visor_PDF_/):
- **`src/App.jsx`**: Interactive React web application designed to preview PDF documents in facing-pages book-spread format (Pliegos), rendering page 1 (cover) on the right and pairs of even/odd pages with 3D spine fold shadows.
- Features preset paper format aspect ratio simulation (**A4**, **A5**, **Carta/Letter**, **Legal**, **Original**), real-time zoom, single-page inspection mode, and `IntersectionObserver` canvas lazy-loading.
- Includes a standalone browser variant ([`visor-pdf.html`](./_Visor_PDF_/visor-pdf.html)) runnable without Node.js. See [`_Visor_PDF_/README.md`](./_Visor_PDF_/README.md) for details.

### Automated PDF Stamping Pipeline
Located in [`_PDF_Stamp_/`](./_PDF_Stamp_/):
- **`Stamps.py`**: PyMuPDF automation script for overlaying sequential 3D graphics, watermarks, or decorative stamps across multi-page PDF documents (e.g. PhD thesis drafts).
- Features alternating odd/even page positioning (`ALTERNATE_MODE`), automatic horizontal coordinate mirroring (`POSITION_MODE_B = "mirror"`), customizable page ranges (`START_PAGE`, `FINAL_PAGE`), and automatic system preview thumbnail generation (`xdg-open`). See [`_PDF_Stamp_/README.md`](./_PDF_Stamp_/README.md) for details.

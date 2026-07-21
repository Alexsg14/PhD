# SUDOE Project: Virtual Reality & Docking B-Factor Analysis

This module provides tools for Virtual Reality (VR) molecular visualization and docking energy mapping onto receptor structural B-factors.

---

## 📂 Subdirectory Overview

```
Repo-SUDOE/
├── VR_BFACTOR/
│   ├── ligand_energy_attribution_bfactor.py  # Maps AutoDock Vina energies to receptor B-factors
│   └── bfactor.sh                             # Shell wrapper script for B-factor mapping
├── split_and_convert_pdbqt_to_pdb.py          # Splits multi-model PDBQT files into PDB format
├── nanover_openmm_guide.md                    # Setup guide for NanoVer + OpenMM interactive VR
├── nanover_openmm_interactive.ipynb           # Jupyter Notebook for interactive VR simulations
└── Images/                                    # Diagram & UI assets for VR setup
```

---

## 🛠️ Key Scripts

### 1. Receptor B-Factor Energy Attribution (`VR_BFACTOR/ligand_energy_attribution_bfactor.py`)
Parses AutoDock Vina multi-model PDBQT docking outputs (`all.pdbqt`), ranks poses by binding energy (`REMARK VINA RESULT`), identifies receptor atoms/residues within a spatial cutoff distance (e.g. 5.0 Å), and writes the pose rank into the receptor's B-factor column.

This allows intuitive 3D color-mapping in VR software (like NanoVer or VMD) to visualize hot spots where high-affinity docking models cluster.

**Usage:**
```bash
python VR_BFACTOR/ligand_energy_attribution_bfactor.py \
    --pdbqt_ligs all.pdbqt \
    --receptor receptor.pdb \
    --dir_models ./modelos_pdb \
    --dir_output ./resultado_final \
    --cutoff 5.0
```

---

### 2. Multi-Model PDBQT Converter (`split_and_convert_pdbqt_to_pdb.py`)
Converts multi-pose `.pdbqt` files from AutoDock Vina into standard `.pdb` files using Open Babel (`obabel`) and splits them into individual model files (`modelo_1.pdb`, `modelo_2.pdb`, etc.).

---

### 3. Interactive NanoVer Simulations (`nanover_openmm_interactive.ipynb`)
Provides an interactive Jupyter Notebook environment for running OpenMM simulations served over NanoVer OmniRunner for Meta Quest headset interaction. See [`nanover_openmm_guide.md`](./nanover_openmm_guide.md) for full instructions.

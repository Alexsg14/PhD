# 🧬 MD Simulation Dashboard — Setup Guide

This is a **real-time web dashboard** to monitor GROMACS molecular dynamics simulations.
It reads simulation files directly (read-only) and displays live energy plots, trajectory
analysis (RMSD, Rg, FEL), and 3D molecular viewers in the browser.

---

## 📦 What's in this zip

```
Dashboard/
├── server.py                  # FastAPI backend + WebSocket server
├── gromacs_parser.py          # Parses GROMACS .log files, scans simulation directories
├── realtime_analysis.py       # MDAnalysis trajectory analysis (RMSD, Rg, FEL, contacts)
├── standalone_analysis_plotter.py  # Offline standalone analysis (no server needed)
├── start_dashboard.sh         # Convenience launcher script
├── requirements.txt           # Python dependencies
└── static/
    ├── index.html             # Frontend UI
    ├── app.js                 # Frontend logic (WebSocket client, charts, 3D viewer)
    └── style.css              # Styles
```

---

## ⚙️ Prerequisites

### 1. Python ≥ 3.10
```bash
python3 --version
```

### 2. Python dependencies
```bash
pip install -r requirements.txt
```
This installs: `fastapi`, `uvicorn`, `websockets`, `MDAnalysis`, `numpy`, `scipy`

> **Note:** `MDAnalysis` can take a few minutes to install. It requires a C compiler.
> On some systems: `sudo apt install python3-dev build-essential` before pip install.

### 3. GROMACS (optional but recommended)
Only needed for the **3D structure viewer** (extracts frames via `gmx trjconv`).  
All energy plots and RMSD/Rg analysis work without it.

```bash
gmx --version   # check if available
```

---

## 🔧 Configuration & Environment Variables

You can configure the simulation directory without modifying any python files by setting the `MD_DASHBOARD_BASE_DIR` environment variable.

### Option A: Set via Environment Variable (Recommended)
Set the variable before launching the server:
```bash
export MD_DASHBOARD_BASE_DIR="/path/to/your/simulations"
```

### Option B: Edit Configuration Fallbacks
Alternatively, you can edit the fallback values directly in:
* `gromacs_parser.py`:
  ```python
  BASE_DIR = os.environ.get("MD_DASHBOARD_BASE_DIR", "/path/to/your/simulations")
  ```
* `standalone_analysis_plotter.py`:
  ```python
  BASE_DIR = os.environ.get("MD_DASHBOARD_BASE_DIR", "/path/to/your/simulations")
  ```

#### Expected directory structure under `BASE_DIR`:

```
BASE_DIR/
├── SYSTEM_NAME_1/            ← folder name must start with TEAD_ or YAP_
│   ├── replica_1/
│   │   ├── r1_step1_eq.log   ← GROMACS log files
│   │   ├── r1_step1_eq.xtc   ← trajectory files
│   │   ├── r1_step1_eq.gro   ← coordinate files (mark step as completed)
│   │   ├── r1_tray.log       ← production run log
│   │   ├── r1_tray.xtc
│   │   └── complex_with_ligand.pdb  ← topology/reference structure
│   ├── replica_2/
│   └── replica_3/
├── SYSTEM_NAME_2/
│   └── ...
└── MDPs_replica_1/           ← optional: .mdp files for position restraint info
    ├── step1_eq.mdp
    └── ...
```

#### File naming convention expected:
- Logs: `r{N}_step{i}_eq.log` (equilibration, steps 1–13) and `r{N}_tray.log` (production)
- Trajectories: `r{N}_step{i}_eq.xtc` and `r{N}_tray.xtc`
- Completed step marker: `r{N}_step{i}_eq.gro` (existence = step finished)
- Replicas: folders named `replica_1`, `replica_2`, `replica_3`
- Systems: folders matching `TEAD_*` or `YAP_*` patterns

> If your naming scheme is different, edit `detect_active_step()` and `scan_all_systems()`
> in `gromacs_parser.py` to match your conventions.

---

### `gromacs_parser.py` — Lines 18–25 (if your protocol is different)

This defines how long each simulation step is expected to run:

```python
STEP_INFO = {
    "step1_eq":  {"dt": 0.001, "nsteps": 8000000, "duration_ns": 8.0},
    "step2_eq":  {"dt": 0.001, "nsteps": 8000000, "duration_ns": 8.0},
    # steps 3–13: dt=0.002, nsteps=4000000, duration_ns=8.0
    "tray":      {"dt": 0.002, "nsteps": 50000000, "duration_ns": 100.0}
}
```

Adapt `dt`, `nsteps`, and `duration_ns` to match your `.mdp` files if different.

---

### `start_dashboard.sh` — Line 3

```bash
# Change the path to where you placed the Dashboard folder:
cd /path/to/your/Dashboard
```

---

## 🚀 Running the dashboard

```bash
# Option A: use the shell script
bash start_dashboard.sh

# Option B: run directly
cd /path/to/Dashboard
python3 server.py
```

Then open your browser at: **http://localhost:8080**

---

## 🧠 What the dashboard monitors

For each system + replica combination found in `BASE_DIR`, it shows:

| Feature | Description |
|---|---|
| **Status** | running / stopped / pending / completed |
| **Progress** | Step progress (%) + overall progress across all 14 steps |
| **Phase** | Equilibration (step N/13) or Production |
| **Energy plots** | Temperature, Pressure, Potential Energy, Total Energy (live from .log) |
| **ns/day** | Live and cumulative simulation speed estimates |
| **Wall time** | Effective compute time (ignores SLURM queue time) |
| **RMSD** | Complex, Chain A, Chain B, Ligand vs. frame 0 |
| **Rg** | Radius of gyration (complex, chain A, chain B) |
| **FEL** | Free Energy Landscape (RMSD vs Rg, Boltzmann-weighted) |
| **Contacts** | Number of Cα contacts between chains/ligand |
| **3D Viewer** | Last frame or short trajectory animation (requires GROMACS) |

---

## 🔄 Update intervals

| Event | Interval |
|---|---|
| System scan (find new replicas/steps) | every 15 seconds |
| Trajectory analysis (RMSD, Rg, FEL) | every 5 minutes (cached) |
| PDB extraction for 3D viewer | on demand (user click) |

---

## 🐛 Troubleshooting

**"No systems found"** → `BASE_DIR` is wrong, or folder names don't match `TEAD_*/YAP_*`

**"No log data"** → Log files exist but naming doesn't match `r{N}_step{i}_eq.log` pattern

**"MDAnalysis not installed"** → `pip install MDAnalysis` (may need build tools)

**RMSD/Rg shows zeros** → Check that `complex_with_ligand.pdb` exists in the replica or system folder

**3D viewer fails silently** → GROMACS (`gmx`) not in PATH; static structure view still works

---

## 📝 Notes

- The dashboard is **completely read-only** on your simulation files. It never writes to `BASE_DIR`.
- The only files it writes are temporary PDBs in `Dashboard/static/viewer/` for the 3D viewer.
- It works with **actively running simulations** — log files are re-read every scan cycle.
- SLURM restarts are handled gracefully: simulation speed is estimated from sim-time deltas, not wall clock.

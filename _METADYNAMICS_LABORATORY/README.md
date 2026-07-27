# Metadynamics & OPES Laboratory (`_METADYNAMICS_LABORATORY`)

[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite 7](https://img.shields.io/badge/Vite-7-purple.svg)](https://vitejs.dev/)
[![Tailwind CSS 3](https://img.shields.io/badge/TailwindCSS-3-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Interactive web-based simulation environment and high-performance analysis suite for **1D & 2D Metadynamics**, **Well-Tempered Metadynamics (WT-MetaD)**, **OPES (On-the-fly Probability Enhanced Sampling)**, and **PLUMED File Visualizers (HILLS & KERNELS)**.

---

## 🌟 Key Features & Modules

The application features 5 specialized, interactive modules accessible from the sidebar navigation:

### 1. 🧪 1D Metadynamics Simulator (`1D`)
- **Overdamped Langevin (Brownian) Dynamics**: Simulates stochastic particle diffusion over 1D energy landscapes with thermal noise via **Box-Muller Gaussian distribution** $\mathcal{N}(0, 1)$.
- **Standard & Well-Tempered Metadynamics (WT-MetaD)**:
  - Standard constant Gaussian deposition over time.
  - Well-Tempered dynamic height scaling based on accumulated bias potential $V_B(x)$:
    $$W(t) = W_0 \exp\left(-\frac{V_B(x)}{\Delta T}\right)$$
- **Custom Energy Surface Parser**: Interactively edit Gaussian potential wells or write arbitrary mathematical functions $V(x)$ supporting functions (`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `abs`), constants (`pi`, `e`), and presets (Double Well, Triple Well, Asymmetric Well).
- **Live Diagnostics**: Real-time charts for walker position $x(t)$, Potential Energy Surface $V(x)$, Bias Potential $V_B(x)$, Estimated Free Energy $F_{\text{est}}(x) = -\frac{\gamma}{\gamma-1} V_B(x)$, and Gaussian height decay $W(t)$.

### 2. 🌐 2D Metadynamics Simulator (`2D`)
- **2D Langevin Trajectory Engine**: Simulates walker diffusion over 2D collective variable surfaces $(CV_x, CV_y)$.
- **High-Performance HTML5 Canvas Heatmap**:
  - Renders 2D potential landscapes ($V$, $V+V_B$, $V_B$, $F_{\text{est}}$) at 60 FPS.
  - Scientific colormaps: **Inferno**, **Viridis**, **Spectral**, **Plasma**, **Coolwarm**.
  - Interactive trajectory path tracing and glowing walker position indicator.
  - Click anywhere on the 2D canvas to instantly relocate the walker.
- **Flexible 2D Potential Surfaces**: Preset surfaces (Symmetric 4-Well, Asymmetric Double Well, Egg-Carton Periodic, Concentric Ring, Mueller-Brown Potential) or custom mathematical functions $V(x, y)$.

### 3. ⚡ OPES 1D Simulator (`OPES`)
- **On-the-Fly Probability Enhanced Sampling**: Simulates OPES Explore / OPES Target distribution sampling with adaptive kernel accumulation.
- **Adaptive Kernel Deposition**: Dynamically adjusts deposited kernel weights $W_k$ and bandwidths $\sigma_k$ to achieve uniform sampling or target probability distribution $P_{target}(s)$.
- **Live Estimation**: Real-time visualization of accumulated probability distribution $P(s)$, bias potential $V(s)$, and reconstructed Free Energy Surface $F(s) = -k_B T \ln P(s)$.
- **Interactive Control Panel**: Configure barrier energy estimates $\Delta E^\ddagger$, kernel pace, initial bandwidth $\sigma_0$, bias factor $\gamma$, and simulation temperature $T$.

### 4. 📈 PLUMED HILLS Visualizer & Inspector (`HILLS`)
- **Background Web Worker Architecture**: Offloads 100% of large text file line parsing, tokenization, and Gaussian summation grid calculations to a background thread to prevent UI freezing.
- **60 FPS Real-Time FES Animation**: Calculates timeline grid frames incrementally. Play, pause, loop, or scrub through the timeline to watch the Free Energy Surface $F(s, t)$ evolve smoothly.
- **Drag & Drop File Loader**: Drag any PLUMED `HILLS` file directly onto the web application window for immediate analysis.
- **Advanced Energy Reference Modes**:
  - **Raw**: Direct potential $-V(s)$.
  - **Min to Zero ($F_{\min} = 0$)**: Shifts the global free energy minimum to 0.
  - **Plateau Zero**: Automatically identifies high-energy unbiased reference regions and sets them to 0.
- **Multi-Stage Convergence Analysis**: Overlays FES profiles at 25%, 50%, 75%, and 100% of total simulation time to verify convergence.
- **PLUMED `fes.dat` Export**: One-click export of reconstructed FES grid files fully compatible with PLUMED `sum_hills`.

### 5. 🔍 PLUMED OPES Inspector (`OPES_INSPECTOR`)
- **PLUMED OPES State Parser**: Reads and parses PLUMED `KERNELS` and `OPES_STATE` output files.
- **Kernel Expansion Analysis**: Computes Free Energy Surfaces from adaptive kernel weights $W_k$ and kernel centers $s_k$.
- **Interactive Timeline Playback**: Step or play through kernel accumulation steps to assess sampling coverage and FES convergence over time.
- **Energy Unit Selection**: Custom energy units ($\text{kJ/mol}$, $\text{kcal/mol}$, $k_B T$) and flexible reference modes.
- **PLUMED Compatibility**: Export reconstructed Free Energy profiles directly to `fes.dat`.

---

## 🛠️ Technology Stack

| Category | Technology |
| :--- | :--- |
| **Framework** | React 19 + Vite 7 |
| **Styling** | TailwindCSS 3 (Dark Mode, Glassmorphism, Neon Glows) |
| **Background Processing** | Web Worker API (Multi-threaded line & Gaussian summation engine) |
| **Graphics & Rendering** | HTML5 Canvas 2D API & Recharts |
| **Iconography** | Lucide React |
| **Code Quality** | ESLint 9 |

---

## 🚀 Quick Start

### Option A: Standard Run (`metadynamics_laboratory`)

1. **Navigate to the application folder and install dependencies**:
   ```bash
   cd _METADYNAMICS_LABORATORY/metadynamics_laboratory
   npm install
   ```

2. **Start the Vite development server**:
   ```bash
   npm run dev
   ```

3. **Open browser**: Navigate to `http://localhost:5173`.

### Option B: Automated Generator Script (`metadynamics_laboratory.sh`)

Generate a fresh standalone project pre-configured with React, Vite, TailwindCSS, and all Metadynamics Laboratory components:

```bash
./metadynamics_laboratory.sh [nombre_proyecto]
```

---

## 🎲 Determinism, PRNG & Session Saving

The simulation engine includes a 100% deterministic pseudo-random number generator (`mulberry32` PRNG):

- **Fixed Seed Mode**: Inputting a custom integer seed automatically locks the PRNG. Re-running or resetting the simulation produces an exact, bit-identical Langevin trajectory.
- **Random Seed Generator**: Click **`New Seed`** to generate a fresh seed while preserving deterministic reproducibility.
- **Session Save & Restore (JSON)**: Export the complete state (active seed, PRNG state, PES formula, Gaussian wells, bias potential, parameters) to a JSON file. Loading a session file fully restores the exact simulation state.

---

## 📂 Directory Structure

```
_METADYNAMICS_LABORATORY/
├── HILLS                               # Sample PLUMED HILLS dataset
├── metadynamics_laboratory.sh          # Generator script for new projects
└── metadynamics_laboratory/            # Web Application Root
    ├── src/
    │   ├── App.jsx                     # Main layout & 5-mode sidebar navigation
    │   ├── MetadynamicsLab.jsx         # 1D Metadynamics simulation engine & UI
    │   ├── MetadynamicsLab2D.jsx       # 2D Metadynamics canvas heatmap engine & UI
    │   ├── OPESSimulator.jsx           # OPES 1D simulator engine & UI
    │   ├── HillsVisualizer.jsx         # PLUMED HILLS parser, web worker & 60 FPS visualizer
    │   ├── OpesVisualizer.jsx          # PLUMED OPES KERNELS parser & visualizer
    │   ├── MathEq.jsx                  # Formula rendering component
    │   ├── sampleHills.js              # Fallback sample dataset
    │   ├── index.css                   # Tailwind CSS styling & custom scrollbars
    │   └── main.jsx                    # React entrypoint
    ├── index.html                      # Single page HTML template
    ├── package.json                    # Project dependencies & scripts
    ├── tailwind.config.js              # Tailwind CSS configuration
    └── vite.config.js                  # Vite configuration
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

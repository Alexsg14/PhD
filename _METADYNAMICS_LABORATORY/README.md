# Metadynamics Laboratory (`_METADYNAMICS_LABORATORY`)

[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite 7](https://img.shields.io/badge/Vite-7-purple.svg)](https://vitejs.dev/)
[![Tailwind CSS 3](https://img.shields.io/badge/TailwindCSS-3-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Interactive web-based simulation environment and analysis tool for **1D & 2D Metadynamics**, **Well-Tempered Metadynamics (WT-MetaD)**, and **PLUMED HILLS File Reconstructions**.

---

## 🌟 Key Features

### 1. 🧪 1D & 2D Interactive Metadynamics Simulators
- **Global Mode Switcher**: Easily toggle between **1D Simulator ($CV_x$)**, **2D Simulator ($CV_x$, $CV_y$)**, and **HILLS Visualizer (PLUMED)** from the top navigation bar.
- **Overdamped Langevin (Brownian) Dynamics**: Simulates particle diffusion over 1D and 2D energy landscapes with thermal noise generated via independent **Box-Muller Gaussian distributions** $\mathcal{N}(0, 1)$.
- **Flexible Potential Energy Surfaces (PES)**:
  - **Gaussian Wells Editor**: Interactively add, remove, and adjust positions and depths of potential wells in 1D and 2D space.
  - **Custom Mathematical Functions $V(x)$ & $V(x, y)$**: Define custom energy surfaces using a safe parser supporting variables `x` and `y`, math functions (`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `abs`), constants (`pi`, `e`), and presets (Symmetric 4-Well, Asymmetric 2D Double Well, Egg-Carton Periodic, Concentric Ring, Mueller-Brown Potential).
- **High-Performance 2D Canvas Heatmap Renderer**:
  - Renders smooth 2D energy landscape heatmaps ($V$, $V+V_B$, $V_B$, $F_{\text{est}}$) with scientific color gradients (Inferno / Viridis / Spectral).
  - Real-time 2D trajectory path tracing and glowing particle marker.
  - Click anywhere on the 2D canvas to relocate the walker particle.
- **Metadynamics Algorithms**:
  - **Standard Metadynamics**: Constant height Gaussian deposition over time.
  - **Well-Tempered Metadynamics (WT-MetaD)**: Dynamic Gaussian height scaling based on accumulated bias potential $W(t) = W_0 \exp\left(-\frac{V_B(x,y)}{\Delta T}\right)$.
  - **Real-Time Free Energy Reconstruction**: Live calculation and rendering of estimated Free Energy Surfaces $F_{\text{est}}(x)$ and $F_{\text{est}}(x, y)$.

### 2. 📊 PLUMED HILLS Visualizer & Inspector (`HillsVisualizer`)
- **Background Web Worker Architecture**: Offloads 100% of large text file line splitting, token parsing, and gaussian summation calculations to a background thread. UI never freezes, eliminating "Page Unresponsive" browser dialogs.
- **60 FPS Real-Time FES Animation**: Pre-calculates 100 timeline grid frames incrementally in the worker thread. Playing or scrubbing the time slider renders the evolving Free Energy Surface $F(s, t)$ smoothly at 60 FPS in real time.
- **Drag & Drop File Upload**: Drag any PLUMED `HILLS` file directly onto the web application window for instant parsing with a visual drop target overlay.
- **Energy Display Modes**: Switch between **Direct Absolute Potential** $F(s) = -V(s)$ and **Relative Potential** ($F_{\min} = 0$).
- **Well-Tempered Scaling & Custom Bias Factor**: Automatically detects or allows custom input for bias factor $\gamma$, applying WT scaling $\frac{\gamma}{\gamma - 1}$.
- **PLUMED `fes.dat` Export**: One-click export of reconstructed FES grid files compatible with PLUMED `sum_hills` format.
- **Multi-Stage Convergence Analysis**: Superimposes FES profiles at 25%, 50%, 75%, and 100% completion to visually assess free energy convergence.

---

## 🛠️ Technology Stack

- **Framework**: React 19 + Vite 7
- **Styling**: TailwindCSS 3
- **Background Worker**: Inline Web Worker API
- **Charting**: Recharts
- **Icons**: Lucide React
- **Linter**: ESLint 9

---

## 🚀 Quick Start

> [!IMPORTANT]
> **Execution Options**:
> - **Pre-configured App (`_METADYNAMICS_LABORATORY/metadynamics_laboratory`)**: The repository includes the complete, fully-functional web application with all simulation and visualizer features. Simply run `cd _METADYNAMICS_LABORATORY/metadynamics_laboratory && npm install && npm run dev`.
> - **Automated Generator Script (`_METADYNAMICS_LABORATORY/metadynamics_laboratory.sh`)**: Initializes a new standalone project from scratch, automatically installs all dependencies (`react`, `vite`, `tailwindcss`, `recharts`, `lucide-react`), configures PostCSS/Tailwind, and embeds all components without extra manual setup.
>   ```bash
>   ./metadynamics_laboratory.sh [nombre_proyecto]
>   ```

### 1. Run Locally

Navigate to the application folder and install dependencies:

```bash
cd _METADYNAMICS_LABORATORY/metadynamics_laboratory
npm install
```

Start the Vite development server:

```bash
npm run dev
```

Open your browser at `http://localhost:5173`.

### 2. Available Scripts

Inside `_METADYNAMICS_LABORATORY/metadynamics_laboratory/`:

- `npm run dev`: Launches local development server with Hot Module Replacement (HMR).
- `npm run build`: Compiles optimized production bundle in `dist/`.
- `npm run lint`: Runs ESLint to verify code quality and React hook purity.
- `npm run preview`: Previews the production build locally.

---

## 🎲 Reproducibility, Seed Management & Session Saving

The simulation engine ensures 100% deterministic reproducibility via the `mulberry32` PRNG:

- **Manual Seed Input**: Typing any custom seed into the **RNG Seed** input field automatically enables **`Fixed Seed`** mode. Whenever you reset or adjust parameters, the simulation restarts with your exact seed value, producing an identical step-by-step Langevin trajectory.
- **Random Seed Generation**: Clicking **`New Seed`** generates a new random seed, locks it in fixed mode, and resets the simulation.
- **Session Save & Restore (JSON)**: Clicking **`Save Session (JSON)`** exports the active seed, fixed-seed state, PES function, parameters, and accumulated bias trajectory. Importing a session file (`Load Session`) restores the exact seed, parameters, and PRNG state automatically.

---

## 📂 Directory Structure

```
_METADYNAMICS_LABORATORY/
├── HILLS                               # Sample PLUMED HILLS input dataset
├── metadynamics_laboratory.sh          # Bash generator script for initializing Vite + React + Tailwind
└── metadynamics_laboratory/            # Web application project root
    ├── src/
    │   ├── App.jsx                     # Main App wrapper with 1D/2D/HILLS mode switcher
    │   ├── MetadynamicsLab.jsx         # 1D Metadynamics simulation engine & UI
    │   ├── MetadynamicsLab2D.jsx      # 2D Metadynamics simulation engine & Canvas heatmap UI
    │   ├── HillsVisualizer.jsx         # PLUMED HILLS visualizer with 60 FPS engine & Web Worker
    │   ├── sampleHills.js              # Default fallback sample data
    │   ├── index.css                   # Tailwind CSS directives & scrollbar styles
    │   └── main.jsx                    # React DOM entrypoint
    ├── index.html                      # Single-page HTML document
    ├── package.json                    # Dependencies and scripts
    ├── tailwind.config.js              # Tailwind CSS configuration
    └── vite.config.js                  # Vite build configuration
```

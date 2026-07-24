# Metadynamics Web Laboratory (`_METADYN_WEB`)

[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Vite 7](https://img.shields.io/badge/Vite-7-purple.svg)](https://vitejs.dev/)
[![Tailwind CSS 3](https://img.shields.io/badge/TailwindCSS-3-38bdf8.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Interactive web-based simulation environment for exploring **1D Metadynamics** and **Well-Tempered Metadynamics (WT-MetaD)** on arbitrary Potential Energy Surfaces (PES).

---

## 🌟 Key Features

- **1D Overdamped Langevin (Brownian) Dynamics**:
  - Simulates particle diffusion over energy landscapes with thermal noise generated via **Box-Muller Gaussian Normal distribution** \(\mathcal{N}(0, 1)\).
  - Reproducible runs using seedable Pseudo-Random Number Generator (`mulberry32`).

- **Flexible Potential Energy Surface (PES)**:
  - **Gaussian Wells Editor**: Interactively add, remove, and adjust positions and depths of potential wells.
  - **Custom Mathematical Function $V(x)$**: Define custom energy surfaces using a safe, zero-dependency parser supporting operators (`+`, `-`, `*`, `/`, `^`), functions (`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `abs`), constants (`pi`, `e`), and pre-configured presets (Symmetric Double Well, Asymmetric Double Well, Triple Well, Sinusoidal Wavy Surface, Harmonic Well).

- **Metadynamics Algorithms**:
  - **Standard Metadynamics**: Constant height Gaussian deposition over time.
  - **Well-Tempered Metadynamics (WT-MetaD)**: Dynamic Gaussian height scaling based on accumulated bias potential \(w(t) = w_0 \exp\left(-\frac{V_B(x)}{\Delta T}\right)\).
  - **Real-Time Free Energy Reconstruction**: Live calculation and rendering of the estimated Free Energy Surface \(F_{est}(x)\).

- **Session Management**:
  - Save and load complete simulation states, configurations, parameters, and bias history via JSON.

---

## 🛠️ Technology Stack

- **Framework**: React 19 + Vite 7
- **Styling**: TailwindCSS 3
- **Charting**: Recharts
- **Icons**: Lucide React
- **Linter**: ESLint 9

---

## 🚀 Quick Start

> [!IMPORTANT]
> **Execution Options**:
> - **Pre-configured App (`_METADYN_WEB/metadyn_web`)**: The repository includes the complete, fully-functional web application with all simulation features. Simply run `cd _METADYN_WEB/metadyn_web && npm install && npm run dev`.
> - **Automated Generator Script (`_METADYN_WEB/metadyn_web.sh`)**: Initializes a new standalone project from scratch, automatically installs all dependencies (`react`, `vite`, `tailwindcss`, `recharts`, `lucide-react`), configures PostCSS/Tailwind, and embeds the complete `MetadynamicsLab` component without requiring extra manual steps.
>   ```bash
>   ./metadyn_web.sh [nombre_proyecto]
>   ```

### 1. Run Locally

Navigate to the application folder and install dependencies:

```bash
cd _METADYN_WEB/metadyn_web
npm install
```

Start the Vite development server:

```bash
npm run dev
```

Open your browser at `http://localhost:5173`.

### 2. Available Scripts

Inside `_METADYN_WEB/metadyn_web/`:

- `npm run dev`: Launches local development server with Hot Module Replacement (HMR).
- `npm run build`: Compiles optimized production bundle in `dist/`.
- `npm run lint`: Runs ESLint to verify code quality and React hook purity.
- `npm run preview`: Previews the production build locally.

## 🎲 Reproducibility, Seed Management & Session Saving

The simulation engine ensures 100% deterministic reproducibility via the `mulberry32` PRNG:

- **Manual Seed Input**: Typing any custom seed into the **RNG Seed** input field automatically enables **`Fixed Seed`** mode. Whenever you reset or adjust parameters, the simulation restarts with your exact seed value, producing an identical step-by-step Langevin trajectory.
- **Random Seed Generation**: Clicking **`New Seed`** generates a new cryptographically random seed, locks it in fixed mode, and resets the simulation.
- **Session Save & Restore (JSON)**: Clicking **`Save Session (JSON)`** exports the active seed, fixed-seed state, PES function, parameters, and accumulated bias trajectory. Importing a session file (`Load Session`) restores the exact seed, parameters, and PRNG state automatically.

---

## 📂 Directory Structure

```
_METADYN_WEB/
├── metadyn_web.sh             # Bash generator script for initializing Vite + React + Tailwind
└── metadyn_web/              # Web application project root
    ├── src/
    │   ├── App.jsx            # Main App wrapper
    │   ├── MetadynamicsLab.jsx# Core Metadynamics simulation engine & UI
    │   ├── index.css          # Tailwind CSS directives
    │   └── main.jsx           # React DOM entrypoint
    ├── index.html             # Single-page HTML document
    ├── package.json           # Dependencies and scripts
    ├── tailwind.config.js     # Tailwind CSS configuration
    └── vite.config.js         # Vite build configuration
```

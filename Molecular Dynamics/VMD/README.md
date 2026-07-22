# 🎬 Automated VMD Rendering & Visualization Styles

This directory contains automated pipelines and custom styling scripts for **VMD (Visual Molecular Dynamics)** to render publication-quality images and video trajectories using the **Tachyon Ray Tracer**.

---

## 📂 Contents

| File | Description |
|---|---|
| **`run_vmd_render.py`** | Python wrapper script to launch VMD in text-only mode and execute Tcl routines. |
| **`RENDER_VMD.tcl`** | Master Tcl script defining render controls, camera spin routines, and movie production. |
| **`materials.tcl`** | Material definition script (e.g., configuring transparent realistic water). |
| **`style_vmd.tcl`** | Default cartoon style for proteins, licorice for ligands, and transparent water representation. |
| **`Alex_style.tcl`** | Specialized styling for protein indices and small molecule complexes (e.g. `MOL`, `0GB`). |
| **`style_yt.tcl`** | Stylized color scheme for protein chains A/B and ligands using high-contrast colors. |
| **`style_vmd_martini.tcl`** | representation system for Martini Coarse-Grained lipid bilayers (POPC, CHOL, POPE, etc.) and peptides. |
| **`style_vmd_martini_peptidomica.tcl`** | Martini coarse-grained style for peptidomimetics with interactive Z-bound water layers. |
| **`style_vmd_docking.tcl`** | Visualizer for docking poses matching receptors and multiple ligand positions. |
| **`style_vmd_RMSD.tcl`** | Color-scale mapper that renders secondary structure color-coded by atomistic RMSD/Beta fluctuations. |

---

## 🚀 Execution Guide (Python Wrapper)

Instead of manually launching the VMD GUI and sourcing scripts, you can run render jobs headlessly from the command line using `run_vmd_render.py`.

### Prerequisites
Make sure `vmd` and `magick` (ImageMagick) or `ffmpeg` (for video compiling) are installed and available in your terminal path.

### CLI Parameters
```bash
python run_vmd_render.py --help
```
* `--render-tcl`: Path to `RENDER_VMD.tcl` (defaults to `RENDER_VMD.tcl`).
* `--pdb`: Path to the input coordinate file (e.g., `MIN_FRAME2.pdb`).
* `--out-name`: Base filename of the rendered output (defaults to `image`).
* `--out-dir`: Directory where outputs will be saved (defaults to `_RENDERS`).
* `--do`: Rendering action: `pic` (single image) or `movie` (trajectory video).
* `--smooth-a` / `--smooth-b`: VMD trajectory smoothing factors.

### Examples

**1. Render a single high-quality transparent PNG image:**
```bash
python run_vmd_render.py --pdb complex.pdb --do pic --out-name structure_still --out-dir renders/
```

**2. Render a 360-degree rotation movie of a trajectory:**
```bash
python run_vmd_render.py --pdb trajectory.pdb --do movie --out-name complex_spin --out-dir renders/ --degrees 360 --fps 24
```

---

## 🛠️ Master Tcl Commands (`RENDER_VMD.tcl`)

If you are using the VMD TK Console, you can load the master file:
```tcl
source RENDER_VMD.tcl
```
This loads all styles and registers the following custom procs:

### 1. `pic <filename> <fuzz_percent> <res_x> <res_y>`
Renders the current camera view to a `.tga` file, converts it to `.png`, and creates a transparent-background version.
* **Example:** `pic frame_01 10 1920 1080` (creates `frame_01.png` and `frame_01_transparent.png`).

### 2. `giro <nframes> <axis>`
Tests a camera rotation along the specified axis (`x`, `y`, or `z`) for `nframes` steps.
* **Example:** `giro 120 y`

### 3. `video <nframes> <axis> <filename>`
Renders a 360° spin video of the static scene and compiles it into an `.mp4` video using `ffmpeg`.
* **Example:** `video 100 y spin_animation`

### 4. `make_movie <nframes> <angle> <axis> <filename>`
Iterates through trajectory frames while rotating the camera, renders each frame, and compiles them into a trajectory video.
* **Example:** `make_movie 240 360 y simulation_traj`

### 5. `double <gro_file> <xtc_file> <nframes> <skip> <output_dir> <basename>`
Renders a side-by-side comparison video of two states and compiles it into an animated `.gif` using ImageMagick.
* **Example:** `double system.gro trajectory.xtc 100 2 comp_dir output`

### 6. `smooth <smooth_factor> <representation_id>`
Applies trajectory smoothing to the specified representation index.
* **Example:** `smooth 10 0`

---

## 🔧 Configuring the Tachyon Renderer Path

Tachyon is VMD's default high-performance raytracer. `RENDER_VMD.tcl` automatically detects the tachyon binary. You can force a specific binary path by setting the `TACHYON_BIN` environment variable in your shell before running VMD:

```bash
export TACHYON_BIN="/path/to/your/custom/tachyon_binary"
```
If not specified, it falls back to checking the default path `/home/ciqus/Descargas/vmd-1.9.4a55/lib/tachyon/tachyon_LINUXAMD64` or uses the system-wide `tachyon` binary.

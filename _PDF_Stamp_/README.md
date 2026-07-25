# 📑 PDF Stamp: Automated Dynamic Stamping & Watermarking Pipeline

A Python automation tool built on top of [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) designed to batch-stamp multi-page PDF documents (such as PhD theses, books, or technical manuscripts) with custom 3D graphics, watermarks, or sequential images.

---

## ✨ Features

- **Alternating Page Layouts (Facing Pages / Mirror Mode):**
  - **Group A & Group B Handling:** Configurable separate positions for left (even) and right (odd) pages, matching physical book binding requirements.
  - **Automatic Horizontal Mirroring (`POSITION_MODE_B = "mirror"`):** Automatically reflects X-coordinates across the page width for symmetrical outer/inner margins.
- **Custom Page Range Filtering:**
  - Define `START_PAGE` and `FINAL_PAGE` bounds to exclude covers, front matter, or indexes.
- **Flexible Image Image Sequencing:**
  - Cycles through image assets (`.png`, `.jpg`, `.jpeg`, `.webp`) in alphabetical order from a designated stamps directory.
- **Interactive System Preview:**
  - Renders `PREVIEW_PAGES` random pages at custom DPI resolution (`PREVIEW_DPI`) to a temporary preview folder and opens them automatically with `xdg-open`.

---

## 📁 Directory Structure

```
_PDF_Stamp_/
├── Stamps.py                               # Core Python stamping script
├── PDF/                                    # Input & output PDF directory
│   ├── [INPUT_PDF_NAME].pdf                # Input target document
│   └── STAMPED_[OUTPUT_PDF_NAME].pdf       # Output processed document
├── peptide_3D_CORRECTED_sin_alpha/         # Directory containing stamp images (PNG/WEBP)
├── Preview/                                # Generated PNG preview thumbnails
└── README.md                               # Module documentation
```

---

## 🚀 Quick Start

### 1. Requirements

Install PyMuPDF (`fitz`):

```bash
pip install pymupdf
```

### 2. Configuration (`Stamps.py`)

Edit the configuration constants at the top of [`Stamps.py`](file:///home/ciqus/GIT/Github_Personal/PhD/_PDF_Stamp_/Stamps.py):

```python
# Document parameters
INPUT_PDF_NAME = "My_Thesis_Document.pdf"
OUTPUT_PDF_NAME = "STAMPED_My_Thesis_Document.pdf"

# Page ranges
START_PAGE = 36          # Start applying stamps from page 36
FINAL_PAGE = None        # Process until the last page

# Alternating pages mode
ALTERNATE_MODE = True    # Enable alternating Group A (odd) / Group B (even)
ALTERNATE_ALSO_STAMP_B = True
POSITION_MODE = "custom"
POSITION_MODE_B = "mirror" # Mirror X coordinate for facing pages

# Stamp dimensions & custom coordinates
STAMP_WIDTH = 85
STAMP_HEIGHT = 85
CUSTOM_X = 520
CUSTOM_Y = 745
```

### 3. Execution

Run the stamping script:

```bash
python Stamps.py
```

Upon completion, output files will be saved in `PDF/` and preview images will open automatically.

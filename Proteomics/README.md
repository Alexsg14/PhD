# Proteomics Data Processing & Clinical Severity Analysis (`Proteomics`)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0+-orange.svg)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/pandas-1.3+-150458.svg)](https://pandas.pydata.org/)
[![Seaborn](https://img.shields.io/badge/seaborn-0.11+-blue.svg)](https://seaborn.pydata.org/)

Automated processing, statistical analysis, unsupervised clustering, differential expression profiling, MLR normalization verification, and clinical severity visualization for SWATH-MS mass spectrometry proteomics datasets (plasma & pellet fractions, v2022 and v2024 libraries).

---

## 📑 Table of Contents

- [Features & Overview](#-features--overview)
- [Directory Architecture](#-directory-architecture)
- [Module Breakdown](#-module-breakdown)
  - [1. SWATH-MS Proteomics Pipeline (`analise_Julio26.py` / `analise_svg.py`)](#1-swath-ms-proteomics-pipeline-analise_julio26py--analise_svgpy)
  - [2. Patient Severity Matrix Heatmaps (`Severity_matrix.py`)](#2-patient-severity-matrix-heatmaps-severity_matrixpy)
  - [3. Differential Expression Volcano Generator (`run_volcano.py`)](#3-differential-expression-volcano-generator-run_volcanopy)
  - [4. MLR Normalization & Fold Change Verification (`fc_S_normalizada_vs_sinnormalizar.py` & `verificacion_MLR.py`)](#4-mlr-normalization--fold-change-verification-fc_s_normalizada_vs_sinnormalizarpy--verificacion_mlrpy)
- [Dependencies & Environment Setup](#-dependencies--environment-setup)

---

## 🎯 Features & Overview

- **SWATH-MS Data Pipelines:** Preprocessing of raw protein peak areas, filtering contaminant/decoy entries (`RRR` prefixes), immunoglobulin detection, UniProt ID normalization, and sample classification (plasma supernatant `_S` vs pellet `_P`).
- **Unsupervised Machine Learning:** Feature scaling (`PowerTransformer` Box-Cox / Yeo-Johnson), Principal Component Analysis (PCA), K-Means clustering, silhouette score optimization, and Jaccard cluster stability metrics.
- **Differential Expression Analysis:** Volcano plots ($\log_2(\text{Fold Change})$ vs $-\log_{10}(p\text{-value})$) with automatic label overlapping adjustment via `adjustText`.
- **Normalization Verification:** Multi-Linear Regression (MLR) normalization factor verification comparing raw vs normalized protein intensities.
- **Clinical Severity Heatmaps:** Ordering patient clinical profiles by calculated severity metrics and rendering high-resolution (600 DPI) Seaborn heatmaps.

---

## 📁 Directory Architecture

```
Proteomics/
├── Data_analysis/
│   ├── analise_Julio26.py                 # Main SWATH-MS pipeline (PCA, K-Means, Volcano plots)
│   ├── analise_svg.py                     # Vector graphic (SVG) export variant of main pipeline
│   ├── Severity_matrix.py                 # Clinical patient severity matrix & heatmap renderer
│   ├── run_volcano.py                     # Standalone Volcano plot differential expression tool
│   ├── fc_S_normalizada_vs_sinnormalizar.py # Fold Change comparison (MLR normalized vs raw)
│   └── verificacion_MLR.py                # MLR normalization factor statistical verification
└── README.md                              # Module documentation
```

---

## 🔬 Module Breakdown

### 1. SWATH-MS Proteomics Pipeline (`analise_Julio26.py` / `analise_svg.py`)

Performs end-to-end processing of SWATH-MS proteomics datasets for 4 primary conditions:
- Plasma / Supernatant (`_S`) with 2024 library
- Pellet (`_P`) with 2024 library
- Plasma / Supernatant (`_S`) with 2022 library
- Pellet (`_P`) with 2022 library

**Workflow:**
1. Data cleaning (`process_raw_areas`): Excludes decoy/contaminant sequences (`RRR`), extracts UniProt accession IDs, and isolates target sample fractions.
2. Variance filtering (`VarianceThreshold`) and feature scaling (`PowerTransformer`).
3. Dimensionality reduction via PCA (scree plots, 2D/3D component loading plots).
4. Unsupervised patient stratification using K-Means clustering and silhouette analysis.
5. Association testing between proteomic clusters and clinical patient variables.

**Usage:**
```bash
python Data_analysis/analise_Julio26.py
```

---

### 2. Patient Severity Matrix Heatmaps (`Severity_matrix.py`)

Merges clinical Excel records (`LIPID-CHUS_Anonimizado_proteomica_para_analizar.xlsx`) with patient severity classifications (`patient_severity.txt`).

**Workflow:**
1. **Patient ID Normalization:** Extracts numeric IDs (`Código del paciente`).
2. **Filtering:** Excludes control groups and extracts binary clinical responses (`SI` = 1, `NO` = 0).
3. **Severity Sorting:** Orders patient rows according to calculated `Severity_Metric`.
4. **Heatmap Rendering:** Generates Seaborn heatmaps displaying patient response patterns.

**Usage:**
```bash
python Data_analysis/Severity_matrix.py
```

---

### 3. Differential Expression Volcano Generator (`run_volcano.py`)

Standalone script dedicated to calculating statistical significance ($t$-test / Mann-Whitney $U$-test) and log fold changes between clinical clusters.

**Math Formulation:**
$$\text{FC} = \frac{\bar{X}_{\text{Class } 1}}{\bar{X}_{\text{Class } 0}}, \quad \text{Log}_2(\text{FC}) = \log_2(\text{FC}), \quad y = -\log_{10}(p)$$

**Usage:**
```bash
python Data_analysis/run_volcano.py
```

---

### 4. MLR Normalization & Fold Change Verification (`fc_S_normalizada_vs_sinnormalizar.py` & `verificacion_MLR.py`)

Statistical validation tools for checking Multi-Linear Regression (MLR) normalization effects on supernatant (`_S`) datasets:
- **`fc_S_normalizada_vs_sinnormalizar.py`**: Computes $\log_2(\text{FC}_{\text{norm}}) - \log_2(\text{FC}_{\text{raw}})$ to evaluate normalization shifts.
- **`verificacion_MLR.py`**: Analyzes per-patient MLR scaling factors, pre-normalization total ion signal distributions, and linear regression fits.

**Usage:**
```bash
python Data_analysis/fc_S_normalizada_vs_sinnormalizar.py
python Data_analysis/verificacion_MLR.py
```

---

## 📦 Dependencies & Environment Setup

```bash
# Install core Python dependencies
pip install numpy pandas scipy scikit-learn seaborn matplotlib adjustText openpyxl Pillow
```

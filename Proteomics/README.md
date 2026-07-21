# Proteomics Data Processing & Clinical Severity Analysis

This directory contains scripts and workflows for processing clinical proteomics datasets and generating patient severity heatmaps.

---

## 📁 Directory Overview

```
Proteomics/
├── Severity_matrix.py       # Patient severity heatmap generator
└── Data_analysis/           # Data sub-directory for clinical tables & exported matrices
```

---

## ⚙️ Workflows & Usage

### Severity Matrix Heatmap (`Severity_matrix.py`)

Processes anonymized clinical Excel workbooks (`LIPID-CHUS_Anonimizado_proteomica_para_analizar.xlsx`) and tab-separated patient severity text files (`patient_severity.txt`):

1. **Patient Normalization**: Extracts numeric patient IDs from anonymized codes (`Código del paciente`).
2. **Filtering**: Removes control entries and filters binary response fields (`SI`/`NO`).
3. **Sorting & Matrix Building**: Orders patient profiles according to the calculated `Severity_Metric`.
4. **Heatmap Generation**: Exports high-resolution Seaborn heatmaps (`600 DPI`) showing individual patient clinical response distributions.

**Execution:**
```bash
python Severity_matrix.py
```

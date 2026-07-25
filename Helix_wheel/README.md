# Helical Wheel & Hydrophobic Moment Generator (`Helix_wheel`)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Matplotlib](https://img.shields.io/badge/matplotlib-3.0+-brightgreen.svg)](https://matplotlib.org/)

Programmatic generation of HeliQuest-style **Helical Wheel** (Rueda Helicoidal) 2D diagrams and calculation of the **Hydrophobic Dipole Moment Vector ($\mu_H$)** for $\alpha$-helical peptide sequences.

---

## 🎯 Features

- **HeliQuest-Style Visualization:** 2D top-down view of $\alpha$-helical oligopeptides (up to 40+ amino acids, arranged across up to 3 concentric rings of 18 residues each).
- **Residue Color Coding:** Color classification based on chemical properties (Hydrophobic: Green, Polar: Yellow, Basic/Positive: Blue, Acidic/Negative: Red).
- **Hydrophobic Dipole Vector ($\mu_H$):** Calculates the vector sum and mean hydrophobic dipole moment according to Fauchere-Pliska or Eisenberg scales, rendering the resultant $\mu_H$ arrow pointing in the visual orientation of hydrophobicity.
- **Dual Interface:** Supports both direct command-line execution (CLI) and import as a Python package (`import Helix_wheel`).
- **Peptide Property Analysis:** Calculates net charge at pH 7.4, mean hydrophobicity $\langle H \rangle$, Keller discrimination factor $D$, and amino acid composition.

---

## 📁 File Structure

```
Helix_wheel/
├── __init__.py           # Package interface & module exports
├── heliquest.py          # Primary wheel renderer & vector plotter
├── hydrophobic_moment.py # Hydrophobicity scale definitions & mathematical calculations
└── README.md             # Module documentation
```

---

## 🚀 Quick Start

### 1. Python Package Usage

You can import `Helix_wheel` directly into your Python scripts or Jupyter notebooks:

```python
import Helix_wheel

# Generate a helical wheel visualization PNG
Helix_wheel.visualize_HW("KGRGKQGGKVRAKAKTRSS", fn_hw="ParI_wheel.png")

# Calculate hydrophobic moment and properties programmatically
hvalues = Helix_wheel.assign_hydrophobicity("KGRGKQGGKVRAKAKTRSS", scale="Fauchere-Pliska")
uH = Helix_wheel.calculate_moment(hvalues, angle=100)
charge = Helix_wheel.calculate_charge("KGRGKQGGKVRAKAKTRSS")

print(f"Mean Hydrophobic Moment: {uH:.3f}, Net Charge: {charge}")
```

### 2. Command Line Interface (CLI)

#### **A. Generate Helical Wheel Diagram (`heliquest.py`)**

```bash
python3 heliquest.py -s KGRGKQGGKVRAKAKTRSS -o ParI_wheel.png
```

**CLI Arguments:**
- `-s`, `--sequence`: Amino acid sequence (1-letter code, case-insensitive, max 40 aa).
- `-o`, `--outfile`: Output image filename (default: `hw.png`).

#### **B. Detailed Sequence Property Analysis (`hydrophobic_moment.py`)**

```bash
# Analyze a single sequence with verbose output
python3 hydrophobic_moment.py -s KGRGKQGGKVRAKAKTRSS -v

# Process a multi-sequence FASTA file and export CSV summary
python3 hydrophobic_moment.py -f sequences.fasta -o properties.csv
```

---

## 🧮 How It Works

```
                        User Input / Command
                                  │
                                  ▼
                            heliquest.py
                        (Main Visualization)
                                  │
                                  │  calls assign_hydrophobicity()
                                  ▼
                        hydrophobic_moment.py
                        (Hydrophobicity Scales)
                                  │
                                  ▼
                   Calculates Hydrophobic Vector (μH)
                                  │
                                  ▼
                      Renders Wheels & Output PNG
```

1. **Spatial Layout:** Residues are placed at $100^\circ$ angular increments ($3.6$ turns per 13 residues in standard $\alpha$-helices), mapping positions 1–18 to the inner ring, 19–36 to the second ring, and 37+ to the outer ring.
2. **Hydrophobic Dipole Vector Calculation:**
   $$\vec{\mu}_H = \frac{1}{N} \sum_{i=1}^N H_i \cdot \begin{pmatrix} \sin(i \cdot 100^\circ) \\ \cos(i \cdot 100^\circ) \end{pmatrix}$$
   where $H_i$ is the residue hydrophobicity value from the Fauchere-Pliska scale.

---

## 📚 References

- **Eisenberg, D., Weiss, R. M., & Terwilliger, T. C. (1982).** The helical hydrophobic moment: a measure of the amphiphilicity of a helix. *Nature*, 299(5881), 371-374.
- **Fauchère, J. L., & Pliska, V. (1983).** Hydrophobic parameters $\pi$ of amino-acid side-chains. *European Journal of Medicinal Chemistry*, 18(4), 369-375.
- **Gautier, R. et al. (2008).** HeliQuest: a web server to screen sequences with amphipathic alpha-helices. *Bioinformatics*, 24(18), 2101-2102.

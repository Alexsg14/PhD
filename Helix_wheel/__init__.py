name = "Helix_wheel"

# Check for dependencies
dependencies = ("numpy", "matplotlib")
missing = []

for mod in dependencies:
    try:
        __import__(mod)
    except ImportError as e:
        missing.append(mod)

if missing:
    raise ImportError(
        "Issue with required dependencies {0}".format(missing))
del dependencies, mod, missing

from .heliquest import visualize_HW
from .hydrophobic_moment import (
    assign_hydrophobicity,
    calculate_moment,
    calculate_charge,
    calculate_discrimination,
    calculate_composition,
    analyze_sequence,
)

# readme
__doc__ = """
Helix_wheel: Helical Wheel & Hydrophobic Moment Generator (HeliQuest style).

This package provides tools for programmatically generating helical wheel diagrams
and calculating hydrophobic moment vectors, net charge, and amino acid composition
for alpha-helical peptide sequences.
"""



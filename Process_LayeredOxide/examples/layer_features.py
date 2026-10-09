"""Read layer spacings and CrystalNN bond lengths; no files overwritten."""
from pathlib import Path
from pymatgen.core import Structure
from Process_LayeredOxide import get_layer_spacing, get_bond_lengths
INPUT = Path("E:/structures/oxide.cif")
LAYER_TOL = 0.5  # angstrom
def main():
    structure = Structure.from_file(INPUT)
    if "O" not in structure.symbol_set:
        raise ValueError("Oxygen layers are required")
    print(get_layer_spacing(structure, tol=LAYER_TOL))
    print(get_bond_lengths(structure))
if __name__ == "__main__":
    main()

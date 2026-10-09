"""Analyze ordered oxide octahedra; inspect missing distortion fields."""
from pathlib import Path
from pymatgen.core import Structure
from Process_Struct import analyze_octahedra_distortion
STRUCTURE_FILE = Path("E:/structures/oxide.cif")
TM_ELEMENTS = ["Fe", "Mn"]
CUTOFF_O = 2.5  # angstrom
def main():
    print(analyze_octahedra_distortion(Structure.from_file(STRUCTURE_FILE),
                                      TM_elements=TM_ELEMENTS, cutoff_O=CUTOFF_O))
if __name__ == "__main__":
    main()

"""Report symmetry groups without serializing PeriodicSite objects."""
from pathlib import Path
from pymatgen.core import Structure
from Process_Struct import get_wyckoff_sites
STRUCTURE_FILE = Path("E:/structures/initial.cif")
SYMPREC = 0.01  # angstrom
def main():
    groups = get_wyckoff_sites(Structure.from_file(STRUCTURE_FILE), symprec=SYMPREC)
    for group in groups:
        print({key: value for key, value in group.items() if key != "sites"})
if __name__ == "__main__":
    main()

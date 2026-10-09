"""Query equivalent atoms; returned partner is not necessarily on the opposite surface."""
from pathlib import Path
from pymatgen.core import Structure
from Process_face import get_symmetry_atom
INPUT = Path("E:/structures/slab.vasp")
INDICES = [0, 1]  # zero-based
def main():
    structure = Structure.from_file(INPUT)
    if any(i < 0 or i >= len(structure) for i in INDICES):
        raise ValueError("Atom index outside structure")
    print(get_symmetry_atom(structure, index_list=INDICES))
if __name__ == "__main__":
    main()

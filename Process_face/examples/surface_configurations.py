"""Generate configurations using the existing single-element-surface algorithm."""
from pathlib import Path
from pymatgen.core import Structure
from Process_face import sym_surface_remove_atoms_single
INPUT = Path("E:/structures/slab_fixed.vasp")
OUTPUT_DIR = Path("E:/results/surface_candidates")
TRIAL_STRUCTURES = 10
KEEP_STRUCTURES = 5
def main():
    if OUTPUT_DIR.exists():
        raise FileExistsError(OUTPUT_DIR)
    structure = Structure.from_file(INPUT)
    if "selective_dynamics" not in structure.site_properties:
        raise ValueError("Existing algorithm requires selective_dynamics")
    OUTPUT_DIR.mkdir(parents=True)
    print(sym_surface_remove_atoms_single(structure.copy(), OUTPUT_DIR,
          nstr=TRIAL_STRUCTURES, select_s=KEEP_STRUCTURES))
if __name__ == "__main__":
    main()

"""Set selective dynamics on a copy; assumes the slab normal is Cartesian z."""
from pathlib import Path
from pymatgen.core import Structure
from Process_face import SurfaceFixer
INPUT = Path("E:/structures/slab.vasp")
OUTPUT = Path("E:/results/slab_fixed.vasp")
BOTTOM_DISTANCE = 2.0  # angstrom from lowest atom; boundary is strict <
def main():
    if BOTTOM_DISTANCE <= 0:
        raise ValueError("BOTTOM_DISTANCE must be positive")
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    structure = Structure.from_file(INPUT).copy()
    fixed = SurfaceFixer(structure).fix_bottom_distance(BOTTOM_DISTANCE)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fixed.to(fmt="poscar", filename=OUTPUT)
    print("Fixed atoms:", sum(not any(flags) for flags in fixed.site_properties["selective_dynamics"]))
if __name__ == "__main__":
    main()

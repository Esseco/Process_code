"""Generate terminations of one Miller plane; inspect before relaxation."""
from pathlib import Path
from pymatgen.core import Structure
from pymatgen.transformations.standard_transformations import OxidationStateDecorationTransformation
from Process_face import LOSlabProcessor
INPUT = Path("E:/structures/bulk.cif")
OUTPUT_DIR = Path("E:/results/slabs_001")
MILLER = (0, 0, 1)
SLAB_THICKNESS = 15.0  # angstrom
VACUUM_THICKNESS = 12.0  # angstrom
OXIDATION_STATES = {"Na": 1, "Fe": 3, "O": -2}  # replace for the actual material
def main():
    if OUTPUT_DIR.exists():
        raise FileExistsError(OUTPUT_DIR)
    structure = Structure.from_file(INPUT)
    if not structure.symbol_set.issubset(OXIDATION_STATES):
        raise ValueError("Set oxidation states for every element")
    processor = LOSlabProcessor(structure,
        OxidationStateDecorationTransformation(OXIDATION_STATES), str(OUTPUT_DIR))
    slabs, _ = processor.generate_slabs(MILLER, min_slab_size=SLAB_THICKNESS,
                                      min_vacuum_size=VACUUM_THICKNESS)
    for i, slab in enumerate(slabs):
        analysis = processor.analyze_face(slab)
        print(i, {key: value for key, value in analysis.items() if key != "slab_obj"})
        slab.to(fmt="poscar", filename=OUTPUT_DIR / f"slab_{i:03d}.vasp")
if __name__ == "__main__":
    main()

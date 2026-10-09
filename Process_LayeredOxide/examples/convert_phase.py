"""Transform a compatible three-layer O3 model; no relaxation is performed."""
from pathlib import Path
from pymatgen.core import Structure
from Process_LayeredOxide import LayerOxide_O3_Transformer
INPUT = Path("E:/structures/O3.cif")
OUTPUT = Path("E:/results/P3.vasp")
PHASE = "p3"  # p3 / o1 / op2_6layer
TM_ELEMENTS = ["Mn", "Ni", "Cu", "Fe"]
def main():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    structure = Structure.from_file(INPUT)
    transformer = LayerOxide_O3_Transformer(tm_elements=TM_ELEMENTS)
    functions = {"p3": transformer.o3_to_p3, "o1": transformer.o3_to_o1,
                 "op2_6layer": transformer.o3_to_op2_6layer}
    result = functions[PHASE](structure)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to(fmt="poscar", filename=OUTPUT)
if __name__ == "__main__":
    main()

"""Feature extraction currently assumes a Na/O-containing oxide."""
from pathlib import Path
from pymatgen.core import Structure
from Process_Struct import StructureFeatureExtractor
STRUCTURE_FILE = Path("E:/structures/Na_oxide.cif")
GLOBAL_GROUPS = ["lattice"]
LOCAL_GROUPS = ["bond_length"]
TM_ELEMENTS = ["Fe", "Mn"]
def main():
    structure = Structure.from_file(STRUCTURE_FILE)
    if not {"Na", "O"}.issubset(structure.symbol_set):
        raise ValueError("This extractor currently assumes Na and O in the composition")
    extractor = StructureFeatureExtractor(global_features=GLOBAL_GROUPS,
                  local_features=LOCAL_GROUPS, tm_elements=TM_ELEMENTS)
    print(extractor.extract(structure))
if __name__ == "__main__":
    main()

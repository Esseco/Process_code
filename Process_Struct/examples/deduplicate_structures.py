"""Keep first structurally distinct representatives; no outputs overwritten."""
from pathlib import Path
from pymatgen.core import Structure
from Process_Struct import deduplicate

INPUT_DIR = Path("E:/structures/candidates")
OUTPUT_DIR = Path("E:/results/unique_structures")


def main():
    if OUTPUT_DIR.exists():
        raise FileExistsError(OUTPUT_DIR)
    paths = sorted(INPUT_DIR.glob("*.vasp"))
    if not paths:
        raise ValueError("No VASP structure files found")
    unique = deduplicate([Structure.from_file(path) for path in paths])
    OUTPUT_DIR.mkdir(parents=True)
    for index, structure in enumerate(unique):
        structure.to(fmt="poscar", filename=OUTPUT_DIR / f"unique_{index:04d}.vasp")
    print(f"Input: {len(paths)}; unique: {len(unique)}")


if __name__ == "__main__":
    main()

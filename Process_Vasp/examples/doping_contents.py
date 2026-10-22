"""Generate lowest-electrostatic-energy orderings for several contents.

Template: put real paths and parameters at the top, then run from the repo root
with ``python -m Process_Vasp.examples.doping_contents``. Only POSCAR files are
written; nothing is submitted and no model is loaded.
"""
from pathlib import Path

from Process_Vasp import gen_ESGS_by_content

REFERENCE = Path("E:/work/Li27.vasp")  # full-occupancy reference, e.g. Li27
SPECIES = "Li"
CONTENTS = [25, 23, 22]  # species count per cell; integers in 0..27
COUNT = 3  # structures kept per content, lowest Ewald energy first
OXIDATION_STATES = None  # e.g. {"Li": 1, "Co": 3, "O": -2}; guessed when None
OUT_DIR = Path("E:/work/Li27_doping")


def main():
    series = gen_ESGS_by_content(
        REFERENCE,
        CONTENTS,
        COUNT,
        species=SPECIES,
        oxidation_states=OXIDATION_STATES,
    )
    for label, structs in series.items():
        folder = OUT_DIR / label
        folder.mkdir(parents=True, exist_ok=True)
        for index, struct in enumerate(structs):
            struct.to(folder / f"{index}.vasp", fmt="poscar")
        print(f"{label}: {len(structs)} structures -> {folder}")


if __name__ == "__main__":
    main()

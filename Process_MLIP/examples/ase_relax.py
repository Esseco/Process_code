"""Run with a calculator factory; importing this template does no work."""
from pathlib import Path
from ase.io import read
from Process_MLIP import MLIPRelaxer

INPUT = Path("E:/structures/initial.cif")
OUTPUT_DIR = Path("E:/results/mlip_relax")
FMAX = 0.05  # eV/angstrom
STEPS = 200
RELAX_CELL = False


def make_calculator():
    """Replace with a calculator compatible with the material and environment."""
    raise NotImplementedError("Supply a tested ASE calculator here")


def main():
    if OUTPUT_DIR.exists():
        raise FileExistsError(OUTPUT_DIR)
    atoms = read(str(INPUT))
    calculator = make_calculator()
    OUTPUT_DIR.mkdir(parents=True)
    result = MLIPRelaxer(atoms.copy(), calculator, fmax=FMAX,
                         steps=STEPS, relax_cell=RELAX_CELL).relax(
        traj_file=str(OUTPUT_DIR / "relax.traj"),
        log_file=str(OUTPUT_DIR / "relax.log"),
        final_structure=str(OUTPUT_DIR / "final.extxyz"),
    )
    print({key: value for key, value in result.items() if key != "final_struct"})


if __name__ == "__main__":
    main()

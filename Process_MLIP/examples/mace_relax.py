"""Use the existing MACE adapter; requires a MACE environment and model."""
from pathlib import Path

INPUT = Path("E:/structures/initial.cif")
MODEL = Path("E:/models/model.model")
OUTPUT = Path("E:/results/mace_relaxed.vasp")
DEVICE = "cuda"
HEAD = None  # explicitly choose for multihead models


def main():
    from Process_MLIP.mace_relax import relax_structure_mace
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    report = relax_structure_mace(INPUT, MODEL, output_path=OUTPUT,
                                  device=DEVICE, head=HEAD,
                                  fmax=0.05, steps=150, relax_cell=False)
    print(report)


if __name__ == "__main__":
    main()

"""Run in the verified py1 environment; edit paths before execution."""
from pathlib import Path

INPUT = Path("E:/structures/initial.cif")
MODEL = Path(__file__).resolve().parents[2] / "MLIP_model/checkpoint_sevennet_omni.pth"
OUTPUT = Path("E:/results/sevennet_relaxed.vasp")
DEVICE = "cpu"
MODAL = "mpa"


def main():
    from Process_MLIP import relax_structure_sevennet
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    report = relax_structure_sevennet(INPUT, MODEL, output_path=OUTPUT,
                                      device=DEVICE, modal=MODAL,
                                      fmax=0.05, steps=150, relax_cell=True)
    print(report)


if __name__ == "__main__":
    main()

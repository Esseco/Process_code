"""Generate two independent same-spin excitation input sets; no VASP launch."""
from pathlib import Path
from Process_Vasp import generate_excited_input

GROUND_DIR = Path("E:/calc/ground_static")
TARGET_DIR = Path("E:/calc/excited_both")
SPIN = "both"  # auto / up / down / both
VALENCE_BAND = None  # 1-based; supply both indices or neither
CONDUCTION_BAND = None


def main():
    reports = generate_excited_input(
        GROUND_DIR, TARGET_DIR, spin=SPIN,
        valence_band=VALENCE_BAND, conduction_band=CONDUCTION_BAND,
    )
    print(reports)


if __name__ == "__main__":
    main()

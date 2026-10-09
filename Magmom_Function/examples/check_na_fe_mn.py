"""Apply the legacy Na-Fe-Mn magnetic heuristic; not a ground-state proof."""
from pathlib import Path
from Magmom_Function.io import check_magnetic_moments
CALC_DIR = Path("E:/calc/NaFeMnO2")
def main():
    flag, suggested_moment = check_magnetic_moments(CALC_DIR)
    print("Heuristic accepted:", bool(flag), "suggested moment:", suggested_moment)
if __name__ == "__main__":
    main()

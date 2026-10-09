"""Read the legacy scalar local-moment table without changing files."""
from pathlib import Path
from Process_Vasp import read_magnetic_moments_outcar
CALC_DIR = Path("E:/calc/static")
def main():
    result = read_magnetic_moments_outcar(CALC_DIR)
    if result == 0:
        raise ValueError("Missing or incomplete magnetization table")
    elements, moments, projected_total = result
    print(list(zip(elements, moments[-1])))
    print("Table total:", projected_total)
if __name__ == "__main__":
    main()

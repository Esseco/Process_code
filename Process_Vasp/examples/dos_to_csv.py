"""Edit paths below, then run from the repository with python -m."""
from pathlib import Path
from Process_Vasp import read_dos

GROUND_DIR = Path("E:/calc/runs/dos/attempt_001")
OUTPUT_CSV = Path("E:/results/dos.csv")
INCLUDE_ORBITAL = False


def main():
    if OUTPUT_CSV.exists():
        raise FileExistsError(OUTPUT_CSV)
    result = read_dos(GROUND_DIR, output_csv=OUTPUT_CSV,
                      include_orbital=INCLUDE_ORBITAL)
    print({key: value for key, value in result.items() if key != "df"})
    print(result["df"].shape)


if __name__ == "__main__":
    main()

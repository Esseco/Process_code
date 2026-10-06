"""Read results independently from the workflow runner; no calculation launch."""
from pathlib import Path
from Process_Vasp import read_vasp_output, read_vasp_status

CALC_DIR = Path("E:/calc/runs/static/attempt_001")
FIELDS = "efs"  # e=energy, f=forces, s=stress, m=magnetization if present
READ_BAND_EDGES = False


def main():
    print(read_vasp_status(CALC_DIR))
    print(read_vasp_output(CALC_DIR, efsm=FIELDS, read_dos=READ_BAND_EDGES))


if __name__ == "__main__":
    main()

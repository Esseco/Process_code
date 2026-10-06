"""Generate a portable task folder; does not submit or run VASP."""
from pathlib import Path
from Process_Vasp import generate_atomate_input

STRUCTURE = Path("E:/structures/initial.cif")
TASK_DIR = Path("E:/tasks/dos_task")
CALCULATION = "dos"  # relax / static / dos / band
INCAR_SETTINGS = {"static": {"LWAVE": True, "LCHARG": True}}
KPOINTS_SETTINGS = {}
RESUME_FROM = {}  # e.g. {"relax": "/server/old_task/job_12345"}
EXPORT_PLOT_DATA = True  # dos.csv or band.csv after a successful final stage


def main():
    if TASK_DIR.exists() and (not TASK_DIR.is_dir() or any(TASK_DIR.iterdir())):
        raise ValueError("Choose an absent or empty task directory")
    print(generate_atomate_input(
        TASK_DIR, STRUCTURE, calculation=CALCULATION,
        incar_settings=INCAR_SETTINGS, kpoints_settings=KPOINTS_SETTINGS,
        resume_from=RESUME_FROM, export_plot_data=EXPORT_PLOT_DATA,
    ))


if __name__ == "__main__":
    main()

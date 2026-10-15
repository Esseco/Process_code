"""Full relaxation -> 5000-step NVT -> MSD. Edit paths/parameters below."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = Path("/path/to/Py-Code")  # contains Process_MLIP/
STRUCTURE = HERE.parent / "initial.cif" # same input file for all eight tasks
MODEL_PATH = Path("/path/to/chgnet.pth.tar")
OUTPUT = HERE / "results"
DEVICE = "cuda"
MODEL_PRESET = 'chgnet'
MODEL_OPTIONS = {}

PRE_RELAX = dict(relax_cell=True, optimizer="FIRE")  # all: atoms + cell
MD = dict(ensemble="nvt", temperature_K=600, steps=5000,
          trajectory_interval=1, log_interval=1, measure_steps_per_second=True)
MSD = dict(enabled=True, species=None, output_csv=OUTPUT / "msd.csv")
# species=None: all elements; change to "Na", "Li", or a list.



def main():
    sys.path.insert(0, str(PROJECT_ROOT))
    from ase.io import read
    from Process_MLIP import model_config, run_mlip_md, export_msd
    atoms = read(str(STRUCTURE))
    model = model_config(MODEL_PRESET, model_path=str(MODEL_PATH),
                         device=DEVICE, **MODEL_OPTIONS)
    result = run_mlip_md(atoms, model=model, output_dir=OUTPUT,
                         pre_relax=PRE_RELAX, **MD)
    print(f"MD: {result['total_steps']} steps; {result['steps_per_second']:.4f} steps/s")
    if MSD["enabled"]:
        exported = export_msd(result["stage_results"][-1]["trajectory_file"],
                               MSD["output_csv"], species=MSD["species"])
        print(f"MSD: {exported['csv_file']}")
    return result


if __name__ == "__main__":
    main()

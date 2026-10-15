"""Full relaxation -> 5000-step NVT -> MSD. Edit paths/parameters below."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = Path("/data/home/lichaoyue/Process_code")  # contains Process_MLIP/
STRUCTURES = [HERE.parent / "LCO.vasp", HERE.parent / "NVP.vasp"]
MODEL_PATH = Path("/data/home/lichaoyue/Process_code/MLIP_model/7net/checkpoint_7net_nano_6.0.pth")
OUTPUT = HERE / "results"
DEVICE = "cuda"
MODEL_PRESET = 'sevennet'
MODEL_OPTIONS = {'enable_flash': True}

PRE_RELAX = dict(relax_cell=True, optimizer="FIRE")  # all: atoms + cell
MD = dict(ensemble="nvt", temperature_K=600, steps=5000,
          trajectory_interval=1, log_interval=1, measure_steps_per_second=True)
MSD = dict(enabled=True, species={"LCO": "Li", "NVP": "Na"})
# MSD: Li for LCO; Na for NVP.


def main():
    sys.path.insert(0, str(PROJECT_ROOT))
    from ase.io import read
    from Process_MLIP import model_config, run_mlip_md, export_msd
    results = []
    for structure in STRUCTURES:
        atoms = read(str(structure))
        output = OUTPUT / structure.stem
        model = model_config(MODEL_PRESET, model_path=str(MODEL_PATH),
                             device=DEVICE, **MODEL_OPTIONS)
        result = run_mlip_md(atoms, model=model, output_dir=output,
                             pre_relax=PRE_RELAX, **MD)
        print(f"{structure.stem} MD: {result['total_steps']} steps; {result['steps_per_second']:.4f} steps/s")
        if MSD["enabled"]:
            exported = export_msd(result["stage_results"][-1]["trajectory_file"],
                                   output / "msd.csv", species=MSD["species"][structure.stem])
            print(f"MSD: {exported['csv_file']}")
        results.append(result)
    return results


if __name__ == "__main__":
    main()

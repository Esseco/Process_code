"""Editable cluster MD example. Importing or --preview does not load models.

From repository root: python -m Process_MLIP.examples.mlip_md --preview
After editing paths/config: python -m Process_MLIP.examples.mlip_md
Use the cluster environment installed for the selected backend; no pip calls.
"""
import argparse
import json
from pathlib import Path

from Process_MLIP import model_config, run_mlip_md


# ==================== Edit these parameters ====================
INPUT = Path("initial.cif")            # enable PRE_RELAX below if preparation is needed
OUTPUT = Path("md_results")           # change for a new independent experiment
MODEL_PRESET = "mace-mh1"              # mace-mh1 / sevennet-omni / chgnet / orb-v3
DEVICE = "cuda"                       # or cuda:0 / cpu

# Each preset already has defaults. Only put overrides here.
# None for SevenNet/CHGNet/ORB means official pretrained loading; on offline
# cluster nodes supply a prepared local checkpoint instead.
MODEL_OVERRIDES = {
    "mace-mh1": {
        # Defaults to <repository>/MLIP_model/mace-mh-1.model; override if needed:
        # "model_path": "/absolute/path/to/mace-mh-1.model",
        "head": "omat_pbe",           # change to matpes_r2scan if appropriate
        "default_dtype": "float64",   # float32 is also selectable
        "enable_cueq": False,         # True enables CuEq; requires cluster support
    },
    "sevennet-omni": {
        "model_path": None,           # or /absolute/path/checkpoint_sevennet_omni.pth
        "modal": "mpa",               # e.g. omat24 / matpes_r2scan
        "enable_flash": False,        # True enables FlashTP
    },
    "chgnet": {
        "model_path": None,           # or /absolute/path/your_chgnet.pth.tar
        "model_name": "0.3.0",        # pretrained version; ignored with model_path
    },
    "orb-v3": {
        "model_path": None,           # or weights matching model_name below
        "model_name": "orb-v3-conservative-inf-omat",
        "precision": "float32-highest",
        "compile": False,             # optional official torch.compile
    },
}

# Optional static pre-relaxation, using the SAME calculator as all MD stages.
# enabled=False: no relaxation; relax_cell=False: atom positions only;
# relax_cell=True: optimize atom positions and cell together (requires stress/3D PBC).
PRE_RELAX = {
    "enabled": False,
    "relax_cell": False,
    "optimizer": "BFGS",              # BFGS / FIRE / LBFGS
    "fmax": 0.05,                     # force threshold eV/angstrom (cell filter also uses stress)
    "steps": 200,
    "require_convergence": True,      # stop before MD if relaxation has not converged
}

# Common defaults, overridden by each STAGES entry where specified.
MD_PARAMETERS = {
    "temperature_K": 800,
    "timestep_fs": 1.0,
    "tdamp_fs": 100.0,
    "pressure_bar": 1.0,              # positive compression; used only for NPT
    "pdamp_fs": 1000.0,               # used only for isotropic MTK NPT
    "seed": 42,
    "initialize_velocities": None,    # sample only if initial momenta absent
    "remove_com": True,               # only during velocity initialization
    "zero_rotation": False,           # leave False for periodic crystals
    "trajectory_interval": 10,
    "log_interval": 10,
    "overwrite": False,               # default refuses to overwrite owned files
}

# One entry = independent NVT or NPT. Multiple entries = continuous stages.
# Defaults below illustrate NVT -> NPT; no stage order is required.
# To run NPT alone, remove the NVT entry. To run NVT alone, remove NPT.
STAGES = [
    {"name": "equilibrate", "ensemble": "nvt", "steps": 1000},
    {"name": "production", "ensemble": "npt", "steps": 5000},
]
# Example of another stage with a different temperature/time step:
# STAGES.append(dict(name="hot", ensemble="nvt", temperature_K=1200,
#                    timestep_fs=0.5, steps=10000))
# Later stages preserve momenta even if target temperature changes. To explicitly
# resample instead, set initialize_velocities=True, seed=43 in that stage.


def main(argv=None):
    """Preview configuration or run MD after editing the parameters above."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="print configuration without reading structures or loading models")
    args = parser.parse_args(argv)
    model = model_config(MODEL_PRESET, device=DEVICE, **MODEL_OVERRIDES[MODEL_PRESET])
    print(json.dumps(dict(input=str(INPUT), output=str(OUTPUT), model=model,
                          pre_relax=PRE_RELAX, common_md=MD_PARAMETERS, stages=STAGES), indent=2))
    if args.preview:
        return
    if not INPUT.is_file():
        raise FileNotFoundError(f"Edit INPUT before running MD: {INPUT}")
    result = run_mlip_md(INPUT, model=model, output_dir=OUTPUT,
                         stages=STAGES, pre_relax=PRE_RELAX, **MD_PARAMETERS)
    if result["pre_relax_result"] is not None:
        relaxation = result["pre_relax_result"]
        print(f"Pre-relax converged: {relaxation['optimizer_converged']}; "
              f"steps: {relaxation['relax_steps_used']}; "
              f"structure: {relaxation['final_structure']}")
    print(f"Completed {result['total_steps']} steps, {result['elapsed_time_fs']} fs")
    print(f"Report: {result['report_file']}")
    print(f"Final atoms with velocities: {result['stage_results'][-1]['final_structure']}")


if __name__ == "__main__":
    main()

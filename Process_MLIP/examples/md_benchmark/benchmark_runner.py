"""Shared runner; imports neither models nor the library during preview."""
import argparse
import json
from pathlib import Path
import sys
import benchmark_config as config

CASES = {
    "mace_mh1": ("mace", "mace_mh1", {"head": "omat_pbe"}),
    "mace_omat": ("mace", "mace_omat", {"head": None}),
    "mace_omat_sym": ("mace", "mace_omat", {"head": None, "enable_symmetrix": True}),
    "sevennet_omni": ("sevennet", "sevennet_omni", {"enable_flash": False}),
    "sevennet_omni_flash": ("sevennet", "sevennet_omni", {"enable_flash": True}),
    "sevennet_nano6": ("sevennet", "sevennet_nano6", {"enable_flash": False}),
    "sevennet_nano6_flash": ("sevennet", "sevennet_nano6", {"enable_flash": True}),
    "chgnet": ("chgnet", "chgnet", {}),
}


def main(case):
    parser = argparse.ArgumentParser(description=f"5000-step NVT benchmark: {case}")
    parser.add_argument("--preview", action="store_true", help="show configuration without loading a model")
    args = parser.parse_args()
    preset, weight_key, extra = CASES[case]
    overrides = dict(model_path=config.MODEL_PATHS[weight_key], device=config.DEVICE, **extra)
    if preset == "mace":
        overrides.update(default_dtype="float64", enable_cueq=False)
    if preset == "sevennet":
        overrides["modal"] = config.SEVENNET_MODAL
    if case == "mace_omat_sym":
        overrides.update(device=config.SYMMETRIX_DEVICE,
                         symmetrix_use_kokkos=config.SYMMETRIX_USE_KOKKOS)
    output = config.OUTPUT_ROOT / case
    print(json.dumps(dict(case=case, structure=str(config.STRUCTURE), preset=preset,
                          model=overrides, pre_relax=False, ensemble="nvt",
                          md=config.MD_PARAMETERS, output=str(output)), indent=2))
    if args.preview:
        return
    if not (config.PROJECT_ROOT / "Process_MLIP").is_dir():
        raise FileNotFoundError("Set PROJECT_ROOT in benchmark_config.py (or PYCODE_ROOT)")
    if not config.STRUCTURE.is_file():
        raise FileNotFoundError(f"Set STRUCTURE: {config.STRUCTURE}")
    if not Path(overrides["model_path"]).is_file():
        raise FileNotFoundError(f"Set MODEL_PATHS[{weight_key!r}]")
    sys.path.insert(0, str(config.PROJECT_ROOT))
    from ase.io import read
    from Process_MLIP import model_config, run_mlip_md
    atoms = read(str(config.STRUCTURE))
    if case == "mace_omat_sym":
        # Reduce conversion cost using exactly the shared structure's elements.
        # A preconverted JSON already fixes elements and requires None instead.
        overrides["symmetrix_species"] = (None if Path(overrides["model_path"]).suffix.lower() == ".json"
                                            else sorted(set(atoms.get_chemical_symbols())))
    model = model_config(preset, **overrides)
    result = run_mlip_md(atoms, model=model, output_dir=output, pre_relax=False,
                         ensemble="nvt", **config.MD_PARAMETERS)
    print(f"{case}: {result['total_steps']} steps; {result['steps_per_second']:.6f} steps/s")
    print(f"Report: {result['report_file']}")


if __name__ == "__main__":
    raise SystemExit("Run one of the numbered scripts")

"""Editable cluster MD example. Importing or --preview does not load models.

From repository root: python -m Process_MLIP.examples.mlip_md --preview
After editing paths/config: python -m Process_MLIP.examples.mlip_md
Use the cluster environment installed for the selected backend; no pip calls.
"""
import argparse
import json
import math
from numbers import Real
from pathlib import Path

from Process_MLIP import export_msd, fit_msd, model_config, run_mlip_md


# ==================== Edit these parameters ====================
INPUT = Path("initial.cif")            # full pre-relaxation is enabled below
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
        "enable_symmetrix": False,    # alternative backend; cannot combine with CuEq
        "symmetrix_use_kokkos": False, # False: CPU float64; True: build-defined Kokkos target
        "symmetrix_species": None,    # e.g. ["Na", "Ni", "Mn", "O"] to reduce conversion cost
        # OMat CPU example: DEVICE="cpu", enable_symmetrix=True,
        # model_path="MLIP_model/mace/mace-omat-0-medium.model", head=None.
        # Preconverted Symmetrix .json: head=None and symmetrix_species=None.
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
    "enabled": True,
    "relax_cell": True,               # all: optimize atoms and full cell
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
    "pdamp_fs": 1000.0,               # used for both MTK NPT modes
    "npt_cell_mode": "isotropic",    # isotropic: fixed shape; full: flexible cell
    "tchain": 3,                      # thermostat chain length (NVT and NPT)
    "pchain": 3,                      # barostat thermostat chain length (NPT)
    "tloop": 1,                       # thermostat integration substeps
    "ploop": 1,                       # barostat integration substeps (NPT)
    "seed": 42,
    "initialize_velocities": None,    # sample only if initial momenta absent
    "remove_com": True,               # only during velocity initialization
    "zero_rotation": False,           # leave False for periodic crystals
    "trajectory_interval": 10,
    "log_interval": 10,
    "measure_steps_per_second": True, # optional MD throughput; excludes loading/pre-relax
    "overwrite": False,               # default refuses to overwrite owned files
}

# One entry = independent NVT or NPT. Multiple entries = continuous stages.
# Default workflow: full static relaxation -> fixed-cell NVT.
# NVT inherits the optimized cell. Add NPT explicitly when needed.
STAGES = [
    {"name": "production", "ensemble": "nvt", "steps": 5000},
]
# Example of another stage with a different temperature/time step:
# STAGES.append(dict(name="hot", ensemble="nvt", temperature_K=1200,
#                    timestep_fs=0.5, steps=10000))
# For full cell flexibility, set npt_cell_mode="full" in the NPT stage;
# requires an ASE environment providing MTKNPT. No fallback/upgrade is automatic.
# STAGES.append(dict(name="pressure", ensemble="npt", steps=5000,
#                    npt_cell_mode="full", tchain=3, pchain=3, tloop=1, ploop=1))
# For ionic-diffusion MSD, append a fixed-cell NVT production stage, then use
# Process_MLIP.examples.msd on its md.traj (change paths/species in that example):
# STAGES.append(dict(name="diffusion", ensemble="nvt", steps=10000))
# Later stages preserve momenta even if target temperature changes. To explicitly
# resample instead, set initialize_velocities=True, seed=43 in that stage.

# Optional automatic MSD export AFTER all MD stages finish successfully.
# Select only an NVT stage; different temperatures/stages are not combined.
MSD_POSTPROCESS = {
    "enabled": False,
    "stage": "last_nvt",             # last NVT, or a stage number starting from 1
    "species": "Na",                 # "Li", ["Na", "Li"], or None for all elements
    "output_csv": None,              # None -> selected stage/msd.csv
    # Relative paths are under OUTPUT, e.g. "analysis/msd_na.csv";
    # an absolute path is used as-is.
    "overwrite": False,
}


# Requires MSD_POSTPROCESS enabled; choose a diffusive production NVT stage.
# Window in ps, inclusive; at least 3 saved samples. Set for YOUR run length.
TRANSPORT_FIT = {
    "enabled": False,
    "fit_start_ps": 2.0,
    "fit_end_ps": 8.0,
    "ion_charge": 1,                  # charge in e; or {"Na": 1, "Li": 1}
    "output_json": None,              # None -> beside MSD CSV: transport.json
    "overwrite": False,
}


def _prepare_msd_postprocess():
    """Check the selected NVT stage and destination before starting MD."""
    if type(MSD_POSTPROCESS.get("enabled", False)) is not bool:
        raise TypeError("MSD_POSTPROCESS enabled must be bool")
    if not MSD_POSTPROCESS.get("enabled", False):
        return None
    if type(MSD_POSTPROCESS.get("overwrite", False)) is not bool:
        raise TypeError("MSD_POSTPROCESS overwrite must be bool")
    modes = [str(stage.get("ensemble", MD_PARAMETERS.get("ensemble", "nvt"))).lower()
             for stage in STAGES]
    choice = MSD_POSTPROCESS.get("stage", "last_nvt")
    if choice == "last_nvt":
        candidates = [index for index, mode in enumerate(modes) if mode == "nvt"]
        if not candidates:
            raise ValueError("Automatic MSD export requires an NVT stage")
        index = candidates[-1]
    elif type(choice) is int and 1 <= choice <= len(STAGES):
        index = choice - 1
    else:
        raise ValueError("MSD stage must be last_nvt or a stage number starting from 1")
    if modes[index] != "nvt":
        raise ValueError("MSD target must be an NVT stage")
    if STAGES[index].get("steps", MD_PARAMETERS.get("steps", 1000)) < 1:
        raise ValueError("MSD target needs at least one MD step and two saved frames")
    stage_dir = Path(OUTPUT) / f"{index + 1:02d}_{STAGES[index].get('name') or modes[index]}"
    configured = MSD_POSTPROCESS.get("output_csv")
    if configured is None:
        destination = stage_dir / "msd.csv"
    else:
        destination = Path(configured)
        if not destination.is_absolute():
            destination = Path(OUTPUT) / destination
    if destination.is_symlink() or destination.is_dir():
        raise FileExistsError(destination)
    destination = destination.resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("MSD output_csv must have a .csv extension")
    log_paths = {(Path(OUTPUT) / f"{i + 1:02d}_{stage.get('name') or modes[i]}" / "md.csv").resolve()
                 for i, stage in enumerate(STAGES)}
    if destination in log_paths:
        raise ValueError("MSD output_csv must not overwrite an MD log")
    if destination.exists() and not MSD_POSTPROCESS.get("overwrite", False):
        raise FileExistsError(destination)
    return index, destination


def main(argv=None):
    """Preview configuration or run MD after editing the parameters above."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="print configuration without reading structures or loading models")
    args = parser.parse_args(argv)
    model = model_config(MODEL_PRESET, device=DEVICE, **MODEL_OVERRIDES[MODEL_PRESET])
    print(json.dumps(dict(input=str(INPUT), output=str(OUTPUT), model=model,
                          pre_relax=PRE_RELAX, common_md=MD_PARAMETERS, stages=STAGES,
                          msd_postprocess=MSD_POSTPROCESS,
                          transport_fit=TRANSPORT_FIT), indent=2, default=str))
    if args.preview:
        return
    if not INPUT.is_file():
        raise FileNotFoundError(f"Edit INPUT before running MD: {INPUT}")
    msd_target = _prepare_msd_postprocess()
    if type(TRANSPORT_FIT.get("enabled", False)) is not bool:
        raise TypeError("TRANSPORT_FIT enabled must be bool")
    fit_destination = None
    if TRANSPORT_FIT.get("enabled", False):
        if msd_target is None:
            raise ValueError("TRANSPORT_FIT requires MSD_POSTPROCESS enabled")
        if type(TRANSPORT_FIT.get("overwrite", False)) is not bool:
            raise TypeError("TRANSPORT_FIT overwrite must be bool")
        start, end = (TRANSPORT_FIT[key] for key in ("fit_start_ps", "fit_end_ps"))
        if any(isinstance(v, bool) or not isinstance(v, Real) or not math.isfinite(v)
               for v in (start, end)) or not 0 <= start < end:
            raise ValueError("Require finite 0 <= fit_start_ps < fit_end_ps")
        stage = STAGES[msd_target[0]]
        steps = stage.get("steps", MD_PARAMETERS.get("steps", 1000))
        dt = stage.get("timestep_fs", MD_PARAMETERS.get("timestep_fs", 1.0))
        interval = stage.get("trajectory_interval", MD_PARAMETERS.get("trajectory_interval", 10))
        if end > steps * dt / 1000:
            raise ValueError("Transport fit window exceeds the selected NVT duration")
        # Count regular saved frames in the window plus the mandatory short last frame.
        first = max(0, math.ceil(start * 1000 / dt / interval - 1e-12))
        last = min(steps // interval, math.floor(end * 1000 / dt / interval + 1e-12))
        samples = max(0, last - first + 1)
        samples += int(steps % interval != 0 and start <= steps * dt / 1000 <= end)
        if samples < 3:
            raise ValueError("Transport fit window needs at least three saved MSD frames")
        charge = TRANSPORT_FIT["ion_charge"]
        values = list(charge.values()) if isinstance(charge, dict) else [charge]
        if not values or any(isinstance(v, bool) or not isinstance(v, Real)
                             or not math.isfinite(v) or v == 0 for v in values):
            raise ValueError("ion_charge must contain finite nonzero charge numbers")
        configured = TRANSPORT_FIT.get("output_json")
        fit_destination = (msd_target[1].with_name("transport.json") if configured is None
                           else Path(configured))
        if configured is not None and not fit_destination.is_absolute():
            fit_destination = Path(OUTPUT) / fit_destination
        if fit_destination.suffix.lower() != ".json":
            raise ValueError("Transport output_json must have .json extension")
        # Keep analysis output away from all simulation reports and inputs.
        forbidden = {Path(INPUT).resolve(), msd_target[1].resolve(),
                     (Path(OUTPUT) / "run_report.json").resolve()}
        for i, stage in enumerate(STAGES):
            mode = stage.get("ensemble", "nvt")
            forbidden.add((Path(OUTPUT) / f"{i+1:02d}_{stage.get('name') or mode}" / "report.json").resolve())
        forbidden.add((Path(OUTPUT) / "00_relax" / "report.json").resolve())
        if fit_destination.resolve() in forbidden:
            raise ValueError("Transport output cannot overwrite simulation data")
        if (fit_destination.is_symlink() or fit_destination.is_dir()
                or (fit_destination.exists() and not TRANSPORT_FIT.get("overwrite", False))):
            raise FileExistsError(fit_destination)
    result = run_mlip_md(INPUT, model=model, output_dir=OUTPUT,
                         stages=STAGES, pre_relax=PRE_RELAX, **MD_PARAMETERS)
    if result["pre_relax_result"] is not None:
        relaxation = result["pre_relax_result"]
        print(f"Pre-relax converged: {relaxation['optimizer_converged']}; "
              f"steps: {relaxation['relax_steps_used']}; "
              f"structure: {relaxation['final_structure']}")
    print(f"Completed {result['total_steps']} steps, {result['elapsed_time_fs']} fs")
    if result["steps_per_second"] is not None:
        print(f"MD throughput: {result['steps_per_second']:.3f} steps/s")
    print(f"Report: {result['report_file']}")
    print(f"Final atoms with velocities: {result['stage_results'][-1]['final_structure']}")
    if msd_target is not None:
        index, destination = msd_target
        exported = export_msd(result["stage_results"][index]["trajectory_file"], destination,
                               species=MSD_POSTPROCESS.get("species"),
                               overwrite=MSD_POSTPROCESS.get("overwrite", False))
        print(f"MSD: {exported['csv_file']} (NVT stage {index + 1})")
        if fit_destination is not None:
            stage = STAGES[index]
            fitted = fit_msd(exported["csv_file"],
                             fit_start_ps=TRANSPORT_FIT["fit_start_ps"],
                             fit_end_ps=TRANSPORT_FIT["fit_end_ps"],
                             ion_charge=TRANSPORT_FIT["ion_charge"],
                             temperature_K=stage.get("temperature_K", MD_PARAMETERS.get("temperature_K", 300)),
                             volume_A3=result["stage_results"][index]["final_atoms"].get_volume(),
                             output_json=fit_destination,
                             overwrite=TRANSPORT_FIT.get("overwrite", False))
            print(f"Transport: {fit_destination}")
            for row in fitted["results"]:
                print(f"{row['species']}: D={row['diffusion_cm2_s']:.6g} cm2/s; "
                      f"sigma_NE={row['conductivity_NE_S_cm']:.6g} S/cm")


if __name__ == "__main__":
    main()

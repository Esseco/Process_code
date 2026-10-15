"""Configure a model once and execute a validated sequence of MD stages."""
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
import re

from .calculators import create_mlip_calculator
from .md import (_check_outputs, _copy_structure, _validate_atoms,
                 _validate_options, _write_json, run_md)
from .model_config import _resolve_model_config
from .pre_relax import _RELAX_FILES, _run_pre_relax, _validate_pre_relax


def run_mlip_md(structure, model="mace-mh1", output_dir="md_results", stages=None,
                *, pre_relax=None, **md_parameters):
    """Load one model and run independent NVT/NPT or consecutive MD stages.

    model is a model_config dict or preset name. stages is a nonempty list
    of parameter dicts; None means one stage with md_parameters. Precedence:
    stage > common md_parameters > run_md defaults. Optional stage name must
    contain only ASCII letters, numbers, underscores or hyphens.

    Stage transitions inherit positions/cell/momenta by default. Only an
    explicit stage initialize_velocities=True resamples later-stage momenta.
    Auxiliary thermostat/barostat variables reset: this is not exact restart.
    pre_relax=None/False disables preparation; True or a dict enables optional
    atoms-only or cell+atoms optimization with this same calculator. Dict keys:
    enabled, relax_cell, optimizer, fmax (eV/Å), steps, require_convergence.
    Unconverged preparation stops by default. Existing momenta are preserved;
    MD velocity initialization runs only after preparation.
    Validates all stages/output collisions before loading the model. Writes
    run_report.json and numbered stage directories; returns final_atoms,
    stage_results, elapsed simulation time and report paths.
    """
    config = _resolve_model_config(model)
    relaxation = _validate_pre_relax(pre_relax)
    common = _validate_options(md_parameters)
    if stages is None:
        stages = [{}]
    if not isinstance(stages, (list, tuple)) or not stages:
        raise ValueError("stages must be a nonempty list of parameter dicts")
    if Path(output_dir).is_symlink():
        raise FileExistsError(f"Output directory must not be a symlink: {output_dir}")
    root = Path(output_dir).resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(root)
    summary_path = root / "run_report.json"
    if summary_path.is_symlink() or summary_path.is_dir() or (
            summary_path.exists() and not common["overwrite"]):
        raise FileExistsError(summary_path)
    atoms = _copy_structure(structure)
    prepared = []
    offset = common["time_offset_fs"]
    for index, stage in enumerate(stages):
        if not isinstance(stage, Mapping):
            raise TypeError("Each stage must be a parameter dict")
        stage = deepcopy(dict(stage))
        name = stage.pop("name", None)
        if name is not None and (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name)):
            raise ValueError("Stage name may contain only ASCII letters, numbers, '_' or '-'")
        if "time_offset_fs" in stage or "overwrite" in stage:
            raise ValueError("time_offset_fs and overwrite must be common parameters")
        parameters = dict(common, **stage)
        if index > 0 and "initialize_velocities" not in stage:
            parameters["initialize_velocities"] = False
        parameters["time_offset_fs"] = offset
        parameters = _validate_options(parameters)
        # Later stages will receive momenta from the preceding stage.
        _validate_atoms(atoms, dict(parameters, initialize_velocities=True)
                        if index else parameters)
        destination = root / f"{index + 1:02d}_{name or parameters['ensemble']}"
        _check_outputs(destination, common["overwrite"])
        prepared.append(dict(output_dir=str(destination), parameters=parameters))
        offset += parameters["steps"] * parameters["timestep_fs"]
    if relaxation["enabled"]:
        _check_outputs(root / "00_relax", common["overwrite"], filenames=_RELAX_FILES)
        if relaxation["relax_cell"]:
            _validate_atoms(atoms, dict(prepared[0]["parameters"], ensemble="npt"))
    calculator = create_mlip_calculator(config)
    root.mkdir(parents=True, exist_ok=True)
    source = str(Path(structure).resolve()) if isinstance(structure, (str, Path)) else type(structure).__name__
    summary = dict(status="running", model=config, input_structure=source,
                   atom_count=len(atoms), stages=prepared,
                   stages_completed=0, stage_results=[], pre_relax_parameters=relaxation,
                   pre_relax_result=None)
    _write_json(summary_path, summary)
    results = []
    relax_result = None
    try:
        if relaxation["enabled"]:
            summary["active_stage"] = "pre_relax"
            _write_json(summary_path, summary)
            relax_result = _run_pre_relax(atoms, calculator, root / "00_relax", relaxation,
                                          overwrite=common["overwrite"], model_metadata=config)
            atoms = relax_result["final_atoms"]
            summary["pre_relax_result"] = {key: value for key, value in relax_result.items()
                                             if key != "final_atoms"}
            _write_json(summary_path, summary)
            if relaxation["require_convergence"] and not relax_result["optimizer_converged"]:
                raise RuntimeError("Pre-relaxation did not converge; increase steps or explicitly "
                                   "set require_convergence=False to continue into MD")
        for index, stage in enumerate(prepared):
            summary["active_stage"] = index + 1
            _write_json(summary_path, summary)
            result = run_md(atoms, calculator, stage["output_dir"],
                            model_metadata=config, **stage["parameters"])
            atoms = result["final_atoms"]
            results.append(result)
            summary["stages_completed"] = len(results)
            summary["stage_results"].append({key: value for key, value in result.items()
                                              if key != "final_atoms"})
            _write_json(summary_path, summary)
        summary.update(status="completed", total_steps=sum(r["steps_completed"] for r in results),
                       end_time_fs=offset, elapsed_time_fs=offset - common["time_offset_fs"])
        _write_json(summary_path, summary)
    except (Exception, KeyboardInterrupt) as exc:
        summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        _write_json(summary_path, summary)
        raise
    return dict(final_atoms=atoms, stage_results=results, pre_relax_result=relax_result,
                status="completed",
                total_steps=summary["total_steps"], elapsed_time_fs=summary["elapsed_time_fs"],
                end_time_fs=offset, report_file=str(summary_path), output_dir=str(root))

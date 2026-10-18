"""Optional geometry preparation using the same calculator as subsequent MD."""
from collections.abc import Mapping
from numbers import Integral, Real

import numpy as np
from ase.calculators.calculator import PropertyNotImplementedError
from ase.io import write

from .MLIP_Relax import MLIPRelaxer
from ._md_support import _check_outputs, _snapshot, _versions, _write_json


_RELAX_FILES = ("relax.traj", "relax.log", "final.traj", "report.json")


def _validate_pre_relax(config):
    options = dict(
        enabled=False,             # 是否预弛豫
        relax_cell=False,          # False: 仅原子；True: 原子+晶胞
        optimizer="FIRE",          # BFGS / FIRE / LBFGS（大写）
        fmax=0.05,                 # 收敛阈值，eV/Å
        steps=200,                 # 最大步数，非负整数
        maxstep=0.05,               # 优化步幅上限，Å（晶胞变量按比例缩放）
        exp_cell_factor=None,      # 晶胞缩放因子；None 使用原子数
        require_convergence=True,  # 未收敛则停止 MD
    )
    if config is None:
        return options
    if type(config) is bool:
        options["enabled"] = config
    elif isinstance(config, Mapping):
        unknown = config.keys() - options.keys()
        if unknown:
            raise ValueError(f"Unknown pre_relax parameters: {sorted(unknown)}")
        options["enabled"] = True
        options.update(dict(config))
    else:
        raise TypeError("pre_relax must be None, bool, or a parameter dict")
    for key in ("enabled", "relax_cell", "require_convergence"):
        if type(options[key]) is not bool:
            raise TypeError(f"pre_relax {key} must be bool")
    if options["optimizer"] not in ("BFGS", "FIRE", "LBFGS"):
        raise ValueError("pre_relax optimizer must be BFGS, FIRE or LBFGS")
    value = options["fmax"]
    if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or value <= 0:
        raise ValueError("pre_relax fmax must be finite and positive (eV/Å)")
    options["fmax"] = float(value)
    value = options["steps"]
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError("pre_relax steps must be a nonnegative integer")
    options["steps"] = int(value)
    for key in ("maxstep", "exp_cell_factor"):
        value = options[key]
        if value is None and key == "exp_cell_factor":
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value) or value <= 0:
            raise ValueError(f"pre_relax {key} must be finite and positive")
        options[key] = float(value)
    return options


def _run_pre_relax(atoms, calculator, output_dir, parameters, *, overwrite=False,
                    model_metadata=None):
    """Optimize a copied structure; preserve momenta and save optimizer facts."""
    root = _check_outputs(output_dir, overwrite, filenames=_RELAX_FILES)
    atoms = atoms.copy()
    atoms.calc = calculator
    if parameters["relax_cell"]:
        try:
            stress = atoms.get_stress()
        except PropertyNotImplementedError as exc:
            raise ValueError("Cell pre-relaxation requires calculator stress support") from exc
        if not np.all(np.isfinite(stress)):
            raise RuntimeError("Pre-relaxation received non-finite stress")
    initial_state = _snapshot(atoms, require_stress=parameters["relax_cell"])
    root.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for name in ("relax.traj", "relax.log", "final.traj"):
            (root / name).unlink(missing_ok=True)
    paths = dict(trajectory_file=str(root / "relax.traj"), log_file=str(root / "relax.log"),
                 final_structure=str(root / "final.traj"), report_file=str(root / "report.json"))
    report = dict(status="running", parameters=parameters,
                  model={} if model_metadata is None else model_metadata,
                  versions=_versions(calculator), initial_state=initial_state,
                  cell_relaxed=parameters["relax_cell"], **paths)
    _write_json(paths["report_file"], report)
    try:
        result = MLIPRelaxer(atoms, calculator, fmax=parameters["fmax"],
                             steps=parameters["steps"], optimizer=parameters["optimizer"],
                             relax_cell=parameters["relax_cell"], maxstep=parameters["maxstep"],
                             exp_cell_factor=parameters["exp_cell_factor"]).relax(
                                 traj_file=paths["trajectory_file"], log_file=paths["log_file"])
        final_state = _snapshot(atoms, require_stress=parameters["relax_cell"])
        write(paths["final_structure"], atoms, format="traj")
        report.update(status="converged" if result["optimizer_converged"] else "not_converged",
                      optimizer_converged=result["optimizer_converged"],
                      relax_steps_used=result["relax_steps_used"], energy=float(result["energy"]),
                      energy_per_atom=float(result["energy_per_atom"]), energy_unit="eV",
                      force_max_ev_per_angstrom=result["force_max_ev_per_angstrom"],
                      cell_filter=result["cell_filter"], maxstep=result["maxstep"],
                      exp_cell_factor=result["exp_cell_factor"],
                      final_state=final_state)
        _write_json(paths["report_file"], report)
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        _write_json(paths["report_file"], report)
        raise
    return dict(report, final_atoms=atoms, output_dir=str(root))

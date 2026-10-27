"""Native GPUMD MD task preparation and execution for NEP models."""
from collections.abc import Mapping
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

import numpy as np
from ase import Atoms
from ase.io import write

from ._md_support import _copy_structure


def _is_link_or_reparse(path):
    path = Path(path)
    if path.is_symlink():
        return True
    try:
        return bool(path.stat(follow_symlinks=False).st_file_attributes &
                    stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False


def _executable(executable):
    path = Path(executable).expanduser()
    if path.is_file():
        return str(path.resolve())
    resolved = shutil.which(str(executable))
    if resolved is None:
        raise FileNotFoundError(f"GPUMD executable not found: {executable}")
    resolved_path = Path(resolved)
    return str(resolved_path.resolve()) if resolved_path.is_file() else str(resolved)


def _render_value(value):
    if isinstance(value, (tuple, list)):
        return " ".join(_render_value(item) for item in value)
    return str(value)


def _render_run(parameters):
    if isinstance(parameters, Mapping):
        items = list(parameters.items())
    elif isinstance(parameters, (list, tuple)):
        items = list(parameters)
        if any(not isinstance(item, (list, tuple)) or len(item) != 2 for item in items):
            raise TypeError("run parameters must be a mapping or (keyword, value) pairs")
    else:
        raise TypeError("parameters must be a mapping or (keyword, value) pairs")
    lines = ["potential nep.txt"]
    for key, value in items:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("GPUMD run keywords must be nonempty strings")
        if key.strip().lower() == "potential":
            raise ValueError("the NEP potential is fixed to the staged nep.txt model")
        lines.append(f"{key} {_render_value(value)}")
    return "\n".join(lines) + "\n"


def _write_model(path, atoms):
    if not isinstance(atoms, Atoms) or len(atoms) == 0:
        raise ValueError("GPUMD MD requires a nonempty ASE structure")
    if atoms.cell.rank != 3 or not np.all(atoms.pbc) or not np.all(np.isfinite(atoms.cell.array)):
        raise ValueError("GPUMD MD requires a finite full periodic cell")
    if not np.all(np.isfinite(atoms.positions)):
        raise ValueError("GPUMD MD positions must be finite")
    frame = atoms.copy()
    frame.arrays["mass"] = frame.get_masses()
    if frame.has("momenta"):
        frame.arrays["vel"] = frame.get_velocities()
    write(path, frame, format="extxyz", write_results=False)


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                     allow_nan=False), encoding="utf-8")


def _json_value(value):
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _output_guard(root, overwrite):
    for name in ("model.xyz", "nep.txt", "run.in", "run.stdout", "run.stderr",
                 "report.json", "manifest.json"):
        path = root / name
        if _is_link_or_reparse(path) or path.is_dir():
            raise FileExistsError(f"Output must be a regular file: {path}")
        if path.exists() and not overwrite:
            raise FileExistsError(path)


def run_nep_md(structure, model_path, output_dir, *, parameters,
               executable="gpumd", overwrite=False, env=None, timeout=None):
    """Run a native GPUMD task with an explicit NEP model and run parameters.

    The task directory contains ``model.xyz``, ``nep.txt``, ``run.in``,
    captured stdout/stderr, and ``report.json``. GPUMD output files such as
    ``thermo.out`` and ``dump.xyz`` are preserved for later analysis.
    """
    if timeout is not None and (isinstance(timeout, bool) or timeout <= 0):
        raise ValueError("timeout must be positive or None")
    model = Path(model_path).expanduser()
    if not model.is_file():
        raise FileNotFoundError(model)
    command = _executable(executable)
    atoms = _copy_structure(structure)
    root = Path(output_dir).expanduser()
    if _is_link_or_reparse(root) or (root.exists() and not root.is_dir()):
        raise FileExistsError(root)
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise FileExistsError(root)
    root.mkdir(parents=True, exist_ok=True)
    _output_guard(root, overwrite)
    model_target = root / "nep.txt"
    if model.resolve() != model_target.resolve():
        shutil.copyfile(model, model_target)
    _write_model(root / "model.xyz", atoms)
    (root / "run.in").write_text(_render_run(parameters), encoding="utf-8")
    merged_env = None if env is None else dict(os.environ, **dict(env))
    explicit_env = {} if env is None else dict(env)
    parameter_data = _json_value(parameters)
    seed = parameters.get("seed") if isinstance(parameters, Mapping) else None
    manifest = {
        "schema_version": 1, "backend": "gpumd", "model_path": str(model),
        "model_file": str(model_target), "run_file": str(root / "run.in"),
        "parameters": parameter_data, "seed": seed,
        "environment": _json_value(explicit_env), "atom_count": len(atoms),
    }
    _write_json(root / "manifest.json", manifest)
    try:
        completed = subprocess.run([command], cwd=str(root), env=merged_env,
                                   capture_output=True, text=True, shell=False,
                                   timeout=timeout, check=False)
    except Exception as exc:
        report = {"status": "failed", "backend": "gpumd", "command": [command],
                  "error": f"{type(exc).__name__}: {exc}",
                  "model_file": str(model_target), "run_file": str(root / "run.in"),
                  "parameters": parameter_data, "seed": seed,
                  "environment": _json_value(explicit_env),
                  "manifest_file": str(root / "manifest.json")}
        _write_json(root / "report.json", report)
        raise
    (root / "run.stdout").write_text(completed.stdout or "", encoding="utf-8")
    (root / "run.stderr").write_text(completed.stderr or "", encoding="utf-8")
    report = {
        "status": "completed" if completed.returncode == 0 else "failed",
        "backend": "gpumd", "command": [command],
        "returncode": int(completed.returncode), "model_file": str(model_target),
        "run_file": str(root / "run.in"), "model_path": str(model),
        "stdout_file": str(root / "run.stdout"), "stderr_file": str(root / "run.stderr"),
        "atom_count": len(atoms), "parameters": parameter_data, "seed": seed,
        "environment": _json_value(explicit_env),
        "manifest_file": str(root / "manifest.json"),
    }
    _write_json(root / "report.json", report)
    if completed.returncode != 0:
        raise RuntimeError(f"GPUMD executable failed with return code {completed.returncode}")
    return report

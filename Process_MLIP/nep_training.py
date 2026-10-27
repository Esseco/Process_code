"""Task generation and explicit subprocess execution for GPUMD ``nep``."""
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


_DEFAULT_PARAMETERS = {
    "lambda_e": 1.0,
    "lambda_f": 1.0,
    "lambda_v": 0.1,
    "batch": 1000,
    "population": 50,
    "generation": 100000,
}
_IMMUTABLE = ("version", "zbl", "cutoff", "n_max", "basis_size", "l_max", "neuron")


def _species(value):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise TypeError("species must be a nonempty sequence of element symbols")
    values = list(value)
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise TypeError("species must contain nonempty strings")
    if len(set(values)) != len(values):
        raise ValueError("species must not contain duplicates")
    return values


def _is_link_or_reparse(path):
    path = Path(path)
    if path.is_symlink():
        return True
    try:
        return bool(path.stat(follow_symlinks=False).st_file_attributes &
                    stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except (AttributeError, OSError):
        return False


def _format(value):
    if isinstance(value, (list, tuple)):
        return " ".join(_format(item) for item in value)
    if isinstance(value, bool):
        return str(int(value))
    return str(value)


def _copy(source, target):
    source = Path(source).expanduser()
    target = Path(target)
    if not source.is_file():
        raise FileNotFoundError(source)
    if _is_link_or_reparse(target) or target.is_dir():
        raise FileExistsError(f"Output must be a regular file: {target}")
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)


def _ensure_dir(path, overwrite):
    root = Path(path).expanduser()
    if _is_link_or_reparse(root) or (root.exists() and not root.is_dir()):
        raise FileExistsError(root)
    if root.exists() and any(root.iterdir()) and not overwrite:
        raise FileExistsError(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                     allow_nan=False), encoding="utf-8")


def _read_architecture(path):
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError("Foundation NEP model is empty")
    first = lines[0].split()
    if len(first) < 3 or not first[0].lower().startswith("nep"):
        raise ValueError("Foundation NEP model has no readable NEP header")
    try:
        version = int(first[0][3:])
        count = int(first[1])
    except ValueError as exc:
        raise ValueError("Foundation NEP header has invalid version/type") from exc
    if version != 4 or count != len(first) - 2:
        raise ValueError("Only a consistent NEP4 foundation header is supported")
    architecture = {"version": version, "type": [count, *first[2:]]}
    aliases = {"ann": "neuron"}
    for line in lines[1:8]:
        tokens = line.split()
        key = aliases.get(tokens[0].lower(), tokens[0].lower())
        if key in _IMMUTABLE and len(tokens) > 1:
            values = tokens[1:]
            architecture[key] = values[0] if len(values) == 1 else values
    missing = [key for key in _IMMUTABLE if key not in architecture]
    if missing:
        raise ValueError(f"Foundation NEP model is missing architecture fields: {', '.join(missing)}")
    return architecture


def _normalise(value):
    if isinstance(value, (tuple, list)):
        return [_normalise(item) for item in value]
    if isinstance(value, float):
        return round(value, 12)
    return value


def _render_input(species, parameters):
    values = dict(parameters)
    version = values.pop("version", 4)
    if int(version) != 4:
        raise ValueError("Only NEP version 4 is supported")
    values.pop("type", None)
    lines = [f"type {len(species)} {' '.join(species)}", "version 4"]
    for key, value in values.items():
        if value is None:
            continue
        lines.append(f"{key} {_format(value)}")
    return "\n".join(lines) + "\n"


def prepare_nep_training(output_dir, train_xyz, test_xyz, *, species,
                         parameters=None, overwrite=False, mode="train"):
    """Create a self-contained GPUMD NEP training/fine-tuning directory."""
    species = _species(species)
    if not isinstance(parameters, (Mapping, type(None))):
        raise TypeError("parameters must be a mapping or None")
    if mode not in ("train", "fine_tune"):
        raise ValueError("mode must be train or fine_tune")
    root = _ensure_dir(output_dir, overwrite)
    train_target, test_target = root / "train.xyz", root / "test.xyz"
    for target in (train_target, test_target, root / "nep.in", root / "manifest.json"):
        if _is_link_or_reparse(target) or target.is_dir():
            raise FileExistsError(f"Output must be a regular file: {target}")
    if (train_target.exists() or test_target.exists()) and not overwrite:
        raise FileExistsError("Training dataset already exists")
    _copy(train_xyz, train_target)
    _copy(test_xyz, test_target)
    effective = dict(_DEFAULT_PARAMETERS)
    if parameters:
        effective.update(dict(parameters))
    (root / "nep.in").write_text(_render_input(species, effective), encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "mode": mode,
        "species": species,
        "parameters": effective,
        "train_file": str(train_target),
        "test_file": str(test_target),
        "seed": effective.get("seed"),
    }
    _write_json(root / "manifest.json", manifest)
    return {"output_dir": str(root), "train_file": str(train_target),
            "test_file": str(test_target), "input_file": str(root / "nep.in"),
            "manifest_file": str(root / "manifest.json"), "mode": mode,
            "parameters": effective}


def fine_tune_nep(output_dir, foundation_model, foundation_restart, *, species,
                  train_xyz=None, test_xyz=None, parameters=None,
                  executable="nep", env=None, timeout=None, overwrite=False):
    """Prepare and run a NEP fine-tuning task from a foundation model/restart."""
    foundation_model = Path(foundation_model).expanduser()
    foundation_restart = Path(foundation_restart).expanduser()
    if not foundation_model.is_file():
        raise FileNotFoundError(foundation_model)
    if not foundation_restart.is_file():
        raise FileNotFoundError(foundation_restart)
    architecture = _read_architecture(foundation_model)
    species = _species(species)
    foundation_species = architecture["type"][1:]
    if species != foundation_species:
        raise ValueError("fine-tune species must match foundation species exactly")
    requested = dict(parameters or {})
    for key in _IMMUTABLE:
        if key in requested and key in architecture and _normalise(requested[key]) != _normalise(architecture[key]):
            raise ValueError(f"fine-tune architecture mismatch for {key}")
        if key in architecture:
            requested[key] = architecture[key]
    requested["fine_tune"] = "foundation.txt foundation.restart"
    if train_xyz is None or test_xyz is None:
        raise ValueError("fine-tune requires train_xyz and test_xyz when preparing a new task")
    result = prepare_nep_training(output_dir, train_xyz, test_xyz, species=species,
                                  parameters=requested, overwrite=overwrite,
                                  mode="fine_tune")
    root = Path(result["output_dir"])
    _copy(foundation_model, root / "foundation.txt")
    _copy(foundation_restart, root / "foundation.restart")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest["foundation_model"] = str(foundation_model)
    manifest["foundation_restart"] = str(foundation_restart)
    _write_json(root / "manifest.json", manifest)
    result["foundation_model"] = str(root / "foundation.txt")
    result["foundation_restart"] = str(root / "foundation.restart")
    result["training"] = train_nep(root, executable=executable, env=env,
                                    timeout=timeout, overwrite=overwrite)
    return result


def _executable(executable):
    path = Path(executable).expanduser()
    if path.is_file():
        return str(path.resolve())
    resolved = shutil.which(str(executable))
    if resolved is None:
        raise FileNotFoundError(f"NEP executable not found: {executable}")
    resolved_path = Path(resolved)
    return str(resolved_path.resolve()) if resolved_path.is_file() else str(resolved)


def _output_guard(root, overwrite):
    for name in ("nep.in", "manifest.json"):
        path = root / name
        if _is_link_or_reparse(path) or path.is_dir():
            raise FileExistsError(f"Output must be a regular file: {path}")
    for name in ("run.stdout", "run.stderr", "training_report.json", "nep.txt"):
        path = root / name
        if _is_link_or_reparse(path) or path.is_dir():
            raise FileExistsError(f"Output must be a regular file: {path}")
        if path.exists() and not overwrite:
            raise FileExistsError(path)


def train_nep(output_dir, *, executable="nep", env=None, timeout=None,
              overwrite=False):
    """Run the external ``nep`` executable in a prepared task directory."""
    root = Path(output_dir).expanduser()
    if not root.is_dir() or not (root / "nep.in").is_file():
        raise FileNotFoundError(f"Prepared NEP task not found: {root / 'nep.in'}")
    if timeout is not None and (isinstance(timeout, bool) or timeout <= 0):
        raise ValueError("timeout must be positive or None")
    _output_guard(root, overwrite)
    command = _executable(executable)
    merged_env = None if env is None else dict(os.environ, **dict(env))
    explicit_env = {} if env is None else dict(env)
    manifest = {}
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata = {"parameters": manifest.get("parameters", {}),
                "species": manifest.get("species", []),
                "seed": manifest.get("seed"),
                "foundation_model": manifest.get("foundation_model"),
                "foundation_restart": manifest.get("foundation_restart"),
                "environment": explicit_env,
                "manifest_file": str(manifest_path),
                "input_file": str(root / "nep.in")}
    try:
        completed = subprocess.run([command], cwd=str(root), env=merged_env,
                                   capture_output=True, text=True, shell=False,
                                   timeout=timeout, check=False)
    except Exception as exc:
        report = {"status": "failed", "command": [command],
                  "error": f"{type(exc).__name__}: {exc}", **metadata}
        _write_json(root / "training_report.json", report)
        raise
    (root / "run.stdout").write_text(completed.stdout or "", encoding="utf-8")
    (root / "run.stderr").write_text(completed.stderr or "", encoding="utf-8")
    report = {"status": "completed" if completed.returncode == 0 else "failed",
              "command": [command], "returncode": int(completed.returncode),
              "stdout_file": str(root / "run.stdout"),
              "stderr_file": str(root / "run.stderr"),
              "model_file": str(root / "nep.txt") if (root / "nep.txt").is_file() else None,
              **metadata}
    _write_json(root / "training_report.json", report)
    if completed.returncode != 0:
        raise RuntimeError(f"NEP executable failed with return code {completed.returncode}")
    if not (root / "nep.txt").is_file():
        raise RuntimeError("NEP executable completed without producing nep.txt")
    return report

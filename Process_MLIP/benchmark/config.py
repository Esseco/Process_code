"""Strict, file-relative YAML configuration; never imports model libraries."""
from copy import deepcopy
from pathlib import Path
import re

import numpy as np
import yaml


def _keys(value, allowed, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    unknown = value.keys() - set(allowed)
    if unknown:
        raise ValueError(f"Unknown {name} keys: {sorted(unknown)}")


def _identifier(value):
    # Reject Windows reserved paths too, since IDs become output directories.
    if (not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value)
            or value.endswith(".") or value.split(".")[0].upper() in
            {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
             *(f"LPT{i}" for i in range(1, 10))}):
        raise ValueError(f"Invalid file-safe ID: {value!r}")
    return value


def _number(value, name, *, integer=False, minimum=0, inclusive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not np.isfinite(value) or (integer and not isinstance(value, int))
            or (value < minimum if inclusive else value <= minimum)):
        raise ValueError(f"Invalid {name}: {value!r}")


def load_config(path):
    """Read YAML, resolve paths relative to it, validate all benchmark parameters."""
    path = Path(path).resolve()
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    _keys(data, ("output_dir", "models", "structures", "relax", "md", "ehull", "seed"), "root")
    data = deepcopy(data)
    for key in ("output_dir", "models", "structures"):
        if not data.get(key):
            raise ValueError(f"Missing {key}")

    def resolve(value):
        return str((path.parent / Path(value).expanduser()).resolve())

    data["output_dir"] = resolve(data["output_dir"])
    for group in ("models", "structures"):
        if not isinstance(data[group], list) or not data[group]:
            raise ValueError(f"{group} must be a nonempty list")
        ids = []
        for item in data[group]:
            allowed = ("id", "type", "device", "parameters") if group == "models" else ("id", "path", "index")
            _keys(item, allowed, group)
            ids.append(_identifier(item.get("id")))
            if group == "models":
                if not isinstance(item.get("type"), str) or not item["type"]:
                    raise ValueError("Each model requires type")
                item.setdefault("device", "cpu")
                if not re.fullmatch(r"cpu|cuda(?::[0-9]+)?", str(item["device"])):
                    raise ValueError("device must be cpu or cuda[:index]")
                item.setdefault("parameters", {})
                if not isinstance(item["parameters"], dict):
                    raise ValueError("Model parameters must be a mapping")
                if "device" in item["parameters"]:
                    raise ValueError("Set device at model level for correct timing")
                if item["type"] == "mace":
                    item["parameters"].setdefault("default_dtype", "float32")
                    model_name = Path(str(item["parameters"].get("model_path", ""))).name.lower()
                    if (item["device"].startswith("cuda") and "omat" in model_name
                            and not item["parameters"].get("enable_cueq", False)):
                        item["parameters"].setdefault("enable_symmetrix", True)
                        if item["parameters"]["enable_symmetrix"]:
                            item["parameters"].setdefault("symmetrix_use_kokkos", True)
                elif item["type"] == "orb":
                    item["parameters"].setdefault("precision", "float32-highest")
                elif item["type"] == "sevennet" and item["device"].startswith("cuda"):
                    item["parameters"].setdefault("enable_flash", True)
                if item["parameters"].get("model_path") is not None:
                    item["parameters"]["model_path"] = resolve(item["parameters"]["model_path"])
                    model_path = Path(item["parameters"]["model_path"])
                    valid = model_path.is_dir() if item["type"] == "grace" else model_path.is_file()
                    if not valid:
                        raise FileNotFoundError(item["parameters"]["model_path"])
            else:
                if not item.get("path"):
                    raise ValueError("Each structure requires path")
                item["path"] = resolve(item["path"])
                if not Path(item["path"]).is_file():
                    raise FileNotFoundError(item["path"])
                item.setdefault("index", -1)
                if type(item["index"]) is not int:
                    raise ValueError("Structure index must select one integer frame")
        if len(set(x.casefold() for x in ids)) != len(ids):
            raise ValueError(f"Duplicate {group} IDs (case insensitive)")

    defaults = {
        "relax": dict(fmax=0.1, steps=2000, maxstep=0.2),
        "md": dict(temperature_K=800.0, timestep_fs=2.0, steps=1000,
                   tdamp_fs=100.0, trajectory_interval=10, log_interval=10),
        "ehull": dict(reference_csv=None, tolerance_eV_per_atom=1e-6),
    }
    for group, values in defaults.items():
        _keys(data.get(group, {}), values, group)
        data[group] = dict(values, **data.get(group, {}))
    for group in ("relax", "md"):
        for key, value in data[group].items():
            integer = key in ("steps", "trajectory_interval", "log_interval")
            _number(value, f"{group}.{key}", integer=integer)
    data.setdefault("seed", 42)
    _number(data["seed"], "seed", integer=True, inclusive=True)
    _number(data["ehull"]["tolerance_eV_per_atom"], "tolerance_eV_per_atom", inclusive=True)
    if data["ehull"]["reference_csv"] is not None:
        data["ehull"]["reference_csv"] = resolve(data["ehull"]["reference_csv"])
        if not Path(data["ehull"]["reference_csv"]).is_file():
            raise FileNotFoundError(data["ehull"]["reference_csv"])
    return data

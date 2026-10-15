"""Canonical, JSON-safe identities for a frozen reference-site search."""

import hashlib
import json
from pathlib import Path
import math
import re


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def file_digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def freeze_model(model):
    """Fingerprint accessible files; remote files require supplied SHA256 values."""
    if not model or not model.get("version") or not model.get("model_path"):
        raise ValueError("A frozen model version and model_path are required")
    result = dict(model)
    paths = list(dict.fromkeys([model["model_path"], *(model.get("model_paths") or [])]))
    provided = dict(model.get("model_checksums") or {})
    if model.get("sha256"):
        provided.setdefault(model["model_path"], model["sha256"])
    checksums = {}
    for value in paths:
        expected = provided.get(value)
        if expected is not None:
            expected = str(expected).removeprefix("sha256:").lower()
            if not re.fullmatch("[0-9a-f]{64}", expected):
                raise ValueError("Invalid model SHA256: " + str(value))
        path = Path(value)
        if path.is_file():
            actual = file_digest(path)
            if expected and actual != expected:
                raise ValueError("Model checksum differs from approved content: " + str(value))
            expected = actual
        if not expected:
            raise ValueError("Remote model SHA256 required before approval: " + str(value))
        checksums[value] = expected
    result["model_checksums"] = checksums
    result["sha256"] = checksums[model["model_path"]]
    return result


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(path)


def occupation_key(occupation):
    # Strings encode arbitrary TM species, unlike the old Na-only bitmap.
    return digest({"na": occupation["na"], "tm": occupation["tm"]})


def tm_key(occupation):
    return digest(occupation["tm"])


def options(values=None):
    result = {
        "chains_per_H": 3,
        "workers": 3,
        "initial_pool_size": 128,
        "initial_exploration_fraction": 0.1,
        "max_steps": 1000,
        "max_duplicate_trials": 100,
        "max_restarts": 2,
        "temperature": 300.0,
        "patience": 10,
        "energy_tol": 0.001,
        "seed": 0,
        "top_k": 5,
        "na_move_fraction": 0.5,
        "move_kind": "auto",
        "fmax": 0.05,
        "relax_steps": 150,
        "relax_cell": True,
        "min_distance": 2.0,
    }
    unknown = set(values or {}) - set(result)
    if unknown:
        raise ValueError("Unknown search options: " + ",".join(sorted(unknown)))
    result.update(values or {})
    for key in (
        "chains_per_H",
        "workers",
        "initial_pool_size",
        "max_steps",
        "max_duplicate_trials",
        "patience",
        "top_k",
        "relax_steps",
    ):
        if type(result[key]) is not int or result[key] <= 0:
            raise ValueError(key + " must be a positive integer")
    for key in ("max_restarts", "seed"):
        if type(result[key]) is not int or result[key] < 0:
            raise ValueError(key + " must be a nonnegative integer")
    for key in ("temperature", "energy_tol", "fmax", "min_distance"):
        value = result[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(key + " must be finite and nonnegative")
    if result["fmax"] == 0:
        raise ValueError("fmax must be positive")
    for key in ("na_move_fraction", "initial_exploration_fraction"):
        if (
            not isinstance(result[key], (float, int))
            or isinstance(result[key], bool)
            or not 0 <= result[key] <= 1
        ):
            raise ValueError(key + " must be in [0,1]")
    if result["move_kind"] not in {"auto", "tm_only", "na_tm"}:
        raise ValueError("move_kind must be auto/tm_only/na_tm")
    if type(result["relax_cell"]) is not bool:
        raise ValueError("relax_cell must be boolean")
    return result

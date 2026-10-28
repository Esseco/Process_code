"""Atomic reports, immutable input identity and reproducibility metadata."""
from contextlib import contextmanager
from datetime import datetime, timezone
import csv
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import NamedTemporaryFile

def write_json(path, value):
    """Atomically replace one owned JSON report, rejecting NaN/Infinity."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            try:
                from monty.json import MontyEncoder
            except ImportError:
                # Speed reports contain ordinary JSON data; Ehull needs Monty.
                json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
            else:
                json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False, cls=MontyEncoder)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_csv(path, rows):
    """Write union-of-columns CSV, retaining explicit error records."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list))
                             else v for k, v in row.items()})


def file_hash(path):
    """Stream SHA256 without loading large checkpoints into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_hash(path):
    """Hash model files or a SavedModel directory, including relative filenames."""
    path = Path(path)
    if path.is_file():
        return file_hash(path)
    if not path.is_dir() or path.is_symlink():
        raise ValueError(f"Model source must be a regular file or directory: {path}")
    entries = sorted(path.rglob("*"))
    if any(item.is_symlink() for item in entries):
        raise ValueError(f"Model directory must not contain symlinks: {path}")
    files = [item for item in entries if item.is_file()]
    if not files:
        raise ValueError(f"Model directory has no files: {path}")
    digest = hashlib.sha256()
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def identity(config):
    """Bind outputs to input bytes, checkpoints, configuration and core implementation."""
    sources = {item["path"] for item in config["structures"]}
    sources.update(model["parameters"]["model_path"] for model in config["models"]
                   if model["parameters"].get("model_path"))
    reference = config["ehull"]["reference_csv"]
    if reference:
        sources.add(reference)
    root = Path(__file__).parent
    sources.update(str(p) for p in root.glob("*.py"))
    sources.update(str(root.parent / name) for name in
                   ("MLIP_Relax.py", "md.py", "_md_support.py", "calculators.py", "model_config.py", "nep.py"))
    document = dict(config=config, sha256={p: source_hash(p) for p in sorted(sources)})
    document["fingerprint"] = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
    return document


@contextmanager
def output_lock(root):
    """Prevent concurrent writers; stale locks require explicit user inspection/removal."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".benchmark.lock"
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
    except FileExistsError as exc:
        raise RuntimeError(f"Output is locked: {path}; check running processes before removing a stale lock") from exc
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def environment():
    """Record environment and GPU inventory without requiring torch on CPU."""
    packages = {}
    for name in ("ase", "numpy", "scipy", "pymatgen", "matplotlib", "PyYAML", "torch",
                 "mace-torch", "sevenn", "orb-models", "chgnet", "calorine",
                 "tensorpotential", "mattersim", "nequip"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    gpu = None
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total",
                                 "--format=csv,noheader"], capture_output=True, text=True,
                                timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode == 0:
            gpu = result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return dict(utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
                executable=sys.executable, platform=platform.platform(), packages=packages,
                gpu=gpu, cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"))

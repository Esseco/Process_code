"""Restartable AMSET CRT postprocessing; no VASP or scattering jobs submitted."""

import argparse
import gzip
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path

from .atomate_runner import _lock, _save


def _transport(directory, tau):
    files = sorted(directory.glob("transport_*.json*"))
    if len(files) != 1:
        raise ValueError(f"Expected one AMSET transport JSON in {directory}, found {len(files)}")
    opener = gzip.open if files[0].suffix == ".gz" else open
    with opener(files[0], "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    doping, temperatures = data["doping"], data["temperatures"]
    sigma = data["conductivity"]
    if len(sigma) != len(doping) or any(len(row) != len(temperatures) for row in sigma):
        raise ValueError("Invalid AMSET conductivity dimensions")
    ratio = []
    for row in sigma:
        tensors = []
        for tensor in row:
            if len(tensor) != 3 or any(len(axis) != 3 for axis in tensor):
                raise ValueError("Expected 3x3 conductivity tensors")
            if any(not math.isfinite(float(v)) for axis in tensor for v in axis):
                raise ValueError("Nonfinite AMSET conductivity")
            tensors.append([[float(v) / tau for v in axis] for axis in tensor])
        ratio.append(tensors)
    return {
        "doping_cm3": doping, "temperatures_K": temperatures,
        "carrier_type": ["electron" if d < 0 else "hole" for d in doping],
        "relaxation_time_s": tau, "conductivity_S_m": sigma,
        "sigma_over_tau_S_m_s": ratio,
        "tensor_axes": ["doping", "temperature", "cartesian_i", "cartesian_j"],
        "transport_file": str(files[0]),
    }


def run_amset_crt(source_dir, output_dir, *, doping=(-1e18, 1e18),
                  temperatures=(300,), relaxation_time=1e-14,
                  interpolation_factor=10, nworkers=1, resume=True):
    """Calculate sigma/tau from an existing uniform-grid vasprun.xml[.gz].

    Doping is cm^-3 (negative electrons, positive holes), temperatures K,
    relaxation_time seconds. Returned tensors have shape (ndoping, nT, 3, 3)
    and sigma/tau units S m^-1 s^-1. Requires an environment with AMSET CLI.
    Writes isolated attempt directories, logs, settings and a JSON checkpoint;
    copies the source XML, never runs VASP. Identical successful requests are
    reused; failures/changed requests create another attempt. No random seed.
    Resume is at completed-calculation level, not inside AMSET interpolation.
    """
    source, root = Path(source_dir).resolve(), Path(output_dir).resolve()
    xml = next((source / name for name in ("vasprun.xml", "vasprun.xml.gz")
                if (source / name).is_file()), None)
    if xml is None:
        raise FileNotFoundError(f"No vasprun.xml[.gz] in {source}; supply the actual DOS output directory")
    if source == root or source in root.parents or root in source.parents:
        raise ValueError("Use separate source and output directories, neither nested in the other")
    doping = [float(x) for x in doping]
    temperatures = [float(x) for x in temperatures]
    if not doping or any(not math.isfinite(x) or x == 0 for x in doping):
        raise ValueError("doping must contain finite nonzero concentrations")
    if not temperatures or any(not math.isfinite(x) or x <= 0 for x in temperatures):
        raise ValueError("temperatures must be positive and finite")
    tau = float(relaxation_time)
    if not math.isfinite(tau) or tau <= 0:
        raise ValueError("relaxation_time must be positive seconds")
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 1
           for x in (interpolation_factor, nworkers)):
        raise ValueError("interpolation_factor and nworkers must be positive integers")
    settings = dict(scattering_type=["CRT"], constant_relaxation_time=tau,
                    doping=doping, temperatures=temperatures,
                    interpolation_factor=interpolation_factor, nworkers=nworkers,
                    file_format="json", write_mesh=False, unity_overlap=True)
    digest = hashlib.sha256()
    with xml.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    fingerprint = hashlib.sha256((digest.hexdigest() + json.dumps(settings, sort_keys=True)).encode()).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    with _lock(root):
        checkpoint = root / "amset_crt_state.json"
        state = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
        if resume and state.get("fingerprint") == fingerprint and state.get("status") == "completed":
            result = _transport(root / state["attempt"], tau)
            _save(root / "amset_crt_result.json", result)
            return result
        executable = shutil.which("amset")
        if executable is None:
            raise RuntimeError("AMSET CLI not found. Activate an environment containing amset before calling this function.")
        index = 1
        while (root / f"attempt_{index:03d}").exists():
            index += 1
        attempt = root / f"attempt_{index:03d}"
        attempt.mkdir()
        state = dict(status="running", fingerprint=fingerprint, attempt=attempt.name,
                     source=str(xml), settings=settings)
        _save(checkpoint, state)
        try:
            if xml.suffix == ".gz":
                with gzip.open(xml, "rb") as src, (attempt / "vasprun.xml").open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            else:
                shutil.copy2(xml, attempt / "vasprun.xml")
            # JSON is valid YAML; avoid an extra dependency just for settings.
            _save(attempt / "settings.yaml", settings)
            with (attempt / "amset.log").open("w", encoding="utf-8") as log:
                subprocess.run([executable, "run"], cwd=attempt, stdout=log,
                               stderr=subprocess.STDOUT, check=True)
            result = _transport(attempt, tau)
            _save(root / "amset_crt_result.json", result)
            state["status"] = "completed"
            _save(checkpoint, state)
            return result
        except Exception as error:
            state.update(status="failed", error=f"{type(error).__name__}: {error}")
            _save(checkpoint, state)
            raise


def main():
    """CLI with the same default electron/hole CRT settings as the Python API."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--doping", nargs="+", type=float, default=[-1e18, 1e18])
    parser.add_argument("--temperatures", nargs="+", type=float, default=[300])
    parser.add_argument("--nworkers", type=int, default=1)
    args = parser.parse_args()
    run_amset_crt(**vars(args))


if __name__ == "__main__":
    main()

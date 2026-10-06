"""Checkpointed atomate2 runner used by generated task scripts."""

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path


def _save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def _tail(path, limit=12000):
    if not path.is_file():
        return ""
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        handle.seek(max(0, handle.tell() - limit))
        return handle.read().decode("utf-8", errors="replace")


def _failure_reason(error, directory):
    stderr = _tail(directory / "std_err.txt") if directory else ""
    output = _tail(directory / "vasp.out") if directory else ""
    combined = "\n".join((str(error), stderr, output)).lower()
    causes = (
        (("disk quota exceeded", "quota exceeded"), "Disk quota exceeded while VASP was writing output"),
        (("no space left on device",), "Filesystem has no free space"),
        (("out of memory", "oom-kill", "oom_kill"), "Job ran out of memory"),
        (("time limit", "timelimit"), "Scheduler time limit reached"),
        (("eddrmm", "zhegv failed"), "VASP electronic diagonalization failed (EDDRMM/ZHEGV)"),
        (("vasprunxmlvalidator", "xmlsyntaxerror"), "VASP XML output is incomplete or invalid"),
    )
    for patterns, reason in causes:
        if any(pattern in combined for pattern in patterns):
            return reason, stderr.strip()[-3000:]
    return f"{type(error).__name__}: {error}", stderr.strip()[-3000:]


def _failure_action(reason):
    if reason.startswith("Disk quota exceeded"):
        return "Check quota -s and task-directory usage; free or increase account quota before resubmitting."
    if reason.startswith("Filesystem has no free space"):
        return "Check df -h and task-directory usage; restore free space before resubmitting."
    if reason.startswith("Job ran out of memory"):
        return "Inspect scheduler memory usage and increase #SBATCH --mem if needed."
    if reason.startswith("Scheduler time limit"):
        return "Increase the Slurm time limit, then resubmit the same task directory."
    if reason.startswith("VASP electronic diagonalization"):
        return "Inspect OUTCAR; consider ALGO=Normal for the failed stage, then resubmit."
    if reason.startswith("VASP XML output"):
        return "Inspect std_err.txt and vasp.out for the underlying failure before resubmitting."
    return "Inspect this stage's std_err.txt, vasp.out, and Slurm err before resubmitting."


def _record_failure(root, stage, directory, error):
    reason, evidence = _failure_reason(error, directory)
    action = _failure_action(reason)
    report = {
        "status": "failed", "time_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage, "directory": str(directory) if directory else None,
        "reason": reason, "recommended_action": action,
        "exception": f"{type(error).__name__}: {error}",
        "stderr_tail": evidence,
    }
    message = f"Workflow stopped at {stage or 'setup'}: {reason}"
    message += f"\nNext step: {action}"
    if directory:
        message += f"\nCalculation directory: {directory}"
    if evidence:
        message += f"\nVASP stderr (tail):\n{evidence}"
    print(message, file=sys.stderr, flush=True)
    try:
        _save(root / "workflow_status.json", report)
        (root / "failure_report.txt").write_text(message + "\n", encoding="utf-8")
    except OSError as write_error:
        print(f"Could not save failure report: {write_error}", file=sys.stderr, flush=True)


def _restart_relax_structure(entry, fingerprint, root, initial_structure):
    """Use a failed matching attempt's last complete geometry when possible."""
    if entry.get("fingerprint") != fingerprint:
        return initial_structure, None
    directory = root / entry.get("directory", "__missing__")
    contcar = directory / "CONTCAR"
    if not contcar.is_file() or contcar.stat().st_size == 0:
        return initial_structure, None
    from pymatgen.core import Structure
    try:
        structure = Structure.from_file(contcar)
    except (OSError, ValueError, IndexError):
        return initial_structure, None
    if (len(structure) != len(initial_structure) or
            [site.species for site in structure] != [site.species for site in initial_structure]):
        return initial_structure, None
    return structure, contcar


def _same_structure(left, right):
    """Compare ordered sites; a legacy stage must start from our predecessor."""
    import numpy as np

    return (len(left) == len(right)
            and [site.species for site in left] == [site.species for site in right]
            and np.allclose(left.lattice.matrix, right.lattice.matrix, atol=1e-4, rtol=0)
            and np.allclose(left.frac_coords, right.frac_coords, atol=1e-4, rtol=0))


def _same_setting(actual, expected):
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)
    return str(actual).lower() == str(expected).lower()


def _legacy_candidate(root, stage, predecessor, config):
    """Find a validated result from the old jobflow runs/job_* layout."""
    from monty.os.path import zpath
    from pymatgen.core import Structure
    from pymatgen.io.vasp.inputs import Incar, Kpoints

    if config.get("kpoints_settings", {}).get(stage):
        return None
    candidates = []
    for directory in (root / "runs").glob("job_*"):
        if not directory.is_dir():
            continue
        try:
            incar = Incar.from_file(zpath(directory / "INCAR"))
            nsw = int(incar.get("NSW", 0))
            icharg = int(incar.get("ICHARG", 2))
            if stage == "relax" and nsw <= 0:
                continue
            if stage == "static" and (nsw != 0 or icharg >= 10):
                continue
            if stage in ("dos", "band") and (nsw != 0 or icharg < 10):
                continue
            if stage in ("dos", "band"):
                kpoints = Kpoints.from_file(zpath(directory / "KPOINTS"))
                line_mode = kpoints.style.name.lower() == "line_mode"
                if line_mode != (stage == "band"):
                    continue
            overrides = config.get("incar_settings", {}).get(stage, {})
            if any(value is not None and not _same_setting(incar.get(key), value)
                   for key, value in overrides.items()):
                continue
            input_structure = Structure.from_file(zpath(directory / "POSCAR"))
            if not _same_structure(input_structure, predecessor):
                continue
            final_structure = _validate(directory, stage)
            if stage != "relax" and not _same_structure(final_structure, predecessor):
                continue
            xml = Path(zpath(directory / "vasprun.xml"))
            candidates.append((xml.stat().st_mtime_ns, directory, final_structure))
        except Exception:
            continue
    if not candidates:
        return None
    _, directory, final_structure = max(candidates, key=lambda item: item[0])
    return directory, final_structure


@contextmanager
def _lock(root):
    # OS releases this lock even if Slurm kills the process.
    with (root / ".workflow.lock").open("a+b") as handle:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            if handle.read(1) == b"":
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise RuntimeError("Another workflow is using this task directory") from error
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise RuntimeError("Another workflow is using this task directory") from error
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _validate(directory, stage):
    from monty.os.path import zpath
    from pymatgen.io.vasp.outputs import Vasprun

    xml = Path(zpath(directory / "vasprun.xml"))
    run = Vasprun(xml, parse_dos=False, parse_eigen=False,
                  parse_projected_eigen=False, parse_potcar_file=False,
                  exception_on_bad_xml=True)
    if not run.converged_electronic or (stage == "relax" and not run.converged_ionic):
        raise ValueError(f"{stage} is not converged: {directory}")
    if stage == "relax" and int(run.parameters.get("NSW", 0)) <= 0:
        raise ValueError("Imported relax output is not an ionic relaxation")
    if stage != "relax" and int(run.parameters.get("NSW", 0)) != 0:
        raise ValueError(f"{stage} output must have NSW=0")
    for filename in ("CONTCAR", "OUTCAR"):
        path = Path(zpath(directory / filename))
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing or empty output: {path}")
    if stage == "static":
        for filename in ("CHGCAR", "WAVECAR"):
            path = Path(zpath(directory / filename))
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"Static output needs {filename} for subsequent calculations")
    return run.final_structure


def _job(stage, structure, previous, config):
    from atomate2.vasp.jobs.core import RelaxMaker, StaticMaker, NonSCFMaker
    from atomate2.vasp.sets.core import RelaxSetGenerator, StaticSetGenerator, NonSCFSetGenerator

    maker, generator = {
        "relax": (RelaxMaker, RelaxSetGenerator),
        "static": (StaticMaker, StaticSetGenerator),
        "dos": (NonSCFMaker, NonSCFSetGenerator),
        "band": (NonSCFMaker, NonSCFSetGenerator),
    }[stage]
    instance = maker(name=stage, input_set_generator=generator(
        user_incar_settings=config.get("incar_settings", {}).get(stage, {}),
        user_kpoints_settings=config.get("kpoints_settings", {}).get(stage, {}),
    ), stop_children_kwargs={"handle_unsuccessful": "error"})
    kwargs = {"prev_dir": str(previous)} if previous else {}
    if stage in ("dos", "band"):
        kwargs["mode"] = "uniform" if stage == "dos" else "line"
    return instance.make(structure, **kwargs)


def _dependency(fingerprint, directory):
    from monty.os.path import zpath
    xml = Path(zpath(directory / "vasprun.xml"))
    stat = xml.stat()
    return f"{fingerprint}:{directory}:{stat.st_size}:{stat.st_mtime_ns}"


def _export_completed(root, stage, directory, config, state, state_path):
    """Export plotting data without changing the completed VASP stage state."""
    if not config.get("export_plot_data", False) or stage not in ("dos", "band"):
        return
    from .plot_exports import export_plot_data

    try:
        files = export_plot_data(stage, directory, root)
    except Exception as error:
        state.setdefault("exports", {})[stage] = {"status": "failed", "error": str(error)}
        _save(state_path, state)
        _record_failure(root, f"{stage} export", directory, error)
        raise
    state.setdefault("exports", {})[stage] = {
        "status": "completed", "source": str(directory), "files": files,
    }
    _save(state_path, state)
    print(f"Exported {stage} plotting data: {', '.join(files)}", flush=True)


def run_workflow(root, *, fresh=False):
    """Resume valid stages, retry interrupted stages, invalidate changed dependencies."""
    from pymatgen.core import Structure
    from jobflow import run_locally

    root = Path(root).resolve()
    with _lock(root):
        config = json.loads((root / "workflow.json").read_text(encoding="utf-8"))
        calculation = config["calculation"]
        stages = {"relax": ["relax"], "static": ["static"],
                  "dos": ["relax", "static", "dos"],
                  "band": ["relax", "static", "band"]}[calculation]
        initial = root / config["structure_file"]
        structure = Structure.from_file(initial)
        state_path = root / "workflow_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"version": 1, "stages": {}}
        if state.get("version") != 1:
            raise ValueError("Unsupported checkpoint version")
        previous = None
        dependency = hashlib.sha256(initial.read_bytes()).hexdigest()
        for stage in stages:
            fingerprint = hashlib.sha256(json.dumps({
                "runner_version": 1, "dependency": dependency, "stage": stage,
                "incar": config.get("incar_settings", {}).get(stage, {}),
                "kpoints": config.get("kpoints_settings", {}).get(stage, {}),
            }, sort_keys=True).encode()).hexdigest()
            entry = state["stages"].get(stage, {})
            directory = root / entry.get("directory", "__missing__")
            reuse = not fresh and entry.get("fingerprint") == fingerprint
            if reuse and directory.is_dir():
                try:
                    final_structure = _validate(directory, stage)
                except Exception as error:
                    print(f"Retry {stage}: existing result is invalid ({error})", flush=True)
                else:
                    # A complete output may survive a kill before checkpoint saving.
                    entry["status"] = "completed"
                    _save(state_path, state)
                    print(f"Skip completed {stage}: {directory}", flush=True)
                    structure, previous = final_structure, directory
                    dependency = _dependency(fingerprint, directory)
                    if stage == calculation:
                        _export_completed(root, stage, directory, config, state, state_path)
                    continue
            imported = config.get("resume_from", {}).get(stage)
            if imported and not entry and not fresh:
                directory = Path(imported)
                if not directory.is_absolute():
                    directory = root / directory
                directory = directory.resolve()
                final_structure = _validate(directory, stage)
                if stage != "relax" and final_structure != structure:
                    raise ValueError(f"Imported {stage} structure does not match its predecessor")
                state["stages"][stage] = {"status": "completed", "directory": str(directory),
                                           "fingerprint": fingerprint, "imported": True}
                _save(state_path, state)
                print(f"Imported {stage}: {directory}", flush=True)
                structure, previous = final_structure, directory
                dependency = _dependency(fingerprint, directory)
                if stage == calculation:
                    _export_completed(root, stage, directory, config, state, state_path)
                continue
            if not imported and not entry and not fresh:
                legacy = _legacy_candidate(root, stage, structure, config)
                if legacy:
                    directory, final_structure = legacy
                    state["stages"][stage] = {
                        "status": "completed", "directory": str(directory),
                        "fingerprint": fingerprint, "imported": True, "legacy": True,
                    }
                    _save(state_path, state)
                    print(f"Reuse completed legacy {stage}: {directory}", flush=True)
                    structure, previous = final_structure, directory
                    dependency = _dependency(fingerprint, directory)
                    if stage == calculation:
                        _export_completed(root, stage, directory, config, state, state_path)
                    continue
            restart_source = None
            if stage == "relax" and not fresh and reuse:
                structure, restart_source = _restart_relax_structure(
                    entry, fingerprint, root, structure
                )
                if restart_source:
                    print(f"Restart relax from last valid geometry: {restart_source}", flush=True)
            stage_root = root / "runs" / stage
            stage_root.mkdir(parents=True, exist_ok=True)
            attempt = 1
            while True:
                directory = stage_root / f"attempt_{attempt:03d}"
                try:
                    directory.mkdir()
                    break
                except FileExistsError:
                    attempt += 1
            entry = {"status": "running", "directory": str(directory.relative_to(root)),
                     "fingerprint": fingerprint, "attempt": attempt}
            if restart_source:
                entry["restart_structure"] = str(restart_source)
            state["stages"][stage] = entry
            _save(state_path, state)
            try:
                stage_job = _job(stage, structure, previous, config)
                responses = run_locally(stage_job, create_folders=False, root_dir=directory,
                                        ensure_success=True, raise_immediately=True)
                response = responses[stage_job.uuid][stage_job.index]
                if response.stop_children or response.stop_jobflow:
                    raise RuntimeError(f"{stage} requested workflow stop")
                final_structure = _validate(directory, stage)
                if stage != "relax" and final_structure != structure:
                    raise ValueError(f"{stage} unexpectedly changed the structure")
            except BaseException as error:
                reason, _ = _failure_reason(error, directory)
                entry.update(status="failed", error=str(error), reason=reason)
                try:
                    _save(state_path, state)
                except OSError as write_error:
                    print(f"Could not save checkpoint: {write_error}", file=sys.stderr, flush=True)
                _record_failure(root, stage, directory, error)
                raise
            entry["status"] = "completed"
            _save(state_path, state)
            structure, previous = final_structure, directory
            dependency = _dependency(fingerprint, directory)
            if stage == calculation:
                _export_completed(root, stage, directory, config, state, state_path)
        print("All requested stages completed", flush=True)
        try:
            _save(root / "workflow_status.json", {
                "status": "completed", "time_utc": datetime.now(timezone.utc).isoformat(),
                "calculation": calculation,
            })
        except OSError as write_error:
            print(f"Could not save completion status: {write_error}", file=sys.stderr, flush=True)
        return state


def main(root):
    parser = argparse.ArgumentParser(description="Resume the generated VASP workflow")
    parser.add_argument("--fresh", action="store_true", help="Recalculate all stages in new attempt directories")
    args = parser.parse_args()
    status = Path(root) / "workflow_status.json"
    previous_mtime = status.stat().st_mtime_ns if status.is_file() else None
    try:
        run_workflow(root, fresh=args.fresh)
    except BaseException as error:
        if not status.is_file() or status.stat().st_mtime_ns == previous_mtime:
            _record_failure(Path(root), None, None, error)
        raise

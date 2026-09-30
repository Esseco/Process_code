"""Portable, checkpointed atomate2 runner copied into generated task folders."""

import argparse
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path


def _save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


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
        path = Path(zpath(directory / "CHGCAR"))
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("Static output needs CHGCAR for subsequent calculations")
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
                continue
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
                entry.update(status="failed", error=str(error))
                _save(state_path, state)
                raise
            entry["status"] = "completed"
            _save(state_path, state)
            structure, previous = final_structure, directory
            dependency = _dependency(fingerprint, directory)
        print("All requested stages completed", flush=True)
        return state


def main(root):
    parser = argparse.ArgumentParser(description="Resume the generated VASP workflow")
    parser.add_argument("--fresh", action="store_true", help="Recalculate all stages in new attempt directories")
    args = parser.parse_args()
    run_workflow(root, fresh=args.fresh)

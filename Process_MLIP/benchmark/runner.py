"""Batch execution, error isolation and stage-granularity restart."""
from collections import Counter
from contextlib import contextmanager
import gc
import json
import logging
from pathlib import Path
import sys

from ase.io import read
import numpy as np

from .config import load_config
from .operations import Measurement, molecular_dynamics, relax, warmup
from .registry import create_calculator
from .storage import environment, file_hash, identity, output_lock, write_csv, write_json


def _completed(path):
    if not path.exists():
        return None
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("status") != "completed":
        return None
    if result.get("final_structure"):
        final = Path(result["final_structure"])
        if not final.is_file() or file_hash(final) != result.get("final_structure_sha256"):
            return None
    return result


@contextmanager
def _log_to(path):
    logger = logging.getLogger("Process_MLIP.benchmark")
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    old = logger.level
    logger.setLevel(logging.INFO)
    try:
        yield logger
    finally:
        logger.removeHandler(handler)
        handler.close()
        logger.setLevel(old)


def _read_structures(config):
    structures = {}
    for item in config["structures"]:
        atoms = read(item["path"], index=item["index"])
        if (not len(atoms) or not np.all(atoms.pbc) or atoms.cell.volume <= 0
                or not np.all(np.isfinite(atoms.positions)) or not np.all(np.isfinite(atoms.cell))):
            raise ValueError(f"{item['id']}: requires finite, nonempty, fully periodic 3D structure")
        if atoms.constraints:
            raise ValueError(f"{item['id']}: constraints conflict with full relaxation and fair MD")
        structures[item["id"]] = atoms
    return structures


def _with_structure_species(model, structures):
    """Limit Symmetrix MACE conversion to the elements actually requested."""
    from ..calculators import _symmetrix_species_from_atoms
    params = model["parameters"]
    path = params.get("model_path")
    if model["type"] != "mace":
        return model
    species = _symmetrix_species_from_atoms(path, params.get("enable_symmetrix"),
                                            params.get("symmetrix_species"), structures.values())
    if species is params.get("symmetrix_species"):
        return model
    return dict(model, parameters=dict(params, symmetrix_species=species))


def _model_stages(config, model, structures, root, mode, logger):
    model = _with_structure_species(model, structures)
    stages = ("relax", "md") if mode == "speed" else ("relax",)
    model_root = root / mode / model["id"]
    model_root.mkdir(parents=True, exist_ok=True)
    completed = {(sid, stage): _completed(model_root / sid / stage / "result.json")
                 for sid in structures for stage in stages}
    if all(completed.values()):
        logger.info("Resume %s/%s: all stages completed", mode, model["id"])
        return list(completed.values())
    calculator = None
    load_error = None
    runtime = environment()
    try:
        external_gpu = model["type"] == "nep" and model["parameters"].get("backend", "cpu") == "gpu"
        backend = "tensorflow" if model["type"] == "grace" else "torch"
        with Measurement(model["device"], external_gpu, backend) as meter:
            calculator = create_calculator(model)
        write_json(model_root / "load.json", dict(status="completed", model=model,
                   measurement=meter.result, environment=runtime))
    except Exception as exc:
        load_error = f"{type(exc).__name__}: {exc}"
        logger.exception("Model load failed: %s", model["id"])
        write_json(model_root / "load.json", dict(status="failed", model=model, error=load_error,
                                                 environment=runtime))
    output = []
    try:
        for sid, atoms in structures.items():
            pending = [stage for stage in stages if completed[sid, stage] is None]
            error = load_error
            if pending and error is None:
                try:
                    result = warmup(atoms, calculator, model["device"])
                    write_json(model_root / sid / "warmup.json", dict(status="completed", model_id=model["id"],
                               structure_id=sid, natoms=len(atoms), environment=runtime, **result))
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    logger.exception("Warmup failed: %s/%s", model["id"], sid)
                    write_json(model_root / sid / "warmup.json", dict(status="failed", error=error,
                               model_id=model["id"], structure_id=sid, natoms=len(atoms)))
            for stage in stages:
                if completed[sid, stage] is not None:
                    output.append(completed[sid, stage])
                    continue
                directory = model_root / sid / stage
                directory.mkdir(parents=True, exist_ok=True)
                row = dict(model_id=model["id"], structure_id=sid, stage=stage,
                           natoms=len(atoms), status="failed", model_type=model["type"], device=model["device"],
                           model_config=model, environment=runtime)
                if error is not None:
                    row["error"] = error
                else:
                    try:
                        logger.info("Run %s/%s/%s/%s", mode, model["id"], sid, stage)
                        if stage == "relax":
                            result = relax(atoms, calculator, directory, config["relax"], model["device"])
                        else:
                            result = molecular_dynamics(atoms, calculator, directory, config["md"],
                                                        model["device"], config["seed"])
                        row.update(result, status="completed")
                        row["final_structure_sha256"] = file_hash(row["final_structure"])
                    except Exception as exc:
                        logger.exception("Stage failed: %s/%s/%s", model["id"], sid, stage)
                        row.update(getattr(exc, "benchmark_measurement", {}))
                        row["error"] = f"{type(exc).__name__}: {exc}"
                        if stage == "md" and (directory / "report.json").is_file():
                            failure = json.loads((directory / "report.json").read_text(encoding="utf-8"))
                            row["steps_completed"] = failure.get("steps_completed", 0)
                            # Existing MD does not expose pure-run timing on failure: never mislabel outer wall time.
                            row["elapsed_seconds"] = None
                write_json(directory / "result.json", row)
                output.append(row)
    finally:
        del calculator
        gc.collect()
        torch = sys.modules.get("torch")
        if model["device"].startswith("cuda") and torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
    return output


def _hull_outputs(config, model_id, rows, root, reference):
    from .ehull import compare_reference, compute_hull
    directory = root / "ehull" / model_id
    # Retire stale success before retry; never leave a prior hull beside current failure.
    owned = ("ehull.csv", "ehull.json", "metrics.json", "phase_diagram.json", "phase_diagram.png", "ehull_by_id.png")
    for name in owned:
        (directory / name).unlink(missing_ok=True)
    try:
        tolerance = config["ehull"]["tolerance_eV_per_atom"]
        diagram, hull_rows = compute_hull(rows, tolerance)
        hull_rows, metrics = compare_reference(hull_rows, reference, tolerance)
        write_json(directory / "phase_diagram.json", diagram.as_dict())
        write_json(directory / "ehull.json", hull_rows)
        write_csv(directory / "ehull.csv", hull_rows)
        if metrics is not None:
            write_json(directory / "metrics.json", metrics)
        from .plotting import phase_plot
        plots = phase_plot(diagram, directory, hull_rows)
        report = dict(status="completed", model_id=model_id, metrics=metrics, **plots)
    except Exception as exc:
        report = dict(status="failed", model_id=model_id, error=f"{type(exc).__name__}: {exc}")
    write_json(directory / "hull_status.json", report)
    return report


def run_benchmark(config_path, mode, model_ids=None):
    """Run speed or ehull; resume completed stages, retry failed stages, reject input drift."""
    if mode not in ("speed", "ehull"):
        raise ValueError("mode must be speed or ehull")
    config = load_config(config_path)
    if model_ids is not None and (not model_ids or set(model_ids) - {m["id"] for m in config["models"]}):
        raise ValueError("--model must select configured model IDs")
    structures = _read_structures(config)
    reference = None
    if mode == "ehull":
        from .ehull import read_reference, validate_endmembers
        validate_endmembers([Counter(a.get_chemical_symbols()) for a in structures.values()])
        reference = read_reference(config["ehull"]["reference_csv"])
        if reference is not None and not structures.keys() & reference.keys():
            raise ValueError("No matching structure IDs in DFT reference")
    root = Path(config["output_dir"])
    document = identity(config)
    with output_lock(root):
        manifest = root / "manifest.json"
        if manifest.exists():
            previous = json.loads(manifest.read_text(encoding="utf-8"))
            if previous["fingerprint"] != document["fingerprint"]:
                raise ValueError("Configuration/input/checkpoint/code changed; use a new output_dir")
        elif any(p.name != ".benchmark.lock" for p in root.iterdir()):
            raise ValueError("Nonempty output_dir has no benchmark manifest; use a new directory")
        else:
            write_json(manifest, document)
        with _log_to(root / "benchmark.log") as logger:
            for model in config["models"]:
                if model_ids is not None and model["id"] not in model_ids:
                    continue
                _model_stages(config, model, structures, root, mode, logger)
            # Aggregate saved stages for every configured model, including other environments' runs.
            rows = []
            for model in config["models"]:
                for sid in structures:
                    for stage in (("relax", "md") if mode == "speed" else ("relax",)):
                        path = root / mode / model["id"] / sid / stage / "result.json"
                        if path.exists():
                            rows.append(json.loads(path.read_text(encoding="utf-8")))
            summaries = []
            if mode == "speed":
                from .plotting import speed_plots
                for stage in ("relax", "md"):
                    stage_rows = [r for r in rows if r["stage"] == stage]
                    write_csv(root / "speed" / f"{stage}.csv", stage_rows)
                    write_json(root / "speed" / f"{stage}.json", stage_rows)
                    speed_plots(stage_rows, root / "speed", stage)
                loading, warming = [], []
                for model in config["models"]:
                    load_path = root / mode / model["id"] / "load.json"
                    if load_path.exists():
                        record = json.loads(load_path.read_text(encoding="utf-8"))
                        loading.append(dict(model_id=model["id"], status=record["status"],
                                            error=record.get("error"), **record.get("measurement", {})))
                    for sid in structures:
                        warm_path = root / mode / model["id"] / sid / "warmup.json"
                        if warm_path.exists():
                            warming.append(json.loads(warm_path.read_text(encoding="utf-8")))
                write_csv(root / mode / "load.csv", loading)
                write_csv(root / mode / "warmup.csv", warming)
            else:
                for model in config["models"]:
                    model_rows = [r for r in rows if r["model_id"] == model["id"]]
                    if not model_rows:
                        continue
                    if len(model_rows) != len(structures):
                        raise ValueError(f"Incomplete saved structure results for {model['id']}")
                    summaries.append(_hull_outputs(config, model["id"], model_rows, root, reference))
                write_json(root / "ehull" / "comparison.json", summaries)
                write_csv(root / "ehull" / "comparison.csv", [dict(model_id=r["model_id"], status=r["status"],
                          error=r.get("error"), **(r.get("metrics") or {})) for r in summaries])
            failed = sum(r["status"] != "completed" for r in rows)
            if mode == "ehull":
                failed += sum(r["status"] != "completed" for r in summaries)
            expected = len(config["models"]) * len(structures) * (2 if mode == "speed" else 1)
            missing = expected - len(rows)
            summary = dict(mode=mode, output_dir=str(root), failed=failed,
                           status="failed" if failed else ("partial" if missing else "completed"),
                           stages_expected=expected, stages_missing=missing,
                           stages_recorded=len(rows), hulls=summaries)
            write_json(root / mode / "summary.json", summary)
            return summary

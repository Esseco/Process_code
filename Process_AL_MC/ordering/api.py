"""Public plan/prepare/run interfaces, independent of the Agent application."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import threading

from .common import digest, write_json, file_digest, freeze_model
from .planning import make_plan
from .history import OccupationStore


def plan_ordering_search(
    reference,
    *,
    phase,
    tm_ratios,
    na_content,
    max_det_H=None,
    h_matrices=None,
    oxidation_states=None,
    model=None,
    options=None,
):
    """Plan fixed-composition H searches and cheap Ewald seeds without MLIP calls.

    ``na_content`` is Na per O2, ``tm_ratios`` are relative counts, H is exact,
    Ewald energies are in eV and MC/ranking energies are eV/atom. A full-Na
    reference fixes site numbering. Exactly one H scope selector is required.
    """
    return make_plan(
        reference,
        phase=phase,
        tm_ratios=tm_ratios,
        na_content=na_content,
        max_det_H=max_det_H,
        h_matrices=h_matrices,
        oxidation_states=oxidation_states,
        model=model,
        search_options=options,
    )


def prepare_ordering_search(plan, output_dir):
    """Save immutable inputs and a portable runner; no model load or submission."""
    if digest({k: v for k, v in plan.items() if k != "plan_id"}) != plan.get("plan_id"):
        raise ValueError("Invalid/modified plan identity")
    freeze_model(plan["model"])
    root = Path(output_dir).resolve()
    manifest = root / "plan.json"
    if root.exists():
        if not manifest.is_file() or json.loads(manifest.read_text(encoding="utf-8")) != plan:
            raise ValueError("Output belongs to a different plan; use a new directory")
        return {
            "status": "reused",
            "directory": str(root),
            "plan_id": plan["plan_id"],
            "submitted": False,
            "workload": plan["workload"],
        }
    root.mkdir(parents=True)
    write_json(manifest, plan)
    (root / "run_search.py").write_text(
        """from pathlib import Path
import sys
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root / "runtime"))
from Process_AL_MC import run_ordering_search
if __name__ == "__main__":
    result = run_ordering_search(root)
    print(result["status"])
    print(result["global_ranking_csv"])
""",
        encoding="utf-8",
    )
    write_json(root / "workload.json", plan["workload"])
    return {
        "status": "prepared",
        "directory": str(root),
        "plan_id": plan["plan_id"],
        "submitted": False,
        "workload": plan["workload"],
    }


def _stores(plan, root, model_binding):
    return {
        m["matrix_id"]: OccupationStore(
            Path(root) / "matrices" / m["matrix_id"] / "history.sqlite",
            {
                "plan_id": plan["plan_id"],
                "matrix_id": m["matrix_id"],
                "model_binding": model_binding,
            },
        )
        for m in plan["matrices"]
    }


def run_ordering_search(directory, *, evaluator=None, evaluator_factory=None):
    """Run bounded concurrent chains, reusing completed observations on rerun.

    Passing an evaluator enables fake-backend validation. Without one, the
    configured main model loads here in its dedicated environment. Interrupted
    running claims require explicit reconciliation; no timer silently retries.
    History resumes are supported; exact stochastic chain continuation is not
    claimed. The output directory has one coordinator and parallel chain workers.
    """
    from filelock import FileLock
    from .search import run_chain
    from .export import export_results

    root = Path(directory).resolve()
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    if digest({k: v for k, v in plan.items() if k != "plan_id"}) != plan["plan_id"]:
        raise ValueError("Modified prepared plan")
    model_binding = "injected-evaluator"
    if evaluator is None and evaluator_factory is None:
        paths = [plan["model"]["model_path"], *(plan["model"].get("model_paths") or [])]
        checksums = {}
        for value in dict.fromkeys(paths):
            path = Path(value)
            if not path.is_file():
                raise FileNotFoundError("Model missing: " + str(path))
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            checksums[value] = hasher.hexdigest()
        model_binding = digest(checksums)
        if checksums != plan["model"].get("model_checksums"):
            raise ValueError("Model content differs from approved checksum")
        from .evaluation import MACEOrderingEvaluator

        def evaluator_factory():
            return MACEOrderingEvaluator(plan["model"], plan["options"])

    with FileLock(str(root / "coordinator.lock"), timeout=0):
        binding = root / "execution_binding.json"
        expected = {"plan_id": plan["plan_id"], "model_binding": model_binding}
        if binding.exists() and json.loads(binding.read_text(encoding="utf-8")) != expected:
            raise ValueError("Different executed model/configuration")
        write_json(binding, expected)
        stores = _stores(plan, root, model_binding)
        running = [
            (key, row["key"])
            for key, store in stores.items()
            for row in store.records()
            if row["status"] == "running"
        ]
        if running:
            raise RuntimeError(
                "Interrupted running occupations require reconciliation: " + str(running)
            )
        result_path = root / "result.json"
        if result_path.exists():
            saved = json.loads(result_path.read_text(encoding="utf-8"))
            if saved["plan_id"] == plan["plan_id"] and saved["status"] == "completed":
                return inspect_ordering_search(root, expected_plan_id=plan["plan_id"])
        local = threading.local()

        def worker(matrix, initial, index):
            try:
                if not hasattr(local, "evaluate"):
                    local.evaluate = evaluator if evaluator is not None else evaluator_factory()
                return run_chain(
                    plan, matrix, initial, index, root, stores[matrix["matrix_id"]], local.evaluate
                )
            except Exception as error:
                return {
                    "status": "failed",
                    "matrix_id": matrix["matrix_id"],
                    "chain_index": index,
                    "error": f"{type(error).__name__}: {error}",
                }

        chains = []
        with ThreadPoolExecutor(max_workers=plan["options"]["workers"]) as pool:
            pending = [
                pool.submit(worker, m, initial, i)
                for m in plan["matrices"]
                for i, initial in enumerate(m["initial_occupations"])
            ]
            for future in as_completed(pending):
                chains.append(future.result())
        chains.sort(key=lambda row: (row["matrix_id"], row["chain_index"]))
        result = export_results(plan, root, stores, chains)
        result["model_binding"] = model_binding
        result["execution_kind"] = (
            "injected_evaluator" if model_binding == "injected-evaluator" else "mlip"
        )
        write_json(root / "result.json", result)
        files = [
            root / "plan.json",
            root / "execution_binding.json",
            root / "result.json",
            *root.glob("*.csv"),
            *root.glob("top_structures.json"),
            *root.glob("matrices/*/ranking.csv"),
            *root.glob("matrices/*/top_structures.json"),
            *root.glob("matrices/*/structures/*.vasp"),
        ]
        write_json(
            root / "result_manifest.json",
            {
                "plan_id": plan["plan_id"],
                "files": {p.relative_to(root).as_posix(): file_digest(p) for p in files},
            },
        )
        return result


def inspect_ordering_search(directory, *, expected_plan_id=None):
    """Inspect completed portable results without loading a model or executing MC."""
    import csv

    root = Path(directory).resolve()
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    if digest({k: v for k, v in plan.items() if k != "plan_id"}) != plan["plan_id"]:
        raise ValueError("Modified prepared plan")
    if expected_plan_id is not None and plan["plan_id"] != expected_plan_id:
        raise ValueError("Returned results belong to a different plan")
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    binding = json.loads((root / "execution_binding.json").read_text(encoding="utf-8"))
    if (
        result["plan_id"] != plan["plan_id"]
        or binding["plan_id"] != plan["plan_id"]
        or result.get("model_binding") != binding["model_binding"]
    ):
        raise ValueError("Result identity/model binding mismatch")
    manifest = json.loads((root / "result_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("plan_id") != plan["plan_id"]:
        raise ValueError("Returned manifest identity mismatch")
    for name, checksum in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or file_digest(path) != checksum:
            raise ValueError("Returned file checksum mismatch: " + name)
    for name in ("global_ranking.csv", "all_joint_records.csv", "diagnostics.csv"):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError("Missing returned CSV: " + name)
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                if not row.get("structure_path"):
                    continue
                structure = (root / row["structure_path"]).resolve()
                if not structure.is_relative_to(root) or not structure.is_file():
                    raise ValueError("Missing/outside returned structure: " + row["structure_path"])
    return {
        **result,
        "global_ranking_csv": str(root / "global_ranking.csv"),
        "all_joint_csv": str(root / "all_joint_records.csv"),
        "diagnostics_csv": str(root / "diagnostics.csv"),
    }


def reconcile_ordering_search(directory, matrix_id, occupation_key, *, verified_not_running, note):
    """Release one checked failed/interrupted claim; preserve evaluation budgets."""
    from filelock import FileLock

    root = Path(directory).resolve()
    with FileLock(str(root / "coordinator.lock"), timeout=0):
        plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
        binding = json.loads((root / "execution_binding.json").read_text(encoding="utf-8"))
        stores = _stores(plan, root, binding["model_binding"])
        if matrix_id not in stores:
            raise ValueError("Unknown H identity")
        stores[matrix_id].reconcile(
            occupation_key, verified_not_running=verified_not_running, note=note
        )
        if (root / "result.json").exists():
            (root / "result.json").rename(
                root
                / (
                    "result.before-reconcile-"
                    + digest([matrix_id, occupation_key, note])[:12]
                    + ".json"
                )
            )
    return {"status": "reconciled", "matrix_id": matrix_id, "occupation_key": occupation_key}

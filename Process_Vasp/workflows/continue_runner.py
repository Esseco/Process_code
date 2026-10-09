"""Resolve previous results on the cluster and execute only required stages."""

import json
from pathlib import Path

from .atomate_runner import _lock, _save, run_workflow
from ..results.completed import get_completed_result


def _plan(root, config, goal):
    chain = ["relax", "static", goal] if goal in {"dos", "band"} else [goal]
    if "previous_task" not in config:
        return {**config, "calculation": goal}
    previous = Path(config["previous_task"])
    previous = previous if previous.is_absolute() else root.parent / previous
    previous = previous.resolve()
    old_file = previous / "workflow.json"
    old = json.loads(old_file.read_text(encoding="utf-8")) if old_file.is_file() else {}
    # Supplied overrides are compared with recorded overrides. A changed earlier
    # stage prevents adoption of that stage and all downstream source stages.
    full_chain = ["relax", "static"] + ([goal] if goal in {"dos", "band"} else [])
    if goal == "relax":
        full_chain = ["relax"]
    first_change = len(full_chain)
    for i, stage in enumerate(full_chain):
        for group in ("incar_settings", "kpoints_settings"):
            requested = config.get(group, {}).get(stage, {})
            recorded = old.get(group, {}).get(stage, {})
            if any(key not in recorded or recorded[key] != value for key, value in requested.items()):
                first_change = min(first_change, i)
    candidates = full_chain[:first_change]
    explicit = config.get("source_stage")
    if explicit:
        candidates = [explicit] if explicit in candidates else []
    selected = None
    for stage in reversed(candidates):
        try:
            directory = get_completed_result(previous, stage, source_dir=config.get("source_dir"))
        except (ValueError, FileNotFoundError):
            continue
        selected = (stage, directory)
        break
    planned = {key: value for key, value in config.items() if key in {
        "incar_settings", "kpoints_settings", "export_plot_data"}}
    # Preserve predecessor overrides unless the new JSON explicitly overrides them.
    for group in ("incar_settings", "kpoints_settings"):
        planned[group] = {stage: {**old.get(group, {}).get(stage, {}),
                                  **config.get(group, {}).get(stage, {})}
                          for stage in full_chain}
    planned["calculation"] = goal
    if selected:
        stage, directory = selected
        remaining = full_chain[full_chain.index(stage)+1:]
        if goal == "static" and stage == "relax":
            remaining = ["static"]
        planned["previous_result"] = dict(task_dir=str(previous), stage=stage, source_dir=str(directory))
        planned["requested_stages"] = remaining
    else:
        if explicit or config.get("source_dir"):
            raise ValueError("Explicit source cannot be reused with requested overrides; select an earlier source stage")
        initial = old.get("structure_file")
        if not initial or not (previous / initial).is_file():
            raise ValueError("No reusable predecessor or original structure; provide a new structure_file")
        planned["structure_file"] = str(previous / initial)
        planned["requested_stages"] = full_chain
    return planned


def execute_task(task_dir):
    """Execute generated task on cluster. Writes plans/checkpoints; may run VASP.

    Original results are read only. AMSET prefers a completed DOS; absent DOS is
    generated from available static/relax results via atomate2 before transport.
    AMSET-only submission scripts require VASP resources/modules to be configured
    if missing precursor calculations need to run. No automatic job submission.
    """
    root = Path(task_dir).resolve()
    with _lock(root):
        config = json.loads((root / "workflow.json").read_text(encoding="utf-8"))
        calculation = config["calculation"]
        execution = root / "execution"
        execution.mkdir(exist_ok=True)
        goal = "dos" if calculation == "amset" else calculation
        plan = _plan(execution, config, goal)
        if "previous_task" not in config and plan.get("structure_file"):
            plan["structure_file"] = str(root / plan["structure_file"])
        _save(execution / "workflow.json", plan)
        if calculation == "amset" and plan.get("requested_stages", ["dos"]):
            if not config.get("amset_settings", {}).get("allow_vasp", False):
                raise ValueError("AMSET needs a new DOS precursor. Set amset_settings.allow_vasp=true and use a VASP-capable submission script, or complete DOS first.")
        state = run_workflow(execution)
        if calculation == "amset":
            from .amset_postprocess import run_amset_postprocess
            if plan.get("requested_stages") == []:
                source = plan["previous_result"]["source_dir"]
            else:
                entry = state["stages"]["dos"]
                source = str(execution / entry["directory"])
            options = dict(config.get("amset_settings", {}))
            options.pop("allow_vasp", None)
            return run_amset_postprocess(root, root / "results", source_dir=source, **options)
        return state

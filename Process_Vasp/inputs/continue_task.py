"""One JSON entry point for new and continuation tasks."""

import json
from pathlib import Path


def continue_task(config, directory=None):
    """Prepare a task from a JSON path or dict; never run or submit calculations.

    JSON selects calculation and exactly one of structure_file/previous_task.
    Local structure_file is relative to the JSON; previous_task is a server path,
    relative to the generated task when not absolute. Default target is a sibling
    <config-stem>_task. Requires an absent/empty target. Writes workflow.json,
    workflow.py, submit.sh and optionally initial structure. No random seed.
    Execution uses the installed Process_Vasp project and atomate2/AMSET as needed.
    """
    if isinstance(config, dict):
        data, base, default_name = dict(config), Path.cwd(), "continue_task"
    else:
        path = Path(config).resolve()
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        base, default_name = path.parent, path.stem + "_task"
    allowed = {"calculation", "structure_file", "previous_task", "source_stage", "source_dir",
               "incar_settings", "kpoints_settings", "export_plot_data", "amset_settings"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError(f"Allowed JSON fields: {sorted(allowed)}")
    calculation = data.get("calculation")
    if calculation not in {"relax", "static", "dos", "band", "amset"}:
        raise ValueError("calculation must be relax/static/dos/band/amset")
    if bool(data.get("structure_file")) == bool(data.get("previous_task")):
        raise ValueError("Specify exactly one of structure_file and previous_task")
    for key in ("incar_settings", "kpoints_settings"):
        values = data.get(key, {})
        if not isinstance(values, dict) or any(stage not in {"relax", "static", "dos", "band"}
                or not isinstance(settings, dict) for stage, settings in values.items()):
            raise ValueError(f"{key} must map VASP stages to dictionaries")
    if not isinstance(data.get("amset_settings", {}), dict):
        raise ValueError("amset_settings must be an object")
    target = Path(directory) if directory is not None else base / default_name
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError(f"Task target must be absent or empty: {target}")
    structure = None
    if data.get("structure_file"):
        structure = Path(data["structure_file"])
        structure = structure if structure.is_absolute() else base / structure
        if not structure.is_file():
            raise FileNotFoundError(structure)
        data["structure_file"] = "initial_structure" + structure.suffix
    templates = Path(__file__).resolve().parents[1] / "templates"
    template = "submit_amset.sh" if calculation == "amset" else "submit_gpu.sh"
    script = (templates / template).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    script = script.replace("python postprocess.py", "python workflow.py").replace("python3 1.py", "python3 workflow.py")
    target.mkdir(parents=True, exist_ok=True)
    if structure is not None:
        (target / data["structure_file"]).write_bytes(structure.read_bytes())
    (target / "workflow.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    code = '''from pathlib import Path
from Process_Vasp.workflows.continue_runner import execute_task

if __name__ == "__main__":
    execute_task(Path(__file__).resolve().parent)
'''
    (target / "workflow.py").write_text(code, encoding="utf-8", newline="\n")
    (target / "submit.sh").write_text(script, encoding="utf-8", newline="\n")
    return target

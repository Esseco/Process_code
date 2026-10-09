"""Generate follow-up tasks whose source is resolved on the execution host."""

import json
import re
from pathlib import Path


def generate_followup_task(directory, previous_task, calculation, *, source_stage=None,
                           source_dir=None, incar_settings=None, kpoints_settings=None,
                           job_name=None, export_plot_data=False, amset_settings=None):
    """Generate relax/static/dos/band/amset from a completed task or raw run.

    previous_task and source_dir are execution-host paths; relative previous_task
    is relative to the new task, source_dir is relative to previous_task. No
    source files are read during generation. Defaults: static <- relax;
    dos/band <- static; relax <- relax; amset <- dos. Explicit source_stage=relax
    for dos/band schedules static then the requested non-SCF calculation.
    AMSET can use a verified uniform static calculation via source_stage=static.
    Writes an absent/empty task directory, never submits. Existing public
    generate_atomate_input remains unchanged. Existing source results are read
    only; completed new stages are reused on resubmission. No random seed.
    """
    if calculation not in {"relax", "static", "dos", "band", "amset"}:
        raise ValueError("Unsupported follow-up calculation")
    default = {"relax": "relax", "static": "relax", "dos": "static",
               "band": "static", "amset": "dos"}
    stage = source_stage or default[calculation]
    allowed = {"relax": {"relax", "static"}, "static": {"relax", "static"},
               "dos": {"relax", "static"}, "band": {"relax", "static"},
               "amset": {"dos", "static"}}
    if stage not in allowed[calculation]:
        raise ValueError(f"{calculation} can start from {sorted(allowed[calculation])}")
    if calculation == "amset":
        if incar_settings or kpoints_settings or export_plot_data:
            raise ValueError("Use amset_settings for AMSET; VASP parameters do not apply")
        from .amset_task import generate_amset_task
        return generate_amset_task(directory, workflow_root=str(previous_task),
                                   source_dir=source_dir, source_stage=stage,
                                   **(amset_settings or {}))
    if amset_settings:
        raise ValueError("amset_settings applies only to calculation='amset'")
    if job_name is not None and not re.fullmatch(r"[A-Za-z0-9_.-]+", job_name):
        raise ValueError("Invalid job_name")
    for settings in (incar_settings, kpoints_settings):
        if settings is not None and (not isinstance(settings, dict) or any(
                key not in {"relax", "static", "dos", "band"} or not isinstance(value, dict)
                for key, value in settings.items())):
            raise ValueError("Settings must map VASP stages to dictionaries")
    target = Path(directory)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError(f"Follow-up task directory must be absent or empty: {target}")
    from .generation import GPU_SCRIPT, _ATOMATE2_WORKFLOW
    script = GPU_SCRIPT.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    script = re.sub(r"(?m)^#SBATCH --job-name=.*$", f"#SBATCH --job-name={job_name or calculation}", script)
    script = re.sub(r"(?m)^python3 1\.py\s*$", "python3 workflow.py", script)
    if "python3 workflow.py" not in script:
        raise ValueError("Submission template has no workflow.py invocation")
    config = dict(calculation=calculation, previous_result={
        "task_dir": str(previous_task), "stage": stage,
        "source_dir": str(source_dir) if source_dir is not None else None},
        incar_settings=incar_settings or {}, kpoints_settings=kpoints_settings or {},
        export_plot_data=bool(export_plot_data))
    target.mkdir(parents=True, exist_ok=True)
    for name, content in {"workflow.json": json.dumps(config, indent=2),
                          "workflow.py": _ATOMATE2_WORKFLOW, GPU_SCRIPT.name: script}.items():
        with (target / name).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    return target

"""VASP completion, convergence, and error status reader."""

from pathlib import Path
from typing import Any
from monty.os.path import zpath

from pymatgen.io.vasp.outputs import Vasprun


def _read_output_status(init_dir: Path) -> tuple[bool, bool]:
    """Return completion and ionic-convergence flags from the latest output block."""
    output_path = init_dir / "out"
    if not output_path.exists():
        return False, False
    content = output_path.read_text(encoding="utf-8", errors="ignore")
    marker = content.rfind("running on")
    latest_run = content[marker:] if marker >= 0 else content
    ionic_steps = latest_run.count("   1 F=")
    finished = ionic_steps > 0 and latest_run.count("Terminated at") == ionic_steps
    return finished, "reached required accuracy" in latest_run


def _read_errors(init_dir: Path) -> str:
    """Return errors reported by custodian, or an empty string."""
    output_path = init_dir / "out"
    if not output_path.exists():
        return "out file not found"
    try:
        from custodian.vasp.handlers import VaspErrorHandler

        handler = VaspErrorHandler(output_filename=output_path)
        if not handler.check(directory=init_dir):
            return ""
        errors = handler.errors
        if isinstance(errors, dict):
            return "; ".join(map(str, errors))
        if isinstance(errors, str):
            return errors
        return "; ".join(map(str, errors))
    except Exception as exc:
        return str(exc)


def read_vasp_status(init_dir: str | Path) -> dict[str, Any]:
    """Read calculation status without modifying VASP input files.

    Args:
        init_dir: VASP calculation directory.

    Returns:
        Completion, convergence, ionic-step, and detected-error information.
    """
    init_dir = Path(init_dir)
    vasprun_path = Path(zpath(init_dir / "vasprun.xml"))
    current_step = 0
    max_step: int | None = None
    converged = False
    parse_error = ""

    if vasprun_path.exists():
        try:
            vasprun = Vasprun(
                vasprun_path,
                parse_dos=False,
                parse_eigen=False,
                parse_projected_eigen=False,
                parse_potcar_file=False,
                exception_on_bad_xml=False,
            )
            current_step = len(vasprun.ionic_steps)
            nsw = vasprun.parameters.get("NSW")
            max_step = int(nsw) if nsw is not None else None
            converged = bool(vasprun.converged)
        except Exception as exc:
            parse_error = str(exc)

    finished, output_converged = _read_output_status(init_dir)
    error_message = _read_errors(init_dir)
    messages = [message for message in (parse_error, error_message) if message]
    return {
        "finished": finished,
        "converged": converged or output_converged,
        "max_ionic_steps": max_step,
        "current_ionic_step": current_step,
        "has_error": bool(messages),
        "error_message": "; ".join(dict.fromkeys(messages)),
    }

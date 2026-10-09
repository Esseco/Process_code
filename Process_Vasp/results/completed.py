"""Resolve completed VASP stages for readers and follow-up workflows."""

import json
from pathlib import Path


def get_completed_result(task_dir, stage, *, source_dir=None, validate=True, require_uniform=False):
    """Return a completed relax/static/dos/band directory without modifying it.

    Prefer the named completed checkpoint; relative directories use task_dir.
    A raw VASP directory can be passed as task_dir or explicitly source_dir.
    validate checks electronic convergence, ionic convergence for relax, NSW
    semantics and rejects line-mode k points for DOS or require_uniform=True.
    This excludes explicit path mode, not a full grid completeness proof. No wavefunction/charge
    files required for read-only reuse; downstream calculations check theirs.
    Requires pymatgen only when validate=True. No random seed or file writes.
    """
    if stage not in {"relax", "static", "dos", "band"}:
        raise ValueError("stage must be relax, static, dos or band")
    root = Path(task_dir).resolve()
    if source_dir is not None:
        directory = Path(source_dir)
        directory = directory if directory.is_absolute() else root / directory
    elif (root / "workflow_state.json").is_file():
        state = json.loads((root / "workflow_state.json").read_text(encoding="utf-8"))
        entry = state.get("stages", {}).get(stage, {})
        if entry.get("status") != "completed" or not entry.get("directory"):
            raise ValueError(f"No completed {stage} checkpoint in {root}; specify a verified source_dir")
        directory = Path(entry["directory"])
        directory = directory if directory.is_absolute() else root / directory
    else:
        directory = root
    directory = directory.resolve()
    xml = next((directory / name for name in ("vasprun.xml", "vasprun.xml.gz")
                if (directory / name).is_file()), None)
    if xml is None:
        raise FileNotFoundError(f"No vasprun.xml[.gz] for {stage}: {directory}")
    if validate:
        from pymatgen.io.vasp.outputs import Vasprun
        run = Vasprun(xml, parse_dos=False, parse_eigen=False,
                      parse_projected_eigen=False, parse_potcar_file=False,
                      exception_on_bad_xml=True)
        if not run.converged_electronic:
            raise ValueError(f"Electronic calculation is not converged: {directory}")
        nsw = int(run.parameters.get("NSW", 0))
        if stage == "relax" and (nsw <= 0 or not run.converged_ionic):
            raise ValueError(f"Not a completed ionic relaxation: {directory}")
        if stage != "relax" and nsw != 0:
            raise ValueError(f"{stage} requires NSW=0: {directory}")
        if (stage == "dos" or require_uniform) and "line" in str(run.kpoints.style).lower():
            raise ValueError("DOS/transport requires a uniform grid, not line-mode k points")
    return directory

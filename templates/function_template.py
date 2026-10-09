"""Copy into a project, implement compute, and document units and limitations."""
from pathlib import Path


def compute(input_path: Path, *, options: dict) -> dict:
    raise NotImplementedError("Replace with a tested project function")


def run(input_path, output_dir=None, *, options=None):
    source = Path(input_path).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    target = Path(output_dir).resolve() if output_dir is not None else None
    if target is not None and target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Choose an absent or empty output directory")
    result = compute(source, options=options or {})
    # Add task-specific serialization after successful computation.
    return {"input_path": str(source), "output_dir": str(target) if target else None,
            "result": result}

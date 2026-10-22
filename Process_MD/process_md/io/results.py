"""JSON/CSV serialization without implicit overwrites or nonfinite numbers."""
from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
import io
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np


def _json_default(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__} to JSON")


def _write_text(path: str | Path, text: str, overwrite: bool) -> Path:
    if type(overwrite) is not bool:
        raise TypeError("overwrite must be bool")
    encoded = text.encode("utf-8")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb" if overwrite else "xb") as handle:
        handle.write(encoded)
    return path


def save_json(data: Any, path: str | Path, *, overwrite: bool = False) -> Path:
    """Serialize before opening the destination, rejecting NaN and infinity.

    Existing files require overwrite=True. This utility is for reports;
    crash-safe checkpoint writes will be implemented with the MD runner.
    """
    text = json.dumps(data, default=_json_default, ensure_ascii=False, indent=2, allow_nan=False)
    return _write_text(path, text + "\n", overwrite)


def save_results(results: Mapping[str, Any], output_dir: str | Path) -> Path:
    """Write a schema-versioned results.json from named data objects.

    Callers choose keys such as structure, md, msd and validation. Unit-bearing
    dataclass field names are preserved; no scientific quantities are inferred.
    """
    return save_json({"schema_version": 1, "results": dict(results)}, Path(output_dir) / "results.json")


def save_csv(
    rows: Iterable[Mapping[str, Any]], path: str | Path, *, overwrite: bool = False,
) -> Path:
    """Write a nonempty scalar table; put units in column names (e.g. time_ps).

    Missing cells and None become blank. Nested arrays/objects and nonfinite
    numbers are rejected before touching the destination; use JSON for them.
    """
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    if not rows or not fields or any(not isinstance(key, str) or not key for key in fields):
        raise ValueError("CSV needs nonempty rows and string column names")
    for row in rows:
        for value in row.values():
            if isinstance(value, np.generic):
                value = value.item()
            if not (value is None or isinstance(value, (str, bool, int, float))):
                raise TypeError("CSV values must be scalar; use JSON for nested data")
            if isinstance(value, float) and not isfinite(value):
                raise ValueError("CSV values must be finite")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return _write_text(path, buffer.getvalue(), overwrite)

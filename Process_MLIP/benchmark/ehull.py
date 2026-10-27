"""Standard composition convex hulls, using only supplied structures and total energies."""
from collections import Counter
import csv
from pathlib import Path

import numpy as np
from pymatgen.analysis.phase_diagram import PDEntry, PhaseDiagram


def validate_endmembers(compositions):
    """Require elemental terminal phases; never invent/reference-download competitors."""
    elements = set().union(*(set(comp) for comp in compositions))
    supplied = {next(iter(comp)) for comp in compositions if len(comp) == 1}
    missing = elements - supplied
    if missing:
        raise ValueError(f"Missing elemental endmembers for standard hull: {sorted(missing)}; "
                         "provide reference structures, no competing phases are fabricated")


def compute_hull(records, tolerance=1e-6):
    """Return PhaseDiagram and per-ID eV/atom values from relaxed whole-cell eV."""
    if not records:
        raise ValueError("Hull needs structures")
    ids = [record["structure_id"] for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate structure IDs in hull")
    compositions = [Counter(record["composition"]) for record in records]
    validate_endmembers(compositions)
    entries = []
    for record, comp in zip(records, compositions):
        if not record.get("converged") or record["status"] != "completed":
            raise ValueError(f"Hull requires every structure converged: {record['structure_id']}")
        if not np.isfinite(record["energy_eV"]):
            raise ValueError("Hull energy must be finite")
        entries.append(PDEntry(dict(comp), record["energy_eV"], name=record["structure_id"]))
    diagram = PhaseDiagram(entries)
    rows = []
    for record, entry in zip(records, entries):
        value = float(diagram.get_e_above_hull(entry))
        decomposition, _ = diagram.get_decomp_and_e_above_hull(entry)
        rows.append(dict(record, ehull_eV_per_atom=value, stable=value <= tolerance,
                         formation_energy_eV_per_atom=float(diagram.get_form_energy_per_atom(entry)),
                         decomposition={phase.name: float(amount) for phase, amount in decomposition.items()}))
    return diagram, rows


def read_reference(path):
    """Strict ID,ehull_eV_per_atom CSV; references are already-normalized Ehull."""
    if path is None:
        return None
    values = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"id", "ehull_eV_per_atom"} <= set(reader.fieldnames or []):
            raise ValueError("DFT reference requires id,ehull_eV_per_atom columns")
        for row in reader:
            name = row["id"]
            if not name or name in values:
                raise ValueError(f"Empty or duplicate reference ID: {name!r}")
            value = float(row["ehull_eV_per_atom"])
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"Reference Ehull must be finite and nonnegative: {name}")
            values[name] = value
    if not values:
        raise ValueError("DFT reference is empty")
    return values


def compare_reference(rows, reference, tolerance=1e-6):
    """Match IDs exactly, report coverage, errors and stable-set confusion counts."""
    if reference is None:
        return rows, None
    predicted = {row["structure_id"]: row["ehull_eV_per_atom"] for row in rows}
    matched = sorted(predicted.keys() & reference.keys())
    if not matched:
        raise ValueError("No matching structure IDs in DFT reference")
    errors = np.array([predicted[name] - reference[name] for name in matched])
    pred_stable = {name for name in matched if predicted[name] <= tolerance}
    ref_stable = {name for name in matched if reference[name] <= tolerance}
    tp = len(pred_stable & ref_stable)
    metrics = dict(n_matched=len(matched), n_predicted=len(rows), coverage=len(matched) / len(rows),
                   missing_reference_ids=sorted(predicted.keys() - reference.keys()),
                   unused_reference_ids=sorted(reference.keys() - predicted.keys()),
                   MAE_eV_per_atom=float(np.abs(errors).mean()),
                   RMSE_eV_per_atom=float(np.sqrt(np.mean(errors**2))),
                   Bias_eV_per_atom=float(errors.mean()),
                   tolerance_eV_per_atom=tolerance,
                   predicted_stable_ids=sorted(pred_stable), reference_stable_ids=sorted(ref_stable),
                   true_positive=tp, false_positive=len(pred_stable - ref_stable),
                   false_negative=len(ref_stable - pred_stable),
                   true_negative=len(matched) - len(pred_stable | ref_stable),
                   stable_precision=tp / len(pred_stable) if pred_stable else None,
                   stable_recall=tp / len(ref_stable) if ref_stable else None)
    output = []
    for row in rows:
        value = reference.get(row["structure_id"])
        output.append(dict(row, reference_ehull_eV_per_atom=value,
                           error_eV_per_atom=None if value is None else row["ehull_eV_per_atom"] - value,
                           reference_stable=None if value is None else value <= tolerance))
    return output, metrics

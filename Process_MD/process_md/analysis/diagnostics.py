"""Numerical evidence for future size/time/temperature review, without decisions."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from pathlib import Path

import numpy as np
from ase import Atoms

from ..models import DiffusionResult
from ..structure import get_structure_info


def describe_cell(atoms: Atoms) -> dict:
    """Return geometry evidence; an atom-count floor is not a size-convergence test.

    Heights correspond to the supplied lattice basis, not Cartesian MSD axes.
    Mapping a fast transport direction to an integer supercell is a separate
    operation that must retain the basis/transformation provenance.
    """
    info = get_structure_info(atoms)
    heights = 1 / np.linalg.norm(np.linalg.inv(atoms.cell.array), axis=0)
    return dict(n_atoms=info.n_atoms, cell_vectors_A=atoms.cell.array.tolist(),
                cell_lengths_A=list(info.cell_lengths_A), perpendicular_heights_A=heights.tolist(),
                minimum_height_A=float(heights.min()), volume_A3=info.volume_A3,
                size_convergence="not_assessed")


@dataclass(frozen=True)
class ThermodynamicSummary:
    n_samples: int
    start_ps: float
    end_ps: float
    means: dict[str, float]
    standard_deviations: dict[str, float]
    minima: dict[str, float]
    maxima: dict[str, float]


def summarize_md_log(path: str | Path, *, start_ps: float = 0) -> ThermodynamicSummary:
    """Summarize an existing md.csv, retaining its unit-bearing column names.

    start_ps is an absolute log time, including any upstream stage offset.
    These are sample statistics, not independent-sample errors or criteria
    for raising/lowering temperature. NVT energy drift is not an NVE test.
    """
    if isinstance(start_ps, bool) or not isinstance(start_ps, Real) or not isfinite(start_ps) or start_ps < 0:
        raise ValueError("start_ps must be finite and nonnegative")
    with Path(path).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"time_fs", "temperature_K"} <= rows[0].keys():
        raise ValueError("MD log requires time_fs and temperature_K samples")
    times = np.array([float(row["time_fs"]) / 1000 for row in rows])
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("MD log times must be finite and strictly increasing")
    selected = [row for time, row in zip(times, rows) if time >= start_ps]
    selected_times = times[times >= start_ps]
    if not selected:
        raise ValueError("No MD samples remain in the requested interval")
    if any(row["temperature_K"] in (None, "") for row in selected):
        raise ValueError("temperature_K samples are missing")
    summaries = [dict() for _ in range(4)]
    for key in rows[0]:
        if key in ("step", "time_fs"):
            continue
        values = [float(row[key]) for row in selected if row[key] not in (None, "")]
        if not values:
            if key == "temperature_K":
                raise ValueError("temperature_K samples are missing")
            continue
        if not np.isfinite(values).all():
            raise ValueError(f"{key} samples must be finite")
        for summary, value in zip(summaries, (np.mean(values), np.std(values), np.min(values), np.max(values))):
            summary[key] = float(value)
    return ThermodynamicSummary(len(selected), float(selected_times[0]), float(selected_times[-1]), *summaries)


def compare_transport(reference: DiffusionResult, candidate: DiffusionResult, *, varied: str) -> dict:
    """Compare two estimates numerically; never recommend an automatic action.

    varied is cell, duration or temperature. Callers must ensure matching
    material, SOC/configuration, model and phase; these cannot be inferred
    from two diffusion values. Size/time comparisons require equal T.
    No single-cell result can establish that enlargement is needed or enough.
    """
    if varied not in ("cell", "duration", "temperature"):
        raise ValueError("varied must be cell, duration or temperature")
    if set(reference.axes) != set(candidate.axes):
        raise ValueError("Transport comparisons require the same Cartesian axes")
    if varied != "temperature" and (reference.temperature_K is None or candidate.temperature_K is None
                                     or not np.isclose(reference.temperature_K, candidate.temperature_K)):
        raise ValueError("Size/time comparisons require matching known temperatures")
    def relative_change(left, right):
        for value in (left, right):
            if value is not None and (not isfinite(value) or value < 0):
                raise ValueError("Transport estimates must be finite and nonnegative")
        if left is None or right is None or left == 0:
            return None
        return float((right - left) / left)
    return dict(
        varied=varied, axes=reference.axes,
        relative_diffusion_change=relative_change(reference.diffusion_cm2_s, candidate.diffusion_cm2_s),
        relative_conductivity_NE_change=relative_change(reference.conductivity_NE_S_cm,
                                                       candidate.conductivity_NE_S_cm),
        convergence="not_assessed", uncertainty="not_evaluated",
        limitations="Requires matched material/SOC/model/phase; thresholds and actions belong to later review.",
    )

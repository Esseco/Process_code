"""Compare prepared hulls and phase intervals without reconstructing phase diagrams."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict

import numpy as np
from numpy.typing import ArrayLike, NDArray

HullInput = ArrayLike | Mapping[str, ArrayLike]
PhaseInput = Mapping[str, ArrayLike]


class _HullResult(TypedDict):
    hull_error: float
    integral_error: float
    x: NotRequired[NDArray[np.float64]]
    pred_relative_energy: NotRequired[NDArray[np.float64]]
    ref_relative_energy: NotRequired[NDArray[np.float64]]


class _PhaseResult(TypedDict):
    phase_error: float
    mean_iou: float
    phase_iou: dict[str, float]


def _finite_array(value: ArrayLike, name: str) -> NDArray[np.float64]:
    try:
        raw = np.asarray(value)
        if np.iscomplexobj(raw):
            raise ValueError("complex values are not supported")
        result = np.asarray(raw, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must contain real numeric values") from exc
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite values")
    return result


def _range(x_range: ArrayLike) -> NDArray[np.float64]:
    bounds = _finite_array(x_range, "x_range")
    if bounds.shape != (2,) or bounds[0] >= bounds[1]:
        raise ValueError("x_range must be (xmin, xmax) with xmin < xmax")
    if not np.isfinite(bounds[1] - bounds[0]):
        raise ValueError("x_range width must be finite")
    return bounds


def _hull(hull: HullInput, name: str) -> NDArray[np.float64]:
    if isinstance(hull, Mapping):
        if "x" not in hull or "energy" not in hull:
            raise ValueError(f"{name} requires 'x' and 'energy' columns")
        x = _finite_array(hull["x"], f"{name}.x")
        energy = _finite_array(hull["energy"], f"{name}.energy")
        if x.ndim != 1 or energy.shape != x.shape:
            raise ValueError(f"{name} columns must be equal-length 1D arrays")
        points = np.column_stack((x, energy))
    else:
        points = _finite_array(hull, name)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        raise ValueError(f"{name} must have shape (N, 2), N >= 2")
    points = points[np.argsort(points[:, 0])]
    dx = np.diff(points[:, 0])
    if np.any(dx <= 0):
        raise ValueError(f"{name} has duplicate x vertices")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        slopes = np.diff(points[:, 1]) / dx
    if not np.all(np.isfinite(dx)) or not np.all(np.isfinite(slopes)):
        raise ValueError(f"{name} has unrepresentable spacings or slopes")
    # Allow only floating-point roundoff; collinear vertices are valid.
    tolerance = 64 * np.finfo(float).eps * np.maximum(
        np.abs(slopes[:-1]), np.abs(slopes[1:])
    )
    if np.any(slopes[:-1] - slopes[1:] > tolerance):
        raise ValueError(f"{name} is not a lower convex hull: slopes must be nondecreasing")
    return points


def calculate_hull_error(
    pred_hull: HullInput,
    ref_hull: HullInput,
    x_range: ArrayLike | None = None,
    *,
    return_curves: bool = False,
) -> _HullResult:
    """Return the exact mean absolute difference between endpoint-relative hulls.

    Parameters
    ----------
    pred_hull, ref_hull
        (N, 2) arrays of (x, energy), or mappings with 1D ``x`` and ``energy``
        columns. Vertices are sorted by x; duplicate x, NaN/Inf, fewer than two
        points and nonconvex inputs raise ValueError. Collinear points are allowed.
        Slopes must be nondecreasing, within 64 machine eps relative roundoff.
        Both energies must use the same unit/normalization, e.g. meV/TM.
    x_range
        (xmin, xmax), strictly increasing and covered by both hulls. Defaults to
        their common coverage. Extrapolation and zero-width ranges are rejected.
    return_curves
        Also return ``x``, ``pred_relative_energy``, ``ref_relative_energy`` on
        the union of interior vertex positions and evaluation endpoints.

    Returns
    -------
    dict
        ``hull_error`` in input energy units and ``integral_error`` in energy
        times x units. Each hull has its own endpoint chord subtracted over the
        evaluation range. Piecewise linear integration splits sign crossings
        analytically, without sampling error (subject to floating-point precision).

    Notes
    -----
    Pure deterministic calculation: no mutation, files, models or random seed.
    Only prepared computational reference hulls are appropriate for this metric.

    Examples
    --------
    >>> calculate_hull_error([[0, 0], [0.5, -2], [1, 0]], [[0, 0], [1, 0]])
    {'hull_error': 1.0, 'integral_error': 1.0}
    """
    pred = _hull(pred_hull, "pred_hull")
    ref = _hull(ref_hull, "ref_hull")
    common = (max(pred[0, 0], ref[0, 0]), min(pred[-1, 0], ref[-1, 0]))
    lo, hi = _range(common if x_range is None else x_range)
    if lo < common[0] or hi > common[1]:
        raise ValueError("x_range must be covered by both hulls; extrapolation is forbidden")
    grid = np.unique(np.concatenate(([lo, hi], pred[:, 0], ref[:, 0])))
    grid = grid[(grid >= lo) & (grid <= hi)]
    relative = []
    for points in (pred, ref):
        energy = np.interp(grid, points[:, 0], points[:, 1])
        chord = np.interp(grid, [lo, hi], [energy[0], energy[-1]])
        relative.append(energy - chord)
    difference = relative[0] - relative[1]
    left, right = np.abs(difference[:-1]), np.abs(difference[1:])
    heights = left / 2 + right / 2
    crossing = ((difference[:-1] < 0) & (difference[1:] > 0)) | (
        (difference[:-1] > 0) & (difference[1:] < 0)
    )
    # Two triangles instead of a trapezoid when a segment crosses zero.
    a, b = left[crossing], right[crossing]
    scale = np.maximum(a, b)
    heights[crossing] = (a * (a / scale) + b * (b / scale)) / (
        2 * (a / scale + b / scale)
    )
    widths = np.diff(grid)
    integral = float(np.sum(widths * heights))
    mean = float(np.sum((widths / (hi - lo)) * heights))
    if not np.isfinite(integral) or not np.isfinite(mean):
        raise ValueError("hull error exceeds floating-point range")
    result: _HullResult = {"hull_error": mean, "integral_error": integral}
    if return_curves:
        result.update(x=grid, pred_relative_energy=relative[0], ref_relative_energy=relative[1])
    return result


def _merged_intervals(
    intervals: ArrayLike, bounds: NDArray[np.float64], delta: float, name: str
) -> NDArray[np.float64]:
    values = _finite_array(intervals, name)
    if values.shape == (0,):
        values = values.reshape(0, 2)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError(f"{name} must have shape (N, 2), or be []")
    if np.any(values[:, 0] >= values[:, 1]):
        raise ValueError(f"{name} intervals must satisfy start < end")
    # Expansion precedes clipping, including intervals originally outside x_range.
    with np.errstate(over="ignore"):
        expanded = np.clip(values + np.array([-delta, delta]), *bounds)
    expanded = expanded[expanded[:, 0] < expanded[:, 1]]
    merged: list[list[float]] = []
    for start, end in expanded[np.argsort(expanded[:, 0])]:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], float(end))
        else:
            merged.append([float(start), float(end)])
    return np.asarray(merged, dtype=float).reshape(-1, 2)


def calculate_phase_iou_error(
    pred_phases: PhaseInput,
    ref_phases: PhaseInput,
    *,
    x_range: ArrayLike,
    delta: float = 0.0,
) -> _PhaseResult:
    """Return macro-averaged phase IoU error after symmetric interval dilation.

    Parameters
    ----------
    pred_phases, ref_phases
        Mappings from phase names (strings) to (N, 2) arrays/lists of (start, end).
        Multiple disconnected intervals and coexistence across labels are allowed.
        Overlapping/touching intervals within a phase are merged. [] is allowed.
        All input intervals must be finite with start < end, even outside x_range.
    x_range
        Required finite (xmin, xmax), xmin < xmax; same x units as intervals/delta.
    delta
        Finite nonnegative scalar. Both predicted and reference intervals expand
        left/right by delta before clipping to x_range. This is dilation IoU,
        not a rule assigning perfect scores to boundary shifts smaller than delta.

    Returns
    -------
    dict
        ``phase_error = 1 - mean_iou``, ``mean_iou`` and ``phase_iou`` (per-label
        IoU), all in [0, 1]. Each label in either mapping has equal weight. A label
        missing from either mapping scores 0. If a label exists in both mappings
        but both dilated/clipped sets are empty, its IoU is 1 (equal empty sets).
        Two empty mappings raise ValueError because the macro mean is undefined.

    Notes
    -----
    No phase identification, mutation, file I/O or randomness. Invalid inputs
    raise ValueError. Repeat calls on identical inputs return identical results.

    Examples
    --------
    >>> calculate_phase_iou_error({'O3': [(0, 1)]}, {'O3': [(0, 1)]}, x_range=(0, 1))
    {'phase_error': 0.0, 'mean_iou': 1.0, 'phase_iou': {'O3': 1.0}}
    """
    bounds = _range(x_range)
    buffer = _finite_array(delta, "delta")
    if buffer.ndim != 0 or buffer < 0:
        raise ValueError("delta must be a finite nonnegative scalar")
    delta = float(buffer)
    for phases in (pred_phases, ref_phases):
        if not isinstance(phases, Mapping) or any(not isinstance(p, str) for p in phases):
            raise ValueError("phases must be mappings with string phase names")
    labels = sorted(set(pred_phases) | set(ref_phases))
    if not labels:
        raise ValueError("at least one phase label is required")
    scores = {}
    for label in labels:
        pred = _merged_intervals(pred_phases.get(label, []), bounds, delta, f"pred.{label}")
        ref = _merged_intervals(ref_phases.get(label, []), bounds, delta, f"ref.{label}")
        if label not in pred_phases or label not in ref_phases:
            scores[label] = 0.0
            continue
        # Normalize lengths first so narrow ranges and large x units stay stable.
        width = bounds[1] - bounds[0]
        pred_length = float(np.sum((pred[:, 1] - pred[:, 0]) / width))
        ref_length = float(np.sum((ref[:, 1] - ref[:, 0]) / width))
        intersection = 0.0
        i = j = 0
        while i < len(pred) and j < len(ref):
            intersection += max(0.0, min(pred[i, 1], ref[j, 1]) - max(pred[i, 0], ref[j, 0])) / width
            if pred[i, 1] < ref[j, 1]:
                i += 1
            else:
                j += 1
        union = pred_length + ref_length - intersection
        scores[label] = float(np.clip(intersection / union, 0, 1)) if union > 0 else 1.0
    mean = float(np.mean(list(scores.values())))
    return {"phase_error": 1.0 - mean, "mean_iou": mean, "phase_iou": scores}

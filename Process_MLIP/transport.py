"""Fit a full or manually selected MSD lag window using pymatgen defaults."""
import csv
import json
from numbers import Real
from pathlib import Path

import numpy as np


def _load_pymatgen_fitter():
    try:
        from pymatgen.analysis.diffusion.analyzer import get_diffusivity_from_msd
    except ImportError as exc:
        raise ImportError("Weighted MSD fitting requires pymatgen-analysis-diffusion "
                          "in the analysis environment") from exc
    return get_diffusivity_from_msd


def _fit_window_mask(times, start, end):
    """Resolve optional bounds per curve; exclude zero lag from weighted fits."""
    for value in (start, end):
        if value is not None and (isinstance(value, bool) or not isinstance(value, Real)
                                  or not np.isfinite(value) or value <= 0):
            raise ValueError("Fit bounds must be finite positive lag times or None")
    times = np.asarray(times)
    positive = times > 0
    if not np.any(positive):
        raise ValueError("Fit window needs at least three positive-lag MSD samples")
    left = times[positive][0] if start is None else start
    right = times[positive][-1] if end is None else end
    if left >= right:
        raise ValueError("Require fit_start_ps < fit_end_ps after resolving None")
    if left < times[0] or right > times[-1]:
        raise ValueError("Fit window must lie within every selected segment")
    mask = positive & (times >= left) & (times <= right)
    if np.count_nonzero(mask) < 3:
        raise ValueError("Fit window needs at least three positive-lag MSD samples")
    return mask


def _validate_dimension_options(mode, axes, threshold, min_msd_A2=1.0):
    if (isinstance(min_msd_A2, bool) or not isinstance(min_msd_A2, Real)
            or not np.isfinite(min_msd_A2) or min_msd_A2 < 0):
        raise ValueError("min_msd_A2 must be finite and nonnegative")
    if (isinstance(threshold, bool) or not isinstance(threshold, Real)
            or not np.isfinite(threshold) or threshold <= 1):
        raise ValueError("anisotropy_threshold must be finite and > 1")
    if mode not in ("auto", "3d", "2d", "1d"):
        raise ValueError("diffusion_mode must be auto, 3d, 2d or 1d")
    if (not isinstance(axes, str) or not axes or any(axis not in "xyz" for axis in axes)
            or len(set(axes)) != len(axes)):
        raise ValueError("axes must contain distinct Cartesian x/y/z letters")
    if mode in ("1d", "2d") and len(axes) != int(mode[0]):
        raise ValueError("axes count must match the selected dimension")
    return float(threshold)


def _add_dimensional_transport(row, times, msd, fitter, mode, axes, threshold, factor, min_msd_A2):
    """Keep 3D values intact; append Cartesian diagnostics and projected fits."""
    directions = np.asarray(row["directional_diffusion_m2_s"])
    row["directional_conductivity_NE_S_m"] = (directions * factor).tolist()
    row["directional_conductivity_NE_S_cm"] = (directions * factor / 100).tolist()
    names = "xyz"
    endpoint = msd[-1, :3]
    endpoint_total = float(msd[-1, 3])
    row["low_msd"] = bool(endpoint_total < min_msd_A2)
    order = np.argsort(-endpoint, kind="stable")
    unresolved = [axis for axis in names if row["pymatgen_slope_floor_applied"][axis]]
    ratios = {"largest_to_middle": None, "middle_to_smallest": None}
    status, selected, reason = "3d", None, "No adjacent endpoint MSD ratio exceeds threshold"
    if mode == "3d":
        status, reason = "disabled", "Dimensional check disabled"
    elif mode == "auto" and row["low_msd"]:
        status, reason = "low_msd", "Endpoint total MSD below min_msd_A2; automatic supplement skipped"
    elif not np.any(endpoint > 0):
        status, reason = "indeterminate", "All endpoint MSD components are zero"
    else:
        fast, middle, slow = endpoint[order]
        ratios = dict(largest_to_middle=float(fast / middle) if middle > 0 else None,
                      middle_to_smallest=float(middle / slow) if slow > 0 else None)
        # Avoid classifying roundoff at exactly the requested threshold as an excess.
        def exceeds(value, reference):
            boundary = threshold * reference
            return value > boundary and not np.isclose(value, boundary, rtol=1e-12, atol=0)

        if exceeds(fast, middle):
            status, selected, reason = "1d", names[order[0]], "Largest/middle endpoint MSD ratio exceeds threshold"
        elif exceeds(middle, slow):
            status = "2d"
            selected = "".join(axis for axis in names if names.index(axis) in order[:2])
            reason = "Middle/smallest endpoint MSD ratio exceeds threshold"
    row["anisotropy"] = dict(status=status, threshold=threshold,
                             min_msd_A2=float(min_msd_A2), endpoint_total_msd_A2=endpoint_total,
                             basis="last_msd_in_fit_window", time_ps=float(times[-1]),
                             endpoint_msd_A2=dict(zip(names, endpoint.tolist())),
                             sorted_axes=[names[i] for i in order],
                             ratios=ratios, unresolved_axes=unresolved, reason=reason)
    row["reduced_dimensional"] = None
    if mode in ("1d", "2d"):
        selected = axes
    if selected is None:
        return
    indices = [names.index(axis) for axis in selected]
    dimension = len(indices)
    projected = msd[:, indices].sum(axis=1)
    native = float(fitter(projected, times * 1000)[0])
    if not np.isfinite(native):
        raise RuntimeError("pymatgen returned non-finite projected diffusivity")
    diffusion = native * (3 / dimension) * 1e-4
    slope = sum(row["slope_A2_per_ps"][axis] for axis in selected)
    intercept = sum(row["intercept_A2"][axis] for axis in selected)
    variance = float(np.sum((projected - projected.mean()) ** 2))
    residual = float(np.sum((projected - (times * slope + intercept)) ** 2))
    row["reduced_dimensional"] = dict(
        dimension=dimension, axes=selected, selection="auto" if mode == "auto" else "manual",
        actual_fit_range_ps=row["actual_fit_range_ps"], samples=row["samples"],
        slope_A2_per_ps=slope, intercept_A2=intercept,
        r_squared=1 - residual / variance if variance > 0 else None,
        pymatgen_slope_floor_applied=bool(native <= 1e-15 / 60),
        diffusion_m2_s=diffusion, diffusion_cm2_s=diffusion * 1e4,
        conductivity_NE_S_m=factor * diffusion,
        conductivity_NE_S_cm=factor * diffusion / 100)


def fit_msd(msd_csv, *, fit_start_ps=None, fit_end_ps=None, temperature_K, volume_A3,
            ion_charge, species=None, output_json=None, overwrite=False,
            diffusion_mode="auto", axes="xy", anisotropy_threshold=10, min_msd_A2=1.0):
    """Fit MSD CSV and estimate uncorrelated Nernst–Einstein conductivity.

    Inclusive fit window in ps; None defaults to the first/last positive lag
    of each species/segment separately. Zero lag is excluded. A manual bound
    may be supplied on either side; this does not detect the diffusive regime.
    Positive temperature in K and fixed cell volume
    in Å³. ion_charge is a signed nonzero charge number (e.g. +1), or a dict
    mapping selected elements to charge numbers. species is a string/list or
    None (all CSV elements). Fits each segment separately, with a free intercept
    and at least three positive-lag samples. Calls pymatgen's native fitter
    with its defaults (max-mode, weights 1/lag, positive slope floor), after
    selecting the window. D_total=slope_total/6; D_axis=slope_axis/2.
    Slopes/intercepts describe the raw weighted line before its slope floor;
    r_squared remains ordinary, unweighted R² of the fitted line.
    Native slope-floor flags identify zero/negative slopes replaced by its
    small positive value; these results do not establish resolved diffusion.
    Returns SI and cm²/s diffusion, S/m and S/cm conductivity, and diagnostics.
    Optional JSON refuses overwrite by default. No uncertainty or correlation
    correction is inferred; R² alone does not establish a diffusive regime.

    diffusion_mode='auto' keeps 3D results, then checks Cartesian MSD at the
    last lag in the fit window: largest/middle > threshold adds 1D; otherwise
    middle/smallest > threshold adds 2D. All zero with the MSD gate disabled
    makes it indeterminate.
    Zero denominators are recorded as None; positive/zero triggers a supplement.
    Native slope-floor flags remain diagnostics, not evidence of diffusion.
    '3d' disables the check; '1d'/'2d' manually projects onto axes ('x'/'xy', etc.).
    axes must be distinct Cartesian letters, not crystallographic directions.
    Threshold must be finite and >1 (default 10); it is a heuristic, not a
    proof of dimensionality. Projected fits use the same lag window and native
    defaults, with D=slope/(2*d). Conductivity still uses the full volume.
    New anisotropy/reduced_dimensional and directional conductivity fields
    supplement, never replace, the original 3D fields. No source files change.
    min_msd_A2=1.0 skips auto supplements when endpoint total MSD is below
    this nonnegative Å² threshold (0 disables this gate). low_msd flags each
    curve; 3D results and manual 1D/2D fits remain available. This does not
    identify thermal vibration or establish a diffusion detection limit.
    """
    def finite(name, value, positive=False):
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not np.isfinite(value) or (positive and value <= 0)):
            raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
        return float(value)

    start = None if fit_start_ps is None else finite("fit_start_ps", fit_start_ps)
    end = None if fit_end_ps is None else finite("fit_end_ps", fit_end_ps)
    temperature = finite("temperature_K", temperature_K, True)
    volume = finite("volume_A3", volume_A3, True)
    threshold = _validate_dimension_options(diffusion_mode, axes, anisotropy_threshold, min_msd_A2)
    if type(overwrite) is not bool:
        raise TypeError("overwrite must be bool")
    source = Path(msd_csv).resolve()
    destination = None
    if output_json is not None:
        destination = Path(output_json)
        if destination.is_symlink() or destination.is_dir():
            raise FileExistsError(destination)
        destination = destination.resolve()
        if destination == source:
            raise ValueError("output_json cannot overwrite MSD input")
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)
    with source.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("MSD CSV is empty")
    available = {row["species"] for row in rows}
    if species is None:
        selected = available
    elif isinstance(species, str):
        selected = {species}
    elif isinstance(species, (list, tuple)) and all(isinstance(s, str) for s in species):
        selected = set(species)
    else:
        raise TypeError("species must be a string, list/tuple, or None")
    if not selected or not selected <= available:
        raise ValueError("Requested species absent from MSD CSV")
    charges = {}
    for element in selected:
        if isinstance(ion_charge, dict) and element not in ion_charge:
            raise ValueError(f"Missing ion_charge for {element}")
        charge = finite("ion_charge", ion_charge[element] if isinstance(ion_charge, dict) else ion_charge)
        if charge == 0:
            raise ValueError("ion_charge must be nonzero")
        charges[element] = charge
    groups = {}
    for row in rows:
        if row["species"] not in selected:
            continue
        segment = int(row["segment"])
        count = int(row["atom_count"])
        values = [float(row[key]) for key in
                  ("time_ps", "msd_x_A2", "msd_y_A2", "msd_z_A2", "msd_total_A2")]
        if segment < 1 or count < 1 or not np.all(np.isfinite(values)) or min(values) < 0:
            raise ValueError("Invalid segment, population, time or MSD")
        if not np.isclose(sum(values[1:4]), values[4], rtol=1e-7, atol=1e-10):
            raise ValueError("MSD total must equal x+y+z")
        groups.setdefault((segment, row["species"]), []).append((count, values))
    results = []
    totals = {}
    fitter = _load_pymatgen_fitter()
    for (segment, element), entries in sorted(groups.items()):
        counts = {entry[0] for entry in entries}
        data = np.asarray([entry[1] for entry in entries])
        data = data[np.argsort(data[:, 0])]
        if len(counts) != 1 or np.any(np.diff(data[:, 0]) <= 0):
            raise ValueError("Population must be constant and sample times unique")
        chosen = data[_fit_window_mask(data[:, 0], start, end)]
        x, y = chosen[:, 0], chosen[:, 1:]
        weights = 1 / x
        mean_x = np.average(x, weights=weights)
        mean_y = np.average(y, weights=weights, axis=0)
        centered = x - mean_x
        slopes = (centered * weights) @ (y - mean_y) / (weights @ centered**2)
        intercepts = mean_y - slopes * mean_x
        flat = np.ptp(y, axis=0) == 0
        slopes[flat] = 0
        intercepts[flat] = y[0, flat]
        residual = np.sum((y - (x[:, None] * slopes + intercepts)) ** 2, axis=0)
        variance = np.sum((y - y.mean(axis=0)) ** 2, axis=0)
        variance[flat] = 0
        r2 = [float(1 - r / v) if v > 0 else None for r, v in zip(residual, variance)]
        # Native defaults only. API takes fs, returns 3D D in cm²/s;
        # multiply directional outputs by 3 to obtain slope_axis/2.
        native = np.array([fitter(column, x * 1000)[0] for column in y.T])
        if not np.all(np.isfinite(native)):
            raise RuntimeError("pymatgen returned non-finite diffusivity")
        diffusion = float(native[3] * 1e-4)
        count = counts.pop()
        factor = count / (volume * 1e-30) * (charges[element] * 1.602176634e-19) ** 2 / (1.380649e-23 * temperature)
        conductivity = factor * diffusion
        results.append(dict(segment=segment, species=element, atom_count=count,
                            ion_charge=charges[element], samples=len(chosen),
                            actual_fit_range_ps=[float(x[0]), float(x[-1])],
                            slope_A2_per_ps=dict(zip(("x", "y", "z", "total"), slopes.tolist())),
                            intercept_A2=dict(zip(("x", "y", "z", "total"), intercepts.tolist())),
                            r_squared=dict(zip(("x", "y", "z", "total"), r2)),
                            pymatgen_slope_floor_applied=dict(zip(
                                ("x", "y", "z", "total"), (native <= 1e-15 / 60).tolist())),
                            diffusion_m2_s=diffusion, diffusion_cm2_s=diffusion * 1e4,
                            directional_diffusion_m2_s=(native[:3] * 3e-4).tolist(),
                            conductivity_NE_S_m=conductivity, conductivity_NE_S_cm=conductivity / 100))
        _add_dimensional_transport(results[-1], x, y, fitter, diffusion_mode,
                                   axes, threshold, factor, min_msd_A2)
        totals[segment] = totals.get(segment, 0.0) + conductivity
    # A partial species sum must never be labeled as the complete selected sum.
    for segment in totals:
        if {r["species"] for r in results if r["segment"] == segment} != selected:
            raise ValueError("Every segment must contain all selected species")
    result = dict(msd_csv=str(source), fit_range_ps=[start, end], temperature_K=temperature,
                  volume_A3=volume, fit_method="pymatgen", fit_weighting="1/lag",
                  diffusion_mode=diffusion_mode, anisotropy_threshold=threshold,
                  min_msd_A2=float(min_msd_A2),
                  method="Einstein free-intercept pymatgen WLS; Nernst-Einstein",
                  results=results, conductivity_NE_sum_S_m={str(k): v for k, v in totals.items()},
                  limitations="Uncorrelated estimate; no uncertainty or diffusive-regime detection; "
                              "endpoint MSD dimensional screen is heuristic, not proof of diffusion")
    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w" if overwrite else "x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
    return result

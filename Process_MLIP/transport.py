"""Fit exported MSD using NumPy least squares; no model or trajectory loading."""
import csv
import json
from numbers import Real
from pathlib import Path

import numpy as np


def fit_msd(msd_csv, *, fit_start_ps, fit_end_ps, temperature_K, volume_A3,
            ion_charge, species=None, output_json=None, overwrite=False):
    """Fit MSD CSV and estimate uncorrelated Nernst–Einstein conductivity.

    Inclusive fit window in ps; positive temperature in K and fixed cell volume
    in Å³. ion_charge is a signed nonzero charge number (e.g. +1), or a dict
    mapping selected elements to charge numbers. species is a string/list or
    None (all CSV elements). Fits each segment separately, with a free intercept
    and at least three samples. D_total=slope_total/6; D_axis=slope_axis/2.
    Returns SI and cm²/s diffusion, S/m and S/cm conductivity, and diagnostics.
    Optional JSON refuses overwrite by default. No uncertainty or correlation
    correction is inferred; R² alone does not establish a diffusive regime.
    """
    def finite(name, value, positive=False):
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not np.isfinite(value) or (positive and value <= 0)):
            raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
        return float(value)

    start = finite("fit_start_ps", fit_start_ps)
    end = finite("fit_end_ps", fit_end_ps)
    temperature = finite("temperature_K", temperature_K, True)
    volume = finite("volume_A3", volume_A3, True)
    if start < 0 or end <= start:
        raise ValueError("Require 0 <= fit_start_ps < fit_end_ps")
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
    for (segment, element), entries in sorted(groups.items()):
        counts = {entry[0] for entry in entries}
        data = np.asarray([entry[1] for entry in entries])
        data = data[np.argsort(data[:, 0])]
        if len(counts) != 1 or np.any(np.diff(data[:, 0]) <= 0):
            raise ValueError("Population must be constant and sample times unique")
        if start < data[0, 0] or end > data[-1, 0]:
            raise ValueError("Fit window must lie within every selected segment")
        chosen = data[(data[:, 0] >= start) & (data[:, 0] <= end)]
        if len(chosen) < 3:
            raise ValueError("Fit window needs at least three MSD samples")
        x, y = chosen[:, 0], chosen[:, 1:]
        centered = x - x.mean()
        slopes = centered @ (y - y.mean(axis=0)) / (centered @ centered)
        intercepts = y.mean(axis=0) - slopes * x.mean()
        residual = np.sum((y - (x[:, None] * slopes + intercepts)) ** 2, axis=0)
        variance = np.sum((y - y.mean(axis=0)) ** 2, axis=0)
        r2 = [float(1 - r / v) if v > 0 else None for r, v in zip(residual, variance)]
        if slopes[3] < 0:
            raise ValueError("Negative total MSD slope: choose a physical diffusion fit window")
        # Å²/ps = 1e-8 m²/s; SI exact elementary charge and Boltzmann constant.
        diffusion = float(slopes[3] / 6 * 1e-8)
        count = counts.pop()
        conductivity = count / (volume * 1e-30) * (charges[element] * 1.602176634e-19) ** 2 * diffusion / (1.380649e-23 * temperature)
        results.append(dict(segment=segment, species=element, atom_count=count,
                            ion_charge=charges[element], samples=len(chosen),
                            actual_fit_range_ps=[float(x[0]), float(x[-1])],
                            slope_A2_per_ps=dict(zip(("x", "y", "z", "total"), slopes.tolist())),
                            intercept_A2=dict(zip(("x", "y", "z", "total"), intercepts.tolist())),
                            r_squared=dict(zip(("x", "y", "z", "total"), r2)),
                            diffusion_m2_s=diffusion, diffusion_cm2_s=diffusion * 1e4,
                            directional_diffusion_m2_s=(slopes[:3] / 2 * 1e-8).tolist(),
                            conductivity_NE_S_m=conductivity, conductivity_NE_S_cm=conductivity / 100))
        totals[segment] = totals.get(segment, 0.0) + conductivity
    # A partial species sum must never be labeled as the complete selected sum.
    for segment in totals:
        if {r["species"] for r in results if r["segment"] == segment} != selected:
            raise ValueError("Every segment must contain all selected species")
    result = dict(msd_csv=str(source), fit_range_ps=[start, end], temperature_K=temperature,
                  volume_A3=volume, method="Einstein free-intercept OLS; Nernst-Einstein",
                  results=results, conductivity_NE_sum_S_m={str(k): v for k, v in totals.items()},
                  limitations="Uncorrelated estimate; no uncertainty or diffusive-regime detection")
    if destination is not None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w" if overwrite else "x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, allow_nan=False)
    return result

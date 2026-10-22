"""Framework displacement, ASE RDF and optional cutoff coordination evidence."""
from numbers import Integral, Real
from pathlib import Path
from typing import Iterable

import numpy as np
from ase import Atoms
from ase.data import atomic_numbers
from ase.geometry.rdf import get_rdf
from ase.neighborlist import neighbor_list

from ..models import ValidationResult
from .trajectory import read_positions


def validate_framework(
    trajectory: str | Path | Iterable[Atoms],
    *,
    mobile_species: tuple[str, ...] = ("Li", "Na"),
    coordinate_mode: str = "unwrapped",
    rdf_rmax_A: float | None = None,
    rdf_bins: int = 75,
    coordination_cutoff_A: float | None = None,
    rdf_window_fraction: float | None = None,
    rdf_frames_per_window: int = 5,
    rdf_repeat: tuple[int, int, int] = (1, 1, 1),
) -> ValidationResult:
    """Compare a fixed-cell trajectory's non-mobile framework with its start.

    Framework MSD (angstrom squared) removes the mass-weighted framework
    center-of-mass translation; framework_drift_A records that translation.
    RDFs use ASE's framework-only number-density normalization. Their
    relative L1 difference integrates the uniform histogram bins; an empty
    initial RDF gives None, not a zero difference. The default radius is
    0.45 times the smallest perpendicular cell height after rdf_repeat, and
    any explicit radius must be strictly below half that height. Repetition
    adds periodic images only for RDF snapshots; MSD, drift and coordination
    use the original trajectory. Images add no independent sampling and do
    not establish finite-size convergence.

    Optional coordination counts framework-only neighbors within the given
    scalar cutoff, including periodic images as handled by ASE. Its change
    fraction compares each framework atom's initial and final counts.
    With rdf_window_fraction, average at most rdf_frames_per_window evenly
    spaced snapshots in the first/last fraction of the trajectory. This
    bounds RDF cost independently of the number of saved frames. None
    retains the original endpoint comparison.

    Thermal broadening, finite sampling, reference choice and
    cutoff choice affect these diagnostics. No stability verdict is made.
    """
    if isinstance(mobile_species, str):
        raise ValueError("mobile_species must be a collection of element symbols")
    mobile = tuple(mobile_species)
    if any(not isinstance(symbol, str) or atomic_numbers.get(symbol, 0) <= 0 for symbol in mobile):
        raise ValueError("mobile_species must contain real element symbols")
    if isinstance(rdf_bins, bool) or not isinstance(rdf_bins, Integral) or rdf_bins <= 0:
        raise ValueError("rdf_bins must be a positive integer")
    if (not isinstance(rdf_repeat, tuple) or len(rdf_repeat) != 3
            or any(isinstance(value, bool) or not isinstance(value, Integral) or value <= 0
                   for value in rdf_repeat)):
        raise ValueError("rdf_repeat must be a tuple of three positive integers")
    if (isinstance(rdf_frames_per_window, bool) or not isinstance(rdf_frames_per_window, Integral)
            or rdf_frames_per_window <= 0):
        raise ValueError("rdf_frames_per_window must be a positive integer")
    if rdf_window_fraction is not None and (
        isinstance(rdf_window_fraction, bool) or not isinstance(rdf_window_fraction, Real)
        or not np.isfinite(rdf_window_fraction) or not 0 < rdf_window_fraction <= 0.5
    ):
        raise ValueError("rdf_window_fraction must be in (0, 0.5] or None")
    for name, value in (("rdf_rmax_A", rdf_rmax_A),
                        ("coordination_cutoff_A", coordination_cutoff_A)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, Real)
                                  or not np.isfinite(value) or value <= 0):
            raise ValueError(f"{name} must be finite and positive")

    first, positions = read_positions(trajectory, coordinate_mode=coordinate_mode)
    if len(positions) < 2:
        raise ValueError("Framework diagnostics require at least two frames")
    mask = np.array([symbol not in mobile for symbol in first.get_chemical_symbols()])
    if not np.any(mask):
        raise ValueError("No framework atoms remain after excluding mobile_species")
    masses = first.get_masses()[mask]
    if not np.all(np.isfinite(masses)) or np.any(masses <= 0):
        raise ValueError("Framework masses must be finite and positive")
    displacement = positions[:, mask] - positions[0, mask]
    drift = np.average(displacement, axis=1, weights=masses)
    centered = displacement - drift[:, None, :]
    curve = np.mean(np.sum(centered**2, axis=2), axis=1)

    rdf_cell = first.cell.array * np.asarray(rdf_repeat)[:, None]
    min_height = float(np.min(1 / np.linalg.norm(np.linalg.inv(rdf_cell), axis=0)))
    rmax = 0.45 * min_height if rdf_rmax_A is None else float(rdf_rmax_A)
    if rmax >= 0.5 * min_height:
        raise ValueError("rdf_rmax_A must be smaller than half the minimum cell height")
    initial = first[mask]
    initial.set_positions(positions[0, mask])
    final = initial.copy()
    final.set_positions(positions[-1, mask])
    width = 1 if rdf_window_fraction is None else max(1, int(len(positions) * rdf_window_fraction))
    offsets = np.unique(np.linspace(0, width - 1, min(width, rdf_frames_per_window), dtype=int))
    early_frames = offsets
    late_frames = len(positions) - width + offsets

    def average_rdf(indices):
        curves = []
        snapshot = initial.copy()
        for index in indices:
            snapshot.positions = positions[index, mask]
            rdf_snapshot = snapshot if rdf_repeat == (1, 1, 1) else snapshot.repeat(rdf_repeat)
            values, radii = get_rdf(rdf_snapshot, rmax=rmax, nbins=int(rdf_bins))
            curves.append(values)
        return np.mean(curves, axis=0), radii

    rdf_initial, radii = average_rdf(early_frames)
    rdf_final, _ = average_rdf(late_frames)
    diagnostics = [
        "RDFs are finite-frame samples; thermal broadening and the initial reference affect comparison.",
        "Framework MSD removes mass-weighted framework translation; these values are not a stability verdict.",
    ]
    if rdf_window_fraction is not None:
        diagnostics.append("RDFs average bounded snapshots in early/late trajectory windows; this is not a melting test.")
    if rdf_repeat != (1, 1, 1):
        diagnostics.append("RDF periodic images add no independent samples and do not establish finite-size convergence.")
    # Both RDFs use identical uniform bins, so bin widths cancel in the ratio.
    rdf_weight = float(np.sum(rdf_initial))
    rdf_difference = None
    if rdf_weight > 0:
        rdf_difference = float(np.sum(np.abs(rdf_final - rdf_initial)) / rdf_weight)
    else:
        diagnostics.append("Initial framework RDF has no signal within rmax; relative difference is undefined.")

    changed = initial_mean = final_mean = None
    if coordination_cutoff_A is None:
        diagnostics.append("Coordination was not evaluated: supply an explicit framework-only cutoff in angstrom.")
    else:
        counts = [np.bincount(neighbor_list("i", atoms, float(coordination_cutoff_A)),
                              minlength=len(initial)) for atoms in (initial, final)]
        changed = float(np.mean(counts[0] != counts[1]))
        initial_mean, final_mean = (float(np.mean(count)) for count in counts)
        diagnostics.append("Framework-only coordination is cutoff dependent; counts include periodic images.")
    return ValidationResult(
        framework_species=tuple(sorted(set(initial.get_chemical_symbols()))),
        framework_msd_A2=float(curve[-1]), framework_msd_curve_A2=curve.tolist(),
        framework_drift_A=drift.tolist(), rdf_difference=rdf_difference,
        rdf_r_A=radii.tolist(), rdf_initial=rdf_initial.tolist(), rdf_final=rdf_final.tolist(),
        coordination_change_fraction=changed, coordination_initial_mean=initial_mean,
        coordination_final_mean=final_mean, diagnostics=diagnostics,
        rdf_reference_frames=early_frames.tolist(), rdf_final_frames=late_frames.tolist(),
        rdf_repeat=rdf_repeat,
    )

"""Optional kinisi 2.1+ self-diffusion posterior and Nernst--Einstein intervals."""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
import inspect
from math import ceil, floor, isfinite
from numbers import Integral, Real
from pathlib import Path
from typing import Iterable
import warnings

import numpy as np
from ase import Atoms
from ase.data import atomic_numbers

from .trajectory import read_positions


@dataclass
class UncertaintyResult:
    """Equal-tailed posterior intervals; estimated does not mean converged.

    n_posterior counts retained walker samples, not independent samples.
    The NE interval propagates the D posterior with fixed N/V, T and charge;
    it excludes their uncertainty, collective correlations and model error.
    """

    species: str
    axes: str
    fit_start_ps: float
    fit_end_ps: float
    credible_mass: float
    n_mobile_atoms: int
    seed: int
    method: str = "kinisi Bayesian self-diffusion; Nernst-Einstein"
    status: str = "estimated"
    diffusion_median_cm2_s: float | None = None
    diffusion_lower_cm2_s: float | None = None
    diffusion_upper_cm2_s: float | None = None
    conductivity_NE_median_S_cm: float | None = None
    conductivity_NE_lower_S_cm: float | None = None
    conductivity_NE_upper_S_cm: float | None = None
    relative_half_width: float | None = None
    n_posterior: int = 0
    diagnostics: list[str] = field(default_factory=list)


def _load_kinisi():
    message = "Uncertainty analysis requires kinisi>=2.1,<3 and its dependencies in a separate NumPy>=2 environment"
    try:
        installed = version("kinisi")
        release = tuple(int(part) for part in installed.split(".")[:2])
    except (PackageNotFoundError, ValueError) as exc:
        raise ImportError(message) from exc
    if not (2, 1) <= release < (3, 0) or np.lib.NumpyVersion(np.__version__) < "2.0.0":
        raise ImportError(f"{message}; found kinisi {installed}, NumPy {np.__version__}")
    try:
        import scipp as sc
        from kinisi.analyze import DiffusionAnalyzer
    except ImportError as exc:
        raise ImportError(message) from exc
    for name, required in (
        ("from_ase", {"specie", "time_step", "step_skip", "dt", "dimension", "progress"}),
        ("diffusion", {"start_dt", "n_samples", "random_state", "progress"}),
    ):
        method = getattr(DiffusionAnalyzer, name, None)
        if not callable(method) or not required <= inspect.signature(method).parameters.keys():
            raise ImportError(f"{message}; the installed public API is unsupported")
    return DiffusionAnalyzer, sc


def check_uncertainty_backend() -> None:
    """Check the optional kinisi environment/API without trajectory analysis or MCMC."""
    _load_kinisi()


def analyze_diffusion_uncertainty(
    trajectory: str | Path | Iterable[Atoms],
    *,
    species: str,
    frame_interval_ps: float,
    fit_start_ps: float,
    fit_end_ps: float,
    temperature_K: float,
    volume_A3: float,
    ion_charge: float = 1,
    axes: str = "xyz",
    credible_mass: float = 0.95,
    n_samples: int = 1000,
    seed: int = 42,
    max_lags: int = 60,
) -> UncertaintyResult:
    """Use native kinisi ASE parsing and Bayesian diffusion on a bounded lag grid.

    Input positions must be continuous, fixed-cell, uniformly saved and 3D
    periodic. Supply production frames only; fit bounds refer to lag time,
    not absolute simulation time. At most max_lags integer-frame lags in
    the inclusive requested window are passed to kinisi, so no lag beyond
    fit_end_ps enters the regression. Actual grid bounds are returned.

    Kinisi rewraps/reconstructs ASE input. Its native displacement is checked
    against the supplied continuous displacement, rejecting ambiguous large
    saved-frame jumps rather than silently aliasing them. No custom unwrap,
    MSD or Bayesian regression is implemented here.

    Kinisi subtracts the arithmetic mean displacement of all non-selected
    atoms (no drift correction when there are none). This differs from
    Process_MLIP's mass-weighted framework correction, especially with other
    mobile species in the reference. No automatic reference matching occurs.

    n_samples is kinisi's MCMC-step option; burn-in, walkers and thinning
    retain its defaults. MCMC convergence, a diffusive regime, time/size
    convergence and model accuracy are not established by these intervals.
    NumPy's legacy RNG state is restored after kinisi's seeded call; avoid
    concurrent in-process calls because the native sampler uses global RNG.
    """
    if not isinstance(species, str) or atomic_numbers.get(species, 0) <= 0:
        raise ValueError("species must be one real element symbol")
    if (not isinstance(axes, str) or not axes or len(set(axes)) != len(axes)
            or set(axes) - set("xyz")):
        raise ValueError("axes must contain distinct Cartesian x/y/z letters")
    axes = "".join(axis for axis in "xyz" if axis in axes)
    for name, value in (("frame_interval_ps", frame_interval_ps), ("fit_start_ps", fit_start_ps),
                        ("fit_end_ps", fit_end_ps), ("temperature_K", temperature_K),
                        ("volume_A3", volume_A3), ("ion_charge", ion_charge),
                        ("credible_mass", credible_mass)):
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if frame_interval_ps <= 0 or temperature_K <= 0 or volume_A3 <= 0 or ion_charge == 0:
        raise ValueError("Frame interval, temperature and volume must be positive; ion_charge must be nonzero")
    if fit_start_ps < 0 or fit_end_ps <= fit_start_ps:
        raise ValueError("Fit bounds must be nonnegative and strictly increasing")
    if not 0 < credible_mass < 1:
        raise ValueError("credible_mass must lie strictly between zero and one")
    for name, value, minimum in (("n_samples", n_samples, 10), ("max_lags", max_lags, 3), ("seed", seed, 0)):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    if seed >= 2**32:
        raise ValueError("seed must be smaller than 2**32 for kinisi RandomState")

    analyzer_class, sc = _load_kinisi()
    first, positions = read_positions(trajectory, coordinate_mode="unwrapped")
    count = first.get_chemical_symbols().count(species)
    if count == 0:
        raise ValueError(f"Requested species {species} is absent")
    if not np.isclose(volume_A3, first.get_volume(), rtol=1e-6, atol=1e-8):
        raise ValueError("volume_A3 must match the fixed trajectory cell volume")
    result = UncertaintyResult(
        species=species, axes=axes, fit_start_ps=float(fit_start_ps), fit_end_ps=float(fit_end_ps),
        credible_mass=float(credible_mass), n_mobile_atoms=count, seed=int(seed),
        diagnostics=[
            "MCMC convergence and effective independent posterior sample count were not checked.",
            "Credible intervals are conditional on the chosen diffusive window and kinisi covariance model; time/size/model error is excluded.",
            "reference_difference: kinisi uses arithmetic-mean displacement of all non-selected atoms; Process_MLIP framework correction is mass weighted.",
            "sigma_NE propagates the self-diffusion posterior at fixed N/V, T and charge; it is not collective conductivity.",
            "Saved-frame spacing is supplied by the caller and must be uniform.",
        ],
    )
    if count == len(first):
        result.diagnostics.append("No non-selected atoms exist; kinisi applies no framework drift correction.")
    lower = max(1, ceil(fit_start_ps / frame_interval_ps - 1e-10))
    upper = floor(fit_end_ps / frame_interval_ps + 1e-10)
    if upper > len(positions) - 1 or upper - lower + 1 < 3:
        result.status = "insufficient_data"
        result.diagnostics.append("Requested window is not covered or contains fewer than three positive frame lags.")
        return result
    lag_indices = np.unique(np.linspace(lower, upper, min(int(max_lags), upper - lower + 1), dtype=int))
    lag_times = lag_indices * float(frame_interval_ps)
    result.fit_start_ps, result.fit_end_ps = float(lag_times[0]), float(lag_times[-1])
    frames = []
    for points in positions:
        atoms = first.copy()
        atoms.positions = points
        frames.append(atoms)

    state = np.random.get_state()
    captured = []
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            analyzer = analyzer_class.from_ase(
                frames, specie=species, time_step=sc.scalar(float(frame_interval_ps), unit="ps"),
                step_skip=sc.scalar(1, unit="dimensionless"),
                dt=sc.array(dims=["time interval"], values=lag_times, unit="ps"),
                dimension=axes, distance_unit=sc.units.angstrom, progress=False,
            )
            native = np.asarray(sc.to_unit(analyzer.trajectory.disp, unit="angstrom").values)
            if native.shape != positions.shape or not np.allclose(native, positions - positions[0], rtol=1e-8, atol=1e-7):
                raise ValueError("Kinisi periodic reconstruction differs from continuous input; save frames more frequently or inspect the cell")
            native_msd = np.asarray(analyzer.msd.values)
            if not np.isfinite(native_msd).all() or np.ptp(native_msd) == 0:
                result.status = "unresolved"
                result.diagnostics.append("Native MSD is non-finite or flat; no posterior diffusion estimate was computed.")
                return result
            analyzer.diffusion(
                start_dt=sc.scalar(result.fit_start_ps, unit="ps"), n_samples=int(n_samples),
                random_state=np.random.RandomState(int(seed)), progress=False,
            )
            diffusion = sc.to_unit(analyzer.D, unit="cm^2/s")
            density = sc.scalar(count / float(volume_A3), unit="1/angstrom^3")
            charge = sc.scalar(float(ion_charge) * 1.602176634e-19, unit="C")
            thermal = sc.scalar(1.380649e-23 * float(temperature_K), unit="J")
            conductivity = sc.to_unit(density * charge**2 * diffusion / thermal, unit="S/cm")
    except (np.linalg.LinAlgError, FloatingPointError) as exc:
        result.status = "unresolved"
        result.diagnostics.append(f"Kinisi numerical inference failed: {type(exc).__name__}: {exc}")
        return result
    finally:
        np.random.set_state(state)
        result.diagnostics.extend(f"kinisi warning: {item.message}" for item in captured)

    d_samples = np.asarray(diffusion.values, dtype=float).reshape(-1)
    s_samples = np.asarray(conductivity.values, dtype=float).reshape(-1)
    result.n_posterior = len(d_samples)
    if (not len(d_samples) or d_samples.shape != s_samples.shape
            or not np.isfinite(d_samples).all() or not np.isfinite(s_samples).all()
            or np.any(d_samples < 0) or np.any(s_samples < 0)):
        result.status = "unresolved"
        result.diagnostics.append("Kinisi returned an empty, invalid or non-finite posterior.")
        return result
    tail = (1 - float(credible_mass)) / 2
    low, median, high = (float(value) for value in np.quantile(d_samples, [tail, 0.5, 1 - tail]))
    if median <= 0:
        result.status = "unresolved"
        result.diagnostics.append("Posterior diffusion median is nonpositive; relative interval width is undefined.")
        return result
    result.diffusion_lower_cm2_s, result.diffusion_median_cm2_s, result.diffusion_upper_cm2_s = low, median, high
    s_low, s_median, s_high = (float(value) for value in np.quantile(s_samples, [tail, 0.5, 1 - tail]))
    result.conductivity_NE_lower_S_cm = s_low
    result.conductivity_NE_median_S_cm = s_median
    result.conductivity_NE_upper_S_cm = s_high
    result.relative_half_width = (high - low) / (2 * median)
    return result

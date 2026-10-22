"""pymatgen-diffusion analysis contracts and an Einstein unit conversion."""
from __future__ import annotations

import csv
from math import isfinite
from numbers import Integral, Real
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

import numpy as np
from ase import Atoms
from ase.data import atomic_numbers
from ase.io import read
from ase.io.trajectory import Trajectory

from ..models import DiffusionResult, MSDResult
from ..io import save_csv
from .trajectory import read_positions


def export_msd(
    trajectory, output_csv, *, species=None, frame_interval_fs=None,
    skip_frames=0, number_of_segments=1, unwrap=False, drift_reference=None,
    overwrite=False, min_obs=30,
):
    """Call Process_MLIP.export_msd with its existing signature and semantics.

    Time spacing is in fs here. Its continuous MD trajectories use
    unwrap=False. The legacy unwrap=True route currently uses ASE MIC;
    a future native-pymatgen route belongs in Process_MLIP itself.
    """
    from Process_MLIP.msd import export_msd as implementation

    return implementation(
        trajectory, output_csv, species=species, frame_interval_fs=frame_interval_fs,
        skip_frames=skip_frames, number_of_segments=number_of_segments, unwrap=unwrap,
        drift_reference=drift_reference, overwrite=overwrite, min_obs=min_obs,
    )


def fit_msd(
    msd_csv, *, fit_start_ps=None, fit_end_ps=None, temperature_K, volume_A3,
    ion_charge, species=None, output_json=None, overwrite=False,
    diffusion_mode="auto", axes="xy", anisotropy_threshold=10, min_msd_A2=1.0,
):
    """Call Process_MLIP.fit_msd, retaining raw diagnostics and units.

    These existing dictionary results are not a confidence verdict. Read
    low_msd/slope-floor flags and the upstream limitations before using D.
    """
    from Process_MLIP.transport import fit_msd as implementation

    return implementation(
        msd_csv, fit_start_ps=fit_start_ps, fit_end_ps=fit_end_ps,
        temperature_K=temperature_K, volume_A3=volume_A3, ion_charge=ion_charge,
        species=species, output_json=output_json, overwrite=overwrite,
        diffusion_mode=diffusion_mode, axes=axes,
        anisotropy_threshold=anisotropy_threshold, min_msd_A2=min_msd_A2,
    )


def diffusion_from_slope(slope_A2_per_ps: float, *, dimensions: int = 3) -> float:
    """Convert a summed d-dimensional MSD slope to D in cm²/s.

    D = slope / (2*d); 1 Å²/ps = 1e-4 cm²/s. This is only a unit
    conversion, not evidence for long-range diffusion or size convergence.
    Negative/unresolved fitted slopes should be diagnosed by the fitter,
    not replaced with a small positive diffusivity here.
    """
    if (isinstance(slope_A2_per_ps, bool) or not isinstance(slope_A2_per_ps, Real)
            or not isfinite(slope_A2_per_ps) or slope_A2_per_ps < 0):
        raise ValueError("slope_A2_per_ps must be finite and nonnegative")
    if (isinstance(dimensions, bool) or not isinstance(dimensions, Integral)
            or dimensions not in (1, 2, 3)):
        raise ValueError("dimensions must be 1, 2 or 3")
    return float(slope_A2_per_ps / (2 * dimensions) * 1e-4)


def calculate_msd(
    trajectory: str | Path | Iterable[Atoms],
    *,
    species: str = "Li",
    frame_interval_ps: float,
    axes: str = "xyz",
    coordinate_mode: str = "unwrapped",
    drift_reference: str | None = None,
    min_obs: int = 30,
) -> MSDResult:
    """Adapt existing multi-origin MSD into data, without retaining temporary files.

    Fixed cell and uniformly spaced frames are required. Process_MLIP MD
    uses unwrapped coordinates. Wrapped snapshots are reconstructed by
    native pymatgen Trajectory before calling the existing MSD backend.
    axes selects Cartesian components to sum, not crystallographic axes.
    """
    if not isinstance(axes, str) or not axes or len(set(axes)) != len(axes) or set(axes) - set("xyz"):
        raise ValueError("axes must contain distinct Cartesian x/y/z letters")
    if (isinstance(frame_interval_ps, bool) or not isinstance(frame_interval_ps, Real)
            or not isfinite(frame_interval_ps) or frame_interval_ps <= 0):
        raise ValueError("frame_interval_ps must be finite and positive")
    if coordinate_mode not in ("unwrapped", "wrapped"):
        raise ValueError("coordinate_mode must be unwrapped or wrapped")
    if not isinstance(species, str) or atomic_numbers.get(species, 0) <= 0:
        raise ValueError("species must be one real element symbol")
    with TemporaryDirectory(prefix="process_md_msd_") as directory:
        root = Path(directory)
        if isinstance(trajectory, (str, Path)) and coordinate_mode == "unwrapped":
            source = Path(trajectory)
            first = read(source, index=0)
            if not first.pbc.all():
                raise ValueError("MSD requires full 3D PBC")
        else:
            first, positions = read_positions(trajectory, coordinate_mode=coordinate_mode)
            source = root / "continuous.traj"
            with Trajectory(source, "w") as output:
                for points in positions:
                    atoms = first.copy()
                    atoms.positions = points
                    output.write(atoms)
        destination = root / "msd.csv"
        metadata = export_msd(
            source, destination, species=species, frame_interval_fs=frame_interval_ps * 1000,
            unwrap=False, drift_reference=drift_reference, min_obs=min_obs,
        )
        with destination.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        components = np.array([[float(row[f"msd_{axis}_A2"]) for axis in "xyz"] for row in rows])
        indices = ["xyz".index(axis) for axis in axes]
        return MSDResult(
            species=species, axes=axes, time_ps=[float(row["time_ps"]) for row in rows],
            msd_A2=components[:, indices].sum(axis=1).tolist(), components_A2=components.tolist(),
            n_mobile_atoms=int(rows[0]["atom_count"]), frame_interval_ps=float(frame_interval_ps),
            coordinate_mode=coordinate_mode, drift_reference=drift_reference,
            method=metadata["method"],
            n_frames=int(metadata["frame_count"]),
            trajectory_duration_ps=(int(metadata["frame_count"]) - 1) * float(frame_interval_ps),
            volume_A3=float(first.get_volume()),
            diagnostics=["Multi-origin lag samples are correlated; independent-sample uncertainty was not evaluated.",
                         "Saved-frame spacing is supplied by the caller and must be uniform."],
        )


def fit_diffusion(
    msd: MSDResult,
    *,
    fit_start_ps: float,
    fit_end_ps: float,
    temperature_K: float,
    volume_A3: float,
    ion_charge: float = 1,
) -> DiffusionResult:
    """Reuse the existing fit and label Nernst–Einstein conductivity (S/cm).

    Requires the actual temperature, cell volume and ion charge. A backend
    slope floor/zero or negative raw slope gives D/sigma=None. Positive fits
    remain estimates: long-range transport, time/size convergence and
    uncertainty are not established by this function or by R².
    """
    if msd.components_A2 is None:
        raise ValueError("MSD components are required; use calculate_msd")
    if (not isinstance(msd.axes, str) or not msd.axes or len(set(msd.axes)) != len(msd.axes)
            or set(msd.axes) - set("xyz")):
        raise ValueError("MSD axes must contain distinct Cartesian x/y/z letters")
    xyz = np.asarray(msd.components_A2, dtype=float)
    times = np.asarray(msd.time_ps, dtype=float)
    if xyz.shape != (len(times), 3) or not np.isfinite(xyz).all() or not np.isfinite(times).all():
        raise ValueError("MSD time/components must be finite arrays of matching length")
    if (np.any(xyz < 0) or np.any(times < 0) or np.any(np.diff(times) <= 0)
            or isinstance(msd.n_mobile_atoms, bool) or not isinstance(msd.n_mobile_atoms, Integral)
            or msd.n_mobile_atoms <= 0):
        raise ValueError("MSD needs nonnegative values, increasing lag times and a positive ion count")
    projected = xyz[:, ["xyz".index(axis) for axis in msd.axes]].sum(axis=1)
    if np.shape(msd.msd_A2) != projected.shape or not np.allclose(msd.msd_A2, projected, rtol=1e-9, atol=1e-12):
        raise ValueError("MSD curve does not match its selected components")
    rows = [dict(segment=1, time_ps=float(time), species=msd.species, atom_count=msd.n_mobile_atoms,
                 msd_x_A2=float(values[0]), msd_y_A2=float(values[1]), msd_z_A2=float(values[2]),
                 msd_total_A2=float(values.sum())) for time, values in zip(times, xyz)]
    dimension = len(msd.axes)
    with TemporaryDirectory(prefix="process_md_fit_") as directory:
        table = save_csv(rows, Path(directory) / "msd.csv")
        fitted = fit_msd(
            table, fit_start_ps=fit_start_ps, fit_end_ps=fit_end_ps,
            temperature_K=temperature_K, volume_A3=volume_A3, ion_charge=ion_charge,
            species=msd.species, diffusion_mode=f"{dimension}d", axes=msd.axes,
        )["results"][0]
    chosen = fitted if dimension == 3 else fitted["reduced_dimensional"]
    slope = chosen["slope_A2_per_ps"] if dimension != 3 else fitted["slope_A2_per_ps"]["total"]
    r_squared = chosen["r_squared"] if dimension != 3 else fitted["r_squared"]["total"]
    floor = chosen["pymatgen_slope_floor_applied"] if dimension != 3 else fitted["pymatgen_slope_floor_applied"]["total"]
    resolved_slope = not floor and slope > 0
    diagnostics = list(msd.diagnostics) + [
        "sigma_NE is an uncorrelated Nernst-Einstein estimate, not collective charge conductivity.",
        "Statistical sufficiency, long-range diffusion and cell/time convergence remain unassessed.",
    ]
    if not resolved_slope:
        diagnostics.append("Raw slope is nonpositive or the backend applied a slope floor; D and sigma_NE are unresolved.")
    return DiffusionResult(
        diffusion_cm2_s=float(chosen["diffusion_cm2_s"]) if resolved_slope else None,
        conductivity_NE_S_cm=float(chosen["conductivity_NE_S_cm"]) if resolved_slope else None,
        fit_start_ps=float(chosen["actual_fit_range_ps"][0]),
        fit_end_ps=float(chosen["actual_fit_range_ps"][1]), r_squared=r_squared,
        slope_A2_per_ps=float(slope), temperature_K=float(temperature_K), volume_A3=float(volume_A3),
        ion_charge=float(ion_charge), n_mobile_atoms=msd.n_mobile_atoms, axes=msd.axes,
        species=msd.species, observation_duration_ps=msd.trajectory_duration_ps,
        diagnostics=diagnostics,
    )

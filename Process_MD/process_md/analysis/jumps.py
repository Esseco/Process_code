"""Optional native GEMDAT site transitions and residence-filtered jumps."""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
import inspect
from math import ceil, isfinite
from numbers import Real
from pathlib import Path
from typing import Iterable
import warnings

import numpy as np
from ase import Atoms
from ase.data import atomic_numbers

from ..structure import estimate_hop_distance
from .trajectory import read_positions


@dataclass
class JumpResult:
    """Observed site jumps, conditional on a supplied or first-frame site map.

    Coverage is the fraction of ion-frame samples assigned to an outer site;
    minimum_ion_site_coverage is the lowest individual ion coverage. Counts
    are None when unresolved, rather than a claim of zero jumps. Estimated
    counts establish neither independent events nor long-range diffusion.
    """

    species: str
    frame_interval_ps: float
    min_residence_ps: float
    site_inner_fraction: float
    n_mobile_atoms: int
    n_sites: int
    n_frames: int
    reference_source: str
    backend_version: str
    site_radius_A: float | None = None
    status: str = "insufficient_data"
    n_jumps: int | None = None
    n_jumping_ions: int | None = None
    site_coverage: float | None = None
    minimum_ion_site_coverage: float | None = None
    max_unmapped_duration_ps: float | None = None
    events: list[dict] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    method: str = "GEMDAT native site transitions and residence-filtered jumps"


def _load_gemdat():
    message = "Jump analysis requires gemdat>=1.8.1,<2 and its dependencies; install the jumps extra in a compatible environment"
    try:
        installed = version("gemdat")
        release = tuple(int(part) for part in installed.split(".")[:3])
    except (PackageNotFoundError, ValueError) as exc:
        raise ImportError(message) from exc
    if not (1, 8, 1) <= release < (2, 0, 0):
        raise ImportError(f"{message}; found gemdat {installed}")
    try:
        from gemdat import Jumps, Trajectory, Transitions
        from pymatgen.core import Structure
    except ImportError as exc:
        raise ImportError(message) from exc
    for method, required in (
        (getattr(Trajectory, "from_ase_trajectory", None), {"trajectory", "constant_lattice", "time_step_ps", "cache"}),
        (getattr(Trajectory, "transitions_between_sites", None), {"sites", "floating_specie", "site_radius", "site_inner_fraction"}),
        (getattr(Trajectory, "apply_drift_correction", None), {"floating_species"}),
        (getattr(Jumps, "__init__", None), {"minimal_residence"}),
    ):
        if not callable(method) or not required <= inspect.signature(method).parameters.keys():
            raise ImportError(f"{message}; the installed public API is unsupported")
    if not callable(getattr(Transitions, "jumps", None)) or not hasattr(Trajectory, "cumulative_displacements"):
        raise ImportError(f"{message}; the installed public API is unsupported")
    return Trajectory, Structure, installed


def check_jump_backend() -> None:
    """Check the optional GEMDAT version/API without trajectories or models."""
    _load_gemdat()


def _native_transitions(native, sites, species, radius, inner_fraction):
    options = dict(sites=sites, floating_specie=species, site_radius=radius,
                   site_inner_fraction=inner_fraction)
    try:
        return native.transitions_between_sites(**options)
    except ValueError as exc:
        if str(exc) != "need at least one array to concatenate":
            raise
        # GEMDAT 1.8.1 stacks an empty event list for constant native states.
        from gemdat.transitions import SiteRadius, Transitions, _calculate_atom_states
        import pandas as pd

        site_radius = SiteRadius.from_given_radius(
            trajectory=native, sites=sites, radius=radius, inner_fraction=inner_fraction,
        )
        selected = native.filter(species)
        states = _calculate_atom_states(
            sites=sites, trajectory=selected, site_radius=site_radius.radius,
            site_inner_fraction=site_radius.outer_states_fraction(),
        )
        inner_states = _calculate_atom_states(
            sites=sites, trajectory=selected, site_radius=site_radius.radius,
            site_inner_fraction=site_radius.inner_fraction,
        )
        if np.any(np.diff(states, axis=0)):
            raise
        # Inner-sphere rattling within the same outer site is not a site jump.
        warnings.warn("GEMDAT empty-event compatibility path: native outer site states are constant.", RuntimeWarning)
        events = pd.DataFrame(columns=["time", "atom index", "start site", "destination site",
                                       "start inner site", "destination inner site"])
        return Transitions(trajectory=native, diff_trajectory=selected, sites=sites,
                           states=states, inner_states=inner_states, events=events,
                           site_radius=site_radius)


def analyze_jumps(
    trajectory: str | Path | Iterable[Atoms],
    *,
    species: str,
    frame_interval_ps: float,
    reference_sites: Atoms | None = None,
    site_radius_A: float | None = None,
    site_inner_fraction: float = 0.5,
    min_residence_ps: float = 0.2,
    coordinate_mode: str = "unwrapped",
) -> JumpResult:
    """Delegate site assignment and residence filtering to native GEMDAT.

    Supply uniformly sampled production frames in a fixed 3D periodic cell.
    Wrapped input uses read_positions' native pymatgen reconstruction; sparse
    wrapped frames cannot reveal multiple crossings. GEMDAT's reconstructed
    displacement is checked against continuous coordinates before analysis.

    By default sites are the selected ions' first-frame occupied positions;
    vacant sites are missing. Supply reference_sites with all candidate sites
    in the same cell and coordinate origin to include vacancies. Only its
    selected species is used. No site discovery or migration-path inference
    occurs. Radius defaults to 0.45 times nearest site separation including
    periodic images, and overlapping outer spheres are rejected.

    Native GEMDAT removes the arithmetic mean drift of all non-selected
    atoms; those atoms must be an appropriate framework. With no such atoms
    no correction is made. No rotation or reference alignment is fitted.

    A single reference site cannot distinguish its periodic images in native
    GEMDAT. Such results, any never-mapped ion, and zero-event results with
    an unmapped run at least as long as the residence cutoff are unmapped.
    Other event counts retain coverage so callers can apply their own
    material-specific coverage requirements. Unmapped run durations use
    the number of consecutive unassigned samples times the frame interval.

    Events use zero-based full ASE atom and selected-reference site indices.
    Native start/stop frame indices are retained and multiplied by the saved
    frame interval for ps times. A stop frame is arrival, not the end of the
    subsequent residence interval. min_residence_ps is converted with ceil.
    """
    if not isinstance(species, str) or atomic_numbers.get(species, 0) <= 0:
        raise ValueError("species must be one real element symbol")
    for name, value in (("frame_interval_ps", frame_interval_ps), ("min_residence_ps", min_residence_ps),
                        ("site_inner_fraction", site_inner_fraction), ("site_radius_A", site_radius_A)):
        if name == "site_radius_A" and value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
            raise ValueError(f"{name} must be finite")
    if frame_interval_ps <= 0 or min_residence_ps < 0:
        raise ValueError("frame_interval_ps must be positive and min_residence_ps nonnegative")
    if not 0 < site_inner_fraction <= 1:
        raise ValueError("site_inner_fraction must lie in (0, 1]")
    if site_radius_A is not None and site_radius_A <= 0:
        raise ValueError("site_radius_A must be positive")
    if coordinate_mode not in ("unwrapped", "wrapped"):
        raise ValueError("coordinate_mode must be unwrapped or wrapped")

    trajectory_class, structure_class, installed = _load_gemdat()
    first, positions = read_positions(trajectory, coordinate_mode=coordinate_mode)
    mobile_indices = np.flatnonzero(np.array(first.get_chemical_symbols()) == species)
    if not len(mobile_indices):
        raise ValueError(f"Requested species {species} is absent")
    source = first if reference_sites is None else reference_sites
    if (not isinstance(source, Atoms) or not len(source) or not source.pbc.all()
            or not np.isfinite(source.positions).all()
            or not np.allclose(source.cell.array, first.cell.array, rtol=1e-9, atol=1e-8)):
        raise ValueError("reference_sites must be finite ASE Atoms with the same cell and 3D PBC")
    site_indices = [i for i, symbol in enumerate(source.get_chemical_symbols()) if symbol == species]
    if not site_indices:
        raise ValueError(f"reference_sites contains no {species} sites")
    sites = source[site_indices]
    nearest = estimate_hop_distance(sites, species=species)
    radius = float(site_radius_A) if site_radius_A is not None else 0.45 * nearest
    if 2 * radius >= nearest:
        raise ValueError("site_radius_A must be smaller than half the nearest reference-site separation (including periodic images)")
    result = JumpResult(
        species=species, frame_interval_ps=float(frame_interval_ps), min_residence_ps=float(min_residence_ps),
        site_inner_fraction=float(site_inner_fraction), n_mobile_atoms=len(mobile_indices), n_sites=len(sites),
        n_frames=len(positions), reference_source="first_frame_occupied" if reference_sites is None else "explicit_reference",
        backend_version=installed, site_radius_A=radius,
        diagnostics=[
            "Saved-frame spacing is supplied by the caller and must be uniform; same-element identity permutations cannot be detected without identifiers.",
            "Site jumps depend on the reference map, site radius, inner fraction and residence cutoff; counts do not establish independent events or long-range diffusion.",
        ],
    )
    if reference_sites is None:
        result.diagnostics.append("Reference sites are first-frame occupied positions only; vacancies and newly visited sites may be absent.")
    residence_frames = ceil(float(min_residence_ps) / float(frame_interval_ps))
    result.diagnostics.append(f"Native minimal_residence={residence_frames} saved-frame intervals.")
    if len(positions) < 2 or (len(positions) - 1) < residence_frames:
        result.diagnostics.append("Trajectory is shorter than the requested residence interval or has fewer than two frames.")
        return result

    frames = []
    for points in positions:
        atoms = first.copy()
        atoms.positions = points
        frames.append(atoms)
    native = trajectory_class.from_ase_trajectory(
        frames, constant_lattice=True, time_step_ps=float(frame_interval_ps), cache=None,
    )
    displacement = np.asarray(native.cumulative_displacements) @ first.cell.array
    if displacement.shape != positions.shape or not np.allclose(displacement, positions - positions[0], rtol=1e-8, atol=1e-7):
        raise ValueError("GEMDAT periodic reconstruction differs from continuous input; save frames more frequently or inspect the cell")
    if len(mobile_indices) < len(first):
        native = native.apply_drift_correction(floating_species=species)
        result.diagnostics.append("Framework drift: native GEMDAT arithmetic mean displacement of all non-selected atoms; no mass weighting or rotational alignment.")
    else:
        result.diagnostics.append("No non-selected atoms exist; framework drift is not corrected.")
    if len(sites) == 1:
        result.status = "unmapped"
        result.diagnostics.append("A single reference site cannot resolve jumps between its periodic images using native GEMDAT site indices; counts and coverage are unknown.")
        return result

    native_sites = structure_class(
        lattice=sites.cell.array, species=sites.get_chemical_symbols(),
        coords=sites.positions, coords_are_cartesian=True,
    )
    captured = []
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            try:
                transitions = _native_transitions(native, native_sites, species, radius, float(site_inner_fraction))
            except IndexError as exc:
                if str(exc) != "index -1 is out of bounds for axis 0 with size 0":
                    raise
                result.status = "unmapped"
                result.diagnostics.append(
                    "GEMDAT could not form an event because an outer-site change had no inner-site transition record; "
                    "jump counts are unknown. Increase site_inner_fraction or review reference-site alignment and site_radius_A."
                )
                return result
            states = np.asarray(transitions.states)
            if states.shape != (len(positions), len(mobile_indices)) or not np.isfinite(states).all() or np.any(states < -1) or np.any(states >= len(sites)):
                raise ValueError("GEMDAT returned invalid site states")
            coverage = np.mean(states >= 0, axis=0)
            result.site_coverage = float(np.mean(coverage))
            result.minimum_ion_site_coverage = float(np.min(coverage))
            max_unmapped_frames = 0
            for column in (states < 0).T:
                boundaries = np.flatnonzero(np.diff(np.r_[False, column, False].astype(int)))
                max_unmapped_frames = max(max_unmapped_frames, int(np.max(boundaries[1::2] - boundaries[::2], initial=0)))
            result.max_unmapped_duration_ps = max_unmapped_frames * float(frame_interval_ps)
            try:
                jumps = transitions.jumps(minimal_residence=residence_frames)
            except ValueError as exc:
                if str(exc) != "No jumps found":
                    raise
                records = []
            else:
                records = jumps.data.to_dict(orient="records")
    finally:
        result.diagnostics.extend(f"gemdat warning: {item.message}" for item in captured)
    for record in records:
        atom = int(record["atom index"])
        start, stop = int(record["start time"]), int(record["stop time"])
        start_site, end_site = int(record["start site"]), int(record["destination site"])
        if not (0 <= atom < len(mobile_indices) and 0 <= start <= stop < len(positions)
                and 0 <= start_site < len(sites) and 0 <= end_site < len(sites) and start_site != end_site):
            raise ValueError("GEMDAT returned invalid jump event indices")
        event = dict(atom_index=int(mobile_indices[atom]), start_site=start_site, end_site=end_site,
                     start_frame=start, stop_frame=stop, start_time_ps=start * float(frame_interval_ps),
                     stop_time_ps=stop * float(frame_interval_ps))
        if "residence_time" in record:
            event["residence_time_ps"] = float(record["residence_time"]) * float(frame_interval_ps)
        result.events.append(event)
    persistent_unmapped = max_unmapped_frames > 0 and result.max_unmapped_duration_ps >= min_residence_ps
    if np.any(coverage == 0) or (not records and persistent_unmapped):
        result.status = "unmapped"
        result.diagnostics.append("Incomplete site mapping cannot establish a reliable absence of jumps; observed events, if any, are retained but counts are unknown.")
        return result
    result.status = "estimated"
    result.n_jumps = len(result.events)
    result.n_jumping_ions = len({event["atom_index"] for event in result.events})
    if result.site_coverage < 1:
        result.diagnostics.append("Some ion-frame samples lie outside all reference sites; counts may omit visits to missing sites and require caller coverage review.")
    return result

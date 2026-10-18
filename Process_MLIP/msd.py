"""Fixed-cell trajectory to multi-time-origin MSD using pymatgen."""
import csv
import json
import warnings
from numbers import Integral, Real
from pathlib import Path

import numpy as np
from ase.geometry import find_mic
from ase.io.trajectory import Trajectory


def _trajectory_times(path, count, frame_interval_fs):
    if frame_interval_fs is not None:
        if (isinstance(frame_interval_fs, bool) or not isinstance(frame_interval_fs, Real)
                or not np.isfinite(frame_interval_fs) or frame_interval_fs <= 0):
            raise ValueError("frame_interval_fs must be finite and positive")
        return np.arange(count, dtype=float) * frame_interval_fs, "frame_interval_fs"
    report_path = path.with_name("report.json")
    message = "Cannot infer trajectory times; supply frame_interval_fs (time between saved frames)"
    if not report_path.is_file():
        raise ValueError(message)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        parameters = report["parameters"]
        steps = report["steps_completed"]
        interval = parameters["trajectory_interval"]
        dt = parameters["timestep_fs"]
        source_name = str(report["trajectory_file"]).replace("\\", "/").rsplit("/", 1)[-1]
        if (report["status"] != "completed" or source_name != path.name
                or type(steps) is not int or steps < 0
                or type(interval) is not int or interval <= 0
                or isinstance(dt, bool) or not isinstance(dt, Real)
                or not np.isfinite(dt) or dt <= 0):
            raise ValueError(message)
        expected = steps // interval + 1 + int(steps % interval != 0)
        if expected != count:
            raise ValueError(message + "; report/frame count mismatch")
        saved_steps = np.arange(0, steps + 1, interval, dtype=float)
        if steps % interval:
            saved_steps = np.append(saved_steps, steps)
        return saved_steps * dt, "report.json"
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(message) from exc


def _load_diffusion_analyzer():
    try:
        from pymatgen.analysis.diffusion.analyzer import DiffusionAnalyzer
    except ImportError as exc:
        raise ImportError("MSD requires pymatgen-analysis-diffusion in the analysis environment; "
                          "there is no ASE MSD fallback") from exc
    return DiffusionAnalyzer


def _msd_lags(frame_count, interval_fs, atom_count, min_obs):
    """Match DiffusionAnalyzer's max-mode lag grid; its internal fit needs 3 points."""
    if not 0 < interval_fs <= 1000:
        raise ValueError("pymatgen MSD requires saved-frame spacing <= 1000 fs")
    first = int(1000 / interval_fs)
    stop = min(atom_count * frame_count // min_obs, frame_count)
    lags = np.arange(first, stop, max(int((stop - first) / 200), 1))
    if len(lags) < 3:
        raise ValueError("Not enough data for pymatgen multi-origin MSD: need at least "
                         "three lag points near/above 1 ps; use a longer trajectory, "
                         "fewer segments, or a smaller min_obs (default 30)")
    return lags


def export_msd(trajectory, output_csv, *, species=None, frame_interval_fs=None,
               skip_frames=0, number_of_segments=1, unwrap=False,
               drift_reference=None, overwrite=False, min_obs=30):
    """Export pymatgen max-mode MSD (Å²), averaged over atoms and time origins.

    species: element/list/None (all). skip_frames removes equilibration;
    number_of_segments splits equally, each analyzed independently. min_obs=30
    controls pymatgen's maximum lag; native sampling starts near 1 ps.
    CSV columns are unchanged; time_fs/time_ps are lag times, frame_index is
    segment start + lag in frames (not a unique displacement endpoint).

    Times come from adjacent report.json or frame_interval_fs. A short final
    saved interval is excluded with a warning; other unequal spacing is rejected.
    unwrap=True uses ASE MIC for wrapped input; default preserves continuous
    MD positions. drift_reference='framework' subtracts the mass-weighted COM
    displacement of unselected atoms; None applies no drift correction.

    Requires pymatgen-analysis-diffusion only when called; no models are loaded.
    Writes only output_csv, refuses overwrite by default. Internal pymatgen
    diffusion/conductivity fits are discarded; use fit_msd explicitly.
    """
    for key, value, minimum in (("skip_frames", skip_frames, 0),
                                 ("number_of_segments", number_of_segments, 1),
                                 ("min_obs", min_obs, 1)):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
    for key, value in (("unwrap", unwrap), ("overwrite", overwrite)):
        if type(value) is not bool:
            raise TypeError(f"{key} must be bool")
    if drift_reference not in (None, "framework"):
        raise ValueError("drift_reference must be None or framework")
    source = Path(trajectory).resolve()
    destination = Path(output_csv)
    if destination.is_symlink():
        raise FileExistsError(destination)
    destination = destination.resolve()
    if source == destination:
        raise ValueError("output_csv cannot overwrite the input trajectory")
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    if not source.is_file():
        raise FileNotFoundError(source)
    processed = []
    dropped = []
    with Trajectory(str(source), "r") as frames:
        count = len(frames)
        times, time_source = _trajectory_times(source, count, frame_interval_fs)
        stop = count
        retained_times = times[skip_frames:]
        if len(retained_times) >= 3:
            differences = np.diff(retained_times)
            if not np.allclose(differences, differences[0], rtol=1e-9, atol=1e-8):
                if (time_source == "report.json"
                        and np.allclose(differences[:-1], differences[0], rtol=1e-9, atol=1e-8)
                        and 0 < differences[-1] < differences[0]):
                    stop -= 1
                    dropped = [count - 1]
                    warnings.warn("Excluded the final short-interval frame from multi-origin MSD; "
                                  "pymatgen requires equally spaced frames", UserWarning, stacklevel=2)
                else:
                    raise ValueError("pymatgen MSD requires equally spaced frames")
        retained = stop - skip_frames
        if retained < 2 * number_of_segments or retained % number_of_segments:
            raise ValueError("Retained frames must divide equally into segments, at least two per segment")
        first = frames[skip_frames]
        if not np.isfinite(first.get_volume()) or first.get_volume() <= 0:
            raise ValueError("pymatgen MSD requires a nonzero 3D cell")
        symbols = np.asarray(first.get_chemical_symbols())
        if species is None:
            requested = set(symbols)
        elif isinstance(species, str):
            requested = {species}
        elif isinstance(species, (list, tuple)) and all(isinstance(item, str) for item in species):
            requested = set(species)
        else:
            raise TypeError("species must be an element string, list/tuple, or None")
        if not requested or not requested.issubset(set(symbols)):
            raise ValueError(f"Requested species not present: {sorted(requested - set(symbols))}")
        selected = np.flatnonzero(np.isin(symbols, list(requested)))
        reference = np.flatnonzero(~np.isin(symbols, list(requested)))
        if drift_reference == "framework" and not len(reference):
            raise ValueError("framework drift correction requires atoms outside selected species")
        interval_fs = float(times[skip_frames + 1] - times[skip_frames])
        elements = sorted(requested)
        lags = {element: _msd_lags(retained // number_of_segments, interval_fs,
                                  int(np.sum(symbols == element)), int(min_obs))
                for element in elements}
        previous = continuous = origin_com = None
        for index in range(skip_frames, stop):
            frame = frames[index]
            if not np.array_equal(frame.numbers, first.numbers):
                raise ValueError("Atom identities and order must remain unchanged")
            if not np.allclose(frame.cell, first.cell, rtol=1e-9, atol=1e-8):
                raise ValueError("MSD export requires a fixed cell (use an NVT trajectory)")
            if not np.array_equal(frame.pbc, first.pbc):
                raise ValueError("PBC flags must remain unchanged")
            raw = frame.get_positions()
            if not np.all(np.isfinite(raw)) or not np.all(np.isfinite(frame.cell)):
                raise ValueError("Trajectory positions and cell must be finite")
            if unwrap and previous is not None:
                increments, _ = find_mic(raw - previous, first.cell, first.pbc)
                continuous = continuous + increments
            else:
                continuous = raw.copy()
            previous = raw
            drift = np.zeros(3)
            if drift_reference == "framework":
                framework = frame[reference]
                framework.set_positions(continuous[reference])
                center = framework.get_center_of_mass()
                if origin_com is None:
                    origin_com = center
                drift = center - origin_com
            processed.append(continuous[selected] - drift)
    analyzer_class = _load_diffusion_analyzer()
    from pymatgen.core import Structure

    positions = np.asarray(processed)
    selected_symbols = symbols[selected]
    length = retained // number_of_segments
    results = []
    for segment in range(number_of_segments):
        start = segment * length
        for element in elements:
            mask = selected_symbols == element
            population = int(mask.sum())
            points = positions[start:start + length, mask]
            displacement = (points - points[0]).transpose(1, 0, 2)
            # pymatgen always removes non-target drift. A fixed reference site
            # keeps that zero: any requested COM correction was already applied.
            reference_element = "He" if element != "He" else "Ne"
            structure = Structure(first.cell.array, [element] * population + [reference_element],
                                  np.zeros((population + 1, 3)), coords_are_cartesian=True)
            displacement = np.concatenate([displacement, np.zeros((1, length, 3))])
            analyzer = analyzer_class(structure, displacement, element, temperature=300,
                                      time_step=interval_fs, step_skip=1,
                                      smoothed="max", min_obs=int(min_obs))
            # Temperature only affects unused automatic conductivity, not MSD.
            xyz = np.asarray(analyzer.msd_components)
            lag_times = lags[element] * interval_fs
            if (xyz.shape != (len(lag_times), 3) or not np.all(np.isfinite(xyz))
                    or not np.allclose(analyzer.dt, lag_times)):
                raise RuntimeError("Unexpected pymatgen MSD values or lag grid")
            results.append((segment, element, population, xyz))
    columns = ["segment", "frame_index", "time_fs", "time_ps", "species", "atom_count",
               "msd_x_A2", "msd_y_A2", "msd_z_A2", "msd_total_A2"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w" if overwrite else "x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for segment, element, population, components in results:
            start = skip_frames + segment * length
            for offset, xyz in zip(lags[element], components):
                lag = float(offset * interval_fs)
                writer.writerow(dict(segment=segment + 1, frame_index=int(start + offset),
                                     time_fs=lag, time_ps=lag / 1000, species=element,
                                     atom_count=population,
                                     msd_x_A2=float(xyz[0]), msd_y_A2=float(xyz[1]),
                                     msd_z_A2=float(xyz[2]), msd_total_A2=float(xyz.sum())))
    return dict(csv_file=str(destination), trajectory_file=str(source), time_source=time_source,
                frame_count=int(retained), skip_frames=int(skip_frames),
                number_of_segments=int(number_of_segments), species=elements,
                method="pymatgen.analysis.diffusion.analyzer.DiffusionAnalyzer",
                smoothed="max", min_obs=int(min_obs), dropped_frame_indices=dropped,
                unwrap=unwrap,
                drift_reference=drift_reference, msd_unit="angstrom^2")

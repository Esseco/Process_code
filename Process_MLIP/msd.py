"""NVT trajectory-to-CSV adapter around ASE's DiffusionCoefficient."""
import csv
import json
from numbers import Integral, Real
from pathlib import Path

import numpy as np
from ase import units
from ase.geometry import find_mic
from ase.io.trajectory import Trajectory
from ase.md.analysis import DiffusionCoefficient


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


def export_msd(trajectory, output_csv, *, species=None, frame_interval_fs=None,
               skip_frames=0, number_of_segments=1, unwrap=False,
               drift_reference=None, overwrite=False):
    """Export true MSD (Å²) from a fixed-cell ASE .traj using ASE analysis.

    species: element string/list, or None for all elements. Times are inferred
    from adjacent completed MD report.json unless frame_interval_fs is given.
    skip_frames removes equilibration frames. ASE divides retained frames into
    non-overlapping segments, each referenced to its own first frame; this is
    not an overlapping all-time-origin MSD. No diffusion coefficient is exported.

    Our MD trajectories are unwrapped, so unwrap defaults False. For wrapped
    input, True reconstructs nearest-image increments via ASE find_mic; saved
    frames must be frequent enough to avoid ambiguous periodic crossings.
    drift_reference='framework' subtracts the mass-weighted COM displacement of
    atoms outside selected species. Default None makes no drift correction.

    Writes only output_csv (default no overwrite), returns path and provenance.
    Source trajectory and report are never modified. No model is loaded.
    """
    for key, value, minimum in (("skip_frames", skip_frames, 0),
                                 ("number_of_segments", number_of_segments, 1)):
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
    with Trajectory(str(source), "r") as frames:
        count = len(frames)
        retained = count - skip_frames
        if retained < 2 * number_of_segments or retained % number_of_segments:
            raise ValueError("Retained frames must divide equally into segments, at least two per segment")
        times, time_source = _trajectory_times(source, count, frame_interval_fs)
        first = frames[skip_frames]
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
        previous = continuous = origin_com = None
        for index in range(skip_frames, count):
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
            reduced = frame[selected]
            reduced.set_positions(continuous[selected] - drift)
            processed.append(reduced)
    # Selecting whole species before invoking ASE also ensures that its
    # normalization counts correspond exactly to the analyzed atom population.
    analyzer = DiffusionCoefficient(processed, timestep=float(times[1] - times[0]) * units.fs)
    analyzer.calculate(number_of_segments=int(number_of_segments))
    # ASE stores sum(displacement²)/(2*N) for its Einstein slope fitting.
    # Export conventional MSD, not that half-MSD. We do not use ASE's fitted
    # coefficients or uniform time grid: CSV uses exact times, including a final
    # short saved interval from run_md's mandatory last frame.
    msd = 2 * np.asarray(analyzer.xyz_segment_ensemble_average)
    if not np.all(np.isfinite(msd)):
        raise RuntimeError("ASE analysis returned non-finite MSD")
    columns = ["segment", "frame_index", "time_fs", "time_ps", "species", "atom_count",
               "msd_x_A2", "msd_y_A2", "msd_z_A2", "msd_total_A2"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w" if overwrite else "x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for segment in range(number_of_segments):
            start = skip_frames + segment * analyzer.len_segments
            for element_index, element in enumerate(analyzer.types_of_atoms):
                for offset in range(analyzer.len_segments):
                    lag = float(times[start + offset] - times[start])
                    xyz = msd[segment, element_index, :, offset]
                    writer.writerow(dict(segment=segment + 1, frame_index=start + offset,
                                         time_fs=lag, time_ps=lag / 1000, species=element,
                                         atom_count=analyzer.no_of_atoms[element_index],
                                         msd_x_A2=float(xyz[0]), msd_y_A2=float(xyz[1]),
                                         msd_z_A2=float(xyz[2]), msd_total_A2=float(xyz.sum())))
    return dict(csv_file=str(destination), trajectory_file=str(source), time_source=time_source,
                frame_count=int(retained), skip_frames=int(skip_frames),
                number_of_segments=int(number_of_segments), species=analyzer.types_of_atoms,
                method="ase.md.analysis.DiffusionCoefficient", unwrap=unwrap,
                drift_reference=drift_reference, msd_unit="angstrom^2")

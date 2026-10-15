"""Single-stage ASE MD; model selection and orchestration live separately."""
import csv
from importlib.metadata import PackageNotFoundError, version
import json
from numbers import Integral, Real
from pathlib import Path
import platform

import numpy as np
from ase import Atoms, units
from ase.calculators.calculator import PropertyNotImplementedError
from ase.io import read, write
from ase.io.trajectory import Trajectory


_DEFAULTS = dict(ensemble="nvt", temperature_K=300.0, steps=1000,
                 timestep_fs=1.0, tdamp_fs=100.0, pressure_bar=1.0,
                 pdamp_fs=1000.0, initialize_velocities=None, seed=42,
                 remove_com=True, zero_rotation=False, trajectory_interval=10,
                 log_interval=10, overwrite=False, time_offset_fs=0.0)
_FILES = ("md.traj", "md.csv", "final.traj", "report.json")


def _validate_options(options):
    unknown = options.keys() - _DEFAULTS.keys()
    if unknown:
        raise ValueError(f"Unknown MD parameters: {sorted(unknown)}")
    result = dict(_DEFAULTS, **options)
    if not isinstance(result["ensemble"], str) or result["ensemble"].lower() not in ("nvt", "npt"):
        raise ValueError("ensemble must be nvt or npt")
    result["ensemble"] = result["ensemble"].lower()
    for key in ("temperature_K", "timestep_fs", "tdamp_fs", "pdamp_fs",
                "pressure_bar", "time_offset_fs"):
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, Real) or not np.isfinite(value):
            raise ValueError(f"{key} must be a finite number")
        if key in ("temperature_K", "timestep_fs", "tdamp_fs", "pdamp_fs") and value <= 0:
            raise ValueError(f"{key} must be positive")
        if key == "time_offset_fs" and value < 0:
            raise ValueError("time_offset_fs must be nonnegative")
        result[key] = float(value)
    for key in ("steps", "seed", "trajectory_interval", "log_interval"):
        value = result[key]
        minimum = 1 if key.endswith("interval") else 0
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{key} must be an integer >= {minimum}")
        result[key] = int(value)
    for key in ("remove_com", "zero_rotation", "overwrite"):
        if type(result[key]) is not bool:
            raise TypeError(f"{key} must be bool")
    if result["initialize_velocities"] is not None and type(result["initialize_velocities"]) is not bool:
        raise TypeError("initialize_velocities must be None, True or False")
    return result


def _copy_structure(structure):
    if isinstance(structure, Atoms):
        return structure.copy()
    if isinstance(structure, (str, Path)):
        return read(str(structure))
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    if isinstance(structure, Structure):
        return AseAtomsAdaptor.get_atoms(structure)
    raise TypeError("structure must be ASE Atoms, a file path or pymatgen Structure")


def _validate_atoms(atoms, options):
    if len(atoms) < 2:
        raise ValueError("MD requires at least two atoms")
    if atoms.constraints:
        raise NotImplementedError("These NHC/MTK integrators do not support atomic constraints")
    if (not np.all(np.isfinite(atoms.positions)) or not np.all(np.isfinite(atoms.cell))
            or not np.all(np.isfinite(atoms.get_momenta()))
            or not np.all(np.isfinite(atoms.get_masses()))
            or np.any(atoms.get_masses() <= 0)):
        raise ValueError("Positions, cell, momenta and positive masses must be finite")
    if options["ensemble"] == "npt" and (
            not np.all(atoms.pbc) or atoms.cell.rank != 3 or np.linalg.det(atoms.cell) <= 0):
        raise ValueError("NPT requires full 3D PBC and a positive-volume right-handed cell")
    if options["zero_rotation"] and np.any(atoms.pbc):
        raise ValueError("zero_rotation is for nonperiodic systems only")
    if options["initialize_velocities"] is False or (
            options["initialize_velocities"] is None and atoms.has("momenta")):
        if not atoms.has("momenta") or atoms.get_kinetic_energy() <= 0:
            raise ValueError("Preserving velocities requires existing nonzero momenta")


def _check_outputs(output_dir, overwrite, filenames=_FILES):
    if Path(output_dir).is_symlink():
        raise FileExistsError(f"Output directory must not be a symlink: {output_dir}")
    root = Path(output_dir).resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(root)
    for name in filenames:
        target = root / name
        if target.is_symlink() or target.is_dir():
            raise FileExistsError(f"Output must be a regular file: {target}")
        if target.exists() and not overwrite:
            raise FileExistsError(f"Output exists; choose a new directory or overwrite=True: {target}")
    return root


def _versions(calculator):
    packages = ["ase", "numpy"]
    module = type(calculator).__module__.split(".")[0]
    package = {"mace": "mace-torch", "sevenn": "sevenn", "chgnet": "chgnet",
               "orb_models": "orb-models"}.get(module)
    if package:
        packages += [package, "torch"]
    result = {"python": platform.python_version()}
    for name in packages:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = "unavailable"
    return result


def _snapshot(atoms, require_stress):
    if (not np.all(np.isfinite(atoms.positions)) or not np.all(np.isfinite(atoms.cell))
            or not np.all(np.isfinite(atoms.get_momenta()))):
        raise RuntimeError("MD produced non-finite positions, cell or momenta")
    energy = float(atoms.get_potential_energy())
    kinetic = float(atoms.get_kinetic_energy())
    temperature = float(atoms.get_temperature())
    forces = np.asarray(atoms.get_forces())
    if not np.all(np.isfinite([energy, kinetic, temperature])) or not np.all(np.isfinite(forces)):
        raise RuntimeError("MD produced non-finite energy, temperature or forces")
    volume = float(atoms.get_volume()) if atoms.cell.rank == 3 else None
    if volume is not None and (not np.isfinite(volume) or volume <= 0):
        raise RuntimeError("MD produced invalid volume")
    pressure = None
    if volume is not None:
        try:
            stress = atoms.get_stress(voigt=False, include_ideal_gas=True)
        except PropertyNotImplementedError as exc:
            if require_stress:
                raise ValueError("NPT requires calculator stress support") from exc
        else:
            if not np.all(np.isfinite(stress)):
                raise RuntimeError("MD produced non-finite stress")
            pressure = float(-np.trace(stress) / 3 / units.bar)
    return dict(temperature_K=temperature, potential_energy_eV=energy,
                kinetic_energy_eV=kinetic, total_energy_eV=energy + kinetic,
                pressure_bar=pressure, volume_angstrom3=volume,
                force_max_eV_per_angstrom=float(np.linalg.norm(forces, axis=1).max()))


def _write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                    allow_nan=False), encoding="utf-8")


def run_md(structure, calculator, output_dir, *, ensemble="nvt", temperature_K=300.0,
           steps=1000, timestep_fs=1.0, tdamp_fs=100.0, pressure_bar=1.0,
           pdamp_fs=1000.0, initialize_velocities=None, seed=42, remove_com=True,
           zero_rotation=False, trajectory_interval=10, log_interval=10,
           overwrite=False, time_offset_fs=0.0, model_metadata=None):
    """Run one NHC NVT or isotropic MTK NPT stage with an ASE calculator.

    Positions/cell use Å; energies eV, temperature K, time/damping fs, pressure
    bar (positive compression). Input atoms are copied. initialize_velocities
    None initializes only when momenta are absent; False preserves velocities;
    True samples Maxwell-Boltzmann momenta using seed. COM removal/rotation
    options apply only to initialization. Constraints are not supported.

    Writes md.traj, md.csv, final.traj (with momenta), report.json. Existing
    owned files require overwrite=True; unrelated files are never removed.
    No exact thermostat/barostat restart is provided. Returns final_atoms,
    output paths, final thermodynamic state and actual completed step count.
    """
    options = _validate_options({key: value for key, value in locals().copy().items()
                                 if key in _DEFAULTS})
    atoms = _copy_structure(structure)
    _validate_atoms(atoms, options)
    root = _check_outputs(output_dir, overwrite)
    metadata = {} if model_metadata is None else model_metadata
    json.dumps(metadata, allow_nan=False)  # fail before producing outputs
    from ase.md.nose_hoover_chain import NoseHooverChainNVT, IsotropicMTKNPT
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
    initialized = initialize_velocities is True or (
        initialize_velocities is None and not atoms.has("momenta"))
    if initialized:
        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature_K,
                                    rng=np.random.default_rng(seed), force_temp=True)
        if remove_com:
            Stationary(atoms)
        if zero_rotation:
            ZeroRotation(atoms)
    atoms.calc = calculator
    # Probe properties before touching outputs (including required NPT stress).
    initial_state = _snapshot(atoms, ensemble.lower() == "npt")
    arguments = dict(atoms=atoms, timestep=timestep_fs * units.fs,
                     temperature_K=temperature_K, tdamp=tdamp_fs * units.fs,
                     logfile=None)
    if ensemble.lower() == "npt":
        dyn = IsotropicMTKNPT(**arguments, pressure_au=pressure_bar * units.bar,
                              pdamp=pdamp_fs * units.fs)
    else:
        dyn = NoseHooverChainNVT(**arguments)
    root.mkdir(parents=True, exist_ok=True)
    paths = dict(trajectory_file=str(root / "md.traj"), log_file=str(root / "md.csv"),
                 final_structure=str(root / "final.traj"), report_file=str(root / "report.json"))
    # In overwrite mode clear stale completion artifacts, never a whole directory.
    for name in ("final.traj",):
        if overwrite and (root / name).exists():
            (root / name).unlink()
    report = dict(status="running", parameters=options, model=metadata,
                  calculator=f"{type(calculator).__module__}.{type(calculator).__name__}",
                  versions=_versions(calculator), steps_completed=0,
                  velocity_initialization="sampled" if initialized else "preserved",
                  initial_state=initial_state, **paths)
    _write_json(paths["report_file"], report)
    fields = ["step", "time_fs", *initial_state]
    try:
        with Trajectory(paths["trajectory_file"], "w", atoms) as trajectory, \
                open(paths["log_file"], "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()

            def observe():
                state = _snapshot(atoms, options["ensemble"] == "npt")
                step = dyn.nsteps
                if step % log_interval == 0 or step == steps:
                    writer.writerow(dict(step=step, time_fs=time_offset_fs + step * timestep_fs,
                                         **state))
                    handle.flush()
                if step % trajectory_interval == 0 or step == steps:
                    trajectory.write(atoms)
                report["final_state"] = state

            dyn.attach(observe, interval=1)
            dyn.run(steps)
        write(paths["final_structure"], atoms, format="traj")
        report.update(status="completed", steps_completed=int(dyn.nsteps),
                      end_time_fs=float(time_offset_fs + dyn.nsteps * timestep_fs))
        _write_json(paths["report_file"], report)
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status="failed", steps_completed=int(dyn.nsteps),
                      error=f"{type(exc).__name__}: {exc}")
        _write_json(paths["report_file"], report)
        raise
    finally:
        dyn.close()
    return dict(report, final_atoms=atoms, output_dir=str(root))

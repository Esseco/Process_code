"""NEP/GPUMD extended-XYZ data preparation and validation."""
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil

import numpy as np
from ase import Atoms
from ase.io import iread, read, write

from .training_data import vasp_to_xyz


def _target(path):
    target = Path(path).expanduser()
    if target.is_symlink() or target.is_dir():
        raise FileExistsError(f"Output must be a regular file: {target}")
    return target


def _copy_nep_frame(atoms):
    _validate_nep_frame(atoms, require_forces=True, require_virial=False)
    energy = atoms.info.get("energy")
    if energy is None:
        energy = atoms.info.get("REF_energy")
    if energy is None and getattr(atoms, "calc", None) is not None:
        energy = getattr(atoms.calc, "results", {}).get("energy")
    forces = atoms.arrays.get("force", atoms.arrays.get("forces",
                                      atoms.arrays.get("REF_forces")))
    frame = Atoms(numbers=atoms.numbers, positions=atoms.positions.copy(),
                  cell=atoms.cell.array.copy(), pbc=atoms.pbc.copy())
    frame.info["energy"] = float(energy)
    frame.arrays["force"] = np.asarray(forces, dtype=float).copy()
    calc_results = getattr(getattr(atoms, "calc", None), "results", {})
    if "virial" in atoms.info or "virial" in calc_results:
        virial_value = atoms.info["virial"] if "virial" in atoms.info else calc_results["virial"]
        virial = np.asarray(virial_value, dtype=float)
        if virial.shape != (3, 3) or not np.all(np.isfinite(virial)):
            raise ValueError("NEP virial must be a finite 3x3 tensor")
        frame.info["virial"] = virial.copy()
    elif ("stress" in atoms.info or "REF_stress" in atoms.info or
          "stress" in calc_results):
        if "stress" in atoms.info:
            stress_value = atoms.info["stress"]
        elif "REF_stress" in atoms.info:
            stress_value = atoms.info["REF_stress"]
        else:
            stress_value = calc_results["stress"]
        stress = np.asarray(stress_value, dtype=float)
        if stress.shape == (6,):
            stress = np.array([[stress[0], stress[5], stress[4]],
                               [stress[5], stress[1], stress[3]],
                               [stress[4], stress[3], stress[2]]])
        if stress.shape != (3, 3) or not np.all(np.isfinite(stress)):
            raise ValueError("NEP stress must be a finite 3x3 tensor")
        frame.info["virial"] = -stress * atoms.get_volume()
    return frame


def _validate_nep_frame(atoms, *, require_forces, require_virial):
    if not isinstance(atoms, Atoms) or len(atoms) == 0:
        raise ValueError("NEP frames must contain at least one atom")
    if atoms.cell.rank != 3 or not np.all(atoms.pbc):
        raise ValueError("NEP frames require a finite full periodic cell")
    if not np.all(np.isfinite(atoms.positions)) or not np.all(np.isfinite(atoms.cell.array)):
        raise ValueError("NEP positions and cell must be finite")
    energy = atoms.info.get("energy")
    if energy is None:
        energy = atoms.info.get("REF_energy")
    if energy is None and getattr(atoms, "calc", None) is not None:
        energy = getattr(atoms.calc, "results", {}).get("energy")
    if energy is None or np.shape(energy) != () or not np.isfinite(energy):
        raise ValueError("NEP frame requires a finite total energy")
    if require_forces:
        forces = atoms.arrays.get("force", atoms.arrays.get("forces",
                                          atoms.arrays.get("REF_forces")))
        if forces is None or np.shape(forces) != (len(atoms), 3) or not np.all(np.isfinite(forces)):
            raise ValueError("NEP frame requires finite force:R:3 labels")
    calc_results = getattr(getattr(atoms, "calc", None), "results", {})
    if require_virial or any(key in atoms.info or key in calc_results
                             for key in ("virial", "stress", "REF_stress")):
        if "virial" in atoms.info or "virial" in calc_results:
            virial_value = atoms.info["virial"] if "virial" in atoms.info else calc_results["virial"]
            virial = np.asarray(virial_value, dtype=float)
            if virial.shape != (3, 3) or not np.all(np.isfinite(virial)):
                raise ValueError("NEP virial must be a finite 3x3 tensor")
        elif "stress" in atoms.info or "REF_stress" in atoms.info or "stress" in calc_results:
            if "stress" in atoms.info:
                stress_value = atoms.info["stress"]
            elif "REF_stress" in atoms.info:
                stress_value = atoms.info["REF_stress"]
            else:
                stress_value = calc_results["stress"]
            stress = np.asarray(stress_value, dtype=float)
            if stress.shape == (6,):
                stress = np.array([[stress[0], stress[5], stress[4]],
                                   [stress[5], stress[1], stress[3]],
                                   [stress[4], stress[3], stress[2]]])
            if stress.shape != (3, 3) or not np.all(np.isfinite(stress)):
                raise ValueError("NEP stress must be a finite 3x3 tensor")
        elif require_virial:
            raise ValueError("NEP frame requires virial or stress labels")


def _write_frames(path, frames):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        write(handle, frames, format="extxyz", write_results=False)


def vasp_to_nep_xyz(inputs, output_file="train.xyz", *, index=":",
                    energy_type="free_energy", include_virial=True,
                    overwrite=False):
    """Convert labelled VASP results to GPUMD NEP extended XYZ."""
    if type(overwrite) is not bool or type(include_virial) is not bool:
        raise TypeError("overwrite and include_virial must be bool")
    target = _target(output_file)
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    pending = None
    with NamedTemporaryFile(prefix=".nep_labels_", suffix=".extxyz",
                            dir=target.parent, delete=False) as handle:
        source = Path(handle.name)
    source.unlink()
    try:
        vasp_to_xyz(inputs, source, index=index, energy_type=energy_type,
                    include_stress=include_virial, overwrite=False)
        with NamedTemporaryFile(prefix=".nep_xyz_", suffix=".extxyz",
                                dir=target.parent, delete=False) as handle:
            pending = Path(handle.name)
        with pending.open("w", encoding="utf-8", newline="\n") as handle:
            for atoms in iread(str(source), index=":", format="extxyz"):
                frame = _copy_nep_frame(atoms)
                frame.info["energy_type"] = energy_type
                if not include_virial:
                    frame.info.pop("virial", None)
                write(handle, frame, format="extxyz", write_results=False)
                count += 1
        if not count:
            raise ValueError("No frames selected")
        shutil.copyfile(pending, target)
    finally:
        source.unlink(missing_ok=True)
        if pending is not None:
            pending.unlink(missing_ok=True)
    return count


def validate_nep_dataset(path, *, expected_species=None, require_forces=True,
                          require_virial=False):
    """Validate a GPUMD NEP extended XYZ dataset and return a summary."""
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    if type(require_forces) is not bool or type(require_virial) is not bool:
        raise TypeError("require_forces and require_virial must be bool")
    expected = None if expected_species is None else list(expected_species)
    if expected is not None and (not expected or len(set(expected)) != len(expected)):
        raise ValueError("expected_species must be a nonempty sequence of unique symbols")
    species = []
    frames = 0
    atom_counts = []
    has_forces = True
    has_virial = True
    for atoms in iread(str(source), index=":", format="extxyz"):
        _validate_nep_frame(atoms, require_forces=require_forces,
                            require_virial=require_virial)
        frames += 1
        frame = _copy_nep_frame(atoms) if require_forces else atoms
        atom_counts.append(len(atoms))
        for symbol in atoms.get_chemical_symbols():
            if symbol not in species:
                species.append(symbol)
        if not any(key in atoms.arrays for key in ("force", "forces", "REF_forces")):
            has_forces = False
        calc_results = getattr(getattr(atoms, "calc", None), "results", {})
        if not any(key in atoms.info or key in calc_results
                   for key in ("virial", "stress", "REF_stress")):
            has_virial = False
    if frames == 0:
        raise ValueError("NEP dataset is empty")
    if expected is not None and set(species) != set(expected):
        raise ValueError(f"Dataset species {species} do not match expected {expected}")
    if require_forces and not has_forces:
        raise ValueError("NEP dataset requires force labels")
    if require_virial and not has_virial:
        raise ValueError("NEP dataset requires virial or stress labels")
    return {"path": str(source), "frames": frames, "species": species,
            "atom_count_min": min(atom_counts), "atom_count_max": max(atom_counts),
            "has_forces": has_forces, "has_virial": has_virial}


def split_nep_dataset(input_file, output_dir, *, train_fraction=0.9, seed=42,
                      overwrite=False):
    """Deterministically split a NEP dataset into train.xyz and test.xyz."""
    if isinstance(train_fraction, bool) or not isinstance(train_fraction, (int, float)):
        raise TypeError("train_fraction must be a number")
    if not np.isfinite(train_fraction) or not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be finite and between 0 and 1")
    if isinstance(seed, bool) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    source = Path(input_file).expanduser()
    if not source.is_file():
        raise FileNotFoundError(source)
    frames = [_copy_nep_frame(frame) for frame in read(str(source), index=":", format="extxyz")]
    if len(frames) < 2:
        raise ValueError("At least two frames are required for a train/test split")
    root = Path(output_dir).expanduser()
    if root.exists() and (not root.is_dir() or any(root.iterdir())) and not overwrite:
        raise FileExistsError(root)
    root.mkdir(parents=True, exist_ok=True)
    n_train = int(round(len(frames) * float(train_fraction)))
    n_train = max(1, min(len(frames) - 1, n_train))
    order = np.random.default_rng(int(seed)).permutation(len(frames))
    train = [frames[i] for i in order[:n_train]]
    test = [frames[i] for i in order[n_train:]]
    outputs = {"train_file": root / "train.xyz", "test_file": root / "test.xyz"}
    for path in outputs.values():
        if path.exists() and (path.is_symlink() or path.is_dir() or not overwrite):
            raise FileExistsError(path)
    with NamedTemporaryFile(prefix=".train_", suffix=".xyz", dir=root, delete=False) as handle:
        pending_train = Path(handle.name)
    with NamedTemporaryFile(prefix=".test_", suffix=".xyz", dir=root, delete=False) as handle:
        pending_test = Path(handle.name)
    try:
        _write_frames(pending_train, train)
        _write_frames(pending_test, test)
        shutil.copyfile(pending_train, outputs["train_file"])
        shutil.copyfile(pending_test, outputs["test_file"])
    finally:
        pending_train.unlink(missing_ok=True)
        pending_test.unlink(missing_ok=True)
    return {"train_file": str(outputs["train_file"]),
            "test_file": str(outputs["test_file"]),
            "train_frames": len(train), "test_frames": len(test),
            "seed": int(seed)}

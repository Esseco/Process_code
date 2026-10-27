"""Convert labelled VASP configurations to MACE extended XYZ using ASE."""
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

import numpy as np
from ase import Atoms
from ase.calculators.calculator import PropertyNotImplementedError
from ase.io import iread, write


def vasp_to_xyz(inputs, output_file="mace_train.xyz", *, index=":",
                energy_type="free_energy", include_stress=True, overwrite=False):
    """Export VASP results to MACE extxyz; return the number of written frames.

    inputs: OUTCAR/vasprun.xml path, calculation directory, or a list of these.
    Directories prefer vasprun.xml over OUTCAR; .gz versions are supported.
    index: ASE frame selector, e.g. ":" (all), -1 (last), or "::10".
    REF_energy is the whole-cell energy in eV. Default "free_energy" uses
    VASP's force-consistent free energy; "energy" selects ASE's extrapolated
    zero-smearing energy. Never mix energy conventions within a dataset.
    REF_forces are raw DFT forces in eV/Angstrom, without applying constraints.
    REF_stress is ASE tensile-positive stress in eV/Angstrom^3 (3x3), including
    ASE's VASP sign/unit conversion. Set include_stress=False if unavailable.

    Coordinates, cell, species and PBC are retained; constraints/calculators
    are removed. Missing/non-finite labels fail without changing an existing
    output. The output is replaced only after every selected frame succeeds.
    No DFT/model calculation, random sampling or convergence filtering occurs;
    the caller must select electronically converged, consistent DFT results.
    Uses the existing ASE/NumPy stack (py1); no MACE training dependency.
    """
    if type(overwrite) is not bool or type(include_stress) is not bool:
        raise TypeError("overwrite and include_stress must be bool")
    if energy_type not in ("energy", "free_energy"):
        raise ValueError("energy_type must be energy or free_energy")
    items = [inputs] if isinstance(inputs, (str, Path)) else list(inputs)
    if not items:
        raise ValueError("No input files supplied")
    sources = []
    for item in items:
        source = Path(item).expanduser().resolve()
        if source.is_dir():
            source = next((source / name for name in
                           ("vasprun.xml", "vasprun.xml.gz", "OUTCAR", "OUTCAR.gz")
                           if (source / name).is_file()), source / "vasprun.xml")
        if not source.is_file():
            raise FileNotFoundError(source)
        sources.append(source)
    target = Path(output_file).expanduser().resolve()
    if target in sources:
        raise ValueError("Cannot overwrite a VASP input file")
    if target.exists() and (not overwrite or not target.is_file()):
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with TemporaryDirectory(prefix=".mace_xyz_", dir=target.parent) as temporary:
        pending = Path(temporary) / "dataset.extxyz"
        with pending.open("w", encoding="utf-8", newline=chr(10)) as handle:
            for source in sources:
                format = "vasp-xml" if ".xml" in source.name.lower() else "vasp-out"
                for selected_index, atoms in enumerate(iread(str(source), index=index, format=format)):
                    context = f"{source}, selected frame {selected_index}"
                    try:
                        energy = atoms.get_potential_energy(force_consistent=energy_type == "free_energy")
                        forces = atoms.get_forces(apply_constraint=False)
                        stress = atoms.get_stress(voigt=False, apply_constraint=False) if include_stress else None
                    except (PropertyNotImplementedError, RuntimeError) as exc:
                        raise ValueError(f"{context}: missing required energy/forces/stress labels: {exc}") from exc
                    if (not len(atoms) or atoms.cell.rank != 3 or not atoms.pbc.all()
                            or not np.isfinite(atoms.positions).all()
                            or not np.isfinite(atoms.cell.array).all()):
                        raise ValueError(f"{context}: expected finite periodic coordinates and a full cell")
                    if (not np.isfinite(energy) or forces.shape != (len(atoms), 3)
                            or not np.isfinite(forces).all()
                            or (stress is not None and (stress.shape != (3, 3) or not np.isfinite(stress).all()))):
                        raise ValueError(f"{context}: energy/forces/stress labels must be finite and correctly shaped")
                    frame = Atoms(numbers=atoms.numbers, positions=atoms.positions,
                                  cell=atoms.cell, pbc=atoms.pbc)
                    frame.info.update(REF_energy=float(energy), config_type="VASP",
                                      source_file=str(source), energy_type=energy_type)
                    frame.arrays["REF_forces"] = forces
                    if stress is not None:
                        frame.info["REF_stress"] = stress
                    write(handle, frame, format="extxyz", write_results=False)
                    count += 1
        if not count:
            raise ValueError("No frames selected")
        if target.exists() and not overwrite:
            raise FileExistsError(target)
        # Windows sandboxed filesystems can deny rename from a temporary
        # child directory to its parent; copy only after all frames validate.
        shutil.copyfile(pending, target)
    return count

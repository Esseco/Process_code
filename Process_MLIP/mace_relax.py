"""Single-structure MACE relaxation without MC setup or trajectory output."""

from pathlib import Path

import numpy as np


def relax_structure_mace(
    structure,
    model_path,
    *,
    output_path=None,
    device="cuda",
    head=None,
    default_dtype="float64",
    fmax=0.05,
    steps=150,
    relax_cell=True,
):
    """Relax one structure and return final energy, forces, and optimizer facts.

    ``structure`` may be a path, ASE ``Atoms``, or pymatgen ``Structure``.
    No trajectory or per-step files are written. If ``output_path`` is given,
    only the final structure is written there.
    """
    from .calculators import create_mace_calculator

    if not np.isfinite(fmax) or fmax <= 0:
        raise ValueError("fmax must be finite and positive")
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    calculator = create_mace_calculator(model_path, device=device, head=head,
                                         default_dtype=default_dtype)
    # MACE exposes the actual selected head, including its own default.
    selected_head = getattr(calculator, "head", head)
    if selected_head is None:
        import re
        if re.search(r"mh[-_]?1(?!\d)", Path(model_path).stem.lower()):
            selected_head = "omat_pbe"
    result = _relax_structure(structure, calculator, output_path=output_path,
                              fmax=fmax, steps=steps, relax_cell=relax_cell)
    result["mace_head"] = selected_head
    return result


def _relax_structure(structure, calculator, *, output_path=None, fmax=0.05,
                     steps=150, relax_cell=True):
    """Shared single-structure optimizer; no trajectory, copied input atoms."""
    from ase import Atoms
    from ase.filters import FrechetCellFilter
    from ase.io import read, write
    from ase.optimize import LBFGS
    if not np.isfinite(fmax) or fmax <= 0:
        raise ValueError("fmax must be finite and positive")
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    if isinstance(structure, (str, Path)):
        atoms = read(str(structure))
    elif isinstance(structure, Atoms):
        atoms = structure.copy()
    else:
        from pymatgen.core import Structure as PymatgenStructure
        from pymatgen.io.ase import AseAtomsAdaptor
        if not isinstance(structure, PymatgenStructure):
            raise TypeError("structure must be a path, ASE Atoms, or pymatgen Structure")
        atoms = AseAtomsAdaptor.get_atoms(structure)
    if len(atoms) == 0:
        raise ValueError("cannot relax an empty structure")

    atoms.calc = calculator

    target = FrechetCellFilter(atoms) if relax_cell else atoms
    optimizer = LBFGS(target, logfile=None)
    optimizer_converged = bool(optimizer.run(fmax=float(fmax), steps=int(steps)))

    energy = float(atoms.get_potential_energy())
    forces = np.asarray(atoms.get_forces(), dtype=float)
    if not np.isfinite(energy) or not np.all(np.isfinite(forces)):
        raise RuntimeError("Model relaxation returned non-finite energy or forces")
    force_norms = np.linalg.norm(forces, axis=1)
    final_path = None
    if output_path is not None:
        final_path = Path(output_path)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        write(str(final_path), atoms, format="vasp", direct=True, vasp5=True)

    return {
        "status": "completed",
        "relax_stopped_normally": True,
        "optimizer_converged": optimizer_converged,
        "energy": energy,
        "energy_per_atom": energy / len(atoms),
        "energy_unit": "eV",
        "forces_ev_per_angstrom": forces.tolist(),
        "force_max_ev_per_angstrom": float(force_norms.max(initial=0.0)),
        "force_rms_ev_per_angstrom": float(np.sqrt(np.mean(force_norms ** 2))),
        "atom_count": len(atoms),
        "relax_steps_used": int(optimizer.get_number_of_steps()),
        "fmax_target_ev_per_angstrom": float(fmax),
        "cell_relaxed": bool(relax_cell),
        "structure_path": str(final_path) if final_path else None,
    }

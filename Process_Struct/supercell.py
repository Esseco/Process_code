"""Symmetry-distinct supercell matrices and shorter equivalent bases."""

from numbers import Integral

import numpy as np


def get_supercell_matrices(structure, size: int, dimensions: str = "abc", *, symprec: float = 1e-5) -> dict:
    """Return inequivalent matrices and a reduced matrix for each one.

    Args:
        structure: Ordered pymatgen Structure or ASE Atoms, preferably a
            primitive cell. The input cell is used as supplied, without
            primitive-cell conversion. Its original PBC flags are not used.
        size: Positive integer volume multiplier relative to the input cell,
            not the final atom count.
        dimensions: Nonempty subset of "abc", e.g. "ab", "ac", or "abc".
            These are lattice directions, not Cartesian axes. Unselected
            directions remain unchanged and are never mixed into selected ones.
        symprec: icet/spglib symmetry tolerance in angstrom (default 1e-5).

    Returns:
        Dict with two equally long lists of integer (3, 3) numpy arrays:
        ``all`` contains icet's symmetry-inequivalent HNF representatives;
        ``recommended[i]`` is a Minkowski-reduced basis of ``all[i]``, using
        only selected directions. Both use ``new_cell = matrix @ old_cell``
        and work with pymatgen ``make_supercell`` or ASE ``make_supercell``.
        Reduction shortens basis vectors; it does not select a globally most
        cubic cell or rank the inequivalent supercells.

    Notes:
        Requires numpy, ASE and icet in py1; pymatgen only for Structure input.
        Equivalence uses the input's atomic species, positions and symmetry,
        not magnetic moments. Supply an ordered structure. No files are
        written and the input is not modified. No randomness is used; repeated
        calls with the same input and library versions give the same order.
        Enumeration can grow rapidly with size, especially in three dimensions.
    """
    if isinstance(size, (bool, np.bool_)) or not isinstance(size, Integral) or size < 1:
        raise ValueError("size must be a positive integer volume multiplier")
    if (not isinstance(dimensions, str) or not dimensions
            or not set(dimensions) <= set("abc") or len(set(dimensions)) != len(dimensions)):
        raise ValueError('dimensions must contain distinct lattice directions from "abc"')
    if not np.isfinite(symprec) or symprec <= 0:
        raise ValueError("symprec must be finite and positive")

    from ase import Atoms
    from ase.geometry import minkowski_reduce
    from icet.tools import enumerate_supercells

    if isinstance(structure, Atoms):
        atoms = structure.copy()
    else:
        from pymatgen.core import Structure
        from pymatgen.io.ase import AseAtomsAdaptor

        if not isinstance(structure, Structure):
            raise TypeError("structure must be an ASE Atoms or pymatgen Structure")
        if not structure.is_ordered:
            raise ValueError("structure must be ordered")
        atoms = AseAtomsAdaptor.get_atoms(structure)
    cell = np.asarray(atoms.cell)
    if not len(atoms) or not np.isfinite(cell).all() or np.linalg.matrix_rank(cell) != 3:
        raise ValueError("structure must be nonempty with a finite, full-rank cell")
    if not np.isfinite(atoms.positions).all():
        raise ValueError("structure positions must be finite")

    pbc = [axis in dimensions for axis in "abc"]
    atoms.set_pbc(pbc)
    result = {"all": [], "recommended": []}
    for supercell in enumerate_supercells(atoms, [int(size)], niggli_reduce=False, symprec=symprec):
        transform = np.linalg.solve(cell.T, np.asarray(supercell.cell).T).T
        matrix = np.rint(transform).astype(int)
        if not np.allclose(transform, matrix, rtol=0, atol=1e-7):
            raise RuntimeError("icet returned a non-integer supercell transformation")
        _, operation = minkowski_reduce(matrix @ cell, pbc=pbc)
        result["all"].append(matrix)
        result["recommended"].append(operation @ matrix)
    return result

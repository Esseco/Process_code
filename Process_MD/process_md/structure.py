"""Crystal input and supercells, implemented with ASE."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from math import ceil
from numbers import Integral
from pathlib import Path
from typing import Sequence

import numpy as np
from ase import Atoms
from ase.build import find_optimal_cell_shape, make_supercell
from ase.io import read
from ase.neighborlist import neighbor_list

from .models import StructureInfo


def _validate_crystal(atoms: Atoms) -> None:
    if not isinstance(atoms, Atoms):
        raise TypeError("structure must be an ASE Atoms object")
    if len(atoms) == 0:
        raise ValueError("structure must contain atoms")
    if not np.isfinite(atoms.positions).all() or not np.isfinite(atoms.cell.array).all():
        raise ValueError("positions and cell must be finite")
    if np.linalg.det(atoms.cell.array) <= 0:
        raise ValueError("a full-rank, right-handed crystal cell is required")


def _matrix(value: Sequence[Sequence[int]] | np.ndarray) -> np.ndarray:
    raw = np.asarray(value)
    if (raw.shape != (3, 3) or raw.dtype.kind not in "iuf"
            or not np.isfinite(raw).all() or not np.equal(raw, np.rint(raw)).all()):
        raise ValueError("supercell_matrix must be a finite integer 3x3 matrix")
    matrix = raw.astype(int)
    if np.linalg.det(matrix) <= 0:
        raise ValueError("supercell_matrix must have a positive determinant")
    return matrix


def prepare_structure(
    source: Atoms | str | Path,
    *,
    target_atoms: int | None = None,
    supercell_matrix: Sequence[Sequence[int]] | np.ndarray | None = None,
    format: str | None = None,
) -> Atoms:
    """Read a crystal and optionally expand it without changing the input.

    Files use ASE format detection (POSCAR/CIF/extxyz, etc.); the first frame
    is selected for multi-frame files. target_atoms is a minimum, rounded up
    to whole input cells. ASE chooses a near-cubic integer supercell, which
    may be non-diagonal and requires full 3D PBC. Alternatively supply a
    positive-determinant matrix; periodic/nonperiodic vectors cannot mix.

    ASE arrays and PBC are preserved. process_md_source_index maps each
    output atom back to its original input index; duplicate indices after
    expansion are intentional. Current indices are the Atoms array indices.
    Attached calculators are not transferred to the returned copy.
    """
    if target_atoms is not None and supercell_matrix is not None:
        raise ValueError("target_atoms and supercell_matrix are mutually exclusive")
    if target_atoms is not None and (isinstance(target_atoms, bool)
                                     or not isinstance(target_atoms, Integral) or target_atoms <= 0):
        raise ValueError("target_atoms must be a positive integer")
    if isinstance(source, Atoms):
        atoms = source.copy()
    elif isinstance(source, (str, Path)):
        atoms = read(str(source), index=0, format=format)
    else:
        raise TypeError("source must be ASE Atoms or a structure file path")
    _validate_crystal(atoms)
    atoms.info = deepcopy(atoms.info)
    if "process_md_source_index" not in atoms.arrays:
        atoms.new_array("process_md_source_index", np.arange(len(atoms)))
    matrix = np.eye(3, dtype=int)
    if supercell_matrix is not None:
        matrix = _matrix(supercell_matrix)
        mixed_boundaries = atoms.pbc[:, None] != atoms.pbc[None, :]
        if np.any(matrix[mixed_boundaries] != 0):
            raise ValueError("supercell_matrix cannot mix periodic and nonperiodic vectors")
    elif target_atoms is not None and target_atoms > len(atoms):
        if not atoms.pbc.all():
            raise ValueError("target_atoms expansion requires 3D PBC; use an explicit supercell_matrix")
        matrix = find_optimal_cell_shape(atoms.cell.array, ceil(target_atoms / len(atoms)), "sc")
    if not np.array_equal(matrix, np.eye(3, dtype=int)):
        metadata = atoms.info
        atoms = make_supercell(atoms, matrix, order="cell-major")
        atoms.info = metadata
    atoms.info["process_md_supercell_matrix"] = np.asarray(matrix).tolist()
    return atoms


def get_structure_info(atoms: Atoms) -> StructureInfo:
    """Return atom counts, cell lengths (Å), angles (degrees) and volume (Å³)."""
    _validate_crystal(atoms)
    counts = dict(Counter(atoms.get_chemical_symbols()))
    return StructureInfo(
        n_atoms=len(atoms), elements=tuple(counts), element_counts=counts,
        cell_lengths_A=tuple(float(x) for x in atoms.cell.lengths()),
        cell_angles_deg=tuple(float(x) for x in atoms.cell.angles()),
        volume_A3=float(atoms.get_volume()), pbc=tuple(bool(x) for x in atoms.pbc),
    )


def estimate_hop_distance(atoms: Atoms, *, species: str = "Li") -> float:
    """Return the nearest occupied same-species separation in Å, including PBC.

    This is a cheap geometric hop-distance proxy, not a migration pathway.
    Vacant sites are absent from atoms; a reference site lattice or a caller
    override is needed when occupied-site spacing misrepresents the hop.
    A single mobile atom uses its periodic images. ASE handles triclinic PBC.
    """
    _validate_crystal(atoms)
    if not atoms.pbc.all():
        raise ValueError("Hop-distance estimation requires full 3D PBC")
    selected = [i for i, symbol in enumerate(atoms.get_chemical_symbols()) if symbol == species]
    if not selected:
        raise ValueError(f"No {species} atoms found")
    mobile = atoms[selected]
    # A basis translation bounds the nearest distance, even for one ion.
    cutoff = float(min(mobile.cell.lengths())) * (1 + 1e-8)
    distances = neighbor_list("d", mobile, cutoff, self_interaction=False)
    if not len(distances) or np.any(distances <= 1e-8):
        raise ValueError("Cannot infer a positive hop distance; check overlapping mobile sites")
    return float(np.min(distances))

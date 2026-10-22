"""Fixed-cell trajectory adaptation; coordinate reconstruction uses pymatgen."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Iterable, Literal

import numpy as np
from ase import Atoms
from ase.io import iread


def read_positions(
    trajectory: str | Path | Iterable[Atoms],
    *,
    coordinate_mode: Literal["unwrapped", "wrapped"] = "unwrapped",
) -> tuple[Atoms, np.ndarray]:
    """Return an initial structure copy and continuous positions (frame, atom, xyz).

    Use unwrapped for Process_MLIP MD. Wrapped data are reconstructed using
    pymatgen Trajectory.to_displacements/to_positions, with its assumption
    that saved-frame fractional increments are resolvable within half a cell.
    No algorithm can infer multiple crossings from sparse wrapped snapshots.

    Cell, PBC, elements and atom order must be constant. Same-element identity
    permutations cannot be detected without persistent trajectory identifiers.
    This in-memory adapter stores coordinates only, not copies of every Atoms.
    """
    if coordinate_mode not in ("unwrapped", "wrapped"):
        raise ValueError("coordinate_mode must be unwrapped or wrapped")
    if isinstance(trajectory, (str, Path)):
        frames = iread(str(trajectory), index=":")
    elif isinstance(trajectory, Atoms):
        raise TypeError("trajectory must contain frames, not a single Atoms object")
    else:
        frames = iter(trajectory)
    first = None
    coordinates = []
    for frame in frames:
        if not isinstance(frame, Atoms) or not len(frame):
            raise ValueError("trajectory frames must be nonempty ASE Atoms")
        if (not np.isfinite(frame.positions).all() or not np.isfinite(frame.cell.array).all()
                or np.linalg.det(frame.cell.array) <= 0 or not frame.pbc.all()):
            raise ValueError("trajectory requires finite positions and a right-handed 3D periodic cell")
        if first is None:
            first = frame.copy()
            first.info = deepcopy(frame.info)
        elif (not np.array_equal(frame.numbers, first.numbers)
              or not np.array_equal(frame.pbc, first.pbc)):
            raise ValueError("trajectory atom identities/order and PBC must remain constant")
        elif not np.allclose(frame.cell.array, first.cell.array, rtol=1e-9, atol=1e-8):
            raise ValueError("trajectory requires a fixed cell")
        coordinates.append(frame.positions.copy())
    if first is None:
        raise ValueError("trajectory contains no frames")
    positions = np.asarray(coordinates)
    if coordinate_mode == "wrapped":
        from pymatgen.core.trajectory import Trajectory

        native = Trajectory(
            species=first.get_chemical_symbols(),
            coords=positions @ np.linalg.inv(first.cell.array),
            lattice=first.cell.array,
        )
        native.to_displacements()
        native.to_positions()
        positions = np.asarray(native.coords) @ first.cell.array
    return first, positions

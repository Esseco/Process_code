"""Surface-atom manipulation for slab models.

Utilities for identifying symmetry-equivalent surface atoms, generating
disordered surface configurations via ``gen_ESGS_structure``, and
removing duplicate structures during screening.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from pymatgen.core import Element, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.transformations.standard_transformations import (
    OxidationStateDecorationTransformation,
)

from Process_Struct import deduplicate
from Process_Vasp import gen_ESGS_structure

from .Fix_atoms import SurfaceFixer

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Commonly encountered oxidation states in Li-rich / O-redox cathodes.
DEFAULT_OXIDATION_STATES: dict[str, int] = {
    "Na": 1, "O": -2, "H": 3, "Li": 1, "Mg": 2, "Al": 3,
    "K": 1, "Ca": 2, "Sc": 3, "Ti": 4, "V": 3, "Cr": 3,
    "Mn": 3, "Fe": 3, "Co": 3, "Ni": 3, "Cu": 2, "Zn": 2,
    "Sr": 3, "Zr": 3, "Nb": 3, "Mo": 3, "Tc": 3, "Ru": 3,
    "Cd": 3,
}

#: Symmetry tolerance used by ``SpacegroupAnalyzer``.
SYMPREC: float = 1e-2

#: Distance tolerance (Å) for matching symmetry-equivalent positions.
SYM_DIST_TOL: float = 1e-2

#: Z-distance threshold (Å) for grouping surface atoms into sub-layers.
SURFACE_Z_DISTANCE: float = 0.5

#: Atom removal step size when generating disordered surfaces.
INTER_ATOM_STEP: int = 2

#: Number of trial structures passed to ``gen_ESGS_structure``.
NSTRUCT: int = 10

#: Maximum number of candidate structures to keep per composition.
SELECT_S: int = 5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_symmetry_atom(
    struct: Structure,
    index_list: list[int] | None = None,
) -> dict[str, list[int | None]]:
    """Find symmetry-equivalent partners for each atom in *index_list*.

    For each atom index, returns the index of a symmetry-equivalent
    atom (different from itself) if one exists within the tolerance
    ``SYM_DIST_TOL``, otherwise ``None``.

    Args:
        struct: A pymatgen ``Structure``.
        index_list: Atom indices to query.  If ``None``, an empty list
            is used.

    Returns:
        Dictionary with keys ``init_list`` (original indices) and
        ``sym_list`` (partner index or ``None`` for each).
    """
    if index_list is None:
        index_list = []

    sga = SpacegroupAnalyzer(struct, symprec=SYMPREC)
    ops = sga.get_symmetry_operations()
    coords = struct.frac_coords

    def _find_symmetric_partner(idx: int) -> int | None:
        """Return a symmetry-equivalent index for *idx*, or ``None``."""
        p = coords[idx]
        for op in ops:
            q = op.operate(p) % 1
            d = np.linalg.norm(coords - q, axis=1)
            j = np.argmin(d)
            if j != idx and d[j] < SYM_DIST_TOL:
                return int(j)
        return None

    results_dict = [_find_symmetric_partner(i) for i in index_list]
    return {
        "init_list": index_list,
        "sym_list": results_dict,
    }


def sym_surface_remove_atoms_single(
    struct: Structure,
    tar_dir: Path,
    inter_atom: int = INTER_ATOM_STEP,
    nstr: int = NSTRUCT,
    select_s: int = SELECT_S,
) -> str | None:
    """Generate disordered surface configurations for single-element surfaces.

    Designed for slabs whose top and bottom surfaces each consist of a
    single element type.  The workflow:

    1. Identify surface atoms via ``SurfaceFixer``.
    2. Replace surface atoms with hydrogen.
    3. Apply a solid-solution (H / original element) disorder.
    4. Generate candidate structures with ``gen_ESGS_structure``.
    5. Keep only structures where the original element is balanced
       between top and bottom surfaces.

    Results are written as POSCAR files under *tar_dir*.

    Args:
        struct: Slab structure (must have ``selective_dynamics`` site
            property).
        tar_dir: Output directory for POSCAR files.
        inter_atom: Atom-removal step size for composition sweeping.
        nstr: Number of trial structures per composition.
        select_s: Maximum structures to keep per composition.

    Returns:
        ``"not single Surface"`` if the surface is not single-element
        on both sides; otherwise ``None`` (results written to disk).
    """
    struct.remove_site_property("selective_dynamics")

    sf = SurfaceFixer(struct)
    info = sf.get_surface_atoms(distance=SURFACE_Z_DISTANCE)

    # Require exactly one element species on each surface
    if not (len(info["top_info"]) == 1 and len(info["bottom_info"]) == 1):
        return "not single Surface"

    surface_element: str = next(iter(info["top_info"]))
    surf_idx: list[int] = [i[1] for i in info["top"]] + [i[1] for i in info["bottom"]]
    el_num: int = len(surf_idx)

    # Save original structure as reference
    struct.sort().to(fmt="poscar", filename=str(tar_dir / "1_1_0.vasp"))

    oxi = OxidationStateDecorationTransformation(DEFAULT_OXIDATION_STATES)

    for atom_inter in range(el_num - inter_atom, 0, -inter_atom):
        frac = atom_inter / el_num

        s = struct.copy()
        for i in surf_idx:
            s.replace(i, "H")

        s.replace_species({"H": {"H": frac}})

        disordered = oxi.apply_transformation(s)
        structs = gen_ESGS_structure(disordered, nstr)

        keep: list[Structure] = []
        for ss in structs:
            ss.replace_species({"H3+": {surface_element: 1}})
            sf2 = SurfaceFixer(ss).get_surface_atoms(distance=SURFACE_Z_DISTANCE)
            if sf2["top_info"].get(surface_element, 0) == sf2["bottom_info"].get(
                surface_element, 0
            ):
                keep.append(ss)

        keep = deduplicate(keep)

        f_str = str(Fraction(atom_inter, el_num)).replace("/", "_")

        for i, st in enumerate(keep[: select_s + 1]):
            st.sort().to(fmt="poscar", filename=str(tar_dir / f"{f_str}_{i}.vasp"))

    return None

"""Utilities for inspecting Wyckoff sites in crystal structures."""

from typing import TypedDict

from pymatgen.core import PeriodicSite, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer


class WyckoffSiteGroup(TypedDict):
    """One group of symmetry-equivalent sites."""

    element: str
    wyckoff: str
    indices: list[int]
    sites: list[PeriodicSite]


def get_wyckoff_sites(
    structure: Structure,
    symprec: float = 0.01,
    angle_tolerance: float = 5.0,
) -> list[WyckoffSiteGroup]:
    """Return the element, Wyckoff label, and sites for each equivalent group.

    Args:
        structure: Structure to analyze.
        symprec: Cartesian distance tolerance used to determine symmetry, in angstrom.
        angle_tolerance: Angle tolerance used to determine symmetry, in degrees.

    Returns:
        A list of dictionaries. Each dictionary describes one symmetry-equivalent
        group and contains ``element``, ``wyckoff``, ``indices``, and ``sites``.
        ``sites`` contains the corresponding sites from the input structure.

    Raises:
        ValueError: If the structure is empty or a tolerance is not positive.
    """
    if not structure:
        raise ValueError("structure must contain at least one site")
    if symprec <= 0 or angle_tolerance <= 0:
        raise ValueError("symprec and angle_tolerance must be positive")

    symmetrized = SpacegroupAnalyzer(
        structure,
        symprec=symprec,
        angle_tolerance=angle_tolerance,
    ).get_symmetrized_structure()

    groups: list[WyckoffSiteGroup] = []
    for wyckoff, indices in zip(
        symmetrized.wyckoff_symbols,
        symmetrized.equivalent_indices,
        strict=True,
    ):
        site_indices = [int(index) for index in indices]
        representative = structure[site_indices[0]]
        elements = sorted(
            {element.symbol for element in representative.species.elements}
        )
        groups.append(
            {
                "element": "/".join(elements),
                "wyckoff": wyckoff,
                "indices": site_indices,
                "sites": [structure[index] for index in site_indices],
            }
        )

    return groups

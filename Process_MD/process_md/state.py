"""Describe actual composition and reference-relative mobile-ion occupancy."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from numbers import Integral

from ase import Atoms
from ase.data import atomic_numbers


@dataclass(frozen=True)
class AlkaliState:
    """Composition counts and fractions for one explicitly supplied structure.

    Fractions are None without a matched-cell reference count. A removed
    fraction is a composition descriptor, not a universal definition of SOC.
    """

    n_atoms: int
    formula: str
    element_counts: dict[str, int]
    mobile_species: str
    n_mobile_atoms: int
    reference_mobile_atoms: int | None = None
    occupancy_fraction: float | None = None
    removed_fraction: float | None = None
    configuration_id: str | None = None


def describe_alkali_state(
    atoms: Atoms,
    *,
    mobile_species: str = "Li",
    reference_mobile_atoms: int | None = None,
    configuration_id: str | None = None,
) -> AlkaliState:
    """Count a real element in a nonempty ASE structure without modifying it.

    Zero mobile atoms are allowed for a fully deintercalated structure.
    reference_mobile_atoms, when supplied, must be a positive integer at
    least as large as the current mobile count. It must count the same
    species in a reference with exactly the same cell multiplicity and
    framework normalization as atoms; a primitive-cell count cannot be
    compared directly with a supercell count. The caller must establish
    this match: a scalar reference count cannot verify it.

    occupancy_fraction = current/reference and removed_fraction = 1 minus
    occupancy_fraction. Neither fraction assigns a universal SOC convention.
    No sites, vacancies, configurations, or model predictions are generated.
    """
    if not isinstance(atoms, Atoms):
        raise TypeError("atoms must be an ASE Atoms object")
    if len(atoms) == 0:
        raise ValueError("atoms must be nonempty")
    if not isinstance(mobile_species, str) or atomic_numbers.get(mobile_species, 0) <= 0:
        raise ValueError("mobile_species must be a real element symbol")

    counts = dict(Counter(atoms.get_chemical_symbols()))
    n_mobile = counts.get(mobile_species, 0)
    occupancy = removed = None
    if reference_mobile_atoms is not None:
        if (isinstance(reference_mobile_atoms, bool)
                or not isinstance(reference_mobile_atoms, Integral)
                or reference_mobile_atoms <= 0 or reference_mobile_atoms < n_mobile):
            raise ValueError("reference_mobile_atoms must be a positive integer >= the mobile count")
        reference_mobile_atoms = int(reference_mobile_atoms)
        occupancy = n_mobile / reference_mobile_atoms
        removed = 1.0 - occupancy

    return AlkaliState(
        n_atoms=len(atoms), formula=atoms.get_chemical_formula(mode="hill"),
        element_counts=counts, mobile_species=mobile_species, n_mobile_atoms=n_mobile,
        reference_mobile_atoms=reference_mobile_atoms, occupancy_fraction=occupancy,
        removed_fraction=removed, configuration_id=configuration_id,
    )

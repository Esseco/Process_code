"""Surface atom fixing utilities for slab models.

Provides :class:`SurfaceFixer` for identifying and constraining surface/bulk
atoms in both ASE and pymatgen structure backends.
"""

from collections import Counter
from typing import Any

import numpy as np
from ase.constraints import FixAtoms
from pymatgen.analysis.local_env import CrystalNN
from pymatgen.io.ase import AseAtomsAdaptor


class SurfaceFixer:
    """Identify and fix atomic layers in slab structures.

    Supports both ASE ``Atoms`` and pymatgen ``Structure`` / ``Slab``
    backends.  Uses coordination-number (CN) heuristics to separate
    surface atoms from bulk atoms, and provides several strategies for
    choosing which atoms to fix (constrain) during a relaxation.

    Attributes:
        structure: The input structure (ASE or pymatgen).
        backend: ``"ase"`` or ``"pymatgen"``.
        coords: Cartesian coordinates (N, 3).
        n_atoms: Total number of atoms.
        z: Cartesian z coordinates of all atoms.
        zmax: Maximum z value.
        zmin: Minimum z value.
        z_center: Midpoint between zmax and zmin.
        frac_z: Fractional c-direction coordinates of all atoms.
    """

    def __init__(self, structure: Any) -> None:
        """Initialize the fixer from an ASE or pymatgen structure.

        Args:
            structure: An ``ase.Atoms`` or ``pymatgen.core.Structure`` (or
                subclass such as ``Slab``).

        Raises:
            TypeError: If *structure* is neither an ASE nor a pymatgen type.
        """
        self.structure = structure

        if hasattr(structure, "positions"):  # ASE
            self.backend = "ase"
            self.coords = structure.positions
            self.n_atoms = len(structure)
            self.mg_struct = AseAtomsAdaptor.get_structure(structure)
        elif hasattr(structure, "cart_coords"):  # pymatgen
            self.backend = "pymatgen"
            self.coords = structure.cart_coords
            self.n_atoms = len(structure)
            self.mg_struct = structure
        else:
            raise TypeError("Unsupported structure type")

        # Cartesian z information
        self.z: np.ndarray = self.coords[:, 2]
        self.zmax: float = float(self.z.max())
        self.zmin: float = float(self.z.min())
        self.z_center: float = (self.zmax + self.zmin) / 2

        # Fractional c-direction component
        if self.backend == "ase":
            self.frac_z: np.ndarray = self.structure.get_scaled_positions()[:, 2]
        else:
            self.frac_z: np.ndarray = self.mg_struct.frac_coords[:, 2]

        self._cn_cache: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_cn(self) -> np.ndarray:
        """Compute (and cache) coordination numbers via CrystalNN.

        Returns:
            Array of coordination numbers, one per atom.
        """
        if self._cn_cache is None:
            cnn = CrystalNN()
            cn_list = []
            for i in range(self.n_atoms):
                try:
                    cn = cnn.get_cn(self.mg_struct, i)
                except Exception:
                    cn = 0
                cn_list.append(cn)
            self._cn_cache = np.array(cn_list)
        return self._cn_cache

    def get_symbol(self, i: int) -> str:
        """Return the element symbol of atom *i*.

        Args:
            i: Atom index.

        Returns:
            Element symbol string (e.g. ``"Ti"``).
        """
        if self.backend == "ase":
            return self.structure[i].symbol
        return self.structure[i].species_string

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze_slab(self, target_cn: int = 6) -> tuple[float, int, list[list[int]]]:
        """Separate atoms into top-surface, bulk, and bottom-surface layers.

        Atoms whose coordination number is below *target_cn* are
        considered surface atoms; the rest are bulk.

        Args:
            target_cn: Minimum coordination number for a bulk atom.

        Returns:
            A tuple of ``(thickness, n_layers, layers)`` where *layers*
            is ``[bottom_indices, bulk_indices, top_indices]``.
        """
        cn = self._get_cn()
        surface_mask = cn < target_cn

        top_indices = np.where(surface_mask & (self.z > self.z_center))[0].tolist()
        bottom_indices = np.where(surface_mask & (self.z <= self.z_center))[0].tolist()
        bulk_indices = np.where(~surface_mask)[0].tolist()

        thickness = self.zmax - self.zmin
        layers: list[list[int]] = [bottom_indices, bulk_indices, top_indices]

        return round(thickness, 2), len(layers), layers

    def get_surface_atoms(
        self,
        target_cn: int = 6,
        distance: float | None = None,
    ) -> dict[str, Any]:
        """Return detailed surface-atom information.

        Args:
            target_cn: Minimum coordination number for a bulk atom.
            distance: If given, group surface atoms by z proximity
                (used to resolve sub-layer structure).

        Returns:
            Dictionary with keys ``top_info``, ``bottom_info``, ``top``,
            ``bottom``.  When *distance* is provided also includes
            ``top_groups``, ``bottom_groups``, ``n_top_groups``,
            ``n_bottom_groups``.
        """
        _, _, layers = self.analyze_slab(target_cn)
        bottom_indices = layers[0]
        top_indices = layers[-1]

        top_symbols = [self.get_symbol(i) for i in top_indices]
        bottom_symbols = [self.get_symbol(i) for i in bottom_indices]

        results: dict[str, Any] = {
            "top_info": dict(Counter(top_symbols)),
            "bottom_info": dict(Counter(bottom_symbols)),
            "top": [[self.structure[i], i] for i in top_indices],
            "bottom": [[self.structure[i], i] for i in bottom_indices],
        }

        if distance is not None:

            def _group_by_z(indices: list[int]) -> list[list[int]]:
                """Group *indices* into sub-layers by z proximity."""
                if not indices:
                    return []
                zvals = [(i, self.z[i]) for i in indices]
                zvals.sort(key=lambda x: x[1])
                groups = [[zvals[0][0]]]
                for k in range(1, len(zvals)):
                    if abs(zvals[k][1] - zvals[k - 1][1]) > distance:
                        groups.append([zvals[k][0]])
                    else:
                        groups[-1].append(zvals[k][0])
                return groups

            results["top_groups"] = _group_by_z(top_indices)
            results["bottom_groups"] = _group_by_z(bottom_indices)
            results["n_top_groups"] = len(results["top_groups"])
            results["n_bottom_groups"] = len(results["bottom_groups"])

        return results

    # ------------------------------------------------------------------
    # Fixing strategies  (each returns the modified structure)
    # ------------------------------------------------------------------

    def fix_center_layers(self, target_cn: int = 6) -> Any:
        """Fix (constrain) the bulk layer identified by CN analysis.

        Args:
            target_cn: Minimum coordination number for a bulk atom.

        Returns:
            The structure with the bulk layer fixed.
        """
        _, _, layers = self.analyze_slab(target_cn)
        return self._apply_fix(layers[1])

    def fix_center_distance(self, thickness: float = 4.0) -> Any:
        """Fix atoms within a slab of *thickness* centered on z_center.

        Args:
            thickness: Total thickness (Å) of the fixed central region.

        Returns:
            The structure with the central region fixed.
        """
        fixed_indices = np.where(abs(self.z - self.z_center) < thickness / 2)[0]
        return self._apply_fix(fixed_indices)

    def fix_center_fraction(self, fraction: float = 1 / 3) -> Any:
        """Fix a given fraction of atoms closest to z_center.

        Atoms are sorted by distance from the slab centre; the
        closest *fraction* are fixed.

        Args:
            fraction: Fraction of total atoms to fix (default 1/3).

        Returns:
            The structure with the closest atoms fixed.
        """
        dist = np.abs(self.z - self.z_center)
        sorted_indices = np.argsort(dist)
        n_fix = int(self.n_atoms * fraction)
        return self._apply_fix(sorted_indices[:n_fix])

    def fix_bottom_fraction(self, fraction: float = 0.5) -> Any:
        """Fix atoms in the bottom *fraction* of the c-axis range.

        Unlike the atom-count-based ``fix_center_fraction``, this
        method uses the fractional c-coordinate range, so that all
        atoms on the same c-layer are either fully fixed or fully free.

        Args:
            fraction: Fraction of the c-axis range to fix, measured from
                the bottom (default 0.5).  Must be in (0, 1].

        Returns:
            The structure with the selected bottom region fixed.

        Raises:
            ValueError: If *fraction* is not in (0, 1].
        """
        if not 0 < fraction <= 1:
            raise ValueError(f"fraction must be in (0, 1], got {fraction}")

        c_min = self.frac_z.min()
        c_range = self.frac_z.max() - c_min
        c_cutoff = c_min + fraction * c_range
        fixed_indices = np.where(self.frac_z <= c_cutoff)[0]
        return self._apply_fix(fixed_indices)

    def fix_bottom_distance(self, distance: float = 2.0) -> Any:
        """Fix atoms within *distance* (Å) of the bottom of the slab.

        Args:
            distance: Maximum distance from ``zmin`` to fix (Å).

        Returns:
            The structure with the bottom region fixed.
        """
        fixed_indices = np.where(self.z - self.zmin < distance)[0]
        return self._apply_fix(fixed_indices)

    # ------------------------------------------------------------------
    # Constraint application
    # ------------------------------------------------------------------

    def _apply_fix(self, fixed_indices: np.ndarray | list[int]) -> Any:
        """Apply a ``FixAtoms`` (ASE) or ``selective_dynamics`` (pymatgen) constraint.

        Args:
            fixed_indices: Indices of atoms to fix.

        Returns:
            The structure with the constraint applied.
        """
        fixed_set = set(fixed_indices)

        if self.backend == "ase":
            mask = [i in fixed_set for i in range(self.n_atoms)]
            self.structure.set_constraint(FixAtoms(mask=mask))
        else:
            sd = [[True, True, True] for _ in range(self.n_atoms)]
            for i in fixed_set:
                sd[i] = [False, False, False]
            self.structure.add_site_property("selective_dynamics", sd)

        return self.structure

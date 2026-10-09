"""Slab generation and face analysis for Li-rich / O-redox cathode materials.

The central class, :class:`LOSlabProcessor`, wraps pymatgen's
``SlabGenerator`` and an oxidation-state transformer to automate the
creation, analysis and export of surface slabs for DFT input.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from pymatgen.core.surface import (
    Slab,
    SlabGenerator,
    Structure,
    get_symmetrically_distinct_miller_indices,
)


class LOSlabProcessor:
    """Generate and classify surface slabs for a bulk structure.

    The processor iterates over symmetrically distinct Miller indices,
    creates slab models, and applies an oxidation-state transformation
    to analyse polarity and symmetry.  Results are written as VASP
    POSCAR files into an output directory tree.

    Attributes:
        struct: The bulk pymatgen ``Structure``.
        oxi: An oxidation-state transformer (e.g.
            ``OxidationStateDecorationTransformation``).
        base_dir: Root output directory as a ``Path``.
    """

    def __init__(
        self,
        structure: Structure,
        oxi_transformer: Any,
        output_dir: str = "output",
    ) -> None:
        """Initialize the processor.

        Args:
            structure: Bulk pymatgen structure.
            oxi_transformer: Callable / transformation that decorates a
                structure with oxidation states.
            output_dir: Root directory for POSCAR output.
        """
        self.struct = structure
        self.oxi = oxi_transformer
        self.base_dir = Path(output_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Miller-index helpers
    # ------------------------------------------------------------------

    def get_miller_indices(self, max_index: int) -> list[tuple[tuple[int, ...], float]]:
        """Return symmetrically distinct Miller indices sorted by d-spacing.

        Args:
            max_index: Maximum Miller index to consider.

        Returns:
            List of ``((h, k, l), d_hkl)`` tuples, descending by
            d-spacing (largest interplanar distance first).
        """
        miller_list = get_symmetrically_distinct_miller_indices(
            self.struct, max_index=max_index
        )
        lattice = self.struct.lattice
        plane_data = [(hkl, lattice.d_hkl(hkl)) for hkl in miller_list]
        return sorted(plane_data, key=lambda x: x[1], reverse=True)

    # ------------------------------------------------------------------
    # Slab generation
    # ------------------------------------------------------------------

    def generate_slabs(
        self,
        miller_index: tuple[int, ...],
        min_slab_size: float = 15.0,
        min_vacuum_size: float = 12.0,
    ) -> tuple[list[Slab], SlabGenerator]:
        """Generate all unique slabs for a given Miller index.

        Args:
            miller_index: (h, k, l) tuple.
            min_slab_size: Minimum slab thickness (Å).
            min_vacuum_size: Minimum vacuum thickness (Å).

        Returns:
            A tuple of ``(slabs, generator)``.
        """
        gen = SlabGenerator(
            initial_structure=self.struct,
            miller_index=miller_index,
            min_slab_size=min_slab_size,
            min_vacuum_size=min_vacuum_size,
            center_slab=True,
            primitive=True,
            lll_reduce=True,
        )
        return gen.get_slabs(), gen

    # ------------------------------------------------------------------
    # Face analysis
    # ------------------------------------------------------------------

    def analyze_face(self, slab_struct: Structure) -> dict[str, Any]:
        """Analyze polarity and symmetry of a slab.

        An oxidation-state transformation is applied to both the slab
        and the bulk before constructing the ``Slab`` analysis object.

        Args:
            slab_struct: A slab ``Structure`` with a ``miller_index``
                attribute.

        Returns:
            Dictionary with keys ``is_polar``, ``is_symmetric``, and
            ``slab_obj`` (the pymatgen ``Slab`` used for analysis).
        """
        s_slab = self.oxi.apply_transformation(slab_struct)
        s_bulk = self.oxi.apply_transformation(self.struct)

        my_slab = Slab(
            lattice=s_slab.lattice,
            species=s_slab.species,
            coords=s_slab.frac_coords,
            miller_index=slab_struct.miller_index,
            oriented_unit_cell=s_bulk,
            shift=0,
            scale_factor=np.eye(3),
        )

        return {
            "is_polar": my_slab.is_polar(),
            "is_symmetric": my_slab.is_symmetric(),
            "slab_obj": my_slab,
        }

    # ------------------------------------------------------------------
    # Main processing pipeline
    # ------------------------------------------------------------------

    def process_and_save(self, max_miller: int = 2) -> None:
        """Run the full slab-generation pipeline for all faces up to *max_miller*.

        Slabs are saved as POSCAR files under
        ``<base_dir>/Polar<p>_Sym<s>/``, where *p* and *s* are 0/1
        flags for polarity and symmetry.

        Non-symmetric or polar slabs are symmetrized via
        ``nonstoichiometric_symmetrized_slab``; if the slab is too thin
        for symmetrization a 2×2×1 supercell is tried first.

        Args:
            max_miller: Maximum Miller index to explore (default 2).
        """
        planes = self.get_miller_indices(max_miller)

        for hkl, _ in planes:
            print(f"Processing Miller Index: {hkl}")
            slabs, gen = self.generate_slabs(hkl)

            for i, s in enumerate(slabs):
                analysis = self.analyze_face(s)
                sym = analysis["is_symmetric"]
                pol = analysis["is_polar"]

                folder_name = f"Polar{int(pol)}_Sym{int(sym)}"
                target_path = self.base_dir / folder_name
                target_path.mkdir(exist_ok=True)

                if sym and not pol:
                    # Ideal stoichiometric slab — save directly.
                    filename = f"{hkl}_{i}.vasp"
                    s.sort().to(filename=str(target_path / filename), fmt="poscar")
                else:
                    ss_list = gen.nonstoichiometric_symmetrized_slab(s)

                    if not ss_list:
                        print(
                            f"  [Notice] Slab {i} too small for symmetrization. "
                            "Applying 2x2x1 supercell..."
                        )
                        s_super = s.copy()
                        s_super.make_supercell([[2, 0, 0], [0, 2, 0], [0, 0, 1]])
                        ss_list = gen.nonstoichiometric_symmetrized_slab(s_super)

                    for j, ss in enumerate(ss_list):
                        filename = f"{hkl}_{i}_{j}.vasp"
                        ss.sort().to(filename=str(target_path / filename), fmt="poscar")

"""Single-structure MACE relaxation without MC setup or trajectory output."""

from pathlib import Path

from ._relaxation import _relax_structure, _validate_relax_settings


def relax_structure_mace(
    structure,
    model_path,
    *,
    output_path=None,
    device="cuda",
    head=None,
    default_dtype="float64",
    enable_cueq=False,
    enable_symmetrix=False,
    symmetrix_use_kokkos=False,
    symmetrix_species=None,
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

    _validate_relax_settings(fmax, steps)
    calculator = create_mace_calculator(model_path, device=device, head=head,
                                         default_dtype=default_dtype,
                                         enable_cueq=enable_cueq,
                                         enable_symmetrix=enable_symmetrix,
                                         symmetrix_use_kokkos=symmetrix_use_kokkos,
                                         symmetrix_species=symmetrix_species)
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

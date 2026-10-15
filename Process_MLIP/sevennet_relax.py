"""Single-structure SevenNet-Omni relaxation using the shared ASE optimizer."""
import numpy as np

from .calculators import create_sevennet_calculator
from .mace_relax import _relax_structure


def relax_structure_sevennet(structure, model="7net-omni", *, output_path=None,
                            device="cpu", modal="mpa", fmax=0.05, steps=150,
                            relax_cell=True):
    """Return energy (eV), forces (eV/Å), convergence and selected modal.

    Inputs are a structure path, ASE Atoms or pymatgen Structure. Atoms are
    copied. Only output_path is written (VASP format, overwrites if present).
    No random sampling, trajectory or log. Named models may download weights;
    supply a trusted local checkpoint for offline repeatable calculations.
    """
    if not np.isfinite(fmax) or fmax <= 0:
        raise ValueError("fmax must be finite and positive")
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    calculator = create_sevennet_calculator(model, device=device, modal=modal)
    result = _relax_structure(structure, calculator, output_path=output_path,
                              fmax=fmax, steps=steps, relax_cell=relax_cell)
    result["sevennet_modal"] = modal
    return result

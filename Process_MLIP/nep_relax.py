"""Single-structure NEP relaxation using the shared ASE optimizer."""
from ._relaxation import _relax_structure, _validate_relax_settings
from .nep import create_nep_calculator


def relax_structure_nep(structure, model_path, *, output_path=None, backend="cpu",
                        gpumd_command=None, directory=None, fmax=0.05, steps=150,
                        relax_cell=True):
    """Relax one structure with a Calorine NEP calculator."""
    _validate_relax_settings(fmax, steps)
    calculator = create_nep_calculator(
        model_path, backend=backend, gpumd_command=gpumd_command, directory=directory
    )
    result = _relax_structure(
        structure, calculator, output_path=output_path, fmax=fmax,
        steps=steps, relax_cell=relax_cell,
    )
    result["nep_backend"] = backend
    result["nep_model_path"] = str(model_path)
    return result

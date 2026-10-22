"""Lazy adapters to the existing Process_MLIP calculator factories."""
from pathlib import Path
from typing import Any


def create_mace_calculator(
    model_path: str | Path,
    *,
    device: str = "cuda",
    head: str | None = None,
    default_dtype: str = "float64",
    enable_cueq: bool = False,
    enable_symmetrix: bool = False,
    symmetrix_use_kokkos: bool = False,
    symmetrix_species=None,
):
    """Delegate a local MACE checkpoint to Process_MLIP without changing options.

    Only this explicit call imports the backend and loads weights. Head
    selection, precision and acceleration retain the upstream factory's
    semantics; no dependency installation or model fallback is performed.
    Supply the OMat checkpoint path explicitly rather than the MH-1 preset.
    """
    from Process_MLIP.calculators import create_mace_calculator as factory

    return factory(
        model_path, device=device, head=head, default_dtype=default_dtype,
        enable_cueq=enable_cueq, enable_symmetrix=enable_symmetrix,
        symmetrix_use_kokkos=symmetrix_use_kokkos, symmetrix_species=symmetrix_species,
    )


def create_chgnet_calculator(
    model_path: str | Path | None = None,
    *,
    device: str = "cpu",
    model_name: str = "0.3.0",
    model: Any = None,
):
    """Delegate to Process_MLIP's existing CHGNet factory.

    Only this explicit call imports CHGNet/torch and loads weights. Upstream
    may obtain weights if absent. No dependency installation, dtype change
    or fallback model is performed. CPU is the library's explicit default.
    """
    from Process_MLIP.calculators import create_chgnet_calculator as factory

    return factory(model_path=model_path, device=device, model_name=model_name, model=model)

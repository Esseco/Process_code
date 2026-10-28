"""Explicit model dispatch; loading remains owned by Process_MD/Process_MLIP."""
import os
from pathlib import Path

from process_md import (create_grace_calculator, create_mace_calculator,
                        create_nep_calculator, create_nequip_calculator,
                        create_orb_calculator, create_sevennet_calculator)

from .config import ScreeningConfig


def mace_model_path(config: ScreeningConfig) -> Path:
    source = config.model_path or os.environ.get("PROCESS_MD_MACE_MODEL")
    if not source:
        raise ValueError("Set model_path or PROCESS_MD_MACE_MODEL to the local MACE-OMat checkpoint")
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"MACE-OMat checkpoint does not exist: {path}")
    return path


def model_path_for_config(config: ScreeningConfig) -> Path:
    """Resolve an explicit local model path without downloading a checkpoint."""
    if config.model_type == "mace":
        return mace_model_path(config)
    if config.model_path is None:
        raise ValueError(f"model_path is required for model_type={config.model_type!r}")
    path = Path(config.model_path).expanduser().resolve()
    if config.model_type == "grace":
        valid = path.is_dir() and (path / "saved_model.pb").is_file()
    else:
        valid = path.is_file()
    if not valid:
        raise FileNotFoundError(f"{config.model_type} model does not exist at the required local path: {path}")
    return path


def create_default_calculator(config: ScreeningConfig, atoms=None):
    """Load the configured local model through Process_MD adapters."""
    model_path = model_path_for_config(config)
    if config.model_type == "sevennet":
        return create_sevennet_calculator(
            model_path, device=config.device, modal=config.modal, enable_flash=config.enable_flash,
        )
    if config.model_type == "orb":
        return create_orb_calculator(
            model_path, device=config.device, model_name=config.model_name or "orb-v3-conservative-inf-omat",
            precision=config.precision, compile=config.compile_model,
        )
    if config.model_type == "nep":
        backend = config.backend or ("gpu" if config.device.startswith("cuda") else "cpu")
        return create_nep_calculator(
            model_path, backend=backend, gpumd_command=config.gpumd_command,
        )
    if config.model_type == "grace":
        return create_grace_calculator(model_path, device=config.device, **config.model_options)
    if config.model_type == "nequip":
        return create_nequip_calculator(
            model_path, device=config.device,
            enable_openequivariance=config.enable_openequivariance,
            **config.model_options,
        )
    species = config.symmetrix_species
    if (species is None and config.enable_symmetrix and atoms is not None
            and model_path.suffix.lower() != ".json"):
        species = tuple(sorted(set(atoms.get_chemical_symbols())))
    return create_mace_calculator(model_path, device=config.device,
                                  default_dtype=config.default_dtype, head=None,
                                  enable_cueq=config.enable_cueq,
                                  enable_symmetrix=config.enable_symmetrix,
                                  symmetrix_use_kokkos=config.symmetrix_use_kokkos,
                                  symmetrix_species=None if species is None else list(species))

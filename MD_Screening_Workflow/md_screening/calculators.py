"""Default MACE-OMat loader; explicit ASE calculator injection is still allowed."""
import os
from pathlib import Path

from process_md import create_mace_calculator

from .config import ScreeningConfig


def mace_model_path(config: ScreeningConfig) -> Path:
    source = config.model_path or os.environ.get("PROCESS_MD_MACE_MODEL")
    if not source:
        raise ValueError("Set model_path or PROCESS_MD_MACE_MODEL to the local MACE-OMat checkpoint")
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"MACE-OMat checkpoint does not exist: {path}")
    return path


def create_default_calculator(config: ScreeningConfig, atoms=None):
    """Load the local model and limit Symmetrix conversion to simulated elements."""
    model_path = mace_model_path(config)
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

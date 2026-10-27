"""Defaults for a caller-prepared supercell; no simulation or model loading."""
from .config import ScreeningConfig


def screening_preset(**overrides) -> ScreeningConfig:
    """GPU MACE screening of an already prepared supercell.

    Full-site reference is supplied separately to run_md. Durations are ps;
    timestep is fs and trajectory_interval is an integer number of MD steps.
    Override any ScreeningConfig field; target_atoms=None preserves the input.
    compress_trajectory=True losslessly archives the completed MD trajectory.
    """
    defaults = dict(target_atoms=None, device="cuda", enable_symmetrix=True,
                    symmetrix_use_kokkos=True, compress_trajectory=True)
    defaults.update(overrides)
    return ScreeningConfig(**defaults)

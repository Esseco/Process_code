"""Shared configuration for eight independent 5000-step NVT benchmarks."""
from pathlib import Path
import os

# EDIT THESE PATHS ON THE CLUSTER. Repository root must contain Process_MLIP/.
PROJECT_ROOT = Path(os.environ.get("PYCODE_ROOT", "/path/to/Py-Code"))
STRUCTURE = Path("/path/to/initial.cif")
OUTPUT_ROOT = Path(__file__).resolve().parent / "results"

# Fill local checkpoints; paired baseline/accelerated runs share the SAME path.
MODEL_PATHS = {
    "mace_mh1": "/path/to/mace-mh-1.model",
    "mace_omat": "/path/to/mace-omat-0-medium.model",
    "sevennet_omni": "/path/to/checkpoint_sevennet_omni.pth",
    "sevennet_nano6": "/path/to/checkpoint_7net_nano_6.0.pth",
    "chgnet": "/path/to/chgnet.pth.tar",
}
DEVICE = "cuda"
# Symmetrix Kokkos target is determined by its installed build, not DEVICE.
SYMMETRIX_DEVICE = "cuda"       # CPU build: set "cpu"
SYMMETRIX_USE_KOKKOS = True     # native CPU float64: set False
SEVENNET_MODAL = "mpa"         # Nano single-modal checkpoint ignores this field

# Identical initial structure, seed, velocities and NVT settings for every case.
# No pre-relaxation: prevents different models from producing different inputs.
MD_PARAMETERS = {
    "temperature_K": 800,
    "steps": 5000,
    "timestep_fs": 1.0,
    "tdamp_fs": 100.0,
    "tchain": 3,
    "tloop": 1,
    "seed": 42,
    "initialize_velocities": True,
    "remove_com": True,
    "trajectory_interval": 10,
    "log_interval": 10,
    "measure_steps_per_second": True,
    "overwrite": False,
}

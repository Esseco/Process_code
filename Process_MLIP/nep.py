"""Lazy Calorine adapters for CPU and GPU NEP calculators."""
from pathlib import Path
import shutil


def create_nep_calculator(model_path, *, backend="cpu", gpumd_command=None,
                          directory=None):
    """Load a NEP4 model through Calorine's explicit CPU/GPU backend.

    ``backend='cpu'`` constructs ``CPUNEP``. ``backend='gpu'`` constructs
    ``GPUNEP`` and optionally forwards a GPUMD command and persistent working
    directory. Optional dependencies are imported only when this function is
    called; no fallback between CPU and GPU is attempted.
    """
    if backend not in ("cpu", "gpu"):
        raise ValueError("backend must be 'cpu' or 'gpu'")
    model = Path(model_path).expanduser()
    if not model.is_file():
        raise FileNotFoundError(f"NEP model not found: {model}")
    if gpumd_command is not None and not isinstance(gpumd_command, (str, Path)):
        raise TypeError("gpumd_command must be a command string/path or None")
    if directory is not None and not isinstance(directory, (str, Path)):
        raise TypeError("directory must be a path or None")

    if backend == "cpu":
        if gpumd_command is not None:
            raise ValueError("gpumd_command is only valid for the GPU backend")
        from calorine.calculators import CPUNEP
        calculator = CPUNEP(str(model))
    else:
        command = None
        if gpumd_command is not None:
            command_path = Path(gpumd_command).expanduser()
            if command_path.is_file():
                command = str(command_path.resolve())
            else:
                command = shutil.which(str(gpumd_command))
            if command is None:
                raise FileNotFoundError(f"GPUMD executable not found: {gpumd_command}")
        # Keep the scheduler's CUDA_VISIBLE_DEVICES instead of replacing it
        # with GPUNEP's default physical GPU index 0.
        kwargs = {"gpu_identifier_index": None}
        if command is not None:
            kwargs["command"] = command
        from calorine.calculators import GPUNEP
        calculator = GPUNEP(str(model), **kwargs)
    if directory is not None:
        setter = getattr(calculator, "set_directory", None)
        if not callable(setter):
            raise TypeError("NEP calculator does not support a persistent directory")
        setter(str(Path(directory).expanduser()))
    return calculator

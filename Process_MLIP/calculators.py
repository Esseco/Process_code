"""Lazy model loaders; importing this module never loads weights or downloads."""
from contextlib import nullcontext
from importlib.metadata import version
from pathlib import Path
import re
import os
import inspect

from .nep import create_nep_calculator


def _e3nn_import_context():
    # e3nn 0.4.x constants contain slice objects; torch >=2.6 defaults to
    # weights_only=True. Allow only this builtin during the library import.
    if tuple(int(part) for part in version("e3nn").split(".")[:2]) >= (0, 5):
        return nullcontext()
    import torch
    safe_globals = getattr(torch.serialization, "safe_globals", None)
    return safe_globals([slice]) if safe_globals else nullcontext()


def _symmetrix_species_from_atoms(model_path, enabled, species, structures):
    """Infer conversion species when structures are available to the caller."""
    if not enabled or species is not None or not model_path or Path(model_path).suffix.lower() == ".json":
        return species
    return sorted({symbol for atoms in structures for symbol in atoms.get_chemical_symbols()})


def create_mace_calculator(model_path, *, device="cuda", head=None,
                           default_dtype="float64", enable_cueq=False,
                           enable_symmetrix=False, symmetrix_use_kokkos=False,
                           symmetrix_species=None):
    """Load a local MACE checkpoint. MH-1 filenames default to omat_pbe.

    Only load trusted checkpoints: MACE deserializes Python model objects.
    Pass head explicitly for renamed multihead weights or other DFT tasks.
    """
    if type(enable_cueq) is not bool:
        raise TypeError("enable_cueq must be bool")
    if type(enable_symmetrix) is not bool or type(symmetrix_use_kokkos) is not bool:
        raise TypeError("Symmetrix switches must be bool")
    if enable_cueq and enable_symmetrix:
        raise ValueError("CuEq and Symmetrix are mutually exclusive")
    model = Path(model_path)
    if not model.is_file():
        raise FileNotFoundError(f"MACE model not found: {model}")
    selected_head = head
    if selected_head is None and re.search(r"mh[-_]?1(?!\d)", model.stem.lower()):
        selected_head = "omat_pbe"
    if enable_symmetrix:
        return _create_symmetrix_calculator(model, device, selected_head, default_dtype,
                                             symmetrix_use_kokkos, symmetrix_species)
    with _e3nn_import_context():
        from mace.calculators import MACECalculator
    if enable_cueq and "enable_cueq" not in inspect.signature(MACECalculator).parameters:
        raise TypeError("Installed MACECalculator does not expose enable_cueq; use a supported MACE version")
    kwargs = dict(model_paths=str(model), device=device, default_dtype=default_dtype,
                  enable_cueq=enable_cueq)
    if selected_head is not None:
        kwargs["head"] = selected_head
    return MACECalculator(**kwargs)


def _create_symmetrix_calculator(model, device, head, dtype, use_kokkos, species):
    """Official Symmetrix adapter; temporary conversion leaves weights untouched.

    Kokkos target is chosen at library build time, not by torch device. Only
    cpu/cuda accepted; indexed GPU selection is intentionally unsupported.
    Preconverted JSON carries its own head/species and needs no torch import.
    """
    if device not in ("cpu", "cuda"):
        raise ValueError("Symmetrix device must be cpu or cuda; select GPUs through the runtime environment")
    if device == "cuda" and not use_kokkos:
        raise ValueError("Symmetrix CUDA requires symmetrix_use_kokkos=True and a CUDA build")
    if dtype not in ("float32", "float64") or (dtype == "float32" and not use_kokkos):
        raise ValueError("Symmetrix requires float64 without Kokkos; Kokkos supports float32/float64")
    if species is not None:
        from ase.data import atomic_numbers
        if (not isinstance(species, (list, tuple)) or not species
                or any(not isinstance(s, str) or s not in atomic_numbers or s == "X" for s in species)):
            raise ValueError("symmetrix_species must be None or a nonempty list of element symbols")
    from symmetrix import Symmetrix
    if model.suffix.lower() == ".json":
        if head is not None or species is not None:
            raise ValueError("Preconverted Symmetrix JSON fixes head/species; set head=None and symmetrix_species=None")
        return Symmetrix(model_file=str(model), dtype=dtype, use_kokkos=use_kokkos)
    # Explicit conversion avoids upstream's open NamedTemporaryFile Windows
    # incompatibility, and flushes/closes JSON before the C++ evaluator reads it.
    import json
    from tempfile import TemporaryDirectory
    with _e3nn_import_context():
        from symmetrix.extract_mace_data import extract_mace_data
    import torch
    original_dtype = torch.get_default_dtype()
    try:
        data = extract_mace_data(str(model), species=species, head=head)
    finally:
        # Upstream multihead conversion can change torch's global default.
        torch.set_default_dtype(original_dtype)
    with TemporaryDirectory(prefix="mlip_symmetrix_") as temporary:
        converted = Path(temporary) / "model.json"
        converted.write_text(json.dumps(data), encoding="utf-8")
        return Symmetrix(model_file=str(converted), dtype=dtype, use_kokkos=use_kokkos)


def create_sevennet_calculator(model="7net-omni", *, device="cpu", modal="mpa",
                               enable_flash=False):
    """Load SevenNet-Omni by official name or trusted local checkpoint.

    Named models may download weights through SevenNet on first use. Local
    paths must exist. modal selects the DFT task (mpa, omat24, etc.); do not
    combine energies from different tasks. No dtype conversion is applied.
    """
    if type(enable_flash) is not bool:
        raise TypeError("enable_flash must be bool")
    # Upstream environment variables override False. Reject conflicts instead
    # of silently enabling a different backend than the requested config.
    for key in ("SEVENNET_ENABLE_CUEQ", "SEVENNET_ENABLE_OEQ"):
        if os.environ.get(key) == "1":
            raise ValueError(f"Unset {key}; this loader selects FlashTP explicitly")
    if os.environ.get("SEVENNET_ENABLE_FLASH") == "1" and not enable_flash:
        raise ValueError("Unset SEVENNET_ENABLE_FLASH to disable FlashTP")
    name = str(model)
    named_model = (re.fullmatch(r"(?:7net|sevennet)-[a-z0-9_.-]+", name.lower())
                   and Path(name).suffix.lower() not in (".pth", ".pt", ".ckpt", ".model"))
    if isinstance(model, Path) or not named_model:
        if not Path(model).is_file():
            raise FileNotFoundError(f"SevenNet checkpoint not found: {model}")
    if not isinstance(modal, str) or not modal.strip():
        raise ValueError("SevenNet-Omni requires an explicit nonempty modal")
    with _e3nn_import_context():
        from sevenn.calculator import SevenNetCalculator
    if enable_flash and "enable_flash" not in inspect.signature(SevenNetCalculator).parameters:
        raise TypeError("Installed SevenNetCalculator does not expose enable_flash; use a supported SevenNet version")
    return SevenNetCalculator(model=name, file_type="checkpoint", device=device,
                              modal=modal, enable_flash=enable_flash)


def create_chgnet_calculator(model_path=None, *, device="cuda", model_name="0.3.0",
                             model=None):
    """Load CHGNet pretrained version, trusted local checkpoint, or loaded model.

    The official calculator converts stress from GPa to ASE eV/Å³. Only one
    of model_path and model may be supplied; no dependencies are installed.
    """
    if model_path is not None and model is not None:
        raise ValueError("Supply model_path or model, not both")
    if model_path is not None and not Path(model_path).is_file():
        raise FileNotFoundError(f"CHGNet checkpoint not found: {model_path}")
    from chgnet.model.model import CHGNet
    from chgnet.model.dynamics import CHGNetCalculator
    if model is None:
        model = (CHGNet.from_file(str(model_path)) if model_path is not None
                 else CHGNet.load(model_name=model_name, use_device=device))
    return CHGNetCalculator(model=model, use_device=device)


def create_orb_calculator(model_path=None, *, device="cuda",
                           model_name="orb-v3-conservative-inf-omat",
                           precision="float32-highest", compile=False):
    """Load an ORB pretrained architecture, optionally with local weights.

    Supports the official model+adapter API and the older model-only API.
    model_path must match model_name's architecture. No fallback model is used.
    """
    if model_path is not None and not Path(model_path).is_file():
        raise FileNotFoundError(f"ORB weights not found: {model_path}")
    from orb_models.forcefield import pretrained
    name = model_name.replace("-", "_")
    if name.startswith("_") or not callable(getattr(pretrained, name, None)):
        raise ValueError(f"ORB pretrained loader not found: {model_name}")
    kwargs = dict(device=device, precision=precision, compile=compile)
    if model_path is not None:
        kwargs["weights_path"] = str(model_path)
    loaded = getattr(pretrained, name)(**kwargs)
    if isinstance(loaded, tuple):
        from orb_models.forcefield.inference.calculator import ORBCalculator
        model, adapter = loaded
        return ORBCalculator(model, atoms_adapter=adapter, device=device)
    from orb_models.forcefield.calculator import ORBCalculator
    return ORBCalculator(loaded, device=device)


def create_mlip_calculator(model="mace-mh1"):
    """Build exactly one calculator from a preset name or model_config dict."""
    from .model_config import _resolve_model_config
    config = _resolve_model_config(model)
    kind = config.pop("type")
    if kind == "sevennet":
        source = config.pop("model_path") or config.pop("model_name")
        config.pop("model_name", None)
        return create_sevennet_calculator(source, **config)
    factories = {"mace": create_mace_calculator, "chgnet": create_chgnet_calculator,
                 "orb": create_orb_calculator}
    if kind == "nep":
        return create_nep_calculator(**config)
    return factories[kind](**config)

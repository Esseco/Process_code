"""Pure configuration presets: no torch/model imports, loading or downloads."""
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path


_PRESETS = {
    "mace-mh1": dict(type="mace", model_path=str(Path(__file__).resolve().parents[1]
                                               / "MLIP_model/mace-mh-1.model"),
                     device="cuda", head="omat_pbe", default_dtype="float64",
                     enable_cueq=False, enable_symmetrix=False,
                     symmetrix_use_kokkos=False, symmetrix_species=None),
    "sevennet-omni": dict(type="sevennet", model_path=None, model_name="7net-omni",
                          device="cuda", modal="mpa", enable_flash=False),
    "chgnet": dict(type="chgnet", model_path=None, model_name="0.3.0", device="cuda"),
    "orb-v3": dict(type="orb", model_path=None,
                   model_name="orb-v3-conservative-inf-omat", device="cuda",
                   precision="float32-highest", compile=False),
}
_ALIASES = dict(mace="mace-mh1", sevennet="sevennet-omni", orb="orb-v3")


def model_config(preset="mace-mh1", **overrides):
    """Return an independent dict of model defaults with explicit overrides.

    Presets: mace-mh1, sevennet-omni, chgnet, orb-v3. Default device is cuda;
    accelerators default off. model_path overrides pretrained weights. This
    function does not check local files, import models, or download anything.
    """
    if not isinstance(preset, str):
        raise TypeError("preset must be a model preset name")
    name = _ALIASES.get(preset.lower(), preset.lower())
    if name not in _PRESETS:
        raise ValueError(f"Unknown model preset {preset!r}; choose {tuple(_PRESETS)}")
    result = deepcopy(_PRESETS[name])
    unknown = overrides.keys() - result.keys()
    if unknown:
        raise ValueError(f"Unknown parameters for {name}: {sorted(unknown)}")
    if "type" in overrides and overrides["type"] != result["type"]:
        raise ValueError("Select another preset to change model type")
    result.update(deepcopy(overrides))
    if isinstance(result["model_path"], Path):
        result["model_path"] = str(result["model_path"])
    for key in ("enable_cueq", "enable_symmetrix", "symmetrix_use_kokkos", "enable_flash", "compile"):
        if key in result and type(result[key]) is not bool:
            raise TypeError(f"{key} must be bool")
    if not isinstance(result["device"], str) or not result["device"]:
        raise ValueError("device must be a nonempty string")
    if result["model_path"] is not None and not isinstance(result["model_path"], str):
        raise TypeError("model_path must be a path string or None")
    if result["type"] == "mace":
        if result["enable_symmetrix"] and result["enable_cueq"]:
            raise ValueError("CuEq and Symmetrix are mutually exclusive")
        if not result["model_path"]:
            raise ValueError("MACE requires a local model_path")
        if result["default_dtype"] not in ("float32", "float64"):
            raise ValueError("MACE default_dtype must be float32 or float64")
        if result["head"] is not None and not isinstance(result["head"], str):
            raise TypeError("MACE head must be a string or None")
    else:
        if not isinstance(result["model_name"], str) or not result["model_name"]:
            raise ValueError("model_name must be a nonempty string")
    if result["type"] == "sevennet" and (
            not isinstance(result["modal"], str) or not result["modal"].strip()):
        raise ValueError("SevenNet requires a nonempty modal")
    if result["type"] == "orb" and result["precision"] not in (
            "float32-high", "float32-highest", "float64"):
        raise ValueError("Unsupported ORB precision")
    return result


def _resolve_model_config(model):
    if isinstance(model, str):
        return model_config(model)
    if not isinstance(model, Mapping) or "type" not in model:
        raise TypeError("model must be a preset name or a model_config dict")
    return model_config(model["type"], **dict(model))

"""Lazy ASE calculator factories. Optional MLIP libraries stay in their own environments."""
from ase.calculators.calculator import BaseCalculator
from pathlib import Path


_FACTORIES = {}


def register_model(name, factory):
    """Register factory(model_config_dict) -> ASE calculator; reject replacement."""
    if name in _FACTORIES:
        raise ValueError(f"Model type already registered: {name}")
    if not isinstance(name, str) or not name or not callable(factory):
        raise ValueError("Model type and callable factory are required")
    _FACTORIES[name] = factory


def _existing(config):
    from ..calculators import create_mlip_calculator
    from ..model_config import model_config
    options = dict(config["parameters"])
    if config["type"] == "nep":
        backend = options.get("backend", "cpu")
        if (backend == "cpu") != (config["device"] == "cpu"):
            raise ValueError("NEP backend and benchmark device must both select CPU or GPU")
        if backend == "gpu" and config["device"] not in ("cuda", "cuda:0"):
            raise ValueError("GPUNEP uses GPU 0; select a single GPU with CUDA_VISIBLE_DEVICES")
    else:
        options["device"] = config["device"]
    calculator = create_mlip_calculator(model_config(config["type"], **options))
    if config["type"] == "nep" and options.get("backend", "cpu") == "gpu":
        calculator.benchmark_external_gpu = True
    return calculator


def _emt(config):
    from ase.calculators.emt import EMT
    if config["device"] != "cpu":
        raise ValueError("EMT is a CPU demonstration calculator, not an MLIP")
    return EMT(**config["parameters"])


def _mattersim(config):
    from mattersim.forcefield import MatterSimCalculator
    options = dict(config["parameters"])
    path = options.pop("model_path", None)
    if not path:
        raise ValueError("MatterSim requires an explicit local model_path")
    return MatterSimCalculator(load_path=str(path), device=config["device"], **options)


def _grace(config):
    import tensorflow as tf
    from tensorpotential.calculator import TPCalculator
    options = dict(config["parameters"])
    path = options.pop("model_path", None)
    if not path or not (Path(path) / "saved_model.pb").is_file():
        raise ValueError("GRACE requires a SavedModel directory containing saved_model.pb")
    visible = tf.config.get_visible_devices("GPU")
    if config["device"] == "cpu" and visible:
        raise ValueError("GRACE CPU execution requires CUDA_VISIBLE_DEVICES=-1 before starting Python")
    if config["device"].startswith("cuda") and len(visible) != 1:
        raise ValueError("GRACE CUDA execution requires exactly one TensorFlow-visible GPU")
    calculator = TPCalculator(str(path), **options)
    calculator.benchmark_backend = "tensorflow"
    return calculator


def _nequip(config):
    options = dict(config["parameters"])
    path = options.pop("model_path", None)
    if not path or str(path).endswith(".nequip.zip"):
        raise ValueError("NequIP requires a compiled ASE model; compile the model package on target hardware first")
    from nequip.integrations.ase import NequIPCalculator
    return NequIPCalculator.from_compiled_model(compile_path=str(path), device=config["device"], **options)


def create_calculator(config):
    """Build one configured calculator without silent model/backend fallback."""
    kind = config["type"]
    if kind not in _FACTORIES:
        raise NotImplementedError(f"Adapter {kind!r} is not implemented; register_model(name, factory)")
    calculator = _FACTORIES[kind](config)
    if not isinstance(calculator, BaseCalculator):
        raise TypeError("Model factory must return an ASE BaseCalculator")
    required = {"energy", "forces", "stress"}
    missing = required - set(calculator.implemented_properties)
    if missing:
        raise ValueError(f"Calculator lacks required properties: {sorted(missing)}")
    return calculator


for _kind in ("mace", "sevennet", "orb", "chgnet", "nep"):
    register_model(_kind, _existing)
register_model("emt", _emt)
register_model("mattersim", _mattersim)
register_model("grace", _grace)
register_model("nequip", _nequip)

"""VASP public API with compatibility for the original flat module paths."""

from importlib import import_module as _import_module
import sys as _sys

from .input import *  # noqa: F403
from .output import *  # noqa: F403
from .input import __all__ as _input_all
from .output import __all__ as _output_all

__all__ = [*_input_all, *_output_all]

# Alias the actual module objects so old imports and mock.patch targets share
# the same globals as the implementations in the functional directories.
for _legacy, _target in {
    "generation": "inputs.generation",
    "incar": "inputs.incar",
    "excitation": "inputs.excitation",
    "dos": "results.dos",
    "reader": "results.reader",
    "status": "results.status",
    "magnetism": "results.magnetism",
    "structure": "structures.structure",
    "atomate_runner": "workflows.atomate_runner",
}.items():
    _module = _import_module(f".{_target}", __name__)
    _sys.modules[f"{__name__}.{_legacy}"] = _module
    globals()[_legacy] = _module

del _legacy, _target, _module, _import_module, _sys

"""Public API when Py-Code is on PYTHONPATH."""
import importlib.util
import sys

# Support the sibling source checkout without an editable installation.
if importlib.util.find_spec("process_md") is None:
    from Process_MD import process_md as _process_md
    sys.modules["process_md"] = _process_md

from .md_screening import *
from .md_screening import __all__, __version__
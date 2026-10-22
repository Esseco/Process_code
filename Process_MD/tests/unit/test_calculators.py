from pathlib import Path
import subprocess
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from process_md import create_mace_calculator
from process_md.md import create_mace_calculator as md_create_mace_calculator


@pytest.fixture
def upstream_factory(monkeypatch):
    package = ModuleType("Process_MLIP")
    package.__path__ = []
    calculators = ModuleType("Process_MLIP.calculators")
    calculators.create_mace_calculator = Mock()
    monkeypatch.setitem(sys.modules, "Process_MLIP", package)
    monkeypatch.setitem(sys.modules, "Process_MLIP.calculators", calculators)
    return calculators.create_mace_calculator


def test_mace_adapter_preserves_all_upstream_defaults(upstream_factory):
    checkpoint = Path("mace-omat-0-medium.model")
    result = create_mace_calculator(checkpoint)
    upstream_factory.assert_called_once_with(
        checkpoint, device="cuda", head=None, default_dtype="float64",
        enable_cueq=False, enable_symmetrix=False, symmetrix_use_kokkos=False,
        symmetrix_species=None,
    )
    assert result is upstream_factory.return_value
    assert md_create_mace_calculator is create_mace_calculator


@pytest.mark.parametrize("acceleration", [
    {"enable_cueq": True, "enable_symmetrix": False, "symmetrix_use_kokkos": False},
    {"enable_cueq": False, "enable_symmetrix": True, "symmetrix_use_kokkos": True},
])
def test_mace_adapter_forwards_explicit_options_without_conversion(upstream_factory, acceleration):
    checkpoint = Path("custom-multihead.model")
    elements = ["Na", "Mn", "O"]
    options = dict(device="cuda:1", head="selected_head", default_dtype="float32",
                   symmetrix_species=elements, **acceleration)
    result = create_mace_calculator(checkpoint, **options)
    upstream_factory.assert_called_once_with(checkpoint, **options)
    assert upstream_factory.call_args.kwargs["symmetrix_species"] is elements
    assert result is upstream_factory.return_value


def test_mace_backend_errors_propagate_without_fallback(upstream_factory):
    upstream_factory.side_effect = RuntimeError("requested backend is unavailable")
    with pytest.raises(RuntimeError, match="requested backend"):
        create_mace_calculator("local.model")
    assert upstream_factory.call_count == 1


def test_importing_mace_adapter_does_not_import_optional_backends():
    subprocess.run(
        [sys.executable, "-B", "-c",
         "from process_md import create_mace_calculator, create_chgnet_calculator; "
         "from process_md.md import create_mace_calculator as factory; "
         "import sys; assert factory is create_mace_calculator; "
         "assert all(name not in sys.modules for name in "
         "('Process_MLIP', 'mace', 'torch', 'chgnet', 'symmetrix', 'cuequivariance'))"],
        check=True, capture_output=True, text=True,
    )

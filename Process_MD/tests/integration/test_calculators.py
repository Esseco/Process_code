from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from process_md import create_chgnet_calculator, create_mace_calculator


def test_missing_weights_fail_before_loading_optional_dependencies(tmp_path):
    pytest.importorskip("Process_MLIP")
    with pytest.raises(FileNotFoundError):
        create_chgnet_calculator(tmp_path / "missing.pth")


def test_path_and_model_are_mutually_exclusive(tmp_path):
    pytest.importorskip("Process_MLIP")
    with pytest.raises(ValueError, match="not both"):
        create_chgnet_calculator(tmp_path / "missing.pth", model=object())


def test_missing_mace_weights_fail_before_loading_mace():
    pytest.importorskip("Process_MLIP")
    with TemporaryDirectory(prefix="process_md_mace_test_") as directory:
        with pytest.raises(FileNotFoundError, match="MACE model not found"):
            create_mace_calculator(Path(directory) / "missing.model")

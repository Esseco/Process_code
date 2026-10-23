from unittest.mock import Mock

import pytest

from md_screening import ScreeningConfig
from md_screening.calculators import create_default_calculator, mace_model_path
import md_screening.calculators as calculators


def test_model_path_and_environment_variable_are_explicit(tmp_path, monkeypatch):
    model = tmp_path / "mace-omat-0-medium.model"
    model.write_bytes(b"not real weights")
    monkeypatch.setenv("PROCESS_MD_MACE_MODEL", str(model))
    assert mace_model_path(ScreeningConfig()) == model
    explicit = tmp_path / "explicit.model"
    explicit.write_bytes(b"not real weights")
    assert mace_model_path(ScreeningConfig(model_path=explicit)) == explicit


def test_mace_omat_defaults_do_not_select_mh1_or_download(tmp_path, monkeypatch):
    model = tmp_path / "mace-omat-0-medium.model"
    model.write_bytes(b"not real weights")
    factory = Mock()
    monkeypatch.setattr(calculators, "create_mace_calculator", factory)
    result = create_default_calculator(ScreeningConfig(model_path=model))
    factory.assert_called_once_with(model, device="cuda", default_dtype="float64", head=None,
                                    enable_cueq=False, enable_symmetrix=False,
                                    symmetrix_use_kokkos=False, symmetrix_species=None)
    assert result is factory.return_value


def test_symmetrix_species_are_inferred_from_md_structure(tmp_path, monkeypatch):
    from ase import Atoms

    model = tmp_path / "mace-omat-0-medium.model"
    model.write_bytes(b"not real weights")
    factory = Mock()
    monkeypatch.setattr(calculators, "create_mace_calculator", factory)
    create_default_calculator(
        ScreeningConfig(model_path=model, enable_symmetrix=True,
                        symmetrix_use_kokkos=True),
        atoms=Atoms("LiCoO2"),
    )
    factory.assert_called_once_with(
        model, device="cuda", default_dtype="float64", head=None,
        enable_cueq=False, enable_symmetrix=True, symmetrix_use_kokkos=True,
        symmetrix_species=["Co", "Li", "O"],
    )


def test_preconverted_symmetrix_json_keeps_its_embedded_species(tmp_path, monkeypatch):
    from ase import Atoms

    model = tmp_path / "mace-omat.json"
    model.write_text("{}")
    factory = Mock()
    monkeypatch.setattr(calculators, "create_mace_calculator", factory)
    create_default_calculator(
        ScreeningConfig(model_path=model, enable_symmetrix=True,
                        symmetrix_use_kokkos=True),
        atoms=Atoms("LiCoO2"),
    )
    factory.assert_called_once_with(
        model, device="cuda", default_dtype="float64", head=None,
        enable_cueq=False, enable_symmetrix=True, symmetrix_use_kokkos=True,
        symmetrix_species=None,
    )

def test_missing_model_is_not_replaced_with_another_model(monkeypatch, tmp_path):
    monkeypatch.delenv("PROCESS_MD_MACE_MODEL", raising=False)
    with pytest.raises(ValueError, match="model_path"):
        create_default_calculator(ScreeningConfig())
    with pytest.raises(FileNotFoundError):
        create_default_calculator(ScreeningConfig(model_path=tmp_path / "missing.model"))


def test_symmetrix_options_reach_process_mlip(tmp_path, monkeypatch):
    model = tmp_path / "mace-omat-0-medium.model"
    model.write_bytes(b"not real weights")
    factory = Mock()
    monkeypatch.setattr(calculators, "create_mace_calculator", factory)
    create_default_calculator(ScreeningConfig(
        model_path=model, enable_symmetrix=True, symmetrix_use_kokkos=True,
        symmetrix_species=("Li", "O"),
    ))
    factory.assert_called_once_with(
        model, device="cuda", default_dtype="float64", head=None,
        enable_cueq=False, enable_symmetrix=True, symmetrix_use_kokkos=True,
        symmetrix_species=["Li", "O"],
    )

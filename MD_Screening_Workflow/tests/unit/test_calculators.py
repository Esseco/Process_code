from unittest.mock import Mock

import pytest

from md_screening import ScreeningConfig
from md_screening.calculators import create_default_calculator, mace_model_path, model_path_for_config
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


@pytest.mark.parametrize(
    ("model_type", "factory_name", "extra"),
    [
        ("sevennet", "create_sevennet_calculator", {"modal": "mpa", "enable_flash": True}),
        ("orb", "create_orb_calculator", {"model_name": "orb-v3-direct-inf-omat", "precision": "float32-highest", "compile": True}),
        ("nep", "create_nep_calculator", {"backend": "gpu", "gpumd_command": "gpumd"}),
        ("grace", "create_grace_calculator", {}),
        ("nequip", "create_nequip_calculator", {"enable_openequivariance": True}),
    ],
)
def test_non_mace_models_are_dispatched_to_process_md(tmp_path, monkeypatch, model_type, factory_name, extra):
    model = tmp_path / ("saved_model" if model_type == "grace" else "model.ckpt")
    if model_type == "grace":
        model.mkdir()
        (model / "saved_model.pb").write_bytes(b"placeholder")
    else:
        model.write_bytes(b"placeholder")
    factory = Mock()
    monkeypatch.setattr(calculators, factory_name, factory)
    config = ScreeningConfig(
        model_type=model_type, model_path=model, model_name=extra.pop("model_name", None),
        modal=extra.pop("modal", "mpa"), precision=extra.pop("precision", "float32-highest"),
        compile_model=extra.pop("compile", True), enable_flash=extra.pop("enable_flash", False),
        enable_openequivariance=extra.pop("enable_openequivariance", False),
        backend=extra.pop("backend", None), gpumd_command=extra.pop("gpumd_command", None),
    )
    assert model_path_for_config(config) == model
    result = create_default_calculator(config)
    assert result is factory.return_value
    kwargs = factory.call_args.kwargs
    if model_type != "nep":
        assert kwargs["device"] == "cuda"
    if model_type in {"sevennet", "orb", "nep", "grace", "nequip"}:
        assert factory.call_args.args[0] == model

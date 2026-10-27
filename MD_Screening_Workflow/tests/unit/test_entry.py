"""The direct entry is a small preset/facade, not another MD implementation."""
from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

from md_screening import ScreeningConfig, run_md, screening_preset
import md_screening.runner as runner


def test_direct_preset_does_not_expand_and_enables_gpu_symmetrix():
    config = screening_preset()
    assert config.target_atoms is None
    assert config.device == "cuda" and config.enable_symmetrix and config.symmetrix_use_kokkos
    assert (config.precheck_ps, config.check_interval_ps, config.max_production_ps) == (5, 10, 200)
    assert config.pre_relax and config.relax_cell
    assert config.relax_optimizer == "LBFGS" and config.relax_steps == 1000
    assert config.timestep_fs == 2 and config.frame_interval_ps == 0.02
    assert config.compress_trajectory is True
    assert screening_preset(compress_trajectory=False).compress_trajectory is False
    assert ScreeningConfig().compress_trajectory is False
    assert screening_preset(temperature_K=700).temperature_K == 700
    assert ScreeningConfig().target_atoms == 200  # legacy explicit API is unchanged


@pytest.mark.parametrize("species", ["Li", "Na"])
def test_entry_auto_species_and_original_supercell_are_forwarded(crystal, monkeypatch, tmp_path, species):
    symbols = [species if atom.symbol == "Li" else atom.symbol for atom in crystal]
    crystal.set_chemical_symbols(symbols)
    positions, cell = crystal.positions.copy(), crystal.cell.array.copy()
    calls = []
    def fake(source, **kwargs):
        assert source is crystal
        assert kwargs["reference_sites"] is crystal
        assert kwargs["config"].target_atoms is None
        assert kwargs["config"].mobile_species == species
        calls.append(kwargs)
        return SimpleNamespace(status="budget_exhausted", output_dir=kwargs["output_dir"])
    monkeypatch.setattr(runner, "run_screening", fake)
    monkeypatch.chdir(tmp_path)
    run_md(crystal, reference_sites=crystal, calculator=object())
    run_md(crystal, reference_sites=crystal, calculator=object())
    assert calls[0]["output_dir"] != calls[1]["output_dir"]
    assert calls[0]["output_dir"].parent == tmp_path / "runs"
    np.testing.assert_array_equal(crystal.positions, positions)
    np.testing.assert_array_equal(crystal.cell.array, cell)


def test_entry_resolves_model_and_preserves_explicit_configuration(crystal, monkeypatch, tmp_path):
    model = tmp_path / "mace-omat.model"
    model.write_bytes(b"not loaded")
    monkeypatch.setenv("PROCESS_MD_MACE_MODEL", str(model))
    captured = []
    monkeypatch.setattr(runner, "run_screening", lambda source, **kw: captured.append(kw) or object())
    run_md(crystal, reference_sites=crystal, config=screening_preset(temperature_K=700),
           max_production_ps=100, output_dir=tmp_path / "run")
    config = captured[0]["config"]
    assert config.model_path == model and config.temperature_K == 700
    assert config.max_production_ps == 100 and config.target_atoms is None


def test_missing_reference_and_bad_input_do_not_create_output(crystal, tmp_path):
    output = tmp_path / "run"
    with pytest.raises(ValueError, match="reference_sites"):
        run_md(crystal, reference_sites=None, output_dir=output)
    with pytest.raises(FileNotFoundError):
        run_md(tmp_path / "missing.vasp", reference_sites=crystal, output_dir=output)
    assert not output.exists()

"""Check the two-input GPU script without a model load or MD."""
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest
from ase import Atoms
from ase.io import write


@pytest.mark.parametrize("species", ["Li", "Na"])
@pytest.mark.parametrize("use_cli", [True, False])
def test_current_and_reference_structures_run_with_gpu_settings(tmp_path, monkeypatch, capsys, species, use_cli):
    script = Path(__file__).resolve().parents[2] / "run_md.py"
    main = runpy.run_path(str(script))["main"]
    structure = tmp_path / "input.extxyz"
    write(structure, Atoms(species + "O", positions=[[1, 1, 1], [3, 3, 3]], cell=[6]*3, pbc=True))
    model = tmp_path / "local.model"
    model.write_bytes(b"fake weights: never loaded")
    monkeypatch.setenv("PROCESS_MD_MACE_MODEL", str(model))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(main.__globals__, "STRUCTURE_PATH", str(structure))
    monkeypatch.setitem(main.__globals__, "REFERENCE_SITES_PATH", str(structure))
    monkeypatch.setattr(sys, "argv", [str(script), str(structure), str(structure)] if use_cli else [str(script)])
    outputs = []

    def run(source, *, reference_sites, config, output_dir):
        assert reference_sites == structure
        assert source == structure
        assert config.mobile_species == species and config.temperature_K == 800
        assert config.device == "cuda" and config.enable_symmetrix and config.symmetrix_use_kokkos
        assert config.model_path == model and config.frame_interval_ps == 0.02
        assert config.max_production_ps == 200
        assert output_dir.parent == tmp_path / "runs" and not output_dir.exists()
        outputs.append(output_dir)
        report = SimpleNamespace(transport=None, msd=None, transport_status="unresolved")
        return SimpleNamespace(status="budget_exhausted", last_check=report)

    monkeypatch.setitem(main.__globals__, "run_screening", run)
    main()
    main()
    assert outputs[0] != outputs[1]
    assert "unresolved" in capsys.readouterr().out


def test_ambiguous_mobile_ions_require_explicit_choice(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[2] / "run_md.py"
    main = runpy.run_path(str(script))["main"]
    structure = tmp_path / "mixed.extxyz"
    write(structure, Atoms("LiNaO", positions=[[1, 1, 1], [2, 2, 2], [3, 3, 3]], cell=[6]*3, pbc=True))
    monkeypatch.setattr(sys, "argv", [str(script), str(structure), str(structure)])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2

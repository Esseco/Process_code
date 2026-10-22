"""Exercise CLI configuration and final output without loading weights or MD."""
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest
from process_md import DiffusionResult, MSDResult


@pytest.mark.parametrize("estimated", [True, False])
def test_cli_passes_temperature_budget_and_prints_transport(tmp_path, monkeypatch, capsys, estimated):
    script = Path(__file__).resolve().parents[2] / "examples/run_case.py"
    main = runpy.run_path(str(script))["main"]
    structure = tmp_path / "POSCAR"
    structure.write_text("CLI input placeholder")
    output = tmp_path / "case"
    calls = []

    def run(source, *, output_dir, config, reference_sites):
        calls.append(config)
        assert source == structure and output_dir == output
        assert reference_sites == structure
        assert config.device == "cuda"
        assert config.enable_symmetrix and config.symmetrix_use_kokkos
        report = SimpleNamespace(
            transport_status="estimated" if estimated else "insufficient_data",
            msd=MSDResult("Li", "xyz", [1, 2], [3, 6], 4) if estimated else None,
            transport=DiffusionResult(1e-5, 1, 2, 0.98, conductivity_NE_S_cm=0.02) if estimated else None,
            decision=None,
        )
        return SimpleNamespace(status="budget_exhausted", output_dir=output,
                               last_check=report, check_reports=[output / "checks/001_production/report.json"])

    monkeypatch.setitem(main.__globals__, "run_screening", run)
    monkeypatch.setattr(sys, "argv", [str(script), str(structure), str(output),
                        "--reference-sites", str(structure), "--temperature-K", "700", "--max-production-ps", "100",
                        "--enable-symmetrix", "--symmetrix-use-kokkos"])
    main()
    assert calls[0].temperature_K == 700 and calls[0].max_production_ps == 100
    printed = capsys.readouterr().out
    assert "700 K" in printed and "total cap 105 ps" in printed
    assert "summary.csv" in printed
    if estimated:
        assert "MSD last lag: 6 A^2 at 2 ps" in printed and "msd.csv" in printed
        assert "D [cm^2/s]: 1e-05" in printed
        assert "sigma_NE [S/cm]: 0.02" in printed and "R^2: 0.98" in printed
    else:
        assert "Transport status: insufficient_data" in printed
        assert "D [cm^2/s]: None" in printed and "sigma_NE [S/cm]: None" in printed

"""Human summaries retain numerical evidence without upgrading its status."""
import csv
import json

from process_md import (DiffusionResult, MSDResult, ThermodynamicSummary,
                        ValidationResult)
from md_screening import CheckReport, Decision, WorkflowResult, screening_preset
from md_screening.reporting import initialize_outputs, write_summary


def test_summary_publishes_latest_curve_and_fit_with_clear_units(tmp_path):
    metadata = dict(config=screening_preset(), input_source="input.vasp",
                    reference_source="full.vasp")
    initialize_outputs(tmp_path, metadata)
    report = CheckReport(1, "production", 15, 10, ValidationResult(("F",)),
                         ThermodynamicSummary(2, 5, 15, {}, {}, {}, {}))
    report.msd = MSDResult("Li", "xyz", [1, 2, 3], [30, 60, 90], 4)
    report.transport = DiffusionResult(1e-5, 1, 3, 0.99,
                                     conductivity_NE_S_cm=0.01, slope_A2_per_ps=30)
    report.transport_status = "estimated"
    report.decision = Decision("accept", "Coarse screen passed")
    directory = tmp_path / "checks/001_production"
    directory.mkdir(parents=True)
    path = directory / "report.json"
    path.write_text("{}")
    (directory / "msd.csv").write_text("lag_time_ps,msd_A2\n1,30\n")
    result = WorkflowResult(tmp_path, status="heuristic_ready",
                            last_check=report, check_reports=[path])
    write_summary(tmp_path, metadata, result)
    summary = json.loads((tmp_path / "results/summary.json").read_text())
    assert summary["ready_for_screening"] is True
    assert summary["diffusion_cm2_s"] == 1e-5
    assert summary["conductivity_NE_S_cm"] == 0.01
    assert summary["r_squared"] == 0.99
    assert summary["fit_start_ps"] == 1 and summary["fit_end_ps"] == 3
    assert summary["files"]["msd"] == "results/msd.csv"
    assert (tmp_path / "results/msd.csv").read_bytes() == (directory / "msd.csv").read_bytes()
    with (tmp_path / "results/summary.csv").open(newline="") as handle:
        row = list(csv.DictReader(handle))[0]
    assert float(row["diffusion_cm2_s"]) == 1e-5
    result.status = "budget_exhausted"
    write_summary(tmp_path, metadata, result)
    assert json.loads((tmp_path / "results/summary.json").read_text())["ready_for_screening"] is False

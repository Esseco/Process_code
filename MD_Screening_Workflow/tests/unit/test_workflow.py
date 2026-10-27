import csv
import json

import pytest
from process_md import MDConfig, MDResult, MSDResult, DiffusionResult, ThermodynamicSummary, ValidationResult

from md_screening import CheckReport, Decision, ScreeningConfig, StopCriteria, run_screening
import md_screening.workflow as workflow


@pytest.fixture
def config():
    return ScreeningConfig(pre_relax=False, target_atoms=8, temperature_K=100, precheck_ps=0.002,
                           check_interval_ps=0.004, max_production_ps=0.012, trajectory_interval=1,
                           stop_criteria=None)


@pytest.fixture
def backend(monkeypatch):
    import process_md
    monkeypatch.setattr(process_md, "check_jump_backend", lambda: None)
    calls = []

    class Runner:
        def __init__(self, calculator):
            pass

        def run(self, atoms, **kwargs):
            calls.append(kwargs)
            config = MDConfig(**{key: kwargs[key] for key in (
                "temperature_K", "duration_ps", "timestep_fs", "trajectory_interval", "segment_ps", "seed")})
            for step in range(config.segment_steps, config.production_steps + 1, config.segment_steps):
                if kwargs["on_segment"]({"steps_completed": step}):
                    return MDResult(config, status="stopped", steps_completed=step)
            return MDResult(config, status="completed", steps_completed=config.production_steps)

    def analyze(event, config, index, **kwargs):
        assert kwargs["reference_sites"] is not None
        total = event["steps_completed"] * config.timestep_fs / 1000
        phase = "precheck" if total == config.precheck_ps else "production"
        report = CheckReport(index, phase, total, total - config.precheck_ps,
                             ValidationResult(("F",), framework_msd_A2=0),
                             ThermodynamicSummary(2, 0, total, {}, {}, {}, {}))
        if phase == "production":
            report.transport = DiffusionResult(1e-5, 1, 4, 0.99, conductivity_NE_S_cm=0.01,
                                               slope_A2_per_ps=0.6)
            report.msd = MSDResult("Li", "xyz", [1, 2, 3, 4], [25, 50, 75, 100], 4,
                                   components_A2=[[value/3]*3 for value in (25, 50, 75, 100)])
            report.transport_status = "estimated"
        return report

    monkeypatch.setattr(workflow, "MDRunner", Runner)
    monkeypatch.setattr(workflow, "analyze_check", analyze)
    return calls


def test_default_collects_to_budget_without_claiming_acceptance(crystal, config, backend, tmp_path):
    result = run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / "case", reference_sites=crystal)
    assert result.status == "budget_exhausted"
    assert result.md.steps_completed == 7
    assert len(backend) == 1  # no repeated MD runs / thermostat reset
    assert backend[0]["segment_ps"] == 0.002
    reports = [json.loads(path.read_text()) for path in result.check_reports]
    assert [r["total_time_ps"] for r in reports] == [0.002, 0.006, 0.010, 0.014]
    assert [r["production_time_ps"] for r in reports] == pytest.approx([0, 0.004, 0.008, 0.012])
    saved = json.loads((result.output_dir / "run.json").read_text())
    assert saved["review_mode"] == "record_only"
    assert saved["result"]["status"] == "budget_exhausted"
    assert result.last_check.transport.diffusion_cm2_s > 0
    assert backend[0]["temperature_K"] == config.temperature_K
    assert backend[0]["duration_ps"] == pytest.approx(config.precheck_ps + config.max_production_ps)
    assert saved["config"]["temperature_K"] == config.temperature_K
    fit = reports[-1]["transport"]
    assert fit["diffusion_cm2_s"] == 1e-5 and fit["conductivity_NE_S_cm"] == 0.01
    assert (result.check_reports[-1].parent / "msd.csv").is_file()
    with (result.output_dir / "summary.csv").open(newline="") as handle:
        last = list(csv.DictReader(handle))[-1]
    assert float(last["diffusion_cm2_s"]) == 1e-5
    assert float(last["conductivity_NE_S_cm"]) == 0.01


@pytest.mark.parametrize("action", ["review_cell", "raise_temperature", "lower_temperature", "review_model", "stop"])
def test_precheck_can_stop_and_record_adjustment_without_executing_it(action, crystal, config, backend, tmp_path):
    result = run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / action,
                           reviewer=lambda report: Decision(action, "Caller requests review"), reference_sites=crystal)
    assert result.status == "needs_review"
    assert result.md.steps_completed == 1
    assert len(result.check_reports) == 1
    assert result.last_check.decision.action == action
    assert len(backend) == 1


def test_caller_can_accept_a_production_estimate(crystal, config, backend, tmp_path):
    def reviewer(report):
        return Decision("continue", "Initial inspection recorded") if report.phase == "precheck" else Decision("accept", "External criteria satisfied")
    result = run_screening(crystal, calculator=object(), config=config, reviewer=reviewer, output_dir=tmp_path / "accept", reference_sites=crystal)
    assert result.status == "accepted"
    assert result.md.steps_completed == 3
    assert len(result.check_reports) == 2


@pytest.mark.parametrize("reviewer,error_type", [
    (lambda report: Decision("accept", "Invalid precheck acceptance"), ValueError),
    (lambda report: True, TypeError),
])
def test_failed_review_keeps_analysis_and_records_failure(crystal, config, backend, tmp_path, reviewer, error_type):
    output = tmp_path / "failed"
    with pytest.raises(error_type):
        run_screening(crystal, calculator=object(), config=config, reviewer=reviewer, output_dir=output, reference_sites=crystal)
    saved = json.loads((output / "run.json").read_text())
    assert saved["result"]["status"] == "failed"
    assert saved["stage"] == "reviewing"
    assert (output / "checks/000_precheck/report.json").is_file()
    assert (output / "summary.csv").is_file()


def test_analysis_errors_propagate_and_do_not_claim_budget_completion(crystal, config, backend, monkeypatch, tmp_path):
    def broken(*args, **kwargs):
        raise RuntimeError("Corrupt trajectory")
    monkeypatch.setattr(workflow, "analyze_check", broken)
    output = tmp_path / "broken"
    with pytest.raises(RuntimeError, match="Corrupt"):
        run_screening(crystal, calculator=object(), config=config, output_dir=output, reference_sites=crystal)
    saved = json.loads((output / "run.json").read_text())
    assert saved["result"]["error"] == "RuntimeError: Corrupt trajectory"
    assert saved["stage"] == "analyzing"


def test_existing_outputs_are_not_overwritten(crystal, config, backend, tmp_path):
    output = tmp_path / "exists"
    output.mkdir()
    sentinel = output / "run.json"
    sentinel.write_text("original")
    with pytest.raises(FileExistsError):
        run_screening(crystal, calculator=object(), config=config, output_dir=output, reference_sites=crystal)
    assert sentinel.read_text() == "original"
    assert backend == []


def test_missing_mobile_ions_fail_before_md(crystal, config, backend, tmp_path):
    crystal.set_chemical_symbols(["F"] * len(crystal))
    with pytest.raises(ValueError, match="mobile ions"):
        run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / "nomobile", reference_sites=crystal)
    assert backend == []


def test_default_rule_stops_at_first_eligible_production_checkpoint(crystal, backend, tmp_path):
    config = ScreeningConfig(pre_relax=False, target_atoms=8, max_production_ps=20)
    result = run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / "coarse", reference_sites=crystal)
    assert result.status == "heuristic_ready"
    assert result.md.steps_completed == 7500
    assert len(result.check_reports) == 2
    assert result.last_check.stop_metrics["curve_pass"]
    assert result.last_check.stop_metrics["msd_threshold_A2"] == pytest.approx(3*(5.3/2**0.5)**2)
    assert result.last_check.uncertainty is None
    assert json.loads((result.output_dir / "run.json").read_text())["review_mode"] == "coarse_transport"


def test_manual_hop_distance_is_recorded(crystal, backend, tmp_path):
    config = ScreeningConfig(pre_relax=False, target_atoms=8, max_production_ps=20, hop_distance_A=2)
    result = run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / "override", reference_sites=crystal)
    assert result.last_check.stop_metrics["msd_threshold_A2"] == 12
    saved = json.loads((result.output_dir / "run.json").read_text())
    assert saved["hop_distance"]["source"] == "user_override"


def test_default_mace_loader_is_used_only_without_injected_calculator(crystal, backend, monkeypatch, tmp_path):
    model = tmp_path / "mace-omat.model"
    model.write_bytes(b"loader boundary test, not weights")
    loaded = []
    marker = object()
    monkeypatch.setattr(workflow, "create_default_calculator", lambda config, atoms=None: loaded.append(config) or marker)
    config = ScreeningConfig(pre_relax=False, target_atoms=8, max_production_ps=20, model_path=model)
    result = run_screening(crystal, config=config, output_dir=tmp_path / "default_model", reference_sites=crystal)
    assert loaded == [config]
    assert result.status == "heuristic_ready"
    run_screening(crystal, calculator=marker, config=config, output_dir=tmp_path / "injected", reference_sites=crystal)
    assert len(loaded) == 1


def test_optional_uncertainty_runs_once_and_does_not_gate_the_coarse_decision(crystal, backend, monkeypatch, tmp_path):
    import process_md
    from process_md import UncertaintyResult
    monkeypatch.setattr(process_md, "check_uncertainty_backend", lambda: None)
    checked = []
    def estimate(event, config, report):
        checked.append(report.phase)
        return UncertaintyResult("Li", "xyz", 1, 4, 0.95, 4, 42, status="unresolved",
                                 diagnostics=["Uncertainty unresolved in this test"])
    monkeypatch.setattr(workflow, "_estimate_uncertainty", estimate)
    config = ScreeningConfig(pre_relax=False, target_atoms=8, max_production_ps=20, uncertainty_on_stop=True)
    result = run_screening(crystal, calculator=object(), config=config, output_dir=tmp_path / "uncertainty", reference_sites=crystal)
    assert result.status == "heuristic_ready"
    assert checked == ["production"]
    assert result.last_check.uncertainty.status == "unresolved"
    assert json.loads(result.check_reports[-1].read_text())["uncertainty"]["status"] == "unresolved"


def test_requested_but_missing_uncertainty_backend_fails_before_md(crystal, backend, monkeypatch, tmp_path):
    import process_md
    def missing():
        raise ImportError("kinisi backend not installed")
    monkeypatch.setattr(process_md, "check_uncertainty_backend", missing)
    config = ScreeningConfig(pre_relax=False, target_atoms=8, uncertainty_on_stop=True)
    output = tmp_path / "missing_kinisi"
    with pytest.raises(ImportError, match="kinisi"):
        run_screening(crystal, calculator=object(), config=config, output_dir=output, reference_sites=crystal)
    assert backend == []
    saved = json.loads((output / "run.json").read_text())
    assert saved["stage"] == "checking_uncertainty_backend"
    assert saved["result"]["status"] == "failed"


def test_missing_jump_backend_fails_before_spending_md(crystal, backend, monkeypatch, tmp_path):
    import process_md
    def missing():
        raise ImportError("GEMDAT backend not installed")
    monkeypatch.setattr(process_md, "check_jump_backend", missing)
    output = tmp_path / "missing_jumps"
    with pytest.raises(ImportError, match="GEMDAT"):
        run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8), output_dir=output, reference_sites=crystal)
    assert backend == []
    assert json.loads((output / "run.json").read_text())["stage"] == "checking_jump_backend"


def test_framework_warning_stops_precheck_before_transport_acceptance(crystal, backend, monkeypatch, tmp_path):
    original = workflow.analyze_check
    def unstable(*args, **kwargs):
        report = original(*args, **kwargs)
        report.framework.framework_msd_curve_A2 = list(range(20))
        report.framework.rdf_difference = 0.8
        return report
    monkeypatch.setattr(workflow, "analyze_check", unstable)
    result = run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8), output_dir=tmp_path / "collapse", reference_sites=crystal)
    assert result.status == "framework_unstable"
    assert result.md.steps_completed == 2500
    assert result.last_check.decision.action == "stop"
    assert result.last_check.framework_status == "unstable"


def test_ten_ps_no_jumps_plateau_stops_at_total_fifteen_ps(crystal, backend, monkeypatch, tmp_path):
    from process_md import JumpResult
    original = workflow.analyze_check
    def immobile(*args, **kwargs):
        report = original(*args, **kwargs)
        if report.phase == "production":
            report.msd.time_ps = list(range(1, 11))
            report.msd.msd_A2 = [0.1] * 10
            report.msd.components_A2 = [[0.1/3]*3]*10
            report.transport_status = "unresolved"
            report.jumps = JumpResult("Li", 0.01, 0.2, 0.5, 4, 4, 1001, "test", "test",
                                      status="estimated", n_jumps=0, n_jumping_ions=0,
                                      site_coverage=1, minimum_ion_site_coverage=1)
        return report
    monkeypatch.setattr(workflow, "analyze_check", immobile)
    result = run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8), output_dir=tmp_path / "immobile", reference_sites=crystal)
    assert result.status == "needs_review"
    assert result.md.steps_completed == 7500
    assert result.last_check.decision.action == "raise_temperature"
    assert backend[0]["temperature_K"] == 800
    saved = json.loads(result.check_reports[-1].read_text())
    assert saved["jumps"]["n_jumps"] == 0
    assert saved["mobility_status"] == "no_jumps_plateau"


def test_partial_jumps_continue_to_two_hundred_ps_budget(crystal, backend, monkeypatch, tmp_path):
    from process_md import JumpResult
    original = workflow.analyze_check
    def sparse(*args, **kwargs):
        report = original(*args, **kwargs)
        if report.phase == "production":
            report.transport_status = "unresolved"
            report.jumps = JumpResult("Li", 0.01, 0.2, 0.5, 4, 4, 1001, "test", "test",
                                      status="estimated", n_jumps=1, n_jumping_ions=1,
                                      site_coverage=1, minimum_ion_site_coverage=1)
        return report
    monkeypatch.setattr(workflow, "analyze_check", sparse)
    result = run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8), output_dir=tmp_path / "sparse", reference_sites=crystal)
    assert result.status == "budget_exhausted"
    assert result.md.steps_completed == 102500
    assert len(result.check_reports) == 21
    assert result.last_check.mobility_status == "jumps_observed"


@pytest.mark.parametrize("mode", ["record_only", "custom"])
def test_unstable_diagnostics_do_not_override_external_modes(mode, crystal, backend, monkeypatch, tmp_path):
    original = workflow.analyze_check
    def analyze(*args, **kwargs):
        assert kwargs["stop_on_instability"] is False
        report = original(*args, **kwargs)
        if report.phase == "production":
            report.framework.framework_msd_curve_A2 = list(range(20))
            report.framework.rdf_difference = 0.8
        return report
    monkeypatch.setattr(workflow, "analyze_check", analyze)
    reviewer = None if mode == "record_only" else lambda report: (
        Decision() if report.phase == "precheck" else Decision("accept", "Caller elects to retain transport"))
    config = ScreeningConfig(pre_relax=False, target_atoms=8, max_production_ps=20,
                             stop_criteria=None if mode == "record_only" else StopCriteria())
    result = run_screening(crystal, calculator=object(), config=config, reviewer=reviewer,
                           output_dir=tmp_path / mode, reference_sites=crystal)
    assert result.status == ("budget_exhausted" if mode == "record_only" else "accepted")
    assert result.last_check.framework_status == "unstable"
    assert result.last_check.transport_status == "estimated"


def test_production_instability_vetoes_an_otherwise_passing_curve(crystal, backend, monkeypatch, tmp_path):
    original = workflow.analyze_check
    def analyze(*args, **kwargs):
        report = original(*args, **kwargs)
        if report.phase == "production":
            report.framework.framework_msd_curve_A2 = list(range(20))
            report.framework.rdf_difference = 0.8
        return report
    monkeypatch.setattr(workflow, "analyze_check", analyze)
    result = run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8),
                           output_dir=tmp_path / "production_collapse", reference_sites=crystal)
    assert result.status == "framework_unstable"
    assert result.md.steps_completed == 7500
    assert result.last_check.decision.action == "stop"


def test_reference_sites_share_the_structure_supercell_matrix(crystal, backend, tmp_path):
    from ase import Atoms
    from ase.io import read
    sites = crystal.copy()
    sites += Atoms("Li", positions=[[2.65, 2.65, 2.65]])
    config = ScreeningConfig(pre_relax=False, target_atoms=16, max_production_ps=20)
    result = run_screening(crystal, calculator=object(), config=config, reference_sites=sites,
                           output_dir=tmp_path / "full_sites")
    prepared = read(result.output_dir / "prepared/structure.extxyz")
    prepared_sites = read(result.output_dir / "prepared/reference_sites.extxyz")
    assert prepared_sites.cell.array == pytest.approx(prepared.cell.array)
    assert prepared_sites.get_chemical_symbols().count("Li") == 10
    saved = json.loads((result.output_dir / "run.json").read_text())
    assert saved["hop_distance"]["source"] == "reference_mobile_sites"
    from process_md import estimate_hop_distance
    distance = estimate_hop_distance(prepared_sites, species="Li")
    assert saved["reference_nearest_neighbor_A"] == pytest.approx(distance)
    assert saved["hop_distance"]["distance_A"] == pytest.approx(distance)
    assert saved["jump_reference"] == "supplied_complete_sites"


def test_reference_required_before_creating_outputs(crystal, backend, tmp_path):
    output = tmp_path / "missing_reference"
    with pytest.raises(ValueError, match="reference_sites is required"):
        run_screening(crystal, calculator=object(), output_dir=output)
    assert not output.exists() and backend == []


def test_reference_with_too_few_sites_fails_before_md(crystal, backend, tmp_path):
    sites = crystal[[0, 1]]
    with pytest.raises(ValueError, match="at least as many"):
        run_screening(crystal, reference_sites=sites, calculator=object(),
                      config=ScreeningConfig(pre_relax=False, target_atoms=8), output_dir=tmp_path / "few_sites")
    assert backend == []


def test_reference_cell_mismatch_is_rejected_before_md(crystal, backend, tmp_path):
    sites = crystal.copy()
    sites.set_cell([10, 10, 10])
    with pytest.raises(ValueError, match="input structure cell"):
        run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8),
                      reference_sites=sites, output_dir=tmp_path / "bad_sites")
    assert backend == []


def test_nonperiodic_reference_sites_are_rejected_before_md(crystal, backend, tmp_path):
    sites = crystal.copy()
    sites.pbc = False
    with pytest.raises(ValueError, match="3D PBC"):
        run_screening(crystal, calculator=object(), config=ScreeningConfig(pre_relax=False, target_atoms=8),
                      reference_sites=sites, output_dir=tmp_path / "nonperiodic_sites")
    assert backend == []

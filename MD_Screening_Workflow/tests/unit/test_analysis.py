import csv

import pytest
from ase import Atoms
from ase.io.trajectory import Trajectory
from process_md import MSDResult

from md_screening import ScreeningConfig
from md_screening.analysis import analyze_check
import md_screening.analysis as analysis


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "md.traj"
    with Trajectory(str(path), "w") as frames:
        for index in range(7):
            frames.write(Atoms("LiO", positions=[[index * 0.01, 0, 0], [5, 5, 5]], cell=[10]*3, pbc=True))
    log = tmp_path / "md.csv"
    with log.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_fs", "temperature_K"])
        writer.writerows((i, 800) for i in range(7))
    event = dict(steps_completed=6, trajectory_file=path, log_file=log)
    config = ScreeningConfig(target_atoms=2, precheck_ps=0.002, check_interval_ps=0.004,
                             max_production_ps=0.004, timestep_fs=1, trajectory_interval=1)
    return event, config


def test_production_excludes_precheck_but_retains_boundary_frame(sample, monkeypatch):
    event, config = sample
    def capture(frames, **kwargs):
        selected = list(frames)
        assert len(selected) == 5
        assert selected[0].positions[0, 0] == pytest.approx(0.02)
        assert kwargs["frame_interval_ps"] == 0.001
        assert kwargs["drift_reference"] == "framework"
        raise ValueError("Not enough data for pymatgen multi-origin MSD: test")
    monkeypatch.setattr(analysis, "calculate_msd", capture)
    report = analyze_check(event, config, 1)
    assert report.transport_status == "insufficient_data"
    assert report.thermodynamics.start_ps == 0.002
    assert report.production_time_ps == 0.004


def test_unrelated_value_error_is_not_swallowed(sample, monkeypatch):
    event, config = sample
    def fail(*args, **kwargs):
        raise ValueError("Trajectory positions and cell must be finite")
    monkeypatch.setattr(analysis, "calculate_msd", fail)
    with pytest.raises(ValueError, match="finite"):
        analyze_check(event, config, 1)


def test_precheck_does_not_fit_diffusion(sample, monkeypatch):
    event, config = sample
    event["steps_completed"] = 2
    monkeypatch.setattr(analysis, "calculate_msd", lambda *args, **kwargs: pytest.fail("MSD during precheck"))
    report = analyze_check(event, config, 0)
    assert report.phase == "precheck"
    assert report.transport is None


def test_unavailable_requested_fit_window_is_pending(sample, monkeypatch):
    event, _ = sample
    config = ScreeningConfig(target_atoms=2, precheck_ps=0.002, check_interval_ps=0.004,
                             max_production_ps=0.004, timestep_fs=1, trajectory_interval=1, fit_end_ps=5)
    msd = MSDResult("Li", "xyz", [1, 2, 3, 4], [6, 12, 18, 24], 1, components_A2=[[2*t]*3 for t in (1, 2, 3, 4)])
    monkeypatch.setattr(analysis, "calculate_msd", lambda *args, **kwargs: msd)
    monkeypatch.setattr(analysis, "fit_diffusion", lambda *args, **kwargs: pytest.fail("fit outside window"))
    assert analyze_check(event, config, 1).transport_status == "insufficient_fit_window"


def test_framework_uses_only_the_current_check_window(sample, monkeypatch):
    from process_md import ValidationResult
    event, config = sample
    selected = []
    def capture(frames, **kwargs):
        selected.extend(list(frames))
        assert kwargs["rdf_window_fraction"] == 0.2
        assert kwargs["rdf_frames_per_window"] == 5
        return ValidationResult(("O",))
    monkeypatch.setattr(analysis, "validate_framework", capture)
    monkeypatch.setattr(analysis, "calculate_msd", lambda *args, **kwargs: (_ for _ in ()).throw(
        ValueError("Not enough data for pymatgen multi-origin MSD: test")))
    analyze_check(event, config, 1)
    assert len(selected) == 5
    assert selected[0].positions[0, 0] == pytest.approx(0.02)
    assert selected[-1].positions[0, 0] == pytest.approx(0.06)


def test_joint_framework_warning_skips_transport_and_jump_cost(sample, monkeypatch):
    from process_md import ValidationResult
    event, config = sample
    monkeypatch.setattr(analysis, "validate_framework", lambda *a, **k: ValidationResult(
        ("O",), framework_msd_curve_A2=list(range(20)), rdf_difference=0.8))
    monkeypatch.setattr(analysis, "calculate_msd", lambda *a, **k: pytest.fail("Unsafe transport fit"))
    report = analyze_check(event, config, 1, stop_on_instability=True)
    assert report.framework_status == "unstable"
    assert report.transport_status == "framework_unstable"
    assert report.jumps is None


def test_unstable_record_only_analysis_keeps_transport_evidence(sample, monkeypatch):
    from process_md import ValidationResult
    event, config = sample
    monkeypatch.setattr(analysis, "validate_framework", lambda *a, **k: ValidationResult(
        ("O",), framework_msd_curve_A2=list(range(20)), rdf_difference=0.8))
    observed = []
    def capture(*args, **kwargs):
        observed.append(True)
        raise ValueError("Not enough data for pymatgen multi-origin MSD: test")
    monkeypatch.setattr(analysis, "calculate_msd", capture)
    report = analyze_check(event, config, 1)
    assert observed == [True]
    assert report.framework_status == "unstable"
    assert report.transport_status == "insufficient_data"


def test_jump_analysis_uses_cumulative_production_frames_and_records_unresolved_fit(sample, monkeypatch):
    from process_md import JumpResult
    import process_md
    from md_screening import StopCriteria
    event, _ = sample
    config = ScreeningConfig(target_atoms=2, precheck_ps=0.002, check_interval_ps=0.004,
                             max_production_ps=0.004, timestep_fs=1, trajectory_interval=1,
                             stop_criteria=StopCriteria(no_jump_stop_ps=0.004),
                             jump_site_inner_fraction=0.65)
    calls = []
    def capture(frames, **kwargs):
        selected = list(frames)
        calls.append(kwargs)
        assert len(selected) == 5
        assert selected[0].positions[0, 0] == pytest.approx(0.02)
        return JumpResult("Li", 0.001, 0.2, 0.5, 1, 1, 5, "test", "test", status="unmapped")
    monkeypatch.setattr(process_md, "analyze_jumps", capture)
    monkeypatch.setattr(analysis, "calculate_msd", lambda *a, **k: (_ for _ in ()).throw(
        ValueError("Not enough data for pymatgen multi-origin MSD: test")))
    from ase.io import read
    reference = read(event["trajectory_file"], index=0)
    with pytest.raises(ValueError, match="reference_sites is required"):
        analyze_check(event, config, 1)
    report = analyze_check(event, config, 1, reference_sites=reference)
    assert len(calls) == 1
    assert calls[0]["reference_sites"] is reference
    assert calls[0]["site_inner_fraction"] == config.jump_site_inner_fraction
    assert report.jumps.status == "unmapped"
    assert report.transport_status == "insufficient_data"

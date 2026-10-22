import json
from inspect import signature

import numpy as np
import pytest
from ase.calculators.lj import LennardJones
from ase.io.trajectory import Trajectory
from process_md import MDRunner

from md_screening import Decision, ScreeningConfig, run_screening


def require_backend():
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    from Process_MLIP.md import run_md
    if "segment_steps" not in signature(run_md).parameters:
        pytest.skip("Process_MLIP continuous-segment extension required")


def calculator():
    return LennardJones(epsilon=0.0103, sigma=1.8, rc=3)


def test_real_nvt_keeps_state_and_checks_at_requested_times(crystal, tmp_path):
    require_backend()
    config = ScreeningConfig(target_atoms=8, temperature_K=100, precheck_ps=0.002,
                             check_interval_ps=0.004, max_production_ps=0.012, trajectory_interval=1)
    screened = run_screening(crystal, calculator=calculator(), config=config, output_dir=tmp_path / "workflow", reference_sites=crystal)
    plain = MDRunner(calculator()).run(crystal, temperature_K=100, duration_ps=0.014,
                                       trajectory_interval=1, output_dir=tmp_path / "plain")
    with Trajectory(str(screened.md.trajectory)) as left, Trajectory(str(plain.trajectory)) as right:
        np.testing.assert_array_equal(left[-1].positions, right[-1].positions)
        np.testing.assert_array_equal(left[-1].get_momenta(), right[-1].get_momenta())
        assert len(left) == 8
    reports = [json.loads(path.read_text()) for path in screened.check_reports]
    assert [report["total_time_ps"] for report in reports] == [0.002, 0.006, 0.010, 0.014]
    assert screened.status == "budget_exhausted"
    assert screened.md.parameters.timestep_fs == 2
    assert screened.md.steps_completed == 7
    assert screened.last_check.transport_status == "insufficient_data"
    assert screened.last_check.transport is None
    assert not list(tmp_path.rglob("*.ckpt"))


def test_real_nvt_stops_after_precheck_for_external_review(crystal, tmp_path):
    require_backend()
    config = ScreeningConfig(target_atoms=8, temperature_K=100, precheck_ps=0.002,
                             check_interval_ps=0.004, max_production_ps=0.012, trajectory_interval=1)
    result = run_screening(crystal, calculator=calculator(), config=config, output_dir=tmp_path / "stop",
                           reviewer=lambda report: Decision("review_model", "Example external review request"), reference_sites=crystal)
    assert result.status == "needs_review"
    assert result.md.status == "stopped"
    assert result.md.steps_completed == 1
    assert result.last_check.phase == "precheck"

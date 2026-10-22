import json

import numpy as np
import pytest
from ase.calculators.lj import LennardJones
from ase.io.trajectory import Trajectory

from process_md import MDRunner


def backend():
    pytest.importorskip("Process_MLIP")
    from Process_MLIP.md import run_md
    from inspect import signature
    if "segment_steps" not in signature(run_md).parameters:
        pytest.skip("Process_MLIP continuous-segment extension is unavailable")
    return run_md


def test_segments_keep_exact_in_process_integrator_state(crystal, tmp_path):
    run = backend()
    events = []
    def observe(event):
        with Trajectory(event["trajectory_file"], "r") as frames:
            assert len(frames) == event["steps_completed"] + 1
        events.append(event)
    plain = run(crystal, LennardJones(), tmp_path / "plain", steps=12, timestep_fs=1,
                trajectory_interval=1, log_interval=1)
    segmented = run(crystal, LennardJones(), tmp_path / "segments", steps=12, timestep_fs=1,
                    trajectory_interval=1, log_interval=1, segment_steps=4, on_segment=observe)
    np.testing.assert_array_equal(plain["final_atoms"].positions, segmented["final_atoms"].positions)
    np.testing.assert_array_equal(plain["final_atoms"].get_momenta(), segmented["final_atoms"].get_momenta())
    assert [event["steps_completed"] for event in events] == [4, 8, 12]
    assert segmented["status"] == "completed"


def test_wrapper_normal_stop_records_actual_steps_and_offset(crystal, tmp_path):
    backend()
    events = []
    def stop(event):
        events.append(event)
        return True
    result = MDRunner(LennardJones()).run(
        crystal, temperature_K=800, duration_ps=0.012, equilibration_ps=0.002,
        segment_ps=0.004, on_segment=stop, trajectory_interval=1, output_dir=tmp_path / "run",
    )
    assert result.status == "stopped"
    assert result.parameters.timestep_fs == 2
    assert result.steps_completed == 2
    assert [event["time_fs"] for event in events] == [6]
    assert json.loads(result.report.read_text())["stop_reason"] == "callback"


def test_callback_options_are_checked_before_outputs(crystal, tmp_path):
    backend()
    with pytest.raises(ValueError, match="on_segment"):
        MDRunner(LennardJones()).run(crystal, temperature_K=800, duration_ps=1,
                                     on_segment=lambda event: None, output_dir=tmp_path / "bad")
    assert not (tmp_path / "bad").exists()


def test_segmented_end_cannot_advertise_a_false_uniform_frame_interval(crystal, tmp_path):
    run = backend()
    output = tmp_path / "short_tail"
    with pytest.raises(ValueError, match="align"):
        run(crystal, LennardJones(), output, steps=25, timestep_fs=1,
            segment_steps=20, trajectory_interval=10, log_interval=10)
    assert not output.exists()

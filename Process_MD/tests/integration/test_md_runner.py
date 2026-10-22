import json

import numpy as np
import pytest
from ase.calculators.lj import LennardJones
from ase.io import read

from process_md import MDRunner


def test_runner_reuses_backend_and_preserves_phase_momenta(crystal, tmp_path):
    pytest.importorskip("Process_MLIP")
    output = tmp_path / "run"
    result = MDRunner(LennardJones()).run(
        crystal, temperature_K=800, duration_ps=0.004, equilibration_ps=0.002,
        timestep_fs=1, output_dir=output, trajectory_interval=1, seed=42,
    )
    assert result.status == "completed"
    assert result.steps_completed == 4
    assert result.checkpoint is None
    assert result.trajectory == output / "production" / "md.traj"
    assert result.equilibration_trajectory == output / "equilibration" / "md.traj"
    previous = read(output / "equilibration" / "final.traj")
    initial = read(result.trajectory, index=0)
    np.testing.assert_array_equal(previous.get_momenta(), initial.get_momenta())
    report = json.loads(result.report.read_text())
    assert report["md_controller"] == "NoseHooverChainNVT"
    assert report["parameters"]["time_offset_fs"] == 2
    assert report["end_time_fs"] == 6
    assert json.loads((output / "results.json").read_text())["results"]["md"]["status"] == "completed"
    assert crystal.calc is None
    assert not crystal.has("momenta")


def test_existing_output_directory_is_not_modified(crystal, tmp_path):
    pytest.importorskip("Process_MLIP")
    marker = tmp_path / "keep.txt"
    marker.write_text("keep me")
    with pytest.raises(FileExistsError):
        MDRunner(LennardJones()).run(crystal, temperature_K=800, duration_ps=0.002,
                                     output_dir=tmp_path)
    assert marker.read_text() == "keep me"


def test_backend_failure_is_recorded_and_propagated(crystal, tmp_path):
    pytest.importorskip("Process_MLIP")
    output = tmp_path / "failure"
    with pytest.raises(RuntimeError, match="calculator"):
        MDRunner(None).run(crystal, temperature_K=800, duration_ps=0.002,
                            output_dir=output)
    result = json.loads((output / "results.json").read_text())["results"]["md"]
    assert result["status"] == "failed"
    assert result["steps_completed"] is None
    assert "calculator" in result["error"]



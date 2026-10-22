import pytest
from ase.io import write

from process_md import MDRunner


def test_checkpoint_request_fails_before_starting_md(crystal, tmp_path):
    output = tmp_path / "run"
    with pytest.raises(NotImplementedError, match="checkpoint"):
        MDRunner(None).run(crystal, temperature_K=800, duration_ps=50,
                           output_dir=output, checkpoint_interval=1000)
    assert not output.exists()


def test_resume_does_not_treat_coordinate_frame_as_checkpoint(crystal, tmp_path):
    write(tmp_path / "final.traj", crystal)
    before = (tmp_path / "final.traj").read_bytes()
    with pytest.raises(NotImplementedError, match="checkpoint"):
        MDRunner(None).resume(previous_run=tmp_path, duration_ps=50)
    assert (tmp_path / "final.traj").read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["final.traj"]

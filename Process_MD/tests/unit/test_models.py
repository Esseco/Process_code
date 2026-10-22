import pytest

from process_md import MDConfig


def test_duration_converts_to_exact_steps():
    config = MDConfig(temperature_K=800, duration_ps=50, equilibration_ps=5)
    assert config.timestep_fs == 2
    assert config.timestep_fs * config.trajectory_interval == 20
    assert config.production_steps == 25000
    assert config.equilibration_steps == 2500


@pytest.mark.parametrize("field,value", [
    ("temperature_K", 0), ("temperature_K", float("nan")),
    ("temperature_K", True), ("duration_ps", -1),
    ("duration_ps", float("inf")), ("duration_ps", 0),
    ("timestep_fs", 0), ("timestep_fs", "1"),
    ("equilibration_ps", -1), ("trajectory_interval", 0),
    ("trajectory_interval", 1.5), ("checkpoint_interval", False),
    ("seed", -1), ("seed", 1.2), ("seed", None),
    ("segment_ps", 0), ("segment_ps", float("nan")), ("segment_ps", True),
])
def test_invalid_parameters_fail(field, value):
    kwargs = dict(temperature_K=800, duration_ps=1)
    kwargs[field] = value
    with pytest.raises(ValueError, match=field):
        MDConfig(**kwargs)


@pytest.mark.parametrize("kwargs", [
    dict(duration_ps=0.0015), dict(equilibration_ps=0.0015),
    dict(duration_ps=1e-12),
])
def test_fractional_steps_are_not_silently_rounded(kwargs):
    options = dict(temperature_K=300, duration_ps=1, timestep_fs=1)
    options.update(kwargs)
    with pytest.raises(ValueError, match="integer number of steps"):
        MDConfig(**options)


def test_segmented_production_end_must_align_with_saved_frames():
    with pytest.raises(ValueError, match="align"):
        MDConfig(temperature_K=800, duration_ps=0.025, segment_ps=0.02,
                  timestep_fs=1, trajectory_interval=10)

import subprocess
import sys

import pytest

from md_screening import Decision, ScreeningConfig


def test_defaults_and_five_ps_precheck_boundary():
    config = ScreeningConfig()
    assert (config.target_atoms, config.temperature_K) == (200, 800)
    assert config.device == "cuda"
    assert config.enable_symmetrix is False
    assert (config.precheck_ps, config.check_interval_ps, config.max_production_ps) == (5, 10, 200)
    assert config.backend_segment_ps == 5
    assert config.timestep_fs == 2
    assert config.frame_interval_ps == 0.02
    assert config.steps(config.precheck_ps) == 2500
    assert config.steps(config.check_interval_ps) == 5000
    assert config.steps(config.precheck_ps + config.max_production_ps) == 102500
    assert config.stop_criteria.min_production_ps == 10
    assert config.stop_criteria.msd_hop_factor == 3
    assert config.uncertainty_on_stop is False
    assert config.jump_analysis is True
    assert config.jump_site_inner_fraction == 0.8
    assert config.stop_criteria.no_jump_stop_ps == 10
    assert config.framework_criteria.min_msd_A2 == 1


@pytest.mark.parametrize("values", [
    {"target_atoms": 0}, {"target_atoms": True}, {"min_obs": 0},
    {"temperature_K": float("nan")}, {"precheck_ps": 0}, {"precheck_ps": 0.0001},
    {"check_interval_ps": -1}, {"max_production_ps": 25},
    {"trajectory_interval": True}, {"trajectory_interval": 1001},
    {"precheck_ps": 5.001}, {"axes": "xx"}, {"axes": "a"},
    {"mobile_species": "Bad"}, {"ion_charge": 0}, {"ion_charge": float("inf")},
    {"fit_start_ps": 0}, {"fit_end_ps": 0.5}, {"coordination_cutoff_A": -1},
    {"model_label": {}},
    {"stop_criteria": {}}, {"hop_distance_A": 0}, {"model_path": 123},
    {"device": ""}, {"default_dtype": "half"}, {"uncertainty_on_stop": "yes"},
    {"uncertainty_samples": 2},
    {"jump_analysis": "yes"}, {"jump_min_residence_ps": 0},
    {"jump_site_radius_A": -1}, {"jump_site_inner_fraction": 0},
    {"jump_site_inner_fraction": 1.01}, {"framework_criteria": {}},
    {"framework_rdf_repeat": (0, 2, 2)}, {"framework_rdf_repeat": (True, 2, 2)},
    {"framework_rdf_repeat": [2, 2, 2]},
    {"enable_symmetrix": "yes"}, {"enable_symmetrix": True}, {"symmetrix_use_kokkos": True},
    {"enable_cueq": True, "enable_symmetrix": True},
    {"symmetrix_species": ("Li", "Bad")}, {"symmetrix_species": ["Li"]},
])
def test_invalid_configs_fail_before_running(values):
    with pytest.raises(ValueError):
        ScreeningConfig(**values)


def test_decision_requires_known_action_and_reason():
    for values in ({"action": "auto_fix"}, {"reason": " "}):
        with pytest.raises(ValueError):
            Decision(**values)


def test_import_does_not_load_models_or_legacy_backend():
    code = "import sys; import md_screening; assert 'torch' not in sys.modules; assert 'Process_MLIP' not in sys.modules"
    subprocess.run([sys.executable, "-B", "-c", code], check=True)

import pytest
from process_md import DiffusionResult, MSDResult, ThermodynamicSummary, ValidationResult

from md_screening import CheckReport, StopCriteria, TransportStopper


def make_report(time=10, msd=28, r_squared=0.96):
    report = CheckReport(1, "production", time + 5, time,
                         ValidationResult(("O",)), ThermodynamicSummary(5, 5, time + 5, {}, {}, {}, {}))
    values = [msd*t/4 for t in (1, 2, 3, 4)]
    report.msd = MSDResult("Li", "xyz", [1, 2, 3, 4], values, 16,
                           components_A2=[[v/3]*3 for v in values])
    report.transport = DiffusionResult(1e-4, 1, 4, r_squared, slope_A2_per_ps=6,
                                      conductivity_NE_S_cm=0.01, axes="xyz", species="Li")
    report.transport_status = "estimated"
    return report


def test_first_eligible_check_stops_without_uncertainty_or_repeated_checks():
    report = make_report()
    assert TransportStopper(hop_distance_A=3)(report).action == "accept"
    assert report.stop_metrics["msd_threshold_A2"] == 27
    assert report.uncertainty is None


@pytest.mark.parametrize("kwargs", [
    {"time": 9.99}, {"msd": 27}, {"msd": 0.01},
    {"r_squared": 0.95}, {"r_squared": float("nan")},
])
def test_each_threshold_is_required(kwargs):
    assert TransportStopper(hop_distance_A=3)(make_report(**kwargs)).action == "continue"


def test_unresolved_or_precheck_data_cannot_pass():
    report = make_report()
    report.phase = "precheck"
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"
    report.phase = "production"
    report.transport_status = "unresolved"
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"


def test_custom_distance_and_factor_set_units_correctly():
    report = make_report(msd=8.1)
    criteria = StopCriteria(msd_hop_factor=2)
    assert TransportStopper(hop_distance_A=2, criteria=criteria)(report).action == "accept"
    assert report.stop_metrics["msd_threshold_A2"] == 8


def test_msd_threshold_uses_the_fitted_window_not_an_unfitted_late_point():
    report = make_report(msd=100)
    report.msd.msd_A2 = [1, 2, 3, 100]
    report.transport.fit_end_ps = 3
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"
    assert report.stop_metrics["msd_at_fit_end_A2"] == 3


def test_negative_slope_does_not_pass_even_with_positive_backend_floor():
    report = make_report()
    report.transport.slope_A2_per_ps = -1
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"


@pytest.mark.parametrize("kwargs", [
    {"min_production_ps": 0}, {"msd_hop_factor": float("nan")},
    {"msd_hop_factor": True}, {"min_r_squared": 1},
])
def test_invalid_policy_config(kwargs):
    with pytest.raises(ValueError):
        StopCriteria(**kwargs)


@pytest.mark.parametrize("distance", [0, -1, float("inf"), True])
def test_invalid_hop_distance(distance):
    with pytest.raises(ValueError):
        TransportStopper(hop_distance_A=distance)


def set_jumps(report, *, count=0, status="estimated", coverage=1.0, minimum=1.0):
    from process_md import JumpResult
    report.jumps = JumpResult("Li", 0.01, 0.2, 0.5, 16, 16, 1001,
                              "occupied_production_start", "test", status=status,
                              n_jumps=count, n_jumping_ions=0 if count == 0 else 1,
                              site_coverage=coverage, minimum_ion_site_coverage=minimum)
    report.msd.time_ps = list(range(1, 11))
    report.msd.msd_A2 = [0.1] * 10
    report.transport_status = "unresolved"  # no successful D fit is needed to stop
    return report


def test_ten_ps_no_jumps_and_plateau_recommends_heating_without_a_diffusion_fit():
    report = set_jumps(make_report(time=10))
    assert TransportStopper(hop_distance_A=3)(report).action == "raise_temperature"
    assert report.mobility_status == "no_jumps_plateau"
    assert report.stop_metrics["plateau_relative_change"] == pytest.approx(0, abs=1e-10)


def test_no_jump_stop_does_not_include_precheck_and_is_configurable():
    report = set_jumps(make_report(time=9.99))
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"
    report.production_time_ps = 10
    stopper = TransportStopper(hop_distance_A=3, criteria=StopCriteria(no_jump_stop_ps=20))
    assert stopper(report).action == "continue"


@pytest.mark.parametrize("options", [{"count": 1}, {"status": "unmapped", "count": None},
                                      {"coverage": 0.9}, {"minimum": 0.5}])
def test_jumps_or_unknown_mapping_continue(options):
    report = set_jumps(make_report(), **options)
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"


def test_no_jumps_but_rising_msd_does_not_trigger_early_stop():
    report = set_jumps(make_report())
    report.msd.msd_A2 = list(range(10))
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"
    assert report.mobility_status == "no_jumps_unresolved"


def test_insufficient_plateau_data_is_unknown():
    report = set_jumps(make_report())
    report.msd.time_ps, report.msd.msd_A2 = [1, 2], [0.1, 0.1]
    assert TransportStopper(hop_distance_A=3)(report).action == "continue"


@pytest.mark.parametrize("options", [{"no_jump_stop_ps": 0}, {"max_plateau_relative_change": float("nan")},
                                     {"min_site_coverage": 1.1}, {"min_ion_site_coverage": 0}])
def test_invalid_no_jump_policy(options):
    with pytest.raises(ValueError):
        StopCriteria(**options)

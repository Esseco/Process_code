import pytest

from process_md import calculate_msd, diffusion_from_slope, fit_diffusion
from process_md.models import MSDResult


@pytest.mark.parametrize("dimensions,slope,expected", [
    (3, 6, 1e-4), (2, 4, 1e-4), (1, 2, 1e-4), (3, 0, 0),
])
def test_einstein_units_are_cm2_per_second(dimensions, slope, expected):
    assert diffusion_from_slope(slope, dimensions=dimensions) == pytest.approx(expected)


@pytest.mark.parametrize("slope,dimensions", [
    (-1, 3), (float("nan"), 3), (float("inf"), 3), (True, 3),
    (1, 0), (1, 4), (1, True), (1, 1.5),
])
def test_invalid_slopes_or_dimensions_are_rejected(slope, dimensions):
    with pytest.raises(ValueError):
        diffusion_from_slope(slope, dimensions=dimensions)


def test_msd_rejects_unknown_axis_before_loading_backend(crystal):
    with pytest.raises(ValueError, match="axes"):
        calculate_msd([crystal], frame_interval_ps=0.01, axes="aa")


def test_fitting_interface_does_not_invent_reliable_diffusion():
    msd = MSDResult(species="Li", axes="xyz", time_ps=[0, 1], msd_A2=[0, 0],
                    n_mobile_atoms=1)
    with pytest.raises(ValueError, match="components"):
        fit_diffusion(msd, fit_start_ps=0, fit_end_ps=1, temperature_K=800, volume_A3=1000)


def test_inconsistent_component_data_are_rejected_before_fitting():
    msd = MSDResult("Li", "x", [1, 2, 3], [100, 200, 300], 1,
                    components_A2=[[1, 0, 0], [2, 0, 0], [3, 0, 0]])
    with pytest.raises(ValueError, match="components"):
        fit_diffusion(msd, fit_start_ps=1, fit_end_ps=3, temperature_K=800, volume_A3=1000)



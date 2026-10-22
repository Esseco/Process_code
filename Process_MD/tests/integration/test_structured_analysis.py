import numpy as np
import pytest
from ase import Atoms

from process_md import MSDResult, calculate_msd, fit_diffusion


def test_native_wrapped_and_continuous_msd_match():
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    continuous = [Atoms("LiO", positions=[[i * 0.2, 0, 0], [5, 5, 5]], cell=[10, 10, 10], pbc=True)
                  for i in range(151)]
    wrapped = [atoms.copy() for atoms in continuous]
    for atoms in wrapped:
        atoms.wrap()
    left = calculate_msd(continuous, frame_interval_ps=1, axes="x")
    right = calculate_msd(wrapped, frame_interval_ps=1, axes="x", coordinate_mode="wrapped")
    np.testing.assert_allclose(left.msd_A2, [0.04, 0.16, 0.36, 0.64], atol=1e-12)
    np.testing.assert_allclose(right.msd_A2, left.msd_A2, atol=1e-12)
    assert left.n_mobile_atoms == 1


@pytest.mark.parametrize("axes", ["xyz", "xy", "x"])
def test_structured_diffusion_and_ne_conductivity_units(axes):
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    components = [[2*t, 2*t, 2*t] for t in (1, 2, 3, 4)]
    msd = MSDResult("Li", axes, [1, 2, 3, 4], [2*len(axes)*t for t in (1, 2, 3, 4)], 2,
                    components_A2=components)
    result = fit_diffusion(msd, fit_start_ps=1, fit_end_ps=4, temperature_K=800, volume_A3=1000)
    assert result.diffusion_cm2_s == pytest.approx(1e-4)
    expected_sigma = 2e21 * (1.602176634e-19)**2 * 1e-4 / (1.380649e-23 * 800)
    assert result.conductivity_NE_S_cm == pytest.approx(expected_sigma)
    assert result.uncertainty_status == "not_evaluated"


def test_flat_msd_does_not_turn_backend_slope_floor_into_diffusion():
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    msd = MSDResult("Li", "xyz", [1, 2, 3, 4], [0]*4, 2, components_A2=[[0, 0, 0]]*4)
    result = fit_diffusion(msd, fit_start_ps=1, fit_end_ps=4, temperature_K=800, volume_A3=1000)
    assert result.diffusion_cm2_s is None
    assert result.conductivity_NE_S_cm is None

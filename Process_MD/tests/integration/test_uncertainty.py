import numpy as np
import pytest
from ase import Atoms

from process_md import analyze_diffusion_uncertainty


def test_native_kinisi_random_walk_posterior_and_ne_units():
    pytest.importorskip("kinisi", minversion="2.1")
    if np.lib.NumpyVersion(np.__version__) < "2.0.0":
        pytest.skip("kinisi 2.1 requires an independent NumPy>=2 analysis environment")
    rng = np.random.default_rng(17)
    initial = Atoms("Li12O8", positions=rng.uniform(8, 32, size=(20, 3)),
                    cell=[40, 40, 40], pbc=True)
    walk = np.cumsum(rng.normal(0, 0.12, size=(181, 12, 3)), axis=0)
    frames = []
    for displacement in walk:
        atoms = initial.copy()
        atoms.positions[:12] += displacement
        frames.append(atoms)
    state = np.random.get_state()
    result = analyze_diffusion_uncertainty(
        frames, species="Li", frame_interval_ps=0.1, fit_start_ps=0.5,
        fit_end_ps=3.0, temperature_K=800, volume_A3=64000,
        n_samples=100, max_lags=12, seed=42,
    )
    after = np.random.get_state()
    assert state[0] == after[0] and np.array_equal(state[1], after[1]) and state[2:] == after[2:]
    assert result.status == "estimated" and result.n_posterior > 0
    assert 0 < result.diffusion_lower_cm2_s <= result.diffusion_median_cm2_s <= result.diffusion_upper_cm2_s
    factor = 12 / (64000 * 1e-30) * 1.602176634e-19**2 / (1.380649e-23 * 800) * 1e-6
    assert result.conductivity_NE_median_S_cm == pytest.approx(factor * result.diffusion_median_cm2_s)
    assert result.conductivity_NE_lower_S_cm == pytest.approx(factor * result.diffusion_lower_cm2_s)
    assert result.conductivity_NE_upper_S_cm == pytest.approx(factor * result.diffusion_upper_cm2_s)
    assert result.relative_half_width == pytest.approx(
        (result.diffusion_upper_cm2_s - result.diffusion_lower_cm2_s) / (2 * result.diffusion_median_cm2_s))

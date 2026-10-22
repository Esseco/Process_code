import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest
from ase import Atoms

from process_md import UncertaintyResult, analyze_diffusion_uncertainty, check_uncertainty_backend
from process_md.analysis import uncertainty


@pytest.fixture
def frames():
    first = Atoms("Li2O", positions=[[1, 1, 1], [3, 3, 3], [6, 6, 6]],
                  cell=[10, 10, 10], pbc=True)
    result = []
    for index in range(21):
        frame = first.copy()
        frame.positions[0, 0] += index * 0.01
        result.append(frame)
    return result


@pytest.fixture
def backend(monkeypatch):
    posterior = np.arange(1, 6) * 1e-5
    analyzer = SimpleNamespace(D=object(), msd=SimpleNamespace(values=np.arange(5.0)))
    analyzer.diffusion = Mock(side_effect=lambda **kwargs: np.random.seed(123))

    def from_ase(atoms, **kwargs):
        positions = np.array([frame.positions for frame in atoms])
        analyzer.trajectory = SimpleNamespace(disp=SimpleNamespace(values=positions - positions[0]))
        return analyzer

    factory = SimpleNamespace(from_ase=Mock(side_effect=from_ase))

    def convert(variable, *, unit):
        if unit == "angstrom":
            return variable
        return SimpleNamespace(values=posterior if unit == "cm^2/s" else posterior * 123)

    sc = SimpleNamespace(
        scalar=Mock(side_effect=lambda *args, **kwargs: MagicMock()),
        array=Mock(side_effect=lambda **kwargs: SimpleNamespace(**kwargs)),
        to_unit=Mock(side_effect=convert), units=SimpleNamespace(angstrom="angstrom"),
    )
    monkeypatch.setattr(uncertainty, "_load_kinisi", lambda: (factory, sc))
    return factory, analyzer, sc


def analyze(frames, **overrides):
    options = dict(species="Li", frame_interval_ps=0.1, fit_start_ps=0.2,
                   fit_end_ps=1.0, temperature_K=800, volume_A3=1000,
                   n_samples=100, max_lags=3)
    options.update(overrides)
    return analyze_diffusion_uncertainty(frames, **options)


def test_posterior_intervals_units_window_and_rng_state(frames, backend):
    factory, analyzer, sc = backend
    before = np.random.get_state()
    result = analyze(frames, credible_mass=0.5, axes="yx", seed=9)
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    assert isinstance(result, UncertaintyResult)
    assert result.status == "estimated" and result.axes == "xy" and result.species == "Li"
    assert result.diffusion_median_cm2_s == pytest.approx(3e-5)
    assert result.diffusion_lower_cm2_s == pytest.approx(2e-5)
    assert result.diffusion_upper_cm2_s == pytest.approx(4e-5)
    assert result.relative_half_width == pytest.approx(1 / 3)
    assert result.conductivity_NE_median_S_cm == pytest.approx(123 * 3e-5)
    assert result.conductivity_NE_lower_S_cm == pytest.approx(123 * 2e-5)
    assert result.conductivity_NE_upper_S_cm == pytest.approx(123 * 4e-5)
    assert result.n_posterior == 5 and result.n_mobile_atoms == 2 and result.seed == 9
    options = factory.from_ase.call_args.kwargs
    assert options["specie"] == "Li" and options["dimension"] == "xy"
    assert options["dt"].values == pytest.approx([0.2, 0.6, 1.0])
    assert options["progress"] is False
    assert {call.kwargs["unit"] for call in sc.to_unit.call_args_list} == {"angstrom", "cm^2/s", "S/cm"}
    assert analyzer.diffusion.call_args.kwargs["n_samples"] == 100
    assert isinstance(analyzer.diffusion.call_args.kwargs["random_state"], np.random.RandomState)
    assert any("reference_difference" in note for note in result.diagnostics)
    assert any("convergence" in note for note in result.diagnostics)


@pytest.mark.parametrize("options", [{"fit_end_ps": 3.0}, {"fit_start_ps": 0.2, "fit_end_ps": 0.3}])
def test_insufficient_window_is_structured_not_a_posterior(frames, backend, options):
    result = analyze(frames, **options)
    assert result.status == "insufficient_data"
    assert result.diffusion_median_cm2_s is None and result.n_posterior == 0
    backend[0].from_ase.assert_not_called()


def test_flat_msd_is_unresolved_without_running_mcmc(frames, backend):
    backend[1].msd.values = np.zeros(5)
    result = analyze(frames)
    assert result.status == "unresolved" and result.relative_half_width is None
    backend[1].diffusion.assert_not_called()


def test_native_periodic_aliasing_is_rejected(frames, backend):
    backend[0].from_ase.side_effect = lambda *args, **kwargs: SimpleNamespace(
        trajectory=SimpleNamespace(disp=SimpleNamespace(values=np.zeros((21, 3, 3)))))
    with pytest.raises(ValueError, match="periodic reconstruction"):
        analyze(frames)


def test_numerical_backend_failure_is_unresolved_and_preserves_rng(frames, backend):
    backend[1].diffusion.side_effect = np.linalg.LinAlgError("singular covariance")
    result = analyze(frames)
    assert result.status == "unresolved" and result.n_posterior == 0
    assert any("singular covariance" in note for note in result.diagnostics)


def test_nonfinite_posterior_does_not_return_a_credible_interval(frames, backend):
    original = backend[2].to_unit.side_effect
    backend[2].to_unit.side_effect = lambda variable, *, unit: (
        SimpleNamespace(values=np.array([float("nan")])) if unit == "cm^2/s"
        else original(variable, unit=unit))
    result = analyze(frames)
    assert result.status == "unresolved" and result.diffusion_median_cm2_s is None


@pytest.mark.parametrize("options", [
    {"species": "Xx"}, {"axes": "xx"}, {"axes": "abc"},
    {"frame_interval_ps": 0}, {"temperature_K": -1}, {"volume_A3": 0},
    {"ion_charge": 0}, {"ion_charge": float("nan")}, {"fit_start_ps": -1},
    {"fit_start_ps": 2, "fit_end_ps": 1}, {"credible_mass": 0}, {"credible_mass": 1},
    {"n_samples": 9}, {"max_lags": 2}, {"max_lags": True}, {"seed": -1}, {"seed": 2**32},
])
def test_invalid_parameters_are_rejected_before_loading_backend(frames, options, monkeypatch):
    loader = Mock(side_effect=AssertionError("Must validate first"))
    monkeypatch.setattr(uncertainty, "_load_kinisi", loader)
    with pytest.raises(ValueError):
        analyze(frames, **options)
    loader.assert_not_called()


def test_cell_volume_and_species_must_match_trajectory(frames, backend):
    with pytest.raises(ValueError, match="volume_A3"):
        analyze(frames, volume_A3=2000)
    with pytest.raises(ValueError, match="absent"):
        analyze(frames, species="Na")
    frames[-1].set_cell([11, 10, 10])
    with pytest.raises(ValueError, match="fixed cell"):
        analyze(frames)


def test_unavailable_or_unsupported_backend_has_clear_import_error(monkeypatch):
    def missing(_):
        raise uncertainty.PackageNotFoundError("kinisi")
    monkeypatch.setattr(uncertainty, "version", missing)
    with pytest.raises(ImportError, match="separate NumPy>=2 environment"):
        uncertainty._load_kinisi()
    monkeypatch.setattr(uncertainty, "version", lambda _: "1.1.0")
    with pytest.raises(ImportError, match="found kinisi 1.1.0"):
        uncertainty._load_kinisi()


def test_importing_uncertainty_is_lazy():
    subprocess.run([sys.executable, "-B", "-c",
                    "from process_md import analyze_diffusion_uncertainty, UncertaintyResult; "
                    "import sys; assert all(name not in sys.modules for name in "
                    "('kinisi', 'scipp', 'emcee', 'torch', 'Process_MLIP'))"],
                   check=True, capture_output=True, text=True)


def test_public_backend_check_only_loads_optional_api(monkeypatch):
    loader = Mock(return_value=(object(), object()))
    monkeypatch.setattr(uncertainty, "_load_kinisi", loader)
    assert check_uncertainty_backend() is None
    loader.assert_called_once_with()
    loader.side_effect = ImportError("optional kinisi environment is unavailable")
    with pytest.raises(ImportError, match="optional kinisi"):
        check_uncertainty_backend()

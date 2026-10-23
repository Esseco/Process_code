import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest
from ase import Atoms

from process_md import JumpResult, analyze_jumps, check_jump_backend
from process_md.analysis import jumps


@pytest.fixture
def frames():
    first = Atoms("OLi2", positions=[[8, 8, 8], [1, 1, 1], [3, 1, 1]],
                  cell=[10, 10, 10], pbc=True)
    return [first.copy() for _ in range(20)]


@pytest.fixture
def backend(monkeypatch):
    states = np.tile([0, 1], (20, 1))
    transition = SimpleNamespace(states=states)
    transition.jumps = Mock(side_effect=ValueError("No jumps found"))
    native = SimpleNamespace(transitions_between_sites=Mock(return_value=transition))
    native.apply_drift_correction = Mock(return_value=native)

    def from_ase(atoms, **kwargs):
        points = np.array([frame.positions for frame in atoms])
        native.cumulative_displacements = (points - points[0]) @ np.linalg.inv(atoms[0].cell.array)
        return native

    factory = SimpleNamespace(from_ase_trajectory=Mock(side_effect=from_ase))
    structure = Mock(return_value=object())
    monkeypatch.setattr(jumps, "_load_gemdat", lambda: (factory, structure, "1.8.1"))
    return factory, native, transition


def analyze(frames, **options):
    parameters = dict(species="Li", frame_interval_ps=0.1, min_residence_ps=0.3)
    parameters.update(options)
    return analyze_jumps(frames, **parameters)


def test_native_events_units_atom_identity_and_residence(frames, backend):
    factory, native, transitions = backend
    transitions.jumps.side_effect = None
    transitions.jumps.return_value = SimpleNamespace(data=SimpleNamespace(to_dict=lambda **_: [
        {"atom index": 1, "start site": 1, "destination site": 0,
         "start time": 9, "stop time": 10, "residence_time": 10},
    ]))
    result = analyze(frames, min_residence_ps=0.201)
    assert isinstance(result, JumpResult) and result.status == "estimated"
    assert result.n_jumps == result.n_jumping_ions == 1
    assert result.n_mobile_atoms == 2 and result.n_sites == 2
    assert result.site_radius_A == pytest.approx(0.9)
    assert result.site_coverage == result.minimum_ion_site_coverage == 1
    assert result.max_unmapped_duration_ps == 0
    assert result.events == [dict(atom_index=2, start_site=1, end_site=0, start_frame=9,
                                  stop_frame=10, start_time_ps=0.9, stop_time_ps=1.0,
                                  residence_time_ps=1.0)]
    assert factory.from_ase_trajectory.call_args.kwargs == dict(constant_lattice=True, time_step_ps=0.1, cache=None)
    transitions.jumps.assert_called_once_with(minimal_residence=3)
    native.apply_drift_correction.assert_called_once_with(floating_species="Li")
    assert any("vacancies" in note for note in result.diagnostics)


def test_empty_inner_state_index_is_unresolved_not_a_measured_zero(frames, backend):
    backend[1].transitions_between_sites.side_effect = IndexError(
        "index -1 is out of bounds for axis 0 with size 0")
    result = analyze(frames)
    assert result.status == "unmapped"
    assert result.n_jumps is None and result.n_jumping_ions is None
    assert result.site_coverage is None
    assert any("inner-site" in note and "site_inner_fraction" in note for note in result.diagnostics)


def test_unrelated_index_error_is_not_hidden(frames, backend):
    backend[1].transitions_between_sites.side_effect = IndexError("unexpected index error")
    with pytest.raises(IndexError, match="unexpected index error"):
        analyze(frames)


def test_fully_mapped_static_trajectory_is_a_measured_zero(frames, backend):
    result = analyze(frames)
    assert result.status == "estimated" and result.n_jumps == result.n_jumping_ions == 0
    assert result.reference_source == "first_frame_occupied" and result.backend_version == "1.8.1"


def test_persistent_missing_site_cannot_be_a_credible_zero(frames, backend):
    backend[2].states[10:, 0] = -1
    result = analyze(frames)
    assert result.status == "unmapped" and result.n_jumps is None and result.n_jumping_ions is None
    assert result.site_coverage == 0.75 and result.minimum_ion_site_coverage == 0.5
    assert result.max_unmapped_duration_ps == 1


def test_brief_unmapped_excursion_retains_zero_with_coverage(frames, backend):
    backend[2].states[10, 0] = -1
    result = analyze(frames)
    assert result.status == "estimated" and result.n_jumps == 0
    assert result.site_coverage == pytest.approx(0.975)
    assert result.minimum_ion_site_coverage == pytest.approx(0.95)
    assert result.max_unmapped_duration_ps == pytest.approx(0.1)


def test_unmapped_runs_are_contiguous_and_not_summed(frames, backend):
    backend[2].states[[2, 4, 6, 8], 0] = -1
    result = analyze(frames)
    assert result.status == "estimated" and result.max_unmapped_duration_ps == pytest.approx(0.1)


def test_single_site_periodic_images_are_unknown(frames, backend):
    reference = frames[0][[1]]
    result = analyze(frames, reference_sites=reference)
    assert result.status == "unmapped" and result.n_jumps is None
    assert result.site_coverage is None and result.reference_source == "explicit_reference"
    backend[1].transitions_between_sites.assert_not_called()


def test_insufficient_duration_does_not_analyze_native_events(frames, backend):
    result = analyze(frames[:2], min_residence_ps=0.2)
    assert result.status == "insufficient_data" and result.n_jumps is None
    backend[0].from_ase_trajectory.assert_not_called()


def test_periodic_aliasing_is_rejected_before_drift_correction(frames, backend):
    backend[0].from_ase_trajectory.side_effect = lambda *a, **k: SimpleNamespace(
        cumulative_displacements=np.ones((20, 3, 3)))
    with pytest.raises(ValueError, match="periodic reconstruction"):
        analyze(frames)


def test_only_native_no_jumps_exception_is_interpreted_as_zero(frames, backend):
    backend[2].jumps.side_effect = ValueError("unsupported geometry")
    with pytest.raises(ValueError, match="unsupported geometry"):
        analyze(frames)


@pytest.mark.parametrize("options", [
    {"species": "Xx"}, {"frame_interval_ps": 0}, {"frame_interval_ps": True},
    {"frame_interval_ps": float("nan")}, {"min_residence_ps": -1},
    {"site_inner_fraction": 0}, {"site_inner_fraction": 1.1},
    {"site_radius_A": 0}, {"site_radius_A": float("inf")}, {"coordinate_mode": "auto"},
])
def test_invalid_parameters_are_rejected_before_loading_backend(frames, monkeypatch, options):
    loader = Mock(side_effect=AssertionError("Must validate first"))
    monkeypatch.setattr(jumps, "_load_gemdat", loader)
    with pytest.raises(ValueError):
        analyze(frames, **options)
    loader.assert_not_called()


def test_reference_cell_species_and_site_overlap_validation(frames, backend):
    reference = frames[0].copy()
    reference.set_cell([11, 10, 10])
    with pytest.raises(ValueError, match="same cell"):
        analyze(frames, reference_sites=reference)
    with pytest.raises(ValueError, match="no Li sites"):
        analyze(frames, reference_sites=frames[0][[0]])
    with pytest.raises(ValueError, match="half the nearest"):
        analyze(frames, site_radius_A=1)
    reference = frames[0].copy()
    reference.positions[2] = reference.positions[1]
    with pytest.raises(ValueError, match="overlapping"):
        analyze(frames, reference_sites=reference)


def test_existing_trajectory_identity_and_cell_checks_are_used(frames, backend):
    frames[-1].numbers[0] = 6
    with pytest.raises(ValueError, match="identities/order"):
        analyze(frames)


def test_missing_or_unsupported_dependency_is_explicit(monkeypatch):
    def missing(_):
        raise jumps.PackageNotFoundError("gemdat")
    monkeypatch.setattr(jumps, "version", missing)
    with pytest.raises(ImportError, match="requires gemdat"):
        jumps._load_gemdat()
    monkeypatch.setattr(jumps, "version", lambda _: "1.6.3")
    with pytest.raises(ImportError, match="found gemdat 1.6.3"):
        jumps._load_gemdat()


def test_public_backend_check_only_loads_optional_api(monkeypatch):
    loader = Mock(return_value=(object(), object(), "1.8.1"))
    monkeypatch.setattr(jumps, "_load_gemdat", loader)
    assert check_jump_backend() is None
    loader.assert_called_once_with()


def test_importing_jumps_does_not_import_optional_analysis_or_models():
    subprocess.run([sys.executable, "-B", "-c",
                    "from process_md import JumpResult, analyze_jumps, check_jump_backend; "
                    "import sys; assert all(name not in sys.modules for name in "
                    "('gemdat', 'MDAnalysis', 'pymatgen', 'kinisi', 'scipp', 'torch', 'Process_MLIP'))"],
                   check=True, capture_output=True, text=True)

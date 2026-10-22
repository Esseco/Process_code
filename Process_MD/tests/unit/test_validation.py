import numpy as np
import pytest
from ase import Atoms
from ase.build import bulk

from process_md import validate_framework


def framework():
    return Atoms("LiOSi", positions=[[1, 1, 1], [3, 3, 3], [5, 3, 3]],
                 cell=[12, 12, 12], pbc=True)


def test_static_framework_returns_evidence_without_a_collapse_verdict():
    atoms = framework()
    result = validate_framework([atoms, atoms.copy()])
    assert result.framework_species == ("O", "Si")
    assert result.framework_msd_A2 == pytest.approx(0)
    assert result.framework_msd_curve_A2 == pytest.approx([0, 0])
    assert result.rdf_difference == pytest.approx(0)
    assert result.rdf_initial == pytest.approx(result.rdf_final)
    assert result.coordination_change_fraction is None
    assert any("explicit" in note for note in result.diagnostics)
    assert not hasattr(result, "stable")
    assert not hasattr(result, "collapsed")


def test_framework_translation_is_mass_weighted_and_removed():
    atoms = framework()
    shifted = atoms.copy()
    shifted.positions[1:] += [1.0, -0.5, 0.25]
    result = validate_framework([atoms, shifted], coordination_cutoff_A=2.5)
    assert result.framework_msd_A2 == pytest.approx(0, abs=1e-28)
    assert np.asarray(result.framework_drift_A)[-1] == pytest.approx([1, -0.5, 0.25])
    assert result.rdf_difference == pytest.approx(0)
    assert result.coordination_change_fraction == 0
    assert result.coordination_initial_mean == 1


def test_local_displacement_changes_framework_msd_rdf_and_coordination():
    atoms = framework()
    moved = atoms.copy()
    moved.positions[2, 0] += 1.0
    result = validate_framework([atoms, moved], coordination_cutoff_A=2.5)
    mass_o, mass_si = atoms.get_masses()[1:]
    com = mass_si / (mass_o + mass_si)
    expected_msd = (com**2 + (1 - com)**2) / 2
    assert result.framework_msd_A2 == pytest.approx(expected_msd)
    assert result.framework_drift_A[-1] == pytest.approx([com, 0, 0])
    assert result.rdf_difference > 0
    assert result.coordination_change_fraction == 1
    assert result.coordination_initial_mean == 1
    assert result.coordination_final_mean == 0


def test_empty_initial_rdf_is_undefined_not_zero_difference(crystal):
    result = validate_framework([crystal, crystal.copy()])
    assert result.rdf_difference is None
    assert any("undefined" in note for note in result.diagnostics)


def test_framework_requires_two_frames_and_nonmobile_atoms():
    atoms = framework()
    with pytest.raises(ValueError, match="at least two frames"):
        validate_framework([atoms])
    with pytest.raises(ValueError, match="No framework"):
        validate_framework([atoms, atoms.copy()], mobile_species=("Li", "O", "Si"))


@pytest.mark.parametrize("options", [
    {"rdf_bins": 0}, {"rdf_bins": -1}, {"rdf_bins": True}, {"rdf_bins": 2.5},
    {"rdf_rmax_A": 0}, {"rdf_rmax_A": -1}, {"rdf_rmax_A": float("nan")},
    {"rdf_rmax_A": True}, {"rdf_rmax_A": 6}, {"rdf_rmax_A": 7},
    {"coordination_cutoff_A": 0}, {"coordination_cutoff_A": -1},
    {"coordination_cutoff_A": float("inf")}, {"coordination_cutoff_A": True},
    {"mobile_species": "Li"}, {"mobile_species": (1,)},
])
def test_invalid_diagnostic_options_are_rejected(options):
    atoms = framework()
    with pytest.raises(ValueError):
        validate_framework([atoms, atoms.copy()], **options)


def test_rdf_radius_uses_perpendicular_height_for_skew_cell():
    atoms = framework()
    atoms.set_cell([[12, 0, 0], [11, 2, 0], [0, 0, 12]])
    with pytest.raises(ValueError, match="minimum cell height"):
        validate_framework([atoms, atoms.copy()], rdf_rmax_A=1.0)


def test_window_rdfs_average_only_a_bounded_number_of_snapshots(monkeypatch):
    from process_md.analysis import framework as module
    atoms = framework()
    snapshots = []
    for index in range(100):
        frame = atoms.copy()
        frame.positions[2, 0] += index / 100
        snapshots.append(frame)
    original = module.get_rdf
    calls = []
    def count(*args, **kwargs):
        calls.append(args[0].positions.copy())
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "get_rdf", count)
    result = validate_framework(snapshots, rdf_window_fraction=0.2, rdf_frames_per_window=3)
    assert result.rdf_reference_frames == [0, 9, 19]
    assert result.rdf_final_frames == [80, 89, 99]
    assert len(calls) == 6
    # Compare the exact selected native ASE histograms, not a reimplemented RDF.
    expected = [original(snapshots[i][1:], rmax=5.4, nbins=75)[0] for i in (0, 9, 19)]
    assert result.rdf_initial == pytest.approx(np.mean(expected, axis=0))


@pytest.mark.parametrize("options", [{"rdf_window_fraction": 0}, {"rdf_window_fraction": 0.6},
                                     {"rdf_window_fraction": True}, {"rdf_frames_per_window": 0}])
def test_invalid_rdf_window(options):
    atoms = framework()
    with pytest.raises(ValueError):
        validate_framework([atoms, atoms.copy()], **options)


def test_default_rdf_repeat_preserves_endpoint_results():
    atoms = framework()
    default = validate_framework([atoms, atoms.copy()])
    explicit = validate_framework([atoms, atoms.copy()], rdf_repeat=(1, 1, 1))
    assert default == explicit
    assert default.rdf_repeat == (1, 1, 1)


@pytest.mark.parametrize("translation", [[0, 0, 0], [1.0, -0.5, 0.25]])
def test_rdf_periodic_images_resolve_small_lif_cell_without_repeating_other_metrics(monkeypatch, translation):
    from process_md.analysis import framework as module
    atoms = bulk("LiF", "rocksalt", a=4, cubic=True)
    shifted = atoms.copy()
    shifted.positions += translation
    original = validate_framework([atoms, shifted], coordination_cutoff_A=3.0)
    assert original.rdf_difference is None

    rdf_sizes, coordination_sizes = [], []
    native_rdf, native_neighbors = module.get_rdf, module.neighbor_list

    def rdf(snapshot, **kwargs):
        rdf_sizes.append(len(snapshot))
        return native_rdf(snapshot, **kwargs)

    def neighbors(quantities, snapshot, cutoff):
        coordination_sizes.append(len(snapshot))
        return native_neighbors(quantities, snapshot, cutoff)

    monkeypatch.setattr(module, "get_rdf", rdf)
    monkeypatch.setattr(module, "neighbor_list", neighbors)
    repeated = validate_framework([atoms, shifted], coordination_cutoff_A=3.0, rdf_repeat=(2, 2, 2))
    assert repeated.rdf_repeat == (2, 2, 2)
    assert rdf_sizes == [32, 32]
    assert coordination_sizes == [4, 4]
    assert np.sum(repeated.rdf_initial) > 0
    assert repeated.rdf_difference == pytest.approx(0)
    assert repeated.rdf_initial == pytest.approx(repeated.rdf_final)
    assert repeated.rdf_r_A[-1] > 3.5
    assert repeated.framework_msd_curve_A2 == pytest.approx(original.framework_msd_curve_A2)
    assert repeated.framework_msd_A2 == pytest.approx(0, abs=1e-28)
    assert np.asarray(repeated.framework_drift_A) == pytest.approx(np.asarray(original.framework_drift_A))
    assert repeated.framework_drift_A[-1] == pytest.approx(translation)
    assert repeated.coordination_initial_mean == original.coordination_initial_mean == 12
    assert repeated.coordination_final_mean == original.coordination_final_mean == 12
    assert repeated.coordination_change_fraction == original.coordination_change_fraction == 0
    assert any("no independent samples" in note for note in repeated.diagnostics)
    assert any("finite-size convergence" in note for note in repeated.diagnostics)
    assert len(atoms) == len(shifted) == 8
    assert atoms.cell.lengths() == pytest.approx([4, 4, 4])


def test_repeated_rdf_radius_uses_repeated_perpendicular_cell_height():
    atoms = bulk("LiF", "rocksalt", a=4, cubic=True)
    result = validate_framework([atoms, atoms.copy()], rdf_repeat=(2, 2, 2), rdf_rmax_A=3.9)
    assert np.sum(result.rdf_initial) > 0
    with pytest.raises(ValueError, match="minimum cell height"):
        validate_framework([atoms, atoms.copy()], rdf_repeat=(2, 2, 2), rdf_rmax_A=4.0)
    with pytest.raises(ValueError, match="minimum cell height"):
        validate_framework([atoms, atoms.copy()], rdf_repeat=(2, 1, 2), rdf_rmax_A=2.0)


@pytest.mark.parametrize("repeat", [None, 2, (2, 2), (2, 2, 2, 2),
                                   (0, 2, 2), (2, -1, 2), (2.0, 2, 2), (True, 2, 2)])
def test_invalid_rdf_repeat(repeat):
    atoms = framework()
    with pytest.raises(ValueError, match="three positive integers"):
        validate_framework([atoms, atoms.copy()], rdf_repeat=repeat)

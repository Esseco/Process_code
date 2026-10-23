import numpy as np
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from ase import Atoms
from ase.io import write

from process_md import analyze_jumps, check_jump_backend


@pytest.fixture(autouse=True)
def native_backend():
    pytest.importorskip("gemdat", minversion="1.8.1")
    check_jump_backend()


def make_frames(x, *, wrap=False, drift=False):
    initial = Atoms("OLi", positions=[[5, 5, 5], [float(x[0]), 1, 1]],
                    cell=[10, 10, 10], pbc=True)
    frames = []
    for index, point in enumerate(x):
        frame = initial.copy()
        frame.positions[1, 0] = point
        if drift:
            frame.positions[:, 0] += index * 0.1
        if wrap:
            frame.wrap()
        frames.append(frame)
    return frames


def reference(x=(1, 3)):
    return Atoms("Li2", positions=[[point, 1, 1] for point in x], cell=[10, 10, 10], pbc=True)


def analyze(frames, **options):
    parameters = dict(species="Li", frame_interval_ps=0.1, reference_sites=reference(),
                      min_residence_ps=0.3)
    parameters.update(options)
    return analyze_jumps(frames, **parameters)


def test_native_static_vibration_has_zero_jumps():
    result = analyze(make_frames(1 + 0.02 * np.sin(np.arange(30))))
    assert result.status == "estimated" and result.n_jumps == result.n_jumping_ions == 0
    assert result.site_coverage == result.minimum_ion_site_coverage == 1


def test_native_inner_boundary_rattling_within_one_outer_site_is_zero():
    # Radius .9 Å, inner radius .45 Å: crosses the inner sphere, never changes site.
    result = analyze(make_frames(1 + 0.6 * np.sin(np.arange(30))))
    assert result.status == "estimated" and result.n_jumps == 0
    assert result.site_coverage == 1


def test_native_short_excursion_and_destination_without_residence_have_no_jump():
    excursion = np.ones(30)
    excursion[10] = 2  # Briefly outside both site spheres, then back to its origin.
    result = analyze(make_frames(excursion))
    assert result.status == "estimated" and result.n_jumps == 0
    assert result.max_unmapped_duration_ps == pytest.approx(0.1)
    destination = np.ones(30)
    destination[-1] = 3
    result = analyze(make_frames(destination))
    assert result.status == "estimated" and result.n_jumps == 0


def test_native_offset_sites_use_configurable_inner_tolerance():
    # Both sites are offset by .6 A: outside .5*.9, inside .8*.9 A.
    frames = make_frames(np.r_[np.full(10, 1.6), np.full(20, 3.6)])
    strict = analyze(frames, site_inner_fraction=0.5)
    assert strict.status == "unmapped" and strict.n_jumps is None
    tolerant = analyze(frames, site_inner_fraction=0.8)
    assert tolerant.status == "estimated" and tolerant.n_jumps == 1
    assert tolerant.site_coverage == 1
    assert tolerant.events[0]["start_site"] == 0
    assert tolerant.events[0]["end_site"] == 1


def test_native_resident_hop_and_event_times():
    result = analyze(make_frames(np.r_[np.ones(10), np.full(20, 3)]))
    assert result.status == "estimated" and result.n_jumps == result.n_jumping_ions == 1
    assert result.events[0]["atom_index"] == 1
    assert result.events[0]["start_site"] == 0 and result.events[0]["end_site"] == 1
    assert result.events[0]["start_time_ps"] == pytest.approx(0.9)
    assert result.events[0]["stop_time_ps"] == pytest.approx(1.0)


@pytest.mark.parametrize("wrapped", [False, True])
def test_native_periodic_crossing_uses_reference_site_identity(wrapped):
    frames = make_frames(np.r_[np.full(10, 9), np.full(20, 11)], wrap=wrapped)
    result = analyze(frames, reference_sites=reference((9, 1)), coordinate_mode="wrapped" if wrapped else "unwrapped")
    assert result.status == "estimated" and result.n_jumps == 1
    assert result.events[0]["start_site"] == 0 and result.events[0]["end_site"] == 1


def test_native_framework_translation_does_not_create_jumps():
    result = analyze(make_frames(np.ones(30), drift=True))
    assert result.status == "estimated" and result.n_jumps == 0
    assert result.site_coverage == 1


def test_native_missing_vacancy_site_is_unknown_with_coverage():
    result = analyze(make_frames(np.r_[np.ones(10), np.full(20, 5)]))
    assert result.status == "unmapped" and result.n_jumps is None
    assert result.site_coverage == result.minimum_ion_site_coverage == pytest.approx(1 / 3)
    assert result.max_unmapped_duration_ps == pytest.approx(2)


def test_native_single_site_periodic_hop_is_unknown():
    frames = make_frames(np.r_[np.ones(10), np.linspace(1, 11, 20)])
    result = analyze(frames, reference_sites=reference()[:1])
    assert result.status == "unmapped" and result.n_jumps is None


def test_native_unwrapped_aliasing_is_rejected():
    frames = make_frames(np.r_[np.ones(10), np.full(20, 7)])
    with pytest.raises(ValueError, match="periodic reconstruction"):
        analyze(frames)


def test_native_file_input_leaves_no_cache():
    with TemporaryDirectory(prefix="gemdat-file-") as folder:
        path = Path(folder) / "production.traj"
        write(path, make_frames(np.r_[np.ones(10), np.full(20, 3)]))
        result = analyze(path)
        assert result.n_jumps == 1
        assert list(path.parent.iterdir()) == [path]
    assert not Path(folder).exists()

import numpy as np
import pytest
from ase import Atoms
from ase.io.trajectory import Trajectory

from process_md.analysis.trajectory import read_positions


def frames():
    return [Atoms("LiO", scaled_positions=[[x, 0, 0], [0.5, 0.5, 0.5]],
                  cell=[[10, 0, 0], [2, 8, 0], [0, 0, 9]], pbc=True)
            for x in (0.9, 0.1, 0.3)]


def test_wrapped_positions_use_native_pymatgen_reconstruction():
    pytest.importorskip("pymatgen.core.trajectory")
    initial, positions = read_positions(frames(), coordinate_mode="wrapped")
    np.testing.assert_allclose(positions[:, 0, 0], [9, 11, 13])
    assert initial.get_chemical_symbols() == ["Li", "O"]


def test_unwrapped_coordinates_are_not_folded_back_into_cell():
    source = frames()
    source[1].positions[0, 0] = 16
    initial, positions = read_positions(source)
    assert positions[1, 0, 0] == 16
    initial.positions[0, 0] = 0
    assert source[0].positions[0, 0] == 9


def test_reads_ase_trajectory_without_touching_input(tmp_path):
    path = tmp_path / "md.traj"
    with Trajectory(path, "w") as output:
        for atoms in frames():
            output.write(atoms)
    before = path.read_bytes()
    _, positions = read_positions(path)
    assert positions.shape == (3, 2, 3)
    assert path.read_bytes() == before


@pytest.mark.parametrize("change", ["cell", "element", "pbc", "nan"])
def test_rejects_unsupported_trajectories(change):
    source = frames()
    if change == "cell":
        source[1].cell[0, 0] = 11
    elif change == "element":
        source[1].numbers[0] = 11
    elif change == "pbc":
        source[1].pbc[0] = False
    else:
        source[1].positions[0, 0] = float("nan")
    with pytest.raises(ValueError):
        read_positions(source)


def test_empty_and_unknown_coordinate_mode_are_rejected():
    with pytest.raises(ValueError, match="no frames"):
        read_positions([])
    with pytest.raises(ValueError, match="coordinate_mode"):
        read_positions(frames(), coordinate_mode="guess")

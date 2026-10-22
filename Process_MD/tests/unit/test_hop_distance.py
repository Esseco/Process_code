import numpy as np
import pytest
from ase import Atoms

from process_md.structure import estimate_hop_distance


def test_nearest_ion_distance_uses_pbc_and_excludes_framework():
    atoms = Atoms("LiLiO", positions=[[0.1, 0, 0], [9.9, 0, 0], [0.11, 0, 0]], cell=[10]*3, pbc=True)
    assert estimate_hop_distance(atoms) == pytest.approx(0.2)


def test_single_ion_uses_native_periodic_images_in_triclinic_cell():
    atoms = Atoms("NaO", positions=[[0, 0, 0], [1, 1, 1]], cell=[[4,0,0], [3.5,2,0], [0,0,7]], pbc=True)
    assert estimate_hop_distance(atoms, species="Na") == pytest.approx(np.sqrt(0.5**2 + 2**2))


@pytest.mark.parametrize("kind", ["missing", "overlap", "nonperiodic"])
def test_invalid_geometry(kind):
    atoms = Atoms("LiLiO", positions=[[0,0,0], [2,0,0], [1,1,1]], cell=[10]*3, pbc=True)
    if kind == "missing":
        atoms.set_chemical_symbols(["O"]*3)
    elif kind == "overlap":
        atoms.positions[1] = atoms.positions[0]
    else:
        atoms.pbc = False
    with pytest.raises(ValueError):
        estimate_hop_distance(atoms)

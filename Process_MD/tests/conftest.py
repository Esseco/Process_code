import numpy as np
import pytest
from ase import Atoms


@pytest.fixture
def crystal():
    atoms = Atoms("LiO", scaled_positions=[[0, 0, 0], [0.5, 0.5, 0.5]],
                  cell=[[3, 0, 0], [0.5, 4, 0], [0.2, 0.3, 5]], pbc=True)
    atoms.new_array("site_label", np.array([12, 34]))
    atoms.info["material"] = "synthetic"
    return atoms

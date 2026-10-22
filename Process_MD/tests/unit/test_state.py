from copy import deepcopy

import numpy as np
import pytest
from ase import Atoms
from ase.calculators.lj import LennardJones

from process_md.state import AlkaliState, describe_alkali_state


def test_counts_actual_composition_and_reference_proportions():
    state = describe_alkali_state(
        Atoms("Li3NaO4"), reference_mobile_atoms=4, configuration_id="vacancy-1",
    )
    assert isinstance(state, AlkaliState)
    assert state.n_atoms == 8
    assert state.formula == "Li3NaO4"
    assert state.element_counts == {"Li": 3, "Na": 1, "O": 4}
    assert state.mobile_species == "Li"
    assert state.n_mobile_atoms == 3
    assert state.reference_mobile_atoms == 4
    assert state.occupancy_fraction == pytest.approx(0.75)
    assert state.removed_fraction == pytest.approx(0.25)
    assert state.configuration_id == "vacancy-1"


def test_missing_reference_does_not_infer_occupancy():
    state = describe_alkali_state(Atoms("LiO"))
    assert state.reference_mobile_atoms is None
    assert state.occupancy_fraction is None
    assert state.removed_fraction is None
    assert state.configuration_id is None


def test_selected_species_and_numpy_reference_count():
    state = describe_alkali_state(
        Atoms("Li3NaO4"), mobile_species="Na", reference_mobile_atoms=np.int64(1),
    )
    assert state.n_mobile_atoms == 1
    assert state.reference_mobile_atoms == 1
    assert state.occupancy_fraction == pytest.approx(1.0)
    assert state.removed_fraction == pytest.approx(0.0)


@pytest.mark.parametrize("reference,occupancy,removed", [(None, None, None), (4, 0, 1)])
def test_zero_mobile_atoms_are_a_valid_deintercalated_state(reference, occupancy, removed):
    state = describe_alkali_state(Atoms("O4"), reference_mobile_atoms=reference)
    assert state.n_mobile_atoms == 0
    assert state.element_counts == {"O": 4}
    assert state.occupancy_fraction == occupancy
    assert state.removed_fraction == removed


@pytest.mark.parametrize("reference", [0, -1, True, False, 1.5, 3.0, "4", np.nan, np.inf, 2])
def test_invalid_or_undersized_reference_is_rejected(reference):
    with pytest.raises(ValueError, match="reference_mobile_atoms"):
        describe_alkali_state(Atoms("Li3O4"), reference_mobile_atoms=reference)


@pytest.mark.parametrize("species", ["X", "Li+", "li", "", "NotAnElement", None, ["Li"]])
def test_mobile_species_must_be_a_real_element_symbol(species):
    with pytest.raises(ValueError, match="mobile_species"):
        describe_alkali_state(Atoms("LiO"), mobile_species=species)


def test_nonempty_ase_structure_is_required():
    with pytest.raises(TypeError, match="ASE Atoms"):
        describe_alkali_state("LiO")
    with pytest.raises(ValueError, match="nonempty"):
        describe_alkali_state(Atoms())


def test_description_preserves_all_input_state():
    atoms = Atoms("Li2O", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                  cell=[[3, 0, 0], [0.5, 4, 0], [0.2, 0.3, 5]], pbc=True)
    atoms.new_array("site_label", np.array([12, 34, 56]))
    atoms.set_momenta([[0.1, 0, 0], [0, 0.2, 0], [0, 0, 0.3]])
    atoms.info["nested"] = {"configuration": [1, 2]}
    atoms.calc = LennardJones()
    before = atoms.copy()
    before_info = deepcopy(atoms.info)
    calculator = atoms.calc

    describe_alkali_state(atoms, reference_mobile_atoms=4)

    assert atoms.calc is calculator
    assert atoms.info == before_info
    assert atoms.arrays.keys() == before.arrays.keys()
    for name in before.arrays:
        np.testing.assert_array_equal(atoms.arrays[name], before.arrays[name])
    np.testing.assert_array_equal(atoms.cell, before.cell)
    np.testing.assert_array_equal(atoms.pbc, before.pbc)

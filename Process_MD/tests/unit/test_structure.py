import numpy as np
import pytest
from ase import Atoms
from ase.io import write

from process_md import get_structure_info, prepare_structure


@pytest.mark.parametrize("filename,fmt", [
    ("POSCAR", "vasp"), ("structure.cif", "cif"), ("structure.extxyz", "extxyz"),
])
def test_reads_common_structures(crystal, tmp_path, filename, fmt):
    path = tmp_path / filename
    write(path, crystal, format=fmt)
    prepared = prepare_structure(path)
    assert prepared.get_chemical_symbols() == ["Li", "O"]
    np.testing.assert_allclose(prepared.cell.lengths(), crystal.cell.lengths())
    assert prepared.pbc.all()


def test_matrix_preserves_cell_pbc_and_original_site_mapping(crystal):
    crystal.pbc = [True, True, False]
    matrix = np.array([[2, 1, 0], [0, 1, 0], [0, 0, 1]])
    prepared = prepare_structure(crystal, supercell_matrix=matrix)
    assert len(prepared) == 4
    np.testing.assert_allclose(prepared.cell, [[6.5, 4, 0], [0.5, 4, 0], [0.2, 0.3, 5]])
    assert prepared.pbc.tolist() == [True, True, False]
    assert prepared.arrays["process_md_source_index"].tolist() == [0, 1, 0, 1]
    assert prepared.arrays["site_label"].tolist() == [12, 34, 12, 34]
    assert len(crystal) == 2
    assert "process_md_source_index" not in crystal.arrays
    prepared.info["nested"] = {"value": 1}
    assert "nested" not in crystal.info


def test_target_is_lower_bound_and_does_not_change_composition(crystal):
    prepared = prepare_structure(crystal, target_atoms=7)
    info = get_structure_info(prepared)
    assert info.n_atoms == 8
    assert info.element_counts == {"Li": 4, "O": 4}
    assert info.volume_A3 == pytest.approx(240)
    assert prepared.arrays["process_md_source_index"].tolist().count(0) == 4


def test_small_target_returns_independent_copy(crystal):
    prepared = prepare_structure(crystal, target_atoms=1)
    prepared.positions[0, 0] = 1
    assert crystal.positions[0, 0] == 0
    assert len(prepared) == 2


@pytest.mark.parametrize("matrix", [
    [[1, 0], [0, 1]], np.zeros((3, 3)), np.diag([-1, 1, 1]),
    np.diag([1.5, 1, 1]), np.diag([float("nan"), 1, 1]),
    np.eye(3, dtype=bool),
])
def test_invalid_supercell_matrices_fail(crystal, matrix):
    with pytest.raises(ValueError, match="supercell_matrix"):
        prepare_structure(crystal, supercell_matrix=matrix)


@pytest.mark.parametrize("target", [0, -1, True, 3.5])
def test_invalid_targets_fail(crystal, target):
    with pytest.raises(ValueError, match="target_atoms"):
        prepare_structure(crystal, target_atoms=target)


def test_mutually_exclusive_supercell_options(crystal):
    with pytest.raises(ValueError, match="mutually exclusive"):
        prepare_structure(crystal, target_atoms=8, supercell_matrix=np.eye(3))


@pytest.mark.parametrize("atoms", [Atoms(), Atoms("Li"),
                                         Atoms("Li", cell=np.diag([-1, 1, 1]))])
def test_invalid_crystals_fail(atoms):
    with pytest.raises(ValueError):
        prepare_structure(atoms)


def test_structure_info_reports_units(crystal):
    info = get_structure_info(crystal)
    assert info.n_atoms == 2
    assert info.elements == ("Li", "O")
    assert info.element_counts == {"Li": 1, "O": 1}
    assert info.cell_lengths_A[0] == 3
    assert info.volume_A3 == pytest.approx(60)


@pytest.mark.parametrize("matrix", [
    [[1, 1, 0], [0, 1, 0], [0, 0, 1]],
    [[1, 0, 0], [1, 1, 0], [0, 0, 1]],
])
def test_partial_pbc_rejects_mixing_periodic_and_nonperiodic_vectors(crystal, matrix):
    crystal.pbc = [True, False, False]
    with pytest.raises(ValueError, match="periodic and nonperiodic"):
        prepare_structure(crystal, supercell_matrix=matrix)


def test_partial_pbc_requires_explicit_matrix_for_target_expansion(crystal):
    crystal.pbc = [True, False, False]
    with pytest.raises(ValueError, match="3D PBC"):
        prepare_structure(crystal, target_atoms=8)

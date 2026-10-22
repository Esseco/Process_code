import unittest
from itertools import combinations

import numpy as np
from ase import Atoms
from ase.build import make_supercell
from ase.geometry import is_minkowski_reduced
from pymatgen.core import Lattice, Structure

from Process_Struct import get_supercell_matrices


class SupercellMatricesTests(unittest.TestCase):
    def test_known_cubic_counts(self):
        atoms = Atoms("Cu", cell=np.eye(3) * 3, pbc=True)
        for axes, count in [("abc", 3), ("ab", 2), ("a", 1)]:
            with self.subTest(axes=axes):
                result = get_supercell_matrices(atoms, 2, axes)
                self.assertEqual(len(result["all"]), count)

    def test_all_direction_subsets_and_equivalent_bases(self):
        cell = np.array([[3.1, 0, 0], [0.9, 4.2, 0], [0.4, 0.7, 5.3]])
        atoms = Atoms("Cu", cell=cell, pbc=False)
        for length in (1, 2, 3):
            for subset in combinations("abc", length):
                axes = "".join(subset)
                with self.subTest(axes=axes):
                    result = get_supercell_matrices(atoms, 2, axes)
                    # Generic triclinic cell has only inversion: no HNF pairs merge.
                    self.assertEqual(len(result["all"]), {1: 1, 2: 3, 3: 7}[length])
                    self.assertEqual(len(result["all"]), len(result["recommended"]))
                    for raw, reduced in zip(result["all"], result["recommended"]):
                        change = reduced @ np.linalg.inv(raw)
                        np.testing.assert_allclose(change, np.rint(change), atol=1e-12)
                        self.assertAlmostEqual(abs(np.linalg.det(change)), 1)
                        for matrix in (raw, reduced):
                            self.assertTrue(np.issubdtype(matrix.dtype, np.integer))
                            self.assertAlmostEqual(np.linalg.det(matrix), 2)
                            self.assertEqual(len(make_supercell(atoms, matrix)), 2)
                            for i, axis in enumerate("abc"):
                                if axis not in axes:
                                    np.testing.assert_array_equal(matrix[i], np.eye(3, dtype=int)[i])
                                    np.testing.assert_array_equal(matrix[:, i], np.eye(3, dtype=int)[:, i])
                        self.assertTrue(is_minkowski_reduced(reduced @ cell, [a in axes for a in "abc"]))
        np.testing.assert_array_equal(atoms.cell, cell)
        self.assertFalse(atoms.pbc.any())

    def test_pymatgen_and_repeatability(self):
        structure = Structure(Lattice.cubic(3), ["Cu"], [[0, 0, 0]])
        original = structure.copy()
        first = get_supercell_matrices(structure, 8, "ab")
        second = get_supercell_matrices(structure, 8, "ba")
        for group in ("all", "recommended"):
            np.testing.assert_array_equal(first[group], second[group])
            for matrix in first[group]:
                expanded = structure.copy()
                expanded.make_supercell(matrix)
                self.assertEqual(len(expanded), 8)
                np.testing.assert_allclose(expanded.lattice.matrix, matrix @ structure.lattice.matrix)
        self.assertEqual(structure, original)

    def test_identity_and_invalid_inputs(self):
        atoms = Atoms("Cu", cell=np.eye(3), pbc=True)
        for matrix in get_supercell_matrices(atoms, 1, "ab").values():
            np.testing.assert_array_equal(matrix, [np.eye(3, dtype=int)])
        for size in (0, -1, 2.5, True, np.bool_(True)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                get_supercell_matrices(atoms, size)
        for axes in ("", "xy", "aa", "abcd", None):
            with self.subTest(axes=axes), self.assertRaises(ValueError):
                get_supercell_matrices(atoms, 2, axes)
        for tolerance in (0, -1, np.nan, np.inf):
            with self.assertRaises(ValueError):
                get_supercell_matrices(atoms, 2, symprec=tolerance)
        with self.assertRaises(ValueError):
            get_supercell_matrices(Atoms("Cu"), 2)
        with self.assertRaises(ValueError):
            get_supercell_matrices(Atoms(cell=np.eye(3)), 2)
        with self.assertRaises(TypeError):
            get_supercell_matrices(np.eye(3), 2)
        disordered = Structure(Lattice.cubic(3), [{"Cu": 0.5, "Ag": 0.5}], [[0, 0, 0]])
        with self.assertRaises(ValueError):
            get_supercell_matrices(disordered, 2)


if __name__ == "__main__":
    unittest.main()

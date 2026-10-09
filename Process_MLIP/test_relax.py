"""Small ASE optimizer checks; no trained model required."""
import unittest
from ase import Atoms
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from Process_MLIP import MLIPRelaxer


class RelaxTests(unittest.TestCase):
    def test_convergence_and_constraints(self):
        atoms = Atoms("Cu2", positions=[[0, 0, 0], [2.8, 0, 0]])
        atoms.set_constraint(FixAtoms(indices=[0]))
        result = MLIPRelaxer(atoms, EMT(), steps=0).relax(traj_file=None, log_file=None)
        self.assertFalse(result["optimizer_converged"])
        self.assertEqual(result["relax_steps_used"], 0)
        result = MLIPRelaxer(atoms, EMT(), steps=100).relax(traj_file=None, log_file=None)
        self.assertTrue(result["optimizer_converged"])
        self.assertAlmostEqual(atoms.positions[0, 0], 0)
        self.assertAlmostEqual(result["energy_per_atom"] * 2, result["energy"])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            MLIPRelaxer(Atoms(), EMT())
        with self.assertRaises(ValueError):
            MLIPRelaxer(Atoms("Cu"), EMT(), fmax=0)


if __name__ == "__main__":
    unittest.main()

"""Verify migration using ASE EMT as a fake MACE calculator; no trained model."""
import sys
import unittest
from types import ModuleType
from unittest.mock import patch

from ase import Atoms
from ase.calculators.emt import EMT
from Process_MLIP import relax_structure_mace


class MaceCompatibilityTests(unittest.TestCase):
    def test_old_and_new_entry_points(self):
        from Process_AL_MC import relax_structure_mace as legacy
        from Process_AL_MC.relax import relax_structure_mace as module_legacy
        self.assertIs(legacy, relax_structure_mace)
        self.assertIs(module_legacy, relax_structure_mace)
        module = ModuleType("mace.calculators")
        captured = []

        def calculator(**kwargs):
            captured.append(kwargs)
            return EMT()

        module.MACECalculator = calculator
        atoms = Atoms("Cu2", positions=[[0, 0, 0], [2.8, 0, 0]])
        with patch.dict(sys.modules, {"mace.calculators": module}), patch("pathlib.Path.is_file", return_value=True):
            result = legacy(atoms, "mh-1.model", device="cpu", steps=0, relax_cell=False)
        self.assertEqual(captured[0]["head"], "omat_pbe")
        self.assertEqual(captured[0]["default_dtype"], "float64")
        self.assertFalse(result["optimizer_converged"])
        self.assertEqual(result["atom_count"], 2)
        self.assertIsNone(result["structure_path"])
        self.assertIsNone(atoms.calc)


if __name__ == "__main__":
    unittest.main()

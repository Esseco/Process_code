"""Contract tests with EMT substitutes; real-model checks are separate."""
from pathlib import Path
from contextlib import nullcontext
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from ase.build import bulk
from ase.calculators.emt import EMT

from Process_MLIP import (create_mace_calculator, create_sevennet_calculator,
                          relax_structure_mace, relax_structure_sevennet)


class ModelAdapterTests(unittest.TestCase):
    def setUp(self):
        loader_context = patch("Process_MLIP.calculators._e3nn_import_context",
                               side_effect=nullcontext)
        loader_context.start()
        self.addCleanup(loader_context.stop)

    def test_mh1_filename_variants_and_explicit_head(self):
        module = ModuleType("mace.calculators")
        calls = []
        module.MACECalculator = lambda **kw: calls.append(kw) or EMT()
        with patch.dict(sys.modules, {"mace.calculators": module}), \
                patch("pathlib.Path.is_file", return_value=True):
            for name in ("mace-mh1.model", "mace-mh-1.model", "mace-mh_1.model"):
                create_mace_calculator(name, device="cpu")
                self.assertEqual(calls[-1]["head"], "omat_pbe")
            create_mace_calculator("renamed.model", head="matpes_r2scan")
            self.assertEqual(calls[-1]["head"], "matpes_r2scan")
            create_mace_calculator("mh-10.model")
            self.assertNotIn("head", calls[-1])

    def test_omni_modal_and_cell_relaxation(self):
        module = ModuleType("sevenn.calculator")
        calls = []
        module.SevenNetCalculator = lambda **kw: calls.append(kw) or EMT()
        atoms = bulk("Cu", "fcc", a=3.7)
        original_cell = atoms.cell.copy()
        with patch.dict(sys.modules, {"sevenn.calculator": module}):
            result = relax_structure_sevennet(atoms, steps=2, relax_cell=True,
                                              modal="omat24")
            self.assertEqual(calls[-1], dict(model="7net-omni", device="cpu",
                                             modal="omat24", file_type="checkpoint",
                                             enable_flash=False))
            self.assertEqual(result["sevennet_modal"], "omat24")
            self.assertEqual(result["energy_unit"], "eV")
            self.assertTrue(result["cell_relaxed"])
            self.assertIsNone(atoms.calc)
            self.assertTrue((atoms.cell == original_cell).all())
            create_sevennet_calculator()
            self.assertEqual(calls[-1]["modal"], "mpa")
            with patch("pathlib.Path.is_file", return_value=True):
                create_sevennet_calculator(Path("local.pth"), modal="matpes_r2scan")
                self.assertEqual(calls[-1]["model"], "local.pth")

    def test_invalid_parameters_and_missing_weights(self):
        for loader in (create_mace_calculator, create_sevennet_calculator):
            with self.assertRaises(FileNotFoundError):
                loader("missing-checkpoint-file.pth")
        with self.assertRaises(ValueError):
            create_sevennet_calculator(modal="")
        for relax in (relax_structure_mace, relax_structure_sevennet):
            args = (None, "missing.model")
            for kw in ({"steps": -1}, {"steps": True}, {"fmax": float("nan")}):
                with self.assertRaises(ValueError):
                    relax(*args, **kw)


if __name__ == "__main__":
    unittest.main()

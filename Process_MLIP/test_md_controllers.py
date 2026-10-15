"""Controller dispatch, chain parameters and real EMT cell dynamics."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from ase import units
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.md import nose_hoover_chain as nhc

from Process_MLIP import run_md, run_mlip_md


class ControllerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tmp_controllers_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)

    def run_stage(self, name="md", **parameters):
        options = dict(steps=2, timestep_fs=0.5)
        options.update(parameters)
        return run_md(self.atoms, EMT(), self.root / name, **options)

    def test_defaults_and_invalid_parameters(self):
        result = self.run_stage()
        for key, expected in dict(npt_cell_mode="isotropic", tchain=3, pchain=3,
                                   tloop=1, ploop=1).items():
            self.assertEqual(result["parameters"][key], expected)
        self.assertEqual(result["md_controller"], "NoseHooverChainNVT")
        for parameters in (dict(npt_cell_mode="typo"), dict(npt_cell_mode=None),
                           dict(tchain=0), dict(tchain=True), dict(pchain=-1),
                           dict(tloop=1.5), dict(ploop=0)):
            with self.subTest(parameters=parameters), self.assertRaises((ValueError, TypeError)):
                self.run_stage("bad", **parameters)
        self.assertFalse((self.root / "bad").exists())

    def test_nvt_forwards_only_thermostat_parameters(self):
        with patch.object(nhc, "NoseHooverChainNVT", wraps=nhc.NoseHooverChainNVT) as factory:
            result = self.run_stage(tchain=5, tloop=2, pchain=4, ploop=3)
        kwargs = factory.call_args.kwargs
        self.assertEqual(kwargs["tchain"], 5)
        self.assertEqual(kwargs["tloop"], 2)
        self.assertNotIn("pchain", kwargs)
        self.assertNotIn("ploop", kwargs)
        self.assertNotIn("pressure_au", kwargs)
        np.testing.assert_array_equal(result["final_atoms"].cell, self.atoms.cell)

    def test_isotropic_forwards_both_chains_and_preserves_shape(self):
        self.atoms.set_cell(self.atoms.cell @ np.diag([1.05, 0.98, 1.0]), scale_atoms=True)
        shape = self.atoms.cell.array / self.atoms.get_volume() ** (1 / 3)
        with patch.object(nhc, "IsotropicMTKNPT", wraps=nhc.IsotropicMTKNPT) as factory:
            result = self.run_stage(ensemble="npt", tchain=4, pchain=5, tloop=2, ploop=3)
        kwargs = factory.call_args.kwargs
        for key, value in dict(tchain=4, pchain=5, tloop=2, ploop=3).items():
            self.assertEqual(kwargs[key], value)
        self.assertEqual(kwargs["pressure_au"], units.bar)
        final = result["final_atoms"]
        np.testing.assert_allclose(final.cell.array / final.get_volume() ** (1 / 3), shape,
                                   rtol=1e-12, atol=1e-12)
        self.assertEqual(result["md_controller"], "IsotropicMTKNPT")

    def test_full_dispatch_contract(self):
        # API forwarding only; the separate real-MTK test verifies shape motion.
        with patch.object(nhc, "MTKNPT", create=True, side_effect=nhc.IsotropicMTKNPT) as factory:
            result = self.run_stage(ensemble="npt", npt_cell_mode="FULL",
                                    tchain=4, pchain=5, tloop=2, ploop=3)
        factory.assert_called_once()
        for key, value in dict(tchain=4, pchain=5, tloop=2, ploop=3).items():
            self.assertEqual(factory.call_args.kwargs[key], value)
        self.assertEqual(result["parameters"]["npt_cell_mode"], "full")

    def test_missing_full_implementation_fails_before_loading_or_writing(self):
        with patch.object(nhc, "MTKNPT", None, create=True), \
                patch("Process_MLIP.md_workflow.create_mlip_calculator") as loader:
            with self.assertRaisesRegex(ImportError, "MTKNPT"):
                self.run_stage(ensemble="npt", npt_cell_mode="full")
            with self.assertRaisesRegex(ImportError, "MTKNPT"):
                run_mlip_md(self.atoms, output_dir=self.root / "workflow", stages=[
                    dict(ensemble="nvt", steps=1),
                    dict(ensemble="npt", npt_cell_mode="full", steps=1)])
            loader.assert_not_called()
            # An NVT stage does not need an NPT implementation, even when a
            # shared config specifies full mode for later stages.
            self.run_stage("nvt", npt_cell_mode="full")
        self.assertFalse((self.root / "md").exists())
        self.assertFalse((self.root / "workflow").exists())

    def test_stage_overrides_and_reporting(self):
        with patch.object(nhc, "MTKNPT", create=True, side_effect=nhc.IsotropicMTKNPT), \
                patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=EMT()) as loader:
            result = run_mlip_md(self.atoms, output_dir=self.root / "workflow",
                                 tchain=4, pchain=4, tloop=1, ploop=1, steps=2,
                                 stages=[dict(ensemble="npt"), dict(ensemble="npt",
                                         npt_cell_mode="full", tchain=5, ploop=2)])
        loader.assert_called_once()
        first, second = result["stage_results"]
        self.assertEqual(first["parameters"]["npt_cell_mode"], "isotropic")
        self.assertEqual(second["parameters"]["tchain"], 5)
        self.assertEqual(second["parameters"]["pchain"], 4)
        report = json.loads(Path(result["report_file"]).read_text())
        self.assertEqual(report["stage_results"][1]["parameters"]["ploop"], 2)

    @unittest.skipUnless(hasattr(nhc, "MTKNPT"), "Installed ASE lacks full MTKNPT")
    def test_real_full_mtk_changes_cell_shape(self):
        deformation = np.array([[1.06, 0.05, 0], [0, 0.97, 0.04], [0, 0, 1.02]])
        self.atoms.set_cell(self.atoms.cell @ deformation, scale_atoms=True)
        shape = self.atoms.cell.array / self.atoms.get_volume() ** (1 / 3)
        result = self.run_stage(ensemble="npt", npt_cell_mode="full", steps=4,
                                pdamp_fs=500, tchain=4, pchain=4, tloop=2, ploop=2)
        final = result["final_atoms"]
        self.assertTrue(np.isfinite(final.positions).all())
        self.assertTrue(np.isfinite(final.get_stress()).all())
        self.assertGreater(np.linalg.det(final.cell), 0)
        final_shape = final.cell.array / final.get_volume() ** (1 / 3)
        self.assertGreater(np.linalg.norm(final_shape - shape), 1e-9)
        self.assertEqual(result["md_controller"], "MTKNPT")


if __name__ == "__main__":
    unittest.main()

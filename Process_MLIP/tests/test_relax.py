"""共享优化器、预弛豫收敛和晶胞稳定性。"""
from pathlib import Path
from unittest.mock import patch
import json
import unittest

from ase import Atoms
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from ase.filters import FrechetCellFilter
from ase.io import read
from ase.optimize import FIRE
import numpy as np

from Process_MLIP import MLIPRelaxer, run_md, run_mlip_md
from Process_MLIP.tests._support import NoStress, TemporaryDirectoryMixin


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


class PreRelaxTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.atoms = Atoms("Cu2", positions=[[1, 1, 1], [3.8, 1, 1]], cell=[10]*3, pbc=True)
        self.calculator = EMT()
        loader = patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=self.calculator)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def run_workflow(self, name="md", **kwargs):
        return run_mlip_md(self.atoms, output_dir=self.root / name, steps=0, **kwargs)

    def test_disabled_by_default(self):
        result = self.run_workflow()
        self.assertIsNone(result["pre_relax_result"])
        self.assertFalse((self.root / "md" / "00_relax").exists())
        self.loader.assert_called_once()

    def test_explicit_enabled_flag_in_configuration(self):
        disabled = self.run_workflow("disabled", pre_relax=dict(enabled=False))
        self.assertIsNone(disabled["pre_relax_result"])
        enabled = self.run_workflow("enabled", pre_relax=dict(enabled=True, fmax=0.02, steps=100))
        self.assertTrue(enabled["pre_relax_result"]["optimizer_converged"])

    def test_alternative_optimizers(self):
        for optimizer in ("FIRE", "LBFGS"):
            with self.subTest(optimizer=optimizer):
                result = self.run_workflow(optimizer, pre_relax=dict(optimizer=optimizer, steps=200))
                self.assertTrue(result["pre_relax_result"]["optimizer_converged"])

    def test_atoms_only_relaxation_reuses_model_and_feeds_md(self):
        original = self.atoms.copy()
        with patch("Process_MLIP.md_workflow.run_md", wraps=run_md) as md:
            result = self.run_workflow(pre_relax=dict(fmax=0.02, steps=100))
        relaxation = result["pre_relax_result"]
        self.loader.assert_called_once()
        self.assertIs(relaxation["final_atoms"].calc, self.calculator)
        self.assertIs(md.call_args.args[1], self.calculator)
        self.assertTrue(relaxation["optimizer_converged"])
        self.assertFalse(relaxation["cell_relaxed"])
        self.assertGreater(relaxation["relax_steps_used"], 0)
        self.assertLessEqual(relaxation["force_max_ev_per_angstrom"], 0.02)
        np.testing.assert_array_equal(relaxation["final_atoms"].cell, original.cell)
        self.assertFalse(np.allclose(relaxation["final_atoms"].positions, original.positions))
        frame = read(result["stage_results"][0]["trajectory_file"], index=0)
        np.testing.assert_allclose(frame.positions, relaxation["final_atoms"].positions)
        np.testing.assert_array_equal(self.atoms.positions, original.positions)
        self.assertFalse(self.atoms.has("momenta"))
        self.assertIsNone(self.atoms.calc)
        report = json.loads(Path(result["report_file"]).read_text())
        self.assertTrue(report["pre_relax_result"]["optimizer_converged"])
        self.assertEqual(report["elapsed_time_fs"], 0)

    def test_cell_relaxation_and_md_cell_inheritance(self):
        self.atoms = bulk("Cu", "fcc", a=4.0, cubic=True)
        cell = self.atoms.cell.copy()
        result = self.run_workflow(pre_relax=dict(relax_cell=True, fmax=0.02, steps=100),
                                   stages=[dict(ensemble="nvt", steps=2),
                                           dict(ensemble="npt", steps=2)])
        relaxation = result["pre_relax_result"]
        self.assertTrue(relaxation["optimizer_converged"])
        self.assertTrue(relaxation["cell_relaxed"])
        self.assertFalse(np.allclose(relaxation["final_atoms"].cell, cell))
        frame = read(result["stage_results"][0]["trajectory_file"], index=0)
        np.testing.assert_allclose(frame.cell, relaxation["final_atoms"].cell)
        self.assertEqual(result["total_steps"], 4)
        self.loader.assert_called_once()
        self.assertTrue(np.isfinite(result["final_atoms"].get_potential_energy()))
        self.assertEqual(self.atoms.get_volume(), abs(np.linalg.det(cell)))

    def test_explicit_overwrite_preserves_unrelated_files(self):
        self.run_workflow(pre_relax=True)
        sentinel = self.root / "md" / "00_relax" / "unrelated.txt"
        sentinel.write_text("keep")
        repeated = self.run_workflow(pre_relax=True, overwrite=True)
        self.assertEqual(repeated["status"], "completed")
        self.assertEqual(sentinel.read_text(), "keep")

    def test_nonconvergence_stops_by_default_or_explicitly_continues(self):
        with self.assertRaisesRegex(RuntimeError, "did not converge"):
            self.run_workflow(pre_relax=dict(steps=0))
        summary = json.loads((self.root / "md" / "run_report.json").read_text())
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["stages_completed"], 0)
        self.assertFalse(summary["pre_relax_result"]["optimizer_converged"])
        self.assertTrue((self.root / "md" / "00_relax" / "final.traj").is_file())
        self.assertFalse((self.root / "md" / "01_nvt").exists())
        result = self.run_workflow("allowed", pre_relax=dict(steps=0, require_convergence=False))
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["pre_relax_result"]["optimizer_converged"])

    def test_bad_configuration_and_collisions_fail_before_loading(self):
        for config in ("yes", dict(enabled="yes"), dict(relax_cell="yes"),
                       dict(steps=-1), dict(steps=True), dict(fmax=0),
                       dict(fmax=float("nan")), dict(optimizer="unknown"),
                       dict(require_convergence="yes"), dict(typo=1)):
            with self.subTest(config=config), self.assertRaises((ValueError, TypeError)):
                self.run_workflow(pre_relax=config)
        self.loader.assert_not_called()
        self.assertFalse((self.root / "md").exists())
        target = self.root / "md" / "00_relax"
        target.mkdir(parents=True)
        (target / "relax.log").write_text("keep")
        with self.assertRaises(FileExistsError):
            self.run_workflow(pre_relax=True)
        self.loader.assert_not_called()
        self.assertEqual((target / "relax.log").read_text(), "keep")

    def test_cell_requires_pbc_and_stress_but_atoms_only_does_not(self):
        self.atoms.pbc = False
        with self.assertRaises(ValueError):
            self.run_workflow(pre_relax=dict(relax_cell=True))
        self.loader.assert_not_called()
        self.atoms.pbc = True
        self.loader.return_value = NoStress()
        with self.assertRaisesRegex(ValueError, "stress"):
            self.run_workflow(pre_relax=dict(relax_cell=True))
        result = self.run_workflow("fixed", pre_relax=True)
        self.assertTrue(result["pre_relax_result"]["optimizer_converged"])

    def test_existing_momenta_preserved_and_new_velocities_initialized_after_relaxation(self):
        self.atoms.set_momenta([[1, 2, 3], [-1, -2, -3]])
        momenta = self.atoms.get_momenta().copy()
        result = self.run_workflow(pre_relax=dict(fmax=0.02, steps=100))
        np.testing.assert_array_equal(result["pre_relax_result"]["final_atoms"].get_momenta(), momenta)
        np.testing.assert_array_equal(result["final_atoms"].get_momenta(), momenta)
        self.assertEqual(result["stage_results"][0]["velocity_initialization"], "preserved")
        self.atoms.arrays.pop("momenta")
        result = self.run_workflow("new", pre_relax=dict(fmax=0.02, steps=100))
        self.assertFalse(result["pre_relax_result"]["final_atoms"].has("momenta"))
        self.assertGreater(result["final_atoms"].get_kinetic_energy(), 0)

    def test_optimizer_failure_stops_md_and_records_failure(self):
        with patch("Process_MLIP.MLIP_Relax.MLIPRelaxer.relax", side_effect=RuntimeError("optimizer failure")):
            with self.assertRaisesRegex(RuntimeError, "optimizer failure"):
                self.run_workflow(pre_relax=True)
        report = json.loads((self.root / "md" / "00_relax" / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertFalse((self.root / "md" / "01_nvt").exists())

    def test_frechet_step_limit_and_effective_scaling_report(self):
        self.atoms = bulk("Cu", "fcc", a=4.0, cubic=True)
        with patch("ase.filters.FrechetCellFilter", wraps=FrechetCellFilter) as cell_filter, \
                patch("Process_MLIP.MLIP_Relax.FIRE", wraps=FIRE) as optimizer:
            result = self.run_workflow(pre_relax=dict(relax_cell=True, steps=2,
                                                     require_convergence=False))
        cell_filter.assert_called_once()
        self.assertIsNone(cell_filter.call_args.kwargs["exp_cell_factor"])
        self.assertEqual(optimizer.call_args.kwargs["maxstep"], 0.05)
        report = result["pre_relax_result"]
        self.assertEqual(report["cell_filter"], "FrechetCellFilter")
        self.assertEqual(report["exp_cell_factor"], len(self.atoms))
        self.assertEqual(report["parameters"]["optimizer"], "FIRE")

    def test_custom_step_and_cell_scaling(self):
        self.atoms = bulk("Cu", "fcc", a=3.9, cubic=True)
        for optimizer in ("BFGS", "FIRE", "LBFGS"):
            with self.subTest(optimizer=optimizer):
                result = self.run_workflow(optimizer, pre_relax=dict(
                    relax_cell=True, optimizer=optimizer, maxstep=0.02,
                    exp_cell_factor=12, steps=2, require_convergence=False))
                report = result["pre_relax_result"]
                self.assertEqual(report["maxstep"], 0.02)
                self.assertEqual(report["exp_cell_factor"], 12)

    def test_invalid_step_settings_fail_before_model_loading(self):
        for key in ("maxstep", "exp_cell_factor"):
            for value in (True, 0, -1, float("nan"), float("inf"), "0.05"):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.run_workflow(pre_relax={key:value})
        with self.assertRaises(ValueError):
            self.run_workflow(pre_relax=dict(maxstep=None))
        self.loader.assert_not_called()

    def test_supercell_full_relaxation_remains_finite_and_reduces_energy(self):
        self.atoms = bulk("Cu", "fcc", a=3.9, cubic=True).repeat((3,3,3))
        initial_volume = self.atoms.get_volume()
        result = self.run_workflow(pre_relax=dict(relax_cell=True, steps=20,
                                                require_convergence=False))
        report = result["pre_relax_result"]
        self.assertLess(report["final_state"]["potential_energy_eV"],
                        report["initial_state"]["potential_energy_eV"])
        frames = read(report["trajectory_file"], index=":")
        for frame in frames:
            self.assertTrue(np.all(np.isfinite(frame.positions)))
            self.assertTrue(0.8 * initial_volume < frame.get_volume() < 1.2 * initial_volume)
        # Cell scaling makes the first update mild for an extensive supercell.
        self.assertLess(abs(frames[1].get_volume()/initial_volume-1), 0.01)


class SharedOptimizerTests(TemporaryDirectoryMixin, unittest.TestCase):
    def test_single_structure_uses_same_optimizer_with_historical_defaults(self):
        from Process_MLIP._relaxation import _relax_structure

        atoms = bulk("Cu", "fcc", a=3.7, cubic=True)
        original = atoms.copy()
        with patch("Process_MLIP._relaxation.MLIPRelaxer", wraps=MLIPRelaxer) as factory:
            result = _relax_structure(atoms, EMT())
        self.assertEqual(factory.call_args.kwargs["optimizer"], "LBFGS")
        self.assertEqual(factory.call_args.kwargs["steps"], 150)
        self.assertNotIn("maxstep", factory.call_args.kwargs)
        self.assertTrue(result["optimizer_converged"])
        self.assertIsNone(result["structure_path"])
        self.assertEqual(set(result), {
            "status", "relax_stopped_normally", "optimizer_converged", "energy",
            "energy_per_atom", "energy_unit", "forces_ev_per_angstrom",
            "force_max_ev_per_angstrom", "force_rms_ev_per_angstrom", "atom_count",
            "relax_steps_used", "fmax_target_ev_per_angstrom", "cell_relaxed", "structure_path",
        })
        np.testing.assert_array_equal(atoms.positions, original.positions)
        np.testing.assert_array_equal(atoms.cell, original.cell)
        self.assertIsNone(atoms.calc)


if __name__ == "__main__":
    unittest.main()

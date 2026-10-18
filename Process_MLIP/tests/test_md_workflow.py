"""模型复用、多阶段衔接及预检查。"""
from pathlib import Path
from unittest.mock import patch
import json
import unittest

from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import read
import numpy as np

from Process_MLIP import model_config, run_mlip_md
from Process_MLIP.tests._support import TemporaryDirectoryMixin


class WorkflowTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)
        self.loader = patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=EMT())
        self.mock_loader = self.loader.start()
        self.addCleanup(self.loader.stop)

    def test_load_once_stage_precedence_and_continuation(self):
        stages = [dict(ensemble="nvt", name="equil", steps=2, timestep_fs=0.5),
                  dict(ensemble="npt", steps=2)]
        result = run_mlip_md(self.atoms, model_config("mace-mh1"), self.root / "md",
                             stages, timestep_fs=1.0, temperature_K=300,
                             initialize_velocities=True)
        self.mock_loader.assert_called_once()
        self.assertEqual(result["total_steps"], 4)
        self.assertEqual(result["elapsed_time_fs"], 3)
        first, second = result["stage_results"]
        initial = read(second["trajectory_file"], index=0)
        np.testing.assert_allclose(initial.get_momenta(), first["final_atoms"].get_momenta())
        np.testing.assert_allclose(initial.cell, first["final_atoms"].cell)
        np.testing.assert_allclose(initial.positions, first["final_atoms"].positions)
        self.assertEqual(second["velocity_initialization"], "preserved")
        self.assertEqual(stages[0]["name"], "equil")  # input configuration not mutated
        summary = json.loads(Path(result["report_file"]).read_text())
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["stages_completed"], 2)
        self.assertEqual(summary["model"]["head"], "omat_pbe")

    def test_independent_single_stage_and_explicit_resampling(self):
        for ensemble in ("nvt", "npt"):
            result = run_mlip_md(self.atoms, "chgnet", self.root / ensemble,
                                 ensemble=ensemble, steps=1)
            self.assertEqual(len(result["stage_results"]), 1)
        result = run_mlip_md(self.atoms, "orb-v3", self.root / "resample", stages=[
            dict(steps=0), dict(steps=0, temperature_K=600, initialize_velocities=True)])
        self.assertEqual(result["stage_results"][1]["velocity_initialization"], "sampled")

    def test_validate_all_stages_and_collisions_before_loading(self):
        bad_sequences = [[], [dict(steps=1), dict(ensemble="wrong")],
                         [dict(steps=1), dict(timestep_fs=0)],
                         [dict(name="../escape")], [dict(misspelled=1)]]
        for stages in bad_sequences:
            with self.assertRaises(ValueError):
                run_mlip_md(self.atoms, output_dir=self.root / "bad", stages=stages)
        self.mock_loader.assert_not_called()
        self.assertFalse((self.root / "bad").exists())
        target = self.root / "exists" / "02_npt"
        target.mkdir(parents=True)
        (target / "md.csv").write_text("keep")
        with self.assertRaises(FileExistsError):
            run_mlip_md(self.atoms, output_dir=target.parent, stages=[
                dict(ensemble="nvt"), dict(ensemble="npt")])
        self.mock_loader.assert_not_called()
        self.assertFalse((target.parent / "01_nvt").exists())
        invalid_root = self.root / "file_not_directory"
        invalid_root.write_text("keep")
        with self.assertRaises(NotADirectoryError):
            run_mlip_md(self.atoms, output_dir=invalid_root, steps=1)
        self.mock_loader.assert_not_called()

    def test_failure_summary_does_not_claim_completion(self):
        with patch("Process_MLIP.md_workflow.run_md", side_effect=RuntimeError("failed stage")):
            with self.assertRaisesRegex(RuntimeError, "failed stage"):
                run_mlip_md(self.atoms, output_dir=self.root / "failed", steps=1)
        report = json.loads((self.root / "failed" / "run_report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["stages_completed"], 0)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from ase.build import bulk

from Process_MLIP.nep_md import run_nep_md


class NepNativeMDTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nep-md-test-")
        self.root = Path(self.tmp.name)
        self.model = self.root / "model.txt"
        self.model.write_text("nep4 1 Cu\n")
        self.addCleanup(self.tmp.cleanup)

    def test_stages_model_xyz_and_run_input(self):
        output = self.root / "run"
        executable = self.root / "gpumd.exe"
        executable.write_text("placeholder")

        def run(command, **kwargs):
            return SimpleNamespace(returncode=0, stdout="done", stderr="")

        with patch("Process_MLIP.nep_md.subprocess.run", side_effect=run) as runner, \
             patch("Process_MLIP.nep_md.shutil.which", return_value=str(executable)):
            result = run_nep_md(
                bulk("Cu", "fcc", a=3.6, cubic=True), self.model, output,
                parameters={"dump_thermo": 10, "dump_xyz": [10, "movie.xyz"], "run": 20},
                executable="gpumd.exe",
            )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(runner.call_args.args[0], [str(executable.resolve())])
        model_text = (output / "model.xyz").read_text()
        self.assertIn("Properties=species:S:1:pos:R:3:mass:R:1", model_text)
        run_text = (output / "run.in").read_text()
        self.assertIn("potential nep.txt", run_text)
        self.assertIn("run 20", run_text)
        report = json.loads((output / "report.json").read_text())
        self.assertEqual(report["backend"], "gpumd")
        self.assertEqual(report["parameters"]["run"], 20)
        self.assertEqual(report["environment"], {})
        self.assertTrue((output / "manifest.json").is_file())

    def test_missing_executable_fails_before_output_creation(self):
        output = self.root / "missing"
        with patch("Process_MLIP.nep_md.shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                run_nep_md(bulk("Cu", "fcc", a=3.6), self.model, output,
                            parameters={"run": 1}, executable="missing-gpumd")
        self.assertFalse(output.exists())

    def test_failed_run_keeps_failure_report(self):
        output = self.root / "failed"
        with patch("Process_MLIP.nep_md.subprocess.run",
                   return_value=SimpleNamespace(returncode=3, stdout="", stderr="bad")), \
             patch("Process_MLIP.nep_md.shutil.which", return_value="gpumd"):
            with self.assertRaisesRegex(RuntimeError, "return code 3"):
                run_nep_md(bulk("Cu", "fcc", a=3.6), self.model, output,
                            parameters={"run": 1})
        report = json.loads((output / "report.json").read_text())
        self.assertEqual(report["status"], "failed")

    def test_nonperiodic_structure_is_rejected(self):
        atoms = bulk("Cu", "fcc", a=3.6)
        atoms.pbc = (True, True, False)
        with patch("Process_MLIP.nep_md.shutil.which", return_value="gpumd"):
            with self.assertRaisesRegex(ValueError, "periodic"):
                run_nep_md(atoms, self.model, self.root / "nonperiodic",
                            parameters={"run": 1})


if __name__ == "__main__":
    unittest.main()

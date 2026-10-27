import json
import tempfile
import unittest
import numpy as np
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ase import Atoms
from ase.io import write

from Process_MLIP.nep_training import (
    fine_tune_nep,
    prepare_nep_training,
    train_nep,
)


def _dataset(path):
    atoms = Atoms("LiO", positions=[[0, 0, 0], [2, 2, 2]],
                  cell=[4, 4, 4], pbc=True)
    atoms.info["energy"] = -1.0
    atoms.arrays["force"] = np.zeros((2, 3))
    write(path, [atoms], format="extxyz", write_results=False)


class NepTrainingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nep-training-test-")
        self.root = Path(self.tmp.name)
        self.train = self.root / "source-train.xyz"
        self.test = self.root / "source-test.xyz"
        _dataset(self.train)
        _dataset(self.test)
        self.addCleanup(self.tmp.cleanup)

    def test_prepare_writes_inputs_and_manifest(self):
        task = self.root / "task"
        result = prepare_nep_training(
            task, self.train, self.test, species=["Li", "O"],
            parameters={"generation": 2, "seed": 7},
        )
        self.assertEqual(result["train_file"], str(task / "train.xyz"))
        text = (task / "nep.in").read_text()
        self.assertIn("type 2 Li O", text)
        self.assertIn("version 4", text)
        self.assertIn("generation 2", text)
        manifest = json.loads((task / "manifest.json").read_text())
        self.assertEqual(manifest["seed"], 7)
        self.assertTrue((task / "train.xyz").is_file())

    def test_train_invokes_explicit_executable_and_writes_report(self):
        task = self.root / "task"
        prepare_nep_training(task, self.train, self.test, species=["Li", "O"])
        executable = self.root / "nep.exe"
        executable.write_text("placeholder")

        def run(command, **kwargs):
            (task / "nep.txt").write_text("nep4 2 Li O\n")
            return SimpleNamespace(returncode=0, stdout="trained", stderr="")

        with patch("Process_MLIP.nep_training.subprocess.run", side_effect=run) as runner, \
             patch("Process_MLIP.nep_training.shutil.which", return_value=str(executable)):
            result = train_nep(task, executable="nep.exe", env={"NEP_SEED": "7"})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(runner.call_args.args[0], [str(executable.resolve())])
        self.assertFalse(runner.call_args.kwargs["shell"])
        report = json.loads((task / "training_report.json").read_text())
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["environment"], {"NEP_SEED": "7"})
        self.assertEqual(report["seed"], None)
        with self.assertRaises(FileExistsError):
            train_nep(task, executable="nep.exe")

    def test_finetune_copies_foundation_and_rejects_architecture_change(self):
        task = self.root / "task"
        foundation = self.root / "foundation.txt"
        restart = self.root / "foundation.restart"
        foundation.write_text(
            "nep4 2 Li O\n"
            "zbl 2\ncutoff 6 5\nn_max 4 4\n"
            "basis_size 8 8\nl_max 4 2 1\nANN 80 0\n"
        )
        restart.write_text("restart")
        executable = self.root / "nep.exe"
        executable.write_text("placeholder")
        def run(command, **kwargs):
            (task / "nep.txt").write_text("nep4 2 Li O\n")
            return SimpleNamespace(returncode=0, stdout="fine-tuned", stderr="")
        with patch("Process_MLIP.nep_training.subprocess.run", side_effect=run), \
             patch("Process_MLIP.nep_training.shutil.which", return_value=str(executable)):
            result = fine_tune_nep(
                task, foundation, restart, species=["Li", "O"],
                train_xyz=self.train, test_xyz=self.test,
                parameters={"generation": 5}, executable="nep.exe",
            )
        self.assertEqual(result["mode"], "fine_tune")
        text = (task / "nep.in").read_text()
        self.assertIn("fine_tune foundation.txt foundation.restart", text)
        self.assertIn("neuron 80", text)
        with self.assertRaisesRegex(ValueError, "architecture"):
            fine_tune_nep(
                self.root / "bad", foundation, restart, species=["Li", "O"],
                train_xyz=self.train, test_xyz=self.test,
                parameters={"neuron": 30},
            )
        with self.assertRaisesRegex(ValueError, "species"):
            fine_tune_nep(
                self.root / "bad-species", foundation, restart, species=["Li", "F"],
                train_xyz=self.train, test_xyz=self.test,
                executable="nep.exe",
            )

    def test_missing_foundation_or_dataset_fails_without_task(self):
        with self.assertRaises(FileNotFoundError):
            fine_tune_nep(self.root / "bad", self.root / "missing.txt",
                          self.root / "missing.restart", species=["Li"])
        with self.assertRaises(FileNotFoundError):
            prepare_nep_training(self.root / "bad", self.root / "missing.xyz",
                                 self.test, species=["Li", "O"])


if __name__ == "__main__":
    unittest.main()

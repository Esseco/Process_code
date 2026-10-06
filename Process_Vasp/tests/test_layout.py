"""Check functional layout, legacy imports and generated project-based tasks."""

import importlib
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pymatgen.core import Lattice, Structure
from pymatgen.io.vasp.inputs import Incar, Kpoints

from Process_Vasp import generate_atomate_input, generate_vasp_input


class LayoutTests(unittest.TestCase):
    def test_legacy_modules_are_same_objects(self):
        for old, new in {
            "generation": "inputs.generation", "incar": "inputs.incar",
            "excitation": "inputs.excitation", "dos": "results.dos",
            "reader": "results.reader", "status": "results.status",
            "magnetism": "results.magnetism", "structure": "structures.structure",
            "atomate_runner": "workflows.atomate_runner",
        }.items():
            with self.subTest(module=old):
                self.assertIs(importlib.import_module(f"Process_Vasp.{old}"),
                              importlib.import_module(f"Process_Vasp.{new}"))

    def test_workflow_uses_project_runner_and_template(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "initial.cif"
            Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]]).to(filename=source)
            target = generate_atomate_input(root / "task", source, job_name="layout_test")
            self.assertEqual(
                set(path.name for path in target.iterdir()),
                {"initial_structure.cif", "workflow.json", "workflow.py", "submit_gpu.sh"},
            )
            script = (target / "submit_gpu.sh").read_text(encoding="utf-8")
            self.assertIn("#SBATCH --job-name=layout_test", script)
            self.assertIn("python3 workflow.py", script)
            self.assertIn("from Process_Vasp.workflows.atomate_runner import main",
                          (target / "workflow.py").read_text(encoding="utf-8"))
            self.assertTrue((target / "workflow.json").is_file())

    def test_vasp_generation_finds_lsf_template(self):
        structure = Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]])
        inputs = SimpleNamespace(incar=Incar({"ENCUT": 520}),
                                 kpoints=Kpoints.gamma_automatic())
        with tempfile.TemporaryDirectory() as folder:
            with patch("Process_Vasp.generation.MPRelaxSet", return_value=inputs):
                generate_vasp_input(structure, folder, {}, False, "layout_test")
            self.assertTrue((Path(folder) / "INCAR").is_file())
            self.assertTrue((Path(folder) / "KPOINTS").is_file())
            self.assertIn("#BSUB -J layout_test",
                          (Path(folder) / "vasp.lsf").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

"""Checkpoint and restart tests; no VASP execution."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pymatgen.core import Lattice, Structure
from Process_Vasp.atomate_runner import run_workflow


class StageDirectoryTests(unittest.TestCase):
    def test_completed_legacy_relax_starts_with_static(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            initial = Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]])
            relaxed = Structure(Lattice.cubic(4), ["Si"], [[0.1, 0, 0]])
            initial.to(filename=root / "initial.cif")
            (root / "workflow.json").write_text(json.dumps({
                "calculation": "dos", "structure_file": "initial.cif",
                "incar_settings": {}, "kpoints_settings": {},
            }), encoding="utf-8")
            old = root / "runs" / "job_2026-10-01-00-00-00"
            old.mkdir(parents=True)
            initial.to(fmt="poscar", filename=old / "POSCAR")
            (old / "INCAR").write_text("NSW = 99\n")
            (old / "vasprun.xml").write_text("stub")
            (old / "complete").write_text("ok")
            calls = []
            def make_job(stage, current, previous, config):
                if stage == "static":
                    self.assertEqual(previous, old)
                    self.assertAlmostEqual(current[0].frac_coords[0], 0.1)
                return SimpleNamespace(uuid=stage, index=1)
            def execute(job, **kwargs):
                directory = Path(kwargs["root_dir"])
                calls.append(job.uuid)
                (directory / "complete").write_text("ok")
                (directory / "vasprun.xml").write_text("stub")
                return {job.uuid: {1: SimpleNamespace(stop_children=False, stop_jobflow=False)}}
            def validate(directory, stage):
                if not (directory / "complete").is_file():
                    raise ValueError("incomplete output")
                return relaxed
            with patch("Process_Vasp.atomate_runner._job", side_effect=make_job), patch("Process_Vasp.atomate_runner._validate", side_effect=validate), patch("jobflow.run_locally", side_effect=execute):
                state = run_workflow(root)
            self.assertEqual(calls, ["static", "dos"])
            self.assertTrue(state["stages"]["relax"]["legacy"])

    def test_failed_relax_uses_valid_contcar_and_reports_quota_error(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            initial = Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]])
            updated = Structure(Lattice.cubic(4), ["Si"], [[0.1, 0, 0]])
            initial.to(filename=root / "initial.cif")
            (root / "workflow.json").write_text(json.dumps({
                "calculation": "relax", "structure_file": "initial.cif",
                "incar_settings": {}, "kpoints_settings": {},
            }), encoding="utf-8")
            inputs = []
            def make_job(stage, current, previous, config):
                inputs.append(current[0].frac_coords[0])
                return SimpleNamespace(uuid=stage, index=1)
            def execute(job, **kwargs):
                directory = Path(kwargs["root_dir"])
                if len(inputs) == 1:
                    updated.to(fmt="poscar", filename=directory / "CONTCAR")
                    (directory / "std_err.txt").write_text("FIO/stdio: Disk quota exceeded")
                    raise RuntimeError("VASP stopped")
                (directory / "complete").write_text("ok")
                (directory / "vasprun.xml").write_text("stub")
                return {job.uuid: {1: SimpleNamespace(stop_children=False, stop_jobflow=False)}}
            def validate(directory, stage):
                if not (directory / "complete").is_file():
                    raise ValueError("incomplete output")
                return updated
            with patch("Process_Vasp.atomate_runner._job", side_effect=make_job), patch("Process_Vasp.atomate_runner._validate", side_effect=validate), patch("jobflow.run_locally", side_effect=execute):
                with self.assertRaisesRegex(RuntimeError, "VASP stopped"):
                    run_workflow(root)
                report = json.loads((root / "workflow_status.json").read_text())
                self.assertEqual(report["stage"], "relax")
                self.assertIn("Disk quota exceeded", report["reason"])
                state = run_workflow(root)
            self.assertAlmostEqual(inputs[0], 0)
            self.assertAlmostEqual(inputs[1], 0.1)
            self.assertEqual(state["stages"]["relax"]["attempt"], 2)
            self.assertEqual(json.loads((root / "workflow_status.json").read_text())["status"], "completed")

    def test_restart_parameters_import_and_kill_window(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            structure = Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]])
            structure.to(filename=root / "initial.cif")
            config = {"calculation": "dos", "structure_file": "initial.cif",
                      "incar_settings": {}, "kpoints_settings": {},
                      "export_plot_data": True}
            def save_config():
                (root / "workflow.json").write_text(json.dumps(config), encoding="utf-8")
            save_config()
            calls = []
            fail = {"static": True}
            def make_job(stage, current, previous, config):
                if previous:
                    self.assertTrue((previous / "complete").exists())
                return SimpleNamespace(uuid=stage, index=1)
            def execute(job, **kwargs):
                directory = Path(kwargs["root_dir"])
                calls.append(job.uuid)
                if fail.get(job.uuid):
                    raise RuntimeError("simulated scheduler termination")
                (directory / "complete").write_text("ok")
                (directory / "vasprun.xml").write_text("stub")
                return {job.uuid: {1: SimpleNamespace(stop_children=False, stop_jobflow=False)}}
            def validate(directory, stage):
                if not (directory / "complete").is_file():
                    raise ValueError("incomplete output")
                return structure
            def export(stage, calculation_dir, task_dir):
                self.assertEqual(stage, "dos")
                self.assertTrue((calculation_dir / "complete").is_file())
                output = task_dir / "dos.csv"
                output.write_text("energy,dos_up\n0,1\n")
                return [str(output)]
            with patch("Process_Vasp.atomate_runner._job", side_effect=make_job), patch("Process_Vasp.atomate_runner._validate", side_effect=validate), patch("jobflow.run_locally", side_effect=execute), patch("Process_Vasp.workflows.plot_exports.export_plot_data", side_effect=export):
                with self.assertRaisesRegex(RuntimeError, "termination"):
                    run_workflow(root)
                fail["static"] = False
                state = run_workflow(root)
                self.assertEqual(calls, ["relax", "static", "static", "dos"])
                self.assertEqual(state["stages"]["static"]["attempt"], 2)
                self.assertEqual(state["exports"]["dos"]["status"], "completed")
                self.assertTrue((root / "dos.csv").is_file())
                run_workflow(root)
                self.assertEqual(len(calls), 4)
                # Resources are not scientific input changes; static ENCUT is.
                config["incar_settings"]["static"] = {"ENCUT": 600}
                save_config()
                run_workflow(root)
                self.assertEqual(calls[-2:], ["static", "dos"])
                self.assertEqual(calls.count("relax"), 1)
                # Complete output survived a kill before completed checkpoint.
                path = root / "workflow_state.json"
                state = json.loads(path.read_text())
                state["stages"]["dos"]["status"] = "running"
                path.write_text(json.dumps(state))
                run_workflow(root)
                self.assertEqual(len(calls), 6)
                # Import old numeric folder into a new task.
                old = root / "12345"
                old.mkdir()
                (old / "complete").write_text("ok")
                (old / "vasprun.xml").write_text("stub")
                other = root / "imported_task"
                other.mkdir()
                structure.to(filename=other / "initial.cif")
                config["resume_from"] = {"relax": str(old)}
                (other / "workflow.json").write_text(json.dumps(config))
                state = run_workflow(other)
                self.assertTrue(state["stages"]["relax"]["imported"])
                self.assertEqual(calls.count("relax"), 1)
                run_workflow(other, fresh=True)
                self.assertEqual(calls.count("relax"), 2)


if __name__ == "__main__":
    unittest.main()

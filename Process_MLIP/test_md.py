"""Short ASE/EMT dynamics tests; no ML model or accelerator required."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from ase import units
from ase.build import bulk
from ase.calculators.calculator import Calculator, all_changes
from ase.calculators.emt import EMT
from ase.constraints import FixAtoms
from ase.io import read

from Process_MLIP import run_md


class NoStress(Calculator):
    implemented_properties = ["energy", "forces"]

    def calculate(self, atoms=None, properties=None, system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        self.results = {"energy": 0.0, "forces": np.zeros((len(atoms), 3))}


class MDTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="tmp_md_", dir=Path(__file__).parent)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)

    def run_stage(self, name="md", **kwargs):
        options = dict(steps=3, timestep_fs=0.5, temperature_K=300, seed=42,
                       trajectory_interval=2, log_interval=2)
        options.update(kwargs)
        return run_md(self.atoms, EMT(), self.root / name, **options)

    def test_nvt_outputs_seed_and_input_copy(self):
        result = self.run_stage()
        final = result["final_atoms"]
        self.assertFalse(self.atoms.has("momenta"))
        self.assertIsNone(self.atoms.calc)
        np.testing.assert_array_equal(final.cell, self.atoms.cell)
        self.assertGreater(final.get_kinetic_energy(), 0)
        frames = read(result["trajectory_file"], index=":")
        self.assertEqual(len(frames), 3)  # steps 0, 2, 3
        np.testing.assert_array_equal(read(result["final_structure"]).get_momenta(),
                                      final.get_momenta())
        with open(result["log_file"], newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual([int(r["step"]) for r in rows], [0, 2, 3])
        expected_pressure = -np.trace(final.get_stress(voigt=False,
                                    include_ideal_gas=True)) / 3 / units.bar
        self.assertAlmostEqual(float(rows[-1]["pressure_bar"]), expected_pressure)
        report = json.loads(Path(result["report_file"]).read_text())
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["steps_completed"], 3)
        self.assertIn("ase", report["versions"])
        repeat = self.run_stage("repeat")
        np.testing.assert_allclose(final.positions, repeat["final_atoms"].positions)
        np.testing.assert_allclose(final.get_momenta(), repeat["final_atoms"].get_momenta())

    def test_independent_npt_and_chained_velocity_preservation(self):
        independent = self.run_stage("npt", ensemble="npt")
        self.assertNotEqual(independent["final_atoms"].get_volume(), self.atoms.get_volume())
        nvt = self.run_stage("nvt")
        first = nvt["final_atoms"]
        second = run_md(first, first.calc, self.root / "continuation", ensemble="npt",
                        temperature_K=400, steps=2, initialize_velocities=False,
                        time_offset_fs=nvt["end_time_fs"])
        initial = read(second["trajectory_file"], index=0)
        np.testing.assert_allclose(initial.positions, first.positions)
        np.testing.assert_allclose(initial.cell, first.cell)
        np.testing.assert_allclose(initial.get_momenta(), first.get_momenta())
        self.assertEqual(second["velocity_initialization"], "preserved")
        self.assertEqual(second["end_time_fs"], nvt["end_time_fs"] + 2)

    def test_zero_steps_and_file_input_preserve_velocities(self):
        first = self.run_stage("first", steps=0)
        second = run_md(first["final_structure"], EMT(), self.root / "from_file",
                        steps=0, seed=999)
        np.testing.assert_allclose(first["final_atoms"].get_momenta(),
                                   second["final_atoms"].get_momenta())
        self.assertEqual(len(read(second["trajectory_file"], index=":")), 1)

    def test_invalid_options_do_not_write(self):
        for kw in ({"ensemble": "typo"}, {"steps": -1}, {"steps": True},
                   {"temperature_K": 0}, {"timestep_fs": float("nan")},
                   {"tdamp_fs": 0}, {"pdamp_fs": 0}, {"trajectory_interval": 0},
                   {"log_interval": True}, {"seed": -1}, {"time_offset_fs": -1},
                   {"initialize_velocities": "yes"}, {"overwrite": "yes"}):
            with self.subTest(kw=kw), self.assertRaises((ValueError, TypeError)):
                self.run_stage(**kw)
        self.assertFalse((self.root / "md").exists())
        with self.assertRaises(ValueError):
            self.run_stage(initialize_velocities=False)

    def test_constraints_and_nonperiodic_npt_rejected(self):
        self.atoms.set_constraint(FixAtoms(indices=[0]))
        with self.assertRaises(NotImplementedError):
            self.run_stage()
        self.atoms.set_constraint()
        self.atoms.pbc = False
        with self.assertRaises(ValueError):
            self.run_stage(ensemble="npt")

    def test_missing_stress_nvt_allowed_npt_rejected(self):
        result = run_md(self.atoms, NoStress(), self.root / "nvt", steps=1)
        self.assertIsNone(result["final_state"]["pressure_bar"])
        with self.assertRaisesRegex(ValueError, "stress"):
            run_md(self.atoms, NoStress(), self.root / "npt", ensemble="npt", steps=1)
        self.assertFalse((self.root / "npt").exists())

    def test_output_collision_requires_explicit_overwrite(self):
        result = self.run_stage()
        original = Path(result["trajectory_file"]).read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_stage()
        self.assertEqual(Path(result["trajectory_file"]).read_bytes(), original)
        sentinel = self.root / "md" / "unrelated.txt"
        sentinel.write_text("keep")
        self.run_stage(overwrite=True, steps=1)
        self.assertEqual(sentinel.read_text(), "keep")

    def test_failed_dynamics_reported_and_nonfinite_preflight_rejected(self):
        class Broken(EMT):
            calls = 0

            def calculate(self, *args, **kwargs):
                self.calls += 1
                if self.calls > 1:
                    raise RuntimeError("model failure")
                return super().calculate(*args, **kwargs)

        with self.assertRaisesRegex(RuntimeError, "model failure"):
            run_md(self.atoms, Broken(), self.root / "broken", steps=2)
        report = json.loads((self.root / "broken" / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertFalse((self.root / "broken" / "final.traj").exists())
        self.atoms.positions[0, 0] = np.nan
        with self.assertRaises(ValueError):
            self.run_stage()

    def test_nonfinite_model_output_stops_dynamics(self):
        class Nonfinite(EMT):
            calls = 0

            def calculate(self, *args, **kwargs):
                self.calls += 1
                super().calculate(*args, **kwargs)
                if self.calls > 1:
                    self.results["energy"] = float("nan")

        with self.assertRaisesRegex(RuntimeError, "non-finite"):
            run_md(self.atoms, Nonfinite(), self.root / "nan", steps=5)
        report = json.loads((self.root / "nan" / "report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertLess(report["steps_completed"], 5)


if __name__ == "__main__":
    unittest.main()

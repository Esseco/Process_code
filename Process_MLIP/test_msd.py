"""Analytic MSD trajectories validate the ASE wrapper, without model loading."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from ase import Atoms
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io.trajectory import Trajectory
from ase.md.analysis import DiffusionCoefficient

from Process_MLIP import export_msd, run_md


class MSDTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tmp_msd_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def trajectory(self, positions, name="md.traj", symbols="NaO", cell=10):
        path = self.root / name
        with Trajectory(path, "w") as output:
            for points in positions:
                output.write(Atoms(symbols, positions=points, cell=[cell]*3, pbc=True))
        return path

    def rows(self, path):
        with open(path, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_true_msd_normalization_and_species_selection_use_ase(self):
        path = self.trajectory([[[0, 0, 0], [5, 5, 5]],
                                [[1, 2, 3], [5, 5, 5]],
                                [[2, 4, 6], [5, 5, 5]]])
        with patch("Process_MLIP.msd.DiffusionCoefficient", wraps=DiffusionCoefficient) as analysis:
            result = export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=10)
        analysis.assert_called_once()
        rows = self.rows(result["csv_file"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(float(rows[1]["msd_total_A2"]), 14)
        self.assertEqual(float(rows[2]["msd_x_A2"]), 4)
        self.assertEqual(float(rows[2]["msd_y_A2"]), 16)
        self.assertEqual(float(rows[2]["msd_z_A2"]), 36)
        self.assertEqual(float(rows[2]["time_ps"]), 0.02)
        self.assertEqual(rows[2]["atom_count"], "1")

    def test_unwrapped_large_displacements_are_preserved_by_default(self):
        path = self.trajectory([[[0, 0, 0], [5, 5, 5]], [[7, 0, 0], [5, 5, 5]]])
        export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=1)
        self.assertEqual(float(self.rows(self.root / "msd.csv")[-1]["msd_total_A2"]), 49)

    def test_species_population_average(self):
        path = self.trajectory([[[0, 0, 0], [0, 0, 1], [5, 5, 5]],
                                [[1, 0, 0], [3, 0, 1], [5, 5, 5]]], symbols="Na2O")
        export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=1)
        row = self.rows(self.root / "msd.csv")[-1]
        self.assertEqual(row["atom_count"], "2")
        self.assertEqual(float(row["msd_total_A2"]), 5)

    def test_real_nvt_trajectory_all_frames_and_automatic_times(self):
        result = run_md(bulk("Cu", "fcc", a=3.6, cubic=True), EMT(), self.root / "nvt",
                        steps=3, timestep_fs=0.5, trajectory_interval=2)
        exported = export_msd(result["trajectory_file"], self.root / "msd.csv", species="Cu")
        rows = self.rows(exported["csv_file"])
        self.assertEqual(len(rows), 3)
        self.assertEqual([float(row["time_fs"]) for row in rows], [0, 1, 1.5])
        self.assertEqual([int(row["frame_index"]) for row in rows], [0, 1, 2])
        self.assertEqual(float(rows[0]["msd_total_A2"]), 0)
        self.assertGreater(float(rows[-1]["msd_total_A2"]), 0)

    def test_wrapped_nonorthogonal_cell(self):
        path = self.root / "triclinic.traj"
        cell = np.array([[5, 0, 0], [2, 4, 0], [0, 0, 6]])
        with Trajectory(path, "w") as output:
            for position in ([0.9, 0.9, 0.1], [0.1, 0.1, 0.1]):
                output.write(Atoms("NaO", scaled_positions=[position, [0.4, 0.4, 0.4]],
                                    cell=cell, pbc=True))
        export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=1, unwrap=True)
        self.assertAlmostEqual(float(self.rows(self.root / "msd.csv")[-1]["msd_total_A2"]), 2.6)

    def test_wrapped_trajectory_uses_ase_minimum_image(self):
        path = self.trajectory([[[9.5, 0, 0], [5, 5, 5]],
                                [[0.5, 0, 0], [5, 5, 5]], [[1.5, 0, 0], [5, 5, 5]]])
        export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=1, unwrap=True)
        np.testing.assert_allclose([float(row["msd_x_A2"]) for row in self.rows(self.root / "msd.csv")],
                                   [0, 1, 4])

    def test_framework_drift_correction(self):
        path = self.trajectory([[[0, 0, 0], [5, 5, 5]], [[1, 0, 0], [6, 5, 5]]])
        export_msd(path, self.root / "msd.csv", species="Na", frame_interval_fs=1,
                    drift_reference="framework")
        self.assertEqual(float(self.rows(self.root / "msd.csv")[-1]["msd_total_A2"]), 0)

    def test_report_time_axis_includes_irregular_last_frame(self):
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(4)])
        report = dict(status="completed", steps_completed=5, trajectory_file=str(path),
                       parameters=dict(timestep_fs=0.5, trajectory_interval=2))
        (self.root / "report.json").write_text(json.dumps(report))
        result = export_msd(path, self.root / "msd.csv", species="Na")
        self.assertEqual(result["time_source"], "report.json")
        np.testing.assert_allclose([float(r["time_fs"]) for r in self.rows(result["csv_file"])],
                                   [0, 1, 2, 2.5])

    def test_skip_segments_and_multiple_species(self):
        path = self.trajectory([[[i, 0, 0], [0, 2*i, 0]] for i in range(5)])
        export_msd(path, self.root / "msd.csv", skip_frames=1, number_of_segments=2,
                    frame_interval_fs=1)
        rows = self.rows(self.root / "msd.csv")
        self.assertEqual(len(rows), 8)
        sodium = [row for row in rows if row["species"] == "Na"]
        self.assertEqual([float(r["msd_total_A2"]) for r in sodium], [0, 1, 0, 1])

    def test_missing_time_invalid_options_and_output_protection(self):
        path = self.trajectory([[[0, 0, 0], [5, 5, 5]], [[1, 0, 0], [5, 5, 5]]])
        with self.assertRaisesRegex(ValueError, "frame_interval_fs"):
            export_msd(path, self.root / "msd.csv", species="Na")
        for kwargs in (dict(species="Li"), dict(frame_interval_fs=0), dict(skip_frames=True),
                        dict(number_of_segments=2), dict(unwrap="yes")):
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, TypeError)):
                options = dict(frame_interval_fs=1)
                options.update(kwargs)
                export_msd(path, self.root / "msd.csv", **options)
        self.assertFalse((self.root / "msd.csv").exists())
        export_msd(path, self.root / "msd.csv", frame_interval_fs=1)
        with self.assertRaises(FileExistsError):
            export_msd(path, self.root / "msd.csv", frame_interval_fs=1)
        with self.assertRaises(ValueError):
            export_msd(path, path, frame_interval_fs=1, overwrite=True)

    def test_changing_cell_and_atom_order_rejected(self):
        path = self.root / "bad.traj"
        atoms = Atoms("NaO", positions=[[0, 0, 0], [5, 5, 5]], cell=[10]*3, pbc=True)
        with Trajectory(path, "w") as output:
            output.write(atoms)
            atoms.set_cell([11, 10, 10])
            output.write(atoms)
        with self.assertRaisesRegex(ValueError, "fixed cell"):
            export_msd(path, self.root / "msd.csv", frame_interval_fs=1)
        with Trajectory(path, "w") as output:
            output.write(atoms)
            output.write(atoms[[1, 0]])
        with self.assertRaisesRegex(ValueError, "order"):
            export_msd(path, self.root / "msd.csv", frame_interval_fs=1)


if __name__ == "__main__":
    unittest.main()

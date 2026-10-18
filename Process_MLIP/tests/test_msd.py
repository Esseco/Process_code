"""pymatgen 多起点数值、周期展开、时间轴与输出保护。"""
from unittest.mock import patch
import csv
import unittest

from ase import Atoms
from ase.build import bulk
from ase.io.trajectory import Trajectory
import numpy as np
from pymatgen.analysis.diffusion.analyzer import DiffusionAnalyzer

from Process_MLIP import export_msd, run_md, fit_msd
from Process_MLIP.tests._support import TemporaryDirectoryMixin, ZeroCalculator


class MSDTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()

    def trajectory(self, positions, symbols="NaO", cell=None):
        path = self.root / "md.traj"
        with Trajectory(path, "w") as output:
            for points in positions:
                output.write(Atoms(symbols, positions=points,
                                   cell=np.eye(3) * 10 if cell is None else cell, pbc=True))
        return path

    def rows(self, path):
        with open(path, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def export(self, path, **kwargs):
        options = dict(species="Na", frame_interval_fs=1000)
        options.update(kwargs)
        result = export_msd(path, self.root / "msd.csv", **options)
        return result, self.rows(result["csv_file"])

    def test_all_origins_match_explicit_pairs_and_use_real_pymatgen(self):
        positions = np.cumsum(np.random.default_rng(42).normal(size=(151, 3, 3)), axis=0)
        path = self.trajectory(positions, symbols="Na2O")
        with patch("Process_MLIP.msd._load_diffusion_analyzer", return_value=DiffusionAnalyzer):
            result, rows = self.export(path)
        self.assertEqual(result["smoothed"], "max")
        self.assertIn("pymatgen", result["method"])
        self.assertEqual(list(rows[0]), ["segment", "frame_index", "time_fs", "time_ps",
                                       "species", "atom_count", "msd_x_A2", "msd_y_A2",
                                       "msd_z_A2", "msd_total_A2"])
        for row in rows:
            lag = int(row["frame_index"])
            expected = np.mean((positions[lag:, :2] - positions[:-lag, :2]) ** 2, axis=(0, 1))
            np.testing.assert_allclose([float(row[f"msd_{a}_A2"]) for a in "xyz"], expected)
            self.assertAlmostEqual(float(row["msd_total_A2"]), expected.sum())
            self.assertEqual(row["atom_count"], "2")
            self.assertEqual(float(row["time_ps"]), lag)
        single = np.mean(np.sum((positions[1, :2] - positions[0, :2]) ** 2, axis=1))
        self.assertNotAlmostEqual(float(rows[0]["msd_total_A2"]), single)
        fit = fit_msd(result["csv_file"], fit_start_ps=1, fit_end_ps=3,
                      temperature_K=600, volume_A3=1000, ion_charge=1)
        self.assertEqual(fit["results"][0]["species"], "Na")

    def test_population_and_large_displacements_without_implicit_drift(self):
        path = self.trajectory([[[i, 0, 0], [3*i, 0, 1], [7*i, 0, 0]]
                                for i in range(151)], symbols="Na2O")
        _, rows = self.export(path)
        self.assertAlmostEqual(float(rows[0]["msd_total_A2"]), 5)
        self.assertAlmostEqual(float(rows[1]["msd_total_A2"]), 20)
        self.assertEqual(rows[0]["atom_count"], "2")

    def test_pure_element_without_framework(self):
        path = self.trajectory([[[7*i, 0, 0]] for i in range(151)], symbols="Na")
        _, rows = self.export(path, species=None)
        self.assertAlmostEqual(float(rows[0]["msd_total_A2"]), 49)

    def test_wrapped_triclinic_trajectory(self):
        cell = np.array([[5, 0, 0], [2, 4, 0], [0, 0, 6]])
        fractional = np.array([[0.9 + 0.2*i, 0.9 + 0.2*i, 0.1] for i in range(151)]) % 1
        path = self.trajectory([[p @ cell, [1, 1, 1]] for p in fractional], cell=cell)
        _, rows = self.export(path, unwrap=True)
        self.assertAlmostEqual(float(rows[0]["msd_total_A2"]), 2.6)

    def test_mass_weighted_drift_and_multiple_species(self):
        path = self.trajectory([[[2*i, 0, 0], [3*i, 0, 0], [i, 0, 0], [4*i, 0, 0]]
                                for i in range(151)], symbols="NaLiOH")
        _, rows = self.export(path, species=["Na", "Li"], drift_reference="framework")
        drift = np.average([1, 4], weights=Atoms("OH").get_masses())
        for element, speed in (("Na", 2), ("Li", 3)):
            row = next(row for row in rows if row["species"] == element)
            self.assertAlmostEqual(float(row["msd_total_A2"]), (speed - drift)**2)

    def test_segments_use_all_origins_within_each_segment(self):
        positions = np.cumsum(np.random.default_rng(7).normal(size=(303, 2, 3)), axis=0)
        path = self.trajectory(positions)
        _, rows = self.export(path, skip_frames=1, number_of_segments=2)
        self.assertEqual({r["segment"] for r in rows}, {"1", "2"})
        for row in rows:
            start = 1 + (int(row["segment"]) - 1) * 151
            lag = int(row["frame_index"]) - start
            segment = positions[start:start+151, 0]
            expected = np.mean(np.sum((segment[lag:] - segment[:-lag])**2, axis=1))
            self.assertAlmostEqual(float(row["msd_total_A2"]), expected)

    def test_real_md_report_short_tail_and_fit_csv(self):
        result = run_md(bulk("Cu", "fcc", a=3.6, cubic=True).repeat((2, 2, 2)),
                        ZeroCalculator(), self.root / "nvt", steps=305,
                        timestep_fs=10, trajectory_interval=10)
        with self.assertWarnsRegex(UserWarning, "final short-interval"):
            exported = export_msd(result["trajectory_file"], self.root / "msd.csv", species="Cu")
        self.assertEqual(exported["time_source"], "report.json")
        self.assertEqual(exported["dropped_frame_indices"], [31])
        self.assertEqual(exported["frame_count"], 31)
        rows = self.rows(exported["csv_file"])
        self.assertAlmostEqual(float(rows[0]["time_ps"]), 1)
        fitted = fit_msd(exported["csv_file"], fit_start_ps=1, fit_end_ps=2,
                         temperature_K=300, volume_A3=3.6**3*8, ion_charge=1)
        self.assertGreaterEqual(fitted["results"][0]["diffusion_m2_s"], 0)

    def test_short_data_and_invalid_options(self):
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(4)])
        with self.assertRaisesRegex(ValueError, "Not enough data"):
            self.export(path)
        _, rows = self.export(path, min_obs=1)
        self.assertEqual(len(rows), 3)
        (self.root / "msd.csv").unlink()
        for kwargs in (dict(species="Li"), dict(frame_interval_fs=0), dict(skip_frames=True),
                       dict(number_of_segments=3), dict(unwrap="yes"), dict(min_obs=0),
                       dict(min_obs=True), dict(frame_interval_fs=1001),
                       dict(species=None, drift_reference="framework")):
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, TypeError)):
                self.export(path, **kwargs)
        self.assertFalse((self.root / "msd.csv").exists())

    def test_missing_dependency_and_output_protection(self):
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)])
        with patch.dict("sys.modules", {"pymatgen.analysis.diffusion.analyzer": None}):
            with self.assertRaisesRegex(ImportError, "pymatgen-analysis-diffusion"):
                self.export(path)
        self.assertFalse((self.root / "msd.csv").exists())
        self.export(path)
        with self.assertRaises(FileExistsError):
            self.export(path)
        self.export(path, overwrite=True)
        with self.assertRaises(ValueError):
            export_msd(path, path, frame_interval_fs=1000, overwrite=True)

    def test_missing_report_changing_cell_and_order(self):
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)])
        with self.assertRaisesRegex(ValueError, "frame_interval_fs"):
            export_msd(path, self.root / "msd.csv")
        atoms = Atoms("NaO", positions=[[0, 0, 0], [5, 5, 5]], cell=[10]*3, pbc=True)
        for change, message in ((lambda a: a.set_cell([11, 10, 10]), "fixed cell"),
                                (lambda a: a.set_atomic_numbers([8, 11]), "order")):
            with Trajectory(path, "w") as output:
                for i in range(151):
                    current = atoms.copy()
                    if i == 150:
                        change(current)
                    output.write(current)
            with self.assertRaisesRegex(ValueError, message):
                self.export(path)

    def test_internal_irregular_times_are_rejected_and_min_obs_limits_lags(self):
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(181)])
        times = np.arange(181, dtype=float) * 1000
        times[50] += 20
        with patch("Process_MLIP.msd._trajectory_times", return_value=(times, "report.json")):
            with self.assertRaisesRegex(ValueError, "equally spaced"):
                self.export(path)
        _, rows = self.export(path, min_obs=30)
        _, fewer = self.export(path, min_obs=40, overwrite=True)
        self.assertGreater(len(rows), len(fewer))

    def test_standalone_example_with_real_backend(self):
        from Process_MLIP.examples import msd as example
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)])
        output = self.root / "standalone.csv"
        transport = self.root / "transport.json"
        with patch.multiple(example, INPUT=path, OUTPUT=output, SPECIES="Na",
                            FRAME_INTERVAL_FS=1000,
                            TRANSPORT_FIT=dict(enabled=True, fit_start_ps=1, fit_end_ps=3,
                                               temperature_K=600,
                                               volume_A3=1000, ion_charge=1, output_json=transport)):
            example.main()
        self.assertAlmostEqual(float(self.rows(output)[0]["msd_total_A2"]), 1)
        import json
        result = json.loads(transport.read_text())
        self.assertEqual(result["fit_method"], "pymatgen")
        self.assertEqual(result["results"][0]["ion_charge"], 1)

    def test_simple_postprocess_example_and_repeat_without_changing_trajectory(self):
        import contextlib
        import io
        from Process_MLIP.examples import postprocess_md as example
        path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)])
        original = path.read_bytes()
        output = self.root / "analysis"
        with patch.multiple(example, TRAJECTORY=path, OUTPUT_DIR=output, SPECIES="Na",
                            FIT_START_PS=None, FIT_END_PS=None, ION_CHARGE=2,
                            TEMPERATURE_K=600, FRAME_INTERVAL_FS=1000), \
                contextlib.redirect_stdout(io.StringIO()):
            first = example.main()
            second = example.main()
        self.assertEqual(first, second)
        self.assertAlmostEqual(second["volume_A3"], 1000)
        self.assertEqual(second["temperature_K"], 600)
        self.assertEqual(second["results"][0]["ion_charge"], 2)
        self.assertEqual(second["results"][0]["actual_fit_range_ps"], [1, 4])
        self.assertEqual(second["fit_range_ps"], [None, None])
        self.assertEqual(second["fit_method"], "pymatgen")
        self.assertTrue((output / "msd.csv").is_file())
        self.assertTrue((output / "transport.json").is_file())
        self.assertEqual(path.read_bytes(), original)

    def test_batch_example_auto_report_metadata_flat_rows_and_failures(self):
        import contextlib
        import io
        import json
        from Process_MLIP.examples import batch_postprocess_md as example
        source = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)])
        original = source.read_bytes()
        for system in ("LCO", "NVP"):
            stage = self.root / "01_model" / "results" / system / "01_nvt"
            stage.mkdir(parents=True)
            if system == "LCO":
                path = self.trajectory([[[i, 0, 0], [5, 5, 5]] for i in range(151)], symbols="LiO")
                (stage / "md.traj").write_bytes(path.read_bytes())
            else:
                (stage / "md.traj").write_bytes(original)
            report = dict(status="completed", steps_completed=150, steps_per_second=3.5,
                          trajectory_file=str(stage / "md.traj"),
                          final_state=dict(volume_angstrom3=1000),
                          parameters=dict(ensemble="nvt", temperature_K=700,
                                          timestep_fs=1000, trajectory_interval=1))
            (stage / "report.json").write_text(json.dumps(report))
        bad = self.root / "02_bad" / "results" / "LCO" / "01_nvt"
        bad.mkdir(parents=True)
        (bad / "md.traj").write_bytes(original)
        summary = self.root / "out.csv"
        with patch.multiple(example, INIT_DIR=self.root, OUTPUT_DIR=self.root/"00-final_results",
                            SUMMARY_CSV=summary, FIT_START_PS=None, FIT_END_PS=None), \
                contextlib.redirect_stdout(io.StringIO()):
            df = example.main()
            with patch.object(example, "FIT_START_PS", 2):
                partial = example.main()
        self.assertEqual(len(df), 3)
        complete = df[df["status"] == "completed"]
        self.assertEqual(set(complete["species"]), {"Li", "Na"})
        self.assertEqual(set(complete["temperature_K"]), {700})
        self.assertEqual(set(complete["time_fs"]), {150000})
        self.assertEqual(set(complete["steps_per_second"]), {3.5})
        self.assertEqual(set(complete["fit_start_ps"]), {1})
        self.assertEqual(set(complete["fit_end_ps"]), {4})
        partial = partial[partial["status"] == "completed"]
        self.assertEqual(set(partial["fit_start_ps"]), {2})
        self.assertEqual(set(partial["fit_end_ps"]), {4})
        self.assertEqual(len(df[df["status"] == "failed"]), 1)
        self.assertTrue(summary.is_file())
        self.assertNotIn("results", df.columns)
        self.assertTrue(all(not isinstance(value, (dict, list)) for value in df.to_numpy().flat))


if __name__ == "__main__":
    unittest.main()

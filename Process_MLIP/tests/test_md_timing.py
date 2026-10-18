"""默认步长、累计模拟时间和 steps/s 计时。"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import contextlib
import csv
import io
import json
import sys
import unittest

from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import write

from Process_MLIP import run_md, run_mlip_md
from Process_MLIP.md import _validate_options
from Process_MLIP.msd import _trajectory_times
from Process_MLIP.tests._support import TemporaryDirectoryMixin, ZeroCalculator


class MDSpeedTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)

    def test_optional_and_validated(self):
        result = run_md(self.atoms, EMT(), self.root / "off", steps=1)
        self.assertIsNone(result["steps_per_second"])
        with self.assertRaises(TypeError):
            run_md(self.atoms, EMT(), self.root / "bad", steps=1,
                   measure_steps_per_second="yes")
        self.assertFalse((self.root / "bad").exists())

    def test_stage_rate_uses_integration_duration_and_is_saved(self):
        with patch("Process_MLIP.md.perf_counter", side_effect=[100.0, 102.0]) as clock:
            result = run_md(self.atoms, EMT(), self.root / "on", steps=4,
                            measure_steps_per_second=True)
        self.assertEqual(clock.call_count, 2)
        self.assertEqual(result["steps_per_second"], 2.0)
        report = json.loads(Path(result["report_file"]).read_text())
        self.assertEqual(report["steps_per_second"], 2.0)

    def test_zero_steps_has_no_rate(self):
        result = run_md(self.atoms, EMT(), self.root / "zero", steps=0,
                        measure_steps_per_second=True)
        self.assertIsNone(result["steps_per_second"])

    def test_gpu_synchronization_brackets_timer(self):
        events = []
        torch = SimpleNamespace(cuda=SimpleNamespace(
            synchronize=Mock(side_effect=lambda device: events.append(("sync", device)))))
        def clock():
            events.append(("clock", None))
            return float(len(events))
        calculator = EMT()
        calculator.device = "cuda:1"  # EMT remains CPU; only synchronization is mocked
        with patch.dict(sys.modules, {"torch": torch}), \
                patch("Process_MLIP.md.perf_counter", side_effect=clock):
            result = run_md(self.atoms, calculator, self.root / "sync", steps=2,
                            measure_steps_per_second=True)
        self.assertEqual(events, [("sync", "cuda:1"), ("clock", None),
                                  ("sync", "cuda:1"), ("clock", None)])
        self.assertEqual(result["steps_per_second"], 1.0)

    def test_workflow_combines_rates_by_total_time(self):
        calculator = EMT()
        calculator.device = "cpu"
        with patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=calculator), \
                patch("Process_MLIP.md.perf_counter", side_effect=[10., 12., 20., 24.]):
            result = run_mlip_md(self.atoms, output_dir=self.root / "workflow",
                                 stages=[dict(steps=2), dict(steps=2)],
                                 measure_steps_per_second=True)
        self.assertEqual([r["steps_per_second"] for r in result["stage_results"]], [1., 0.5])
        self.assertAlmostEqual(result["steps_per_second"], 4 / 6)
        report = json.loads(Path(result["report_file"]).read_text())
        self.assertAlmostEqual(report["steps_per_second"], 4 / 6)


class TimestepTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)

    def test_defaults_and_explicit_values(self):
        for ensemble, dt in (("nvt",2.0),("NPT",1.0)):
            self.assertEqual(_validate_options(dict(ensemble=ensemble))["timestep_fs"],dt)
            self.assertEqual(_validate_options(dict(ensemble=ensemble,timestep_fs=None))["timestep_fs"],dt)
            self.assertEqual(_validate_options(dict(ensemble=ensemble,timestep_fs=0.5))["timestep_fs"],0.5)
        for value in (False,0,-1,float("nan")):
            with self.assertRaises(ValueError):
                _validate_options(dict(timestep_fs=value))

    def test_run_md_and_msd_time_grid(self):
        for ensemble, dt in (("nvt",2.0),("npt",1.0)):
            result = run_md(self.atoms, EMT(), self.root/ensemble, ensemble=ensemble,
                            steps=3, trajectory_interval=2, log_interval=1)
            self.assertEqual(result["parameters"]["timestep_fs"],dt)
            self.assertEqual(result["end_time_fs"],3*dt)
            if ensemble=="nvt":
                times, source = _trajectory_times(Path(result["trajectory_file"]), 3, None)
                self.assertEqual(times.tolist(), [0,4,6])
                self.assertEqual(source, "report.json")

    def test_stage_defaults_and_common_stage_overrides(self):
        with patch("Process_MLIP.md_workflow.create_mlip_calculator",side_effect=lambda c:EMT()):
            for common_dt, expected in ((None,[2,1,0.25]),(0.5,[0.5,0.5,0.25])):
                result=run_mlip_md(self.atoms,output_dir=self.root/str(common_dt),
                    timestep_fs=common_dt, stages=[dict(ensemble="nvt",steps=2),
                    dict(ensemble="npt",steps=2),dict(ensemble="nvt",steps=2,timestep_fs=0.25)])
                stages=result["stage_results"]
                self.assertEqual([r["parameters"]["timestep_fs"] for r in stages],expected)
                self.assertEqual(result["elapsed_time_fs"],2*sum(expected))
                self.assertEqual(stages[1]["parameters"]["time_offset_fs"],2*expected[0])
            reset=run_mlip_md(self.atoms,output_dir=self.root/"reset",timestep_fs=0.5,
                             stages=[dict(ensemble="npt",steps=1,timestep_fs=None)])
            self.assertEqual(reset["stage_results"][0]["parameters"]["timestep_fs"],1)

    def test_example_transport_preflight_with_auto_timestep(self):
        from Process_MLIP.examples import mlip_md as example
        source=self.root/"initial.traj"
        write(source,self.atoms.repeat((2,2,2)))
        with patch.multiple(example, INPUT=source, OUTPUT=self.root/"example",
                 PRE_RELAX=False, STAGES=[dict(ensemble="nvt",steps=1500)],
                 MD_PARAMETERS=dict(timestep_fs=None,trajectory_interval=50),
                 MSD_POSTPROCESS=dict(enabled=True,species="Cu"),
                 TRANSPORT_FIT=dict(enabled=True,fit_start_ps=1,fit_end_ps=2,ion_charge=1)), \
                patch("Process_MLIP.md_workflow.create_mlip_calculator",return_value=ZeroCalculator()), \
                contextlib.redirect_stdout(io.StringIO()):
            example.main([])
        self.assertTrue((self.root/"example"/"01_nvt"/"transport.json").is_file())


if __name__ == "__main__":
    unittest.main()

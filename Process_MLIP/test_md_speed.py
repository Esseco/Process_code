"""Timing boundaries and optional steps/s reporting without model dependencies."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ase.build import bulk
from ase.calculators.emt import EMT

from Process_MLIP import run_md, run_mlip_md


class MDSpeedTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tmp_speed_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
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


if __name__ == "__main__":
    unittest.main()

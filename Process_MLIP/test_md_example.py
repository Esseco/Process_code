"""The editable MD example integrates MSD without loading any MLIP model."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import write

from Process_MLIP.examples import mlip_md as example


class MDExampleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="tmp_mdexample_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.input = self.root / "initial.traj"
        write(self.input, bulk("Cu", "fcc", a=3.6, cubic=True))
        calculator = EMT()
        calculator.device = "cpu"
        loader = patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=calculator)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def run_example(self, config, stages=None, preview=False):
        with patch.multiple(example, INPUT=self.input, OUTPUT=self.root / "md",
                            STAGES=stages or [dict(name="equil", ensemble="nvt", steps=2),
                                              dict(name="final", ensemble="nvt", steps=3)],
                            MD_PARAMETERS=dict(temperature_K=300, timestep_fs=0.5,
                                               trajectory_interval=2),
                            PRE_RELAX=False, MSD_POSTPROCESS=config), \
                contextlib.redirect_stdout(io.StringIO()) as stream:
            example.main(["--preview"] if preview else [])
        return stream.getvalue()

    def test_enabled_exports_last_nvt_after_md(self):
        text = self.run_example(dict(enabled=True, stage="last_nvt", species="Cu",
                                     output_csv=None, overwrite=False))
        path = self.root / "md" / "02_final" / "msd.csv"
        self.assertTrue(path.is_file())
        self.assertEqual(len(path.read_text().splitlines()), 4)  # header + frames 0,2,3
        self.assertIn("MSD:", text)
        self.loader.assert_called_once()

    def test_disabled_does_not_call_exporter(self):
        with patch.object(example, "export_msd") as exporter:
            self.run_example(dict(enabled=False))
        exporter.assert_not_called()

    def test_last_nvt_selection_skips_later_npt(self):
        self.run_example(dict(enabled=True, stage="last_nvt", species="Cu",
                              output_csv=None, overwrite=False),
                          stages=[dict(name="thermal", ensemble="nvt", steps=2),
                                  dict(name="pressure", ensemble="npt", steps=2)])
        self.assertTrue((self.root / "md" / "01_thermal" / "msd.csv").is_file())
        self.assertFalse((self.root / "md" / "02_pressure" / "msd.csv").exists())

    def test_custom_path_and_explicit_nvt_stage(self):
        self.run_example(dict(enabled=True, stage=1, species="Cu",
                              output_csv="analysis/cu.csv", overwrite=False))
        self.assertTrue((self.root / "md" / "analysis" / "cu.csv").is_file())
        self.assertFalse((self.root / "md" / "02_final" / "msd.csv").exists())

    def test_no_nvt_or_wrong_stage_rejected_before_loading(self):
        config = dict(enabled=True, stage="last_nvt", species="Cu", output_csv=None, overwrite=False)
        with self.assertRaisesRegex(ValueError, "NVT"):
            self.run_example(config, stages=[dict(ensemble="npt", steps=2)])
        with self.assertRaisesRegex(ValueError, "NVT"):
            self.run_example(dict(config, stage=2), stages=[dict(ensemble="nvt", steps=2),
                                                           dict(ensemble="npt", steps=2)])
        self.loader.assert_not_called()

    def test_existing_csv_rejected_before_loading_and_preview_is_readonly(self):
        path = self.root / "existing.csv"
        path.write_text("keep")
        config = dict(enabled=True, stage="last_nvt", species="Cu", output_csv=str(path), overwrite=False)
        self.run_example(config, preview=True)
        with self.assertRaises(FileExistsError):
            self.run_example(config)
        self.assertEqual(path.read_text(), "keep")
        self.loader.assert_not_called()

    def test_md_log_cannot_be_overwritten_and_zero_steps_rejected(self):
        config = dict(enabled=True, stage=1, species="Cu", output_csv="01_equil/md.csv",
                       overwrite=True)
        with self.assertRaisesRegex(ValueError, "MD log"):
            self.run_example(config)
        with self.assertRaisesRegex(ValueError, "at least one"):
            self.run_example(dict(config, output_csv=None), stages=[dict(ensemble="nvt", steps=0)])
        self.loader.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Ensemble-dependent defaults, overrides and physical time accounting."""
import csv
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import write
from Process_MLIP import export_msd, run_md, run_mlip_md
from Process_MLIP.md import _validate_options


class TimestepTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix="tmp_timestep_")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
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
                path=self.root/"msd.csv"
                export_msd(result["trajectory_file"],path,species="Cu")
                with path.open() as f:
                    rows=list(csv.DictReader(f))
                self.assertEqual([float(r["time_fs"]) for r in rows],[0,4,6])

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
        write(source,self.atoms)
        with patch.multiple(example, INPUT=source, OUTPUT=self.root/"example",
                 PRE_RELAX=False, STAGES=[dict(ensemble="nvt",steps=3)],
                 MD_PARAMETERS=dict(timestep_fs=None,trajectory_interval=1),
                 MSD_POSTPROCESS=dict(enabled=True,species="Cu"),
                 TRANSPORT_FIT=dict(enabled=True,fit_start_ps=0,fit_end_ps=0.006,ion_charge=1)), \
                patch("Process_MLIP.md_workflow.create_mlip_calculator",return_value=EMT()), \
                contextlib.redirect_stdout(io.StringIO()):
            example.main([])
        self.assertTrue((self.root/"example"/"01_nvt"/"transport.json").is_file())


if __name__=="__main__":
    unittest.main()

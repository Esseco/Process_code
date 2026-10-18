"""可编辑示例与批量任务的端到端调用。"""
from pathlib import Path
from unittest.mock import patch
import contextlib
import csv
import io
import json
import runpy
import tempfile
import unittest

from ase import Atoms
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import write

from Process_MLIP.examples import mlip_md as example
from Process_MLIP.tests._support import (
    EXAMPLES_DIR,
    MDExampleHarness,
    PROJECT_ROOT,
    ZeroCalculator,
)


BENCHMARK_TASKS = EXAMPLES_DIR / "md_benchmark" / "tasks"
SYM_SCAN_TASKS = EXAMPLES_DIR / "sym_md_scan"


class MDExampleTests(MDExampleHarness, unittest.TestCase):
    def test_enabled_exports_last_nvt_after_md(self):
        text = self.run_example(dict(enabled=True, stage="last_nvt", species="Cu",
                                     output_csv=None, overwrite=False))
        path = self.root / "md" / "02_final" / "msd.csv"
        self.assertTrue(path.is_file())
        self.assertEqual(len(path.read_text().splitlines()), 22)  # header + lags 1.0..3.0 ps
        self.assertIn("MSD:", text)
        self.loader.assert_called_once()

    def test_disabled_does_not_call_exporter(self):
        with patch.object(example, "export_msd") as exporter:
            self.run_example(dict(enabled=False))
        exporter.assert_not_called()

    def test_msd_sampling_and_dependency_rejected_before_model_loading(self):
        with self.assertRaisesRegex(ValueError, "Not enough data"):
            self.run_example(dict(enabled=True, species="Cu"), stages=[dict(steps=2)])
        self.loader.assert_not_called()
        with patch.object(example, "_load_diffusion_analyzer", side_effect=ImportError("missing analysis package")):
            with self.assertRaisesRegex(ImportError, "missing analysis"):
                self.run_example(dict(enabled=True, species="Cu"))
        self.loader.assert_not_called()

    def test_skip_and_drift_parameters_forwarded(self):
        from Process_MLIP import export_msd
        # Forwarding is checked with the real backend, no model or library stubs.
        with patch.object(example, "export_msd", wraps=export_msd) as exporter:
            self.run_example(dict(enabled=True, species="Cu", skip_frames=1, min_obs=20))
        self.assertEqual(exporter.call_args.kwargs["skip_frames"], 1)
        self.assertEqual(exporter.call_args.kwargs["min_obs"], 20)
        self.assertIsNone(exporter.call_args.kwargs["drift_reference"])

    def test_last_nvt_selection_skips_later_npt(self):
        self.run_example(dict(enabled=True, stage="last_nvt", species="Cu",
                              output_csv=None, overwrite=False),
                          stages=[dict(name="thermal", ensemble="nvt", steps=300),
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


class TransportExampleTests(MDExampleHarness, unittest.TestCase):
    def test_automatic_and_partial_fit_windows(self):
        base = self.root
        for index, (start, end, expected) in enumerate([
                (None, None, [1, 3]), (None, 2, [1, 2]), (2, None, [2, 3])]):
            config = dict(enabled=True, fit_start_ps=start, fit_end_ps=end,
                          ion_charge=1, output_json=None, overwrite=False)
            with self.subTest(start=start, end=end), \
                    patch.object(self, 'root', base/str(index)), \
                    patch.object(example, 'TRANSPORT_FIT', config):
                self.run_example(dict(enabled=True, species='Cu'))
                result = json.loads((self.root/'md'/'02_final'/'transport.json').read_text())
                self.assertEqual(result['fit_range_ps'], [start, end])
                self.assertEqual(result['results'][0]['actual_fit_range_ps'], expected)

    def test_transport_integration(self):
        # Fits a short EMT trajectory only to test plumbing, not diffusion physics.
        config = dict(enabled=True, fit_start_ps=1, fit_end_ps=2,
                      ion_charge=1, output_json=None, overwrite=False)
        with patch.object(example, 'TRANSPORT_FIT', config):
            text = self.run_example(dict(enabled=True, species='Cu'))
        self.assertIn('Transport:', text)
        path = self.root / 'md' / '02_final' / 'transport.json'
        result = json.loads(path.read_text())
        self.assertEqual(result['temperature_K'], 300)
        self.assertEqual(result['fit_method'], 'pymatgen')
        self.assertAlmostEqual(result['volume_A3'], 3.6**3*8)

    def test_fitter_dependency_rejected_before_model_loading(self):
        config = dict(enabled=True, fit_start_ps=1, fit_end_ps=2,
                      ion_charge=1, output_json=None, overwrite=False)
        with patch.object(example, 'TRANSPORT_FIT', config), \
                patch.object(example, '_load_pymatgen_fitter', side_effect=ImportError('missing fitter')):
            with self.assertRaisesRegex(ImportError, 'missing fitter'):
                self.run_example(dict(enabled=True, species='Cu'))
        self.loader.assert_not_called()

    def test_requires_msd_before_model_loading(self):
        with patch.object(example, 'TRANSPORT_FIT', dict(enabled=True)):
            with self.assertRaises(ValueError):
                self.run_example(dict(enabled=False))
        self.loader.assert_not_called()

    def test_invalid_fit_window_before_model_loading(self):
        with patch.object(example, 'TRANSPORT_FIT', dict(enabled=True,
                          fit_start_ps=2, fit_end_ps=8, ion_charge=1)):
            with self.assertRaises(ValueError):
                self.run_example(dict(enabled=True, species='Cu'))
        self.loader.assert_not_called()


class BenchmarkTaskTests(unittest.TestCase):
    def test_all_eight_default_and_submission_configs(self):
        folders=sorted(p for p in BENCHMARK_TASKS.iterdir() if p.is_dir() and not p.name.startswith('tmp_'))
        self.assertEqual(len(folders),8)
        for folder in folders:
            with self.subTest(case=folder.name):
                scope=runpy.run_path(str(folder/'run_md.py'))
                self.assertEqual(scope['MD']['steps'],5000)
                self.assertEqual(scope['MD']['ensemble'],'nvt')
                self.assertEqual([p.name for p in scope['STRUCTURES']], ['LCO.vasp', 'NVP.vasp'])
                self.assertTrue(scope['MSD']['enabled'])
                self.assertEqual(scope['MSD']['species'], {'LCO':'Li','NVP':'Na'})
                self.assertEqual(scope['PRE_RELAX']['optimizer'],'FIRE')
                self.assertEqual(scope['MD']['temperature_K'],600)
                self.assertEqual(scope['MD']['trajectory_interval'],1)
                self.assertEqual(scope['MD']['log_interval'],1)
                if 'mace' in folder.name:
                    self.assertEqual(scope['MODEL_OPTIONS']['default_dtype'],'float32')
                self.assertTrue(scope['PRE_RELAX']['relax_cell'])
                env='mace_cueq' if 'mace' in folder.name else ('sevennet_flash' if 'sevennet' in folder.name else 'python')
                submit=(folder/'submit.sh').read_text()
                self.assertIn(f'conda activate {env}',submit)
                self.assertTrue(submit.startswith('#!/bin/bash\n'))
                self.assertNotIn(b'\r',(folder/'submit.sh').read_bytes())

    def test_all_eight_real_nvt_msd_pipelines_with_zero_calculator(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent,prefix='tmp_benchmarks_') as temporary:
            temp=Path(temporary)
            structure=temp/'initial.traj'
            weight=temp/'dummy.model'
            write(structure,bulk('Cu','fcc',a=3.6,cubic=True).repeat((2,2,2)))
            second = temp/'second.traj'
            write(second,bulk('Cu','fcc',a=3.7,cubic=True).repeat((2,2,2)))
            weight.write_text('test')
            for folder in sorted(BENCHMARK_TASKS.iterdir()):
                if not folder.is_dir():
                    continue
                with self.subTest(case=folder.name):
                    scope=runpy.run_path(str(folder/'run_md.py'))
                    g=scope['main'].__globals__
                    output=temp/folder.name
                    g.update(PROJECT_ROOT=PROJECT_ROOT, STRUCTURES=[structure, second],
                             MODEL_PATH=weight,OUTPUT=output)
                    g['MD'].update(steps=300,timestep_fs=10,trajectory_interval=10)
                    g['MSD']['species']={'initial':'Cu','second':'Cu'}
                    g['PRE_RELAX'].update(steps=2,require_convergence=False)
                    calc=ZeroCalculator()
                    calc.device='cpu'  # timing must use the actual test calculator device
                    with patch('Process_MLIP.md_workflow.create_mlip_calculator',return_value=calc) as loader,contextlib.redirect_stdout(io.StringIO()):
                        result=g['main']()
                    self.assertEqual(len(result),2)
                    self.assertEqual(loader.call_count,2)
                    model=loader.call_args.args[0]
                    if 'sym' in folder.name:
                        self.assertTrue(model['enable_symmetrix'])
                        self.assertEqual(model['symmetrix_species'],['Cu'])
                    if 'sevennet' in folder.name:
                        self.assertEqual(model['enable_flash'],'flash' in folder.name)
                    for input_structure, item in zip((structure,second),result):
                        destination=output/input_structure.stem
                        self.assertEqual(item['total_steps'],300)
                        self.assertEqual(len((destination/'msd.csv').read_text().splitlines()),22)
                        self.assertGreater(item['steps_per_second'],0)
                        self.assertIsNotNone(item['pre_relax_result'])
                        self.assertTrue((destination/'00_relax'/'relax.traj').is_file())


class SymScanTests(unittest.TestCase):
    def test_six_unique_configs_and_slurm(self):
        found=set()
        for folder in sorted(SYM_SCAN_TASKS.glob('sym_*')):
            scope=runpy.run_path(str(folder/'run_md.py'))
            pair=(scope['TEMPERATURE_K'],scope['DURATION_PS'])
            found.add(pair)
            self.assertEqual(scope['MD']['steps']*scope['MD']['timestep_fs']/1000,pair[1])
            self.assertEqual(scope['MD']['temperature_K'],pair[0])
            self.assertTrue(scope['MODEL_OPTIONS']['enable_symmetrix'])
            self.assertEqual(scope['MODEL_OPTIONS']['default_dtype'],'float32')
            self.assertEqual(scope['PRE_RELAX']['optimizer'],'FIRE')
            self.assertEqual(scope['MSD']['species'],{'LCO':'Li','NVP':'Na'})
            self.assertIn('conda activate mace_cueq',(folder/'submit.sh').read_text())
            self.assertNotIn(b'\r',(folder/'submit.sh').read_bytes())
        self.assertEqual(found,{(500,30),(700,30),(900,30),(700,10),(700,50),(700,70)})

    def test_each_case_runs_both_species_and_separate_msd(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent,prefix='tmp_symscan_') as temporary:
            temp=Path(temporary)
            structures=[]
            for name,symbol in (('LCO','Li'),('NVP','Na')):
                path=temp/f'{name}.traj'
                write(path,Atoms([symbol]*30+['O','O'],positions=[[i%8,i//8,0] for i in range(32)],cell=[8]*3,pbc=True))
                structures.append(path)
            for folder in sorted(SYM_SCAN_TASKS.glob('sym_*')):
                scope=runpy.run_path(str(folder/'run_md.py'))
                g=scope['main'].__globals__
                g.update(PROJECT_ROOT=PROJECT_ROOT,
                         STRUCTURES=structures,OUTPUT=temp/folder.name)
                g['MD'].update(steps=300,timestep_fs=10,trajectory_interval=10)
                with patch('Process_MLIP.md_workflow.create_mlip_calculator',side_effect=lambda c:ZeroCalculator()) as loader, \
                        contextlib.redirect_stdout(io.StringIO()):
                    result=g['main']()
                self.assertEqual(loader.call_count,2)
                self.assertEqual(len(result),2)
                for name,symbol in (('LCO','Li'),('NVP','Na')):
                    output=g['OUTPUT']/name
                    self.assertTrue((output/'00_relax'/'report.json').is_file())
                    with (output/'msd.csv').open() as f:
                        rows=list(csv.DictReader(f))
                    self.assertEqual({r['species'] for r in rows},{symbol})
                    self.assertEqual([float(r['time_fs']) for r in rows],list(range(1000,3001,100)))


if __name__ == "__main__":
    unittest.main()

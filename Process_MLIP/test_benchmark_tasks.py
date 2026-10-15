"""Standalone cluster scripts: configuration and short real ASE/EMT pipelines."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
from ase.build import bulk
from ase.io import write
from ase.calculators.emt import EMT

ROOT = Path(__file__).parent / 'examples' / 'md_benchmark' / 'tasks'


class BenchmarkTaskTests(unittest.TestCase):
    def test_all_eight_default_and_submission_configs(self):
        folders=sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith('tmp_'))
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

    def test_all_eight_real_nvt_msd_pipelines_with_emt(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent,prefix='tmp_benchmarks_') as temporary:
            temp=Path(temporary)
            structure=temp/'initial.traj'
            weight=temp/'dummy.model'
            write(structure,bulk('Cu','fcc',a=3.6,cubic=True))
            second = temp/'second.traj'
            write(second,bulk('Cu','fcc',a=3.7,cubic=True))
            weight.write_text('test')
            for folder in sorted(ROOT.iterdir()):
                if not folder.is_dir():
                    continue
                with self.subTest(case=folder.name):
                    scope=runpy.run_path(str(folder/'run_md.py'))
                    g=scope['main'].__globals__
                    output=temp/folder.name
                    g.update(PROJECT_ROOT=Path(__file__).resolve().parents[1], STRUCTURES=[structure, second],
                             MODEL_PATH=weight,OUTPUT=output)
                    g['MD'].update(steps=4)
                    g['MSD']['species']={'initial':'Cu','second':'Cu'}
                    g['PRE_RELAX'].update(steps=2,require_convergence=False)
                    calc=EMT()
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
                        self.assertEqual(item['total_steps'],4)
                        self.assertEqual(len((destination/'msd.csv').read_text().splitlines()),6)
                        self.assertGreater(item['steps_per_second'],0)
                        self.assertIsNotNone(item['pre_relax_result'])
                        self.assertTrue((destination/'00_relax'/'relax.traj').is_file())


if __name__=='__main__':
    unittest.main()

"""Symmetrix contract tests: no dependency installation or real model load."""
import json
from contextlib import nullcontext
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
from ase.build import bulk
from ase.calculators.emt import EMT
from Process_MLIP import create_mace_calculator, create_mlip_calculator, model_config, run_mlip_md


class SymmetrixTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix='tmp_symmetrix_')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.weights = self.root / 'omat.model'
        self.weights.write_text('placeholder')
        self.module = ModuleType('symmetrix')
        self.module.Symmetrix = Mock(return_value=EMT())
        self.extract = ModuleType('symmetrix.extract_mace_data')
        self.extract.extract_mace_data = Mock(return_value={'atomic_numbers':[29]})
        self.torch = ModuleType('torch')
        self.torch.get_default_dtype = Mock(return_value='original')
        self.torch.set_default_dtype = Mock()
        mods = patch.dict(sys.modules, {'symmetrix':self.module,
                          'symmetrix.extract_mace_data':self.extract, 'torch':self.torch})
        mods.start()
        self.addCleanup(mods.stop)
        ctx = patch('Process_MLIP.calculators._e3nn_import_context', side_effect=nullcontext)
        ctx.start()
        self.addCleanup(ctx.stop)
        real_tmp = tempfile.TemporaryDirectory
        tmp_patch = patch('tempfile.TemporaryDirectory', side_effect=lambda **kw: real_tmp(dir=self.root, **kw))
        tmp_patch.start()
        self.addCleanup(tmp_patch.stop)

    def test_conversion_closes_json_cleans_and_restores_dtype(self):
        observed=[]
        def build(**kw):
            observed.append(kw)
            self.assertEqual(json.loads(Path(kw['model_file']).read_text()), {'atomic_numbers':[29]})
            return EMT()
        self.module.Symmetrix.side_effect=build
        create_mace_calculator(self.weights, device='cpu', enable_symmetrix=True,
                               symmetrix_species=['Cu'])
        self.extract.extract_mace_data.assert_called_once_with(str(self.weights), species=['Cu'], head=None)
        self.assertFalse(Path(observed[0]['model_file']).exists())
        self.assertEqual(observed[0]['dtype'], 'float64')
        self.torch.set_default_dtype.assert_called_once_with('original')

    def test_json_no_conversion_and_kokkos_forwarding(self):
        path=self.root/'converted.json'
        path.write_text('{}')
        create_mace_calculator(path, device='cuda', enable_symmetrix=True,
                               symmetrix_use_kokkos=True, default_dtype='float32')
        self.module.Symmetrix.assert_called_once_with(model_file=str(path), dtype='float32', use_kokkos=True)
        self.extract.extract_mace_data.assert_not_called()
        self.torch.get_default_dtype.assert_not_called()

    def test_invalid_options(self):
        for kw in [dict(enable_cueq=True),dict(enable_symmetrix='yes'),
                   dict(symmetrix_use_kokkos=1),dict(device='cuda'),
                   dict(device='cuda:1',symmetrix_use_kokkos=True),
                   dict(default_dtype='float32'),dict(symmetrix_species=['NotElement'])]:
            config=dict(device='cpu', enable_symmetrix=True)
            config.update(kw)
            with self.subTest(kw=kw), self.assertRaises((ValueError,TypeError)):
                create_mace_calculator(self.weights,**config)
        path=self.root/'model.json'
        path.write_text('{}')
        with self.assertRaises(ValueError):
            create_mace_calculator(path,device='cpu',head='omat_pbe',enable_symmetrix=True)

    def test_conversion_failure_propagates_and_restores_dtype(self):
        self.extract.extract_mace_data.side_effect=RuntimeError('unsupported architecture')
        with self.assertRaisesRegex(RuntimeError,'unsupported architecture'):
            create_mace_calculator(self.weights,device='cpu',enable_symmetrix=True)
        self.torch.set_default_dtype.assert_called_once_with('original')
        self.module.Symmetrix.assert_not_called()

    def test_config_dispatch_and_workflow_reuses_calculator(self):
        config=model_config('mace',model_path=str(self.weights),head=None,
                            device='cpu',enable_symmetrix=True,symmetrix_species=['Cu'])
        calc=create_mlip_calculator(config)
        self.assertIs(calc,self.module.Symmetrix.return_value)
        self.module.Symmetrix.reset_mock()
        result=run_mlip_md(bulk('Cu','fcc',a=3.6,cubic=True),model=config,
                           output_dir=self.root/'md',pre_relax=dict(steps=0,require_convergence=False),
                           stages=[dict(ensemble='nvt',steps=2),dict(ensemble='npt',steps=2)])
        self.module.Symmetrix.assert_called_once()
        self.assertEqual(result['total_steps'],4)
        for stage in result['stage_results']:
            self.assertTrue(stage['model']['enable_symmetrix'])
        with self.assertRaises(ValueError):
            model_config('mace',enable_symmetrix=True,enable_cueq=True)


if __name__=='__main__':
    unittest.main()

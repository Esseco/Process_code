import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, mock
import sys


class SelectionTest(TestCase):
    def test_selected_structure_and_invalid_selection(self):
        calls = []
        fake = SimpleNamespace(ScreeningConfig=object, screening_preset=lambda **kw: kw,
                               run_screening=lambda structure, **kw: calls.append(structure.stem) or SimpleNamespace(status='done'))
        with mock.patch.dict(sys.modules, {'md_screening': fake}):
            spec = importlib.util.spec_from_file_location('soc_test', Path(__file__).with_name('run_soc_workflow.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            module.ROOT = Path(tmp)
            module.SOURCES = {'LCO': module.ROOT / 'reference.vasp'}
            module.SOURCES['LCO'].touch()
            module.MODELS['nip_l']['model_path'] = str(module.ROOT / 'model.pth')
            (module.ROOT / 'model.pth').touch()
            (module.ROOT / 'structures').mkdir()
            for name in ('LCO_SOC025', 'LCO_SOC038'):
                (module.ROOT / 'structures' / (name + '.vasp')).touch()
            env = {'MLIP_MODEL_ID': 'nip_l', 'MLIP_RESULTS_NAME': 'test', 'MLIP_STRUCTURE_IDS': 'LCO_SOC038'}
            with mock.patch.dict(os.environ, env), mock.patch.dict(sys.modules, {'process_md': SimpleNamespace(check_jump_backend=lambda: None)}):
                module.main()
            self.assertEqual(calls, ['LCO_SOC038'])
            with mock.patch.dict(os.environ, {**env, 'MLIP_RESULTS_NAME': 'invalid', 'MLIP_STRUCTURE_IDS': 'missing'}):
                with self.assertRaises(ValueError):
                    module.main()
            self.assertFalse((module.ROOT / 'results' / 'invalid').exists())
            module.SOURCES['LCO'].unlink()
            with mock.patch.dict(os.environ, {**env, 'MLIP_RESULTS_NAME': 'missing_input'}):
                with self.assertRaises(FileNotFoundError):
                    module.main()
            self.assertFalse((module.ROOT / 'results' / 'missing_input').exists())
            module.SOURCES['LCO'].touch()
            def missing_backend():
                raise ImportError('missing jump dependency')
            with mock.patch.dict(os.environ, {**env, 'MLIP_RESULTS_NAME': 'missing_backend'}), mock.patch.dict(sys.modules, {'process_md': SimpleNamespace(check_jump_backend=missing_backend)}):
                with self.assertRaises(ImportError):
                    module.main()
            self.assertFalse((module.ROOT / 'results' / 'missing_backend').exists())

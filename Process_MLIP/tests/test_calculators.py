"""模型预设、适配器、加速后端与公开接口兼容性。"""
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
import inspect
import json
import sys
import tempfile
import unittest

from ase import Atoms
from ase.build import bulk
from ase.calculators.emt import EMT

from Process_MLIP import (
    create_chgnet_calculator,
    create_mace_calculator,
    create_mlip_calculator,
    create_orb_calculator,
    create_sevennet_calculator,
    model_config,
    relax_structure_mace,
    relax_structure_sevennet,
    run_mlip_md,
)
from Process_MLIP.tests._support import TemporaryDirectoryMixin


class PresetTests(unittest.TestCase):
    def test_independent_defaults_and_overrides(self):
        config = model_config("mace-mh1", head="matpes_r2scan", enable_cueq=True)
        self.assertEqual(config["device"], "cuda")
        self.assertEqual(config["head"], "matpes_r2scan")
        config["head"] = "changed"
        self.assertEqual(model_config("mace-mh1")["head"], "omat_pbe")
        self.assertFalse(model_config("sevennet-omni")["enable_flash"])
        self.assertEqual(model_config("chgnet")["model_name"], "0.3.0")
        self.assertIn("conservative", model_config("orb-v3")["model_name"])
        for kw in ({"typo": 1}, {"enable_cueq": "True"}, {"type": "orb"}, {"model_path": None}):
            with self.assertRaises((TypeError, ValueError)):
                model_config("mace-mh1", **kw)
        with self.assertRaises(ValueError):
            model_config("unknown")

    def test_dispatch_all_four_backends(self):
        for preset, factory in (("mace-mh1", "create_mace_calculator"),
                                ("sevennet-omni", "create_sevennet_calculator"),
                                ("chgnet", "create_chgnet_calculator"),
                                ("orb-v3", "create_orb_calculator")):
            with self.subTest(preset=preset), patch("Process_MLIP.calculators." + factory) as mock:
                result = create_mlip_calculator(model_config(preset))
                self.assertIs(result, mock.return_value)
                mock.assert_called_once()
        with patch("Process_MLIP.calculators.create_sevennet_calculator") as mock:
            create_mlip_calculator(model_config("sevennet-omni", model_path="/weights/omni.pth",
                                                enable_flash=True))
            self.assertEqual(mock.call_args.args, ("/weights/omni.pth",))
            self.assertTrue(mock.call_args.kwargs["enable_flash"])


class BackendContractTests(unittest.TestCase):
    def test_mace_and_sevennet_acceleration_flags(self):
        from Process_MLIP import create_mace_calculator, create_sevennet_calculator
        mace = ModuleType("mace.calculators")
        mace.MACECalculator = Mock()
        mace.MACECalculator.__signature__ = inspect.Signature([
            inspect.Parameter("enable_cueq", inspect.Parameter.KEYWORD_ONLY, default=False)])
        seven = ModuleType("sevenn.calculator")
        seven.SevenNetCalculator = Mock()
        seven.SevenNetCalculator.__signature__ = inspect.Signature([
            inspect.Parameter("enable_flash", inspect.Parameter.KEYWORD_ONLY, default=False)])
        with patch.dict(sys.modules, {"mace.calculators": mace, "sevenn.calculator": seven}), \
                patch("Process_MLIP.calculators._e3nn_import_context", side_effect=nullcontext), \
                patch("pathlib.Path.is_file", return_value=True), \
                patch.dict("os.environ", {"SEVENNET_ENABLE_FLASH": "0",
                                          "SEVENNET_ENABLE_CUEQ": "0", "SEVENNET_ENABLE_OEQ": "0"}):
            for enabled in (True, False):
                create_mace_calculator("mh-1.model", enable_cueq=enabled)
                self.assertIs(mace.MACECalculator.call_args.kwargs["enable_cueq"], enabled)
                create_sevennet_calculator(enable_flash=enabled)
                self.assertIs(seven.SevenNetCalculator.call_args.kwargs["enable_flash"], enabled)
            mace.MACECalculator.side_effect = ImportError("CuEq unavailable")
            with self.assertRaisesRegex(ImportError, "CuEq unavailable"):
                create_mace_calculator("mh-1.model", enable_cueq=True)
            seven.SevenNetCalculator.side_effect = ImportError("FlashTP unavailable")
            with self.assertRaisesRegex(ImportError, "FlashTP unavailable"):
                create_sevennet_calculator(enable_flash=True)
            with patch.dict("os.environ", {"SEVENNET_ENABLE_FLASH": "1"}):
                with self.assertRaisesRegex(ValueError, "Unset"):
                    create_sevennet_calculator(enable_flash=False)
            mace.MACECalculator.__signature__ = inspect.Signature()
            with self.assertRaisesRegex(TypeError, "does not expose"):
                create_mace_calculator("mh-1.model", enable_cueq=True)
            seven.SevenNetCalculator.__signature__ = inspect.Signature()
            with self.assertRaisesRegex(TypeError, "does not expose"):
                create_sevennet_calculator(enable_flash=True)

    def test_chgnet_pretrained_checkpoint_and_model_instance(self):
        model_module = ModuleType("chgnet.model.model")
        dynamics = ModuleType("chgnet.model.dynamics")
        model_module.CHGNet = SimpleNamespace(load=Mock(), from_file=Mock())
        dynamics.CHGNetCalculator = Mock()
        with patch.dict(sys.modules, {"chgnet.model.model": model_module,
                                      "chgnet.model.dynamics": dynamics}):
            create_chgnet_calculator(device="cuda", model_name="0.3.0")
            model_module.CHGNet.load.assert_called_once_with(model_name="0.3.0", use_device="cuda")
            with patch("pathlib.Path.is_file", return_value=True):
                create_chgnet_calculator("local.pth", device="cpu")
            model_module.CHGNet.from_file.assert_called_once_with("local.pth")
            loaded = object()
            create_chgnet_calculator(model=loaded, device="cuda")
            dynamics.CHGNetCalculator.assert_called_with(model=loaded, use_device="cuda")
        with self.assertRaises(ValueError):
            create_chgnet_calculator("local.pth", model=object())
        with self.assertRaises(FileNotFoundError):
            create_chgnet_calculator("nonexistent.pth")

    def test_orb_new_and_legacy_api_local_weights(self):
        forcefield = ModuleType("orb_models.forcefield")
        forcefield.pretrained = SimpleNamespace(orb_v3_conservative_inf_omat=Mock())
        new = ModuleType("orb_models.forcefield.inference.calculator")
        old = ModuleType("orb_models.forcefield.calculator")
        new.ORBCalculator = Mock()
        old.ORBCalculator = Mock()
        model, adapter = object(), object()
        factory = forcefield.pretrained.orb_v3_conservative_inf_omat
        with patch.dict(sys.modules, {"orb_models.forcefield": forcefield,
                                      "orb_models.forcefield.inference.calculator": new,
                                      "orb_models.forcefield.calculator": old}):
            factory.return_value = (model, adapter)
            with patch("pathlib.Path.is_file", return_value=True):
                create_orb_calculator("local.ckpt", device="cuda", compile=False)
            self.assertEqual(factory.call_args.kwargs["weights_path"], "local.ckpt")
            new.ORBCalculator.assert_called_once_with(model, atoms_adapter=adapter, device="cuda")
            factory.return_value = model
            create_orb_calculator(device="cpu")
            old.ORBCalculator.assert_called_once_with(model, device="cpu")


class ModelAdapterTests(unittest.TestCase):
    def setUp(self):
        loader_context = patch("Process_MLIP.calculators._e3nn_import_context",
                               side_effect=nullcontext)
        loader_context.start()
        self.addCleanup(loader_context.stop)

    def test_mh1_filename_variants_and_explicit_head(self):
        module = ModuleType("mace.calculators")
        calls = []
        module.MACECalculator = lambda **kw: calls.append(kw) or EMT()
        with patch.dict(sys.modules, {"mace.calculators": module}), \
                patch("pathlib.Path.is_file", return_value=True):
            for name in ("mace-mh1.model", "mace-mh-1.model", "mace-mh_1.model"):
                create_mace_calculator(name, device="cpu")
                self.assertEqual(calls[-1]["head"], "omat_pbe")
            create_mace_calculator("renamed.model", head="matpes_r2scan")
            self.assertEqual(calls[-1]["head"], "matpes_r2scan")
            create_mace_calculator("mh-10.model")
            self.assertNotIn("head", calls[-1])

    def test_omni_modal_and_cell_relaxation(self):
        module = ModuleType("sevenn.calculator")
        calls = []
        module.SevenNetCalculator = lambda **kw: calls.append(kw) or EMT()
        atoms = bulk("Cu", "fcc", a=3.7)
        original_cell = atoms.cell.copy()
        with patch.dict(sys.modules, {"sevenn.calculator": module}):
            result = relax_structure_sevennet(atoms, steps=2, relax_cell=True,
                                              modal="omat24")
            self.assertEqual(calls[-1], dict(model="7net-omni", device="cpu",
                                             modal="omat24", file_type="checkpoint",
                                             enable_flash=False))
            self.assertEqual(result["sevennet_modal"], "omat24")
            self.assertEqual(result["energy_unit"], "eV")
            self.assertTrue(result["cell_relaxed"])
            self.assertIsNone(atoms.calc)
            self.assertTrue((atoms.cell == original_cell).all())
            create_sevennet_calculator()
            self.assertEqual(calls[-1]["modal"], "mpa")
            with patch("pathlib.Path.is_file", return_value=True):
                create_sevennet_calculator(Path("local.pth"), modal="matpes_r2scan")
                self.assertEqual(calls[-1]["model"], "local.pth")

    def test_invalid_parameters_and_missing_weights(self):
        for loader in (create_mace_calculator, create_sevennet_calculator):
            with self.assertRaises(FileNotFoundError):
                loader("missing-checkpoint-file.pth")
        with self.assertRaises(ValueError):
            create_sevennet_calculator(modal="")
        for relax in (relax_structure_mace, relax_structure_sevennet):
            args = (None, "missing.model")
            for kw in ({"steps": -1}, {"steps": True}, {"fmax": float("nan")}):
                with self.assertRaises(ValueError):
                    relax(*args, **kw)


class MaceCompatibilityTests(unittest.TestCase):
    def test_old_and_new_entry_points(self):
        from Process_AL_MC import relax_structure_mace as legacy
        from Process_AL_MC.relax import relax_structure_mace as module_legacy
        self.assertIs(legacy, relax_structure_mace)
        self.assertIs(module_legacy, relax_structure_mace)
        module = ModuleType("mace.calculators")
        captured = []

        def calculator(**kwargs):
            captured.append(kwargs)
            return EMT()

        module.MACECalculator = calculator
        atoms = Atoms("Cu2", positions=[[0, 0, 0], [2.8, 0, 0]])
        with patch.dict(sys.modules, {"mace.calculators": module}), patch("pathlib.Path.is_file", return_value=True), \
                patch("Process_MLIP.calculators._e3nn_import_context", side_effect=nullcontext):
            result = legacy(atoms, "mh-1.model", device="cpu", steps=0, relax_cell=False)
        self.assertEqual(captured[0]["head"], "omat_pbe")
        self.assertEqual(captured[0]["default_dtype"], "float64")
        self.assertFalse(result["optimizer_converged"])
        self.assertEqual(result["atom_count"], 2)
        self.assertIsNone(result["structure_path"])
        self.assertIsNone(atoms.calc)


class SymmetrixTests(TemporaryDirectoryMixin, unittest.TestCase):
    def setUp(self):
        self.root = self.make_temp_directory()
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


class PublicAPITests(unittest.TestCase):
    def test_public_signatures_and_legacy_module_exports(self):
        import importlib
        import Process_MLIP as package

        expected = json.loads((Path(__file__).parent / "public_api.json").read_text())
        self.assertEqual(package.__all__, list(expected))
        for name, signature in expected.items():
            with self.subTest(name=name):
                exported = getattr(package, name)
                self.assertEqual(str(inspect.signature(exported)), signature)
                module = importlib.import_module(exported.__module__)
                self.assertIs(getattr(module, name), exported)

    def test_import_does_not_load_models(self):
        import subprocess
        from Process_MLIP.tests._support import PROJECT_ROOT

        subprocess.run([
            sys.executable, "-c",
            "import sys; import Process_MLIP; "
            "assert not any(m in sys.modules for m in "
            "('torch','mace','sevenn','chgnet','orb_models','symmetrix'))",
        ], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)

    def test_tests_are_isolated_and_do_not_import_other_test_cases(self):
        import ast
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(list(root.glob("test_*.py")), [])
        for path in (root / "tests").glob("test_*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or "").startswith("Process_MLIP.tests.test_"))


if __name__ == "__main__":
    unittest.main()

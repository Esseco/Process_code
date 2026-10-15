"""Workflow and lazy backend contracts, independent of model installations."""
from contextlib import nullcontext
import json
import inspect
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
from ase.build import bulk
from ase.calculators.emt import EMT
from ase.io import read

from Process_MLIP import (create_chgnet_calculator, create_mlip_calculator,
                          create_orb_calculator, model_config, run_mlip_md)


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


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="tmp_workflow_", dir=Path(__file__).parent)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.atoms = bulk("Cu", "fcc", a=3.6, cubic=True)
        self.loader = patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=EMT())
        self.mock_loader = self.loader.start()
        self.addCleanup(self.loader.stop)

    def test_load_once_stage_precedence_and_continuation(self):
        stages = [dict(ensemble="nvt", name="equil", steps=2, timestep_fs=0.5),
                  dict(ensemble="npt", steps=2)]
        result = run_mlip_md(self.atoms, model_config("mace-mh1"), self.root / "md",
                             stages, timestep_fs=1.0, temperature_K=300,
                             initialize_velocities=True)
        self.mock_loader.assert_called_once()
        self.assertEqual(result["total_steps"], 4)
        self.assertEqual(result["elapsed_time_fs"], 3)
        first, second = result["stage_results"]
        initial = read(second["trajectory_file"], index=0)
        np.testing.assert_allclose(initial.get_momenta(), first["final_atoms"].get_momenta())
        np.testing.assert_allclose(initial.cell, first["final_atoms"].cell)
        np.testing.assert_allclose(initial.positions, first["final_atoms"].positions)
        self.assertEqual(second["velocity_initialization"], "preserved")
        self.assertEqual(stages[0]["name"], "equil")  # input configuration not mutated
        summary = json.loads(Path(result["report_file"]).read_text())
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["stages_completed"], 2)
        self.assertEqual(summary["model"]["head"], "omat_pbe")

    def test_independent_single_stage_and_explicit_resampling(self):
        for ensemble in ("nvt", "npt"):
            result = run_mlip_md(self.atoms, "chgnet", self.root / ensemble,
                                 ensemble=ensemble, steps=1)
            self.assertEqual(len(result["stage_results"]), 1)
        result = run_mlip_md(self.atoms, "orb-v3", self.root / "resample", stages=[
            dict(steps=0), dict(steps=0, temperature_K=600, initialize_velocities=True)])
        self.assertEqual(result["stage_results"][1]["velocity_initialization"], "sampled")

    def test_validate_all_stages_and_collisions_before_loading(self):
        bad_sequences = [[], [dict(steps=1), dict(ensemble="wrong")],
                         [dict(steps=1), dict(timestep_fs=0)],
                         [dict(name="../escape")], [dict(misspelled=1)]]
        for stages in bad_sequences:
            with self.assertRaises(ValueError):
                run_mlip_md(self.atoms, output_dir=self.root / "bad", stages=stages)
        self.mock_loader.assert_not_called()
        self.assertFalse((self.root / "bad").exists())
        target = self.root / "exists" / "02_npt"
        target.mkdir(parents=True)
        (target / "md.csv").write_text("keep")
        with self.assertRaises(FileExistsError):
            run_mlip_md(self.atoms, output_dir=target.parent, stages=[
                dict(ensemble="nvt"), dict(ensemble="npt")])
        self.mock_loader.assert_not_called()
        self.assertFalse((target.parent / "01_nvt").exists())
        invalid_root = self.root / "file_not_directory"
        invalid_root.write_text("keep")
        with self.assertRaises(NotADirectoryError):
            run_mlip_md(self.atoms, output_dir=invalid_root, steps=1)
        self.mock_loader.assert_not_called()

    def test_failure_summary_does_not_claim_completion(self):
        with patch("Process_MLIP.md_workflow.run_md", side_effect=RuntimeError("failed stage")):
            with self.assertRaisesRegex(RuntimeError, "failed stage"):
                run_mlip_md(self.atoms, output_dir=self.root / "failed", steps=1)
        report = json.loads((self.root / "failed" / "run_report.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["stages_completed"], 0)


if __name__ == "__main__":
    unittest.main()

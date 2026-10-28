"""NEP backend contracts without importing Calorine or loading a model."""
import inspect
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch
import unittest

from ase.build import bulk
from ase.calculators.emt import EMT

from Process_MLIP import (
    create_mlip_calculator,
    create_nep_calculator,
    model_config,
    relax_structure_nep,
)


class NepBackendTests(unittest.TestCase):
    def test_package_import_is_lazy(self):
        subprocess.run([
            sys.executable, "-c",
            "import sys; import Process_MLIP; "
            "assert 'calorine' not in sys.modules; "
            "assert 'gpumd' not in sys.modules",
        ], check=True, capture_output=True, text=True)

    def _modules(self):
        calculators = ModuleType("calorine.calculators")
        calculators.CPUNEP = Mock(return_value=EMT())
        calculators.GPUNEP = Mock(return_value=Mock())
        package = ModuleType("calorine")
        package.calculators = calculators
        return package, calculators

    def test_cpu_and_gpu_backend_selection(self):
        package, calculators = self._modules()
        with patch.dict(sys.modules, {
            "calorine": package,
            "calorine.calculators": calculators,
        }), patch("pathlib.Path.is_file", return_value=True), \
             patch("Process_MLIP.nep.shutil.which", return_value="gpumd-custom"):
            create_nep_calculator("model.txt", backend="cpu")
            calculators.CPUNEP.assert_called_once_with("model.txt")

            gpu = calculators.GPUNEP.return_value
            create_nep_calculator("model.txt", backend="gpu",
                                  gpumd_command="gpumd-custom", directory="run")
            calculators.GPUNEP.assert_called_once_with(
                "model.txt", command=str(Path("gpumd-custom").resolve()), gpu_identifier_index=None)
            gpu.set_directory.assert_called_once_with("run")

    def test_invalid_backend_and_missing_model_fail_before_loading(self):
        with self.assertRaises(ValueError):
            create_nep_calculator("model.txt", backend="tpu")
        with self.assertRaises(FileNotFoundError):
            create_nep_calculator("missing-nep.txt")

    def test_model_config_and_generic_dispatch(self):
        config = model_config("nep", model_path="model.txt", backend="gpu")
        self.assertEqual(config["type"], "nep")
        self.assertEqual(config["backend"], "gpu")
        with patch("Process_MLIP.calculators.create_nep_calculator", return_value=object()) as loader:
            result = create_mlip_calculator(config)
        self.assertIs(result, loader.return_value)
        loader.assert_called_once_with(model_path="model.txt", backend="gpu",
                                       gpumd_command=None, directory=None)

    def test_relaxation_reuses_shared_ase_relaxer(self):
        with patch("Process_MLIP.nep_relax.create_nep_calculator", return_value=EMT()) as loader:
            result = relax_structure_nep(
                bulk("Cu", "fcc", a=3.6, cubic=True), "model.txt",
                backend="cpu", steps=0, relax_cell=True,
            )
        loader.assert_called_once_with("model.txt", backend="cpu",
                                       gpumd_command=None, directory=None)
        self.assertIn("nep_backend", result)
        self.assertEqual(result["nep_backend"], "cpu")


if __name__ == "__main__":
    unittest.main()

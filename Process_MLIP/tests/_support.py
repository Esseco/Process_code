"""共享测试夹具；不导入 TestCase，避免重复发现测试。"""
from pathlib import Path
from unittest.mock import patch
import contextlib
import io
import tempfile

from ase.build import bulk
from ase.calculators.calculator import Calculator, all_changes
from ase.calculators.emt import EMT
from ase.io import write
import numpy as np

from Process_MLIP.examples import mlip_md as example


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = PROJECT_ROOT / "Process_MLIP" / "examples"


class TemporaryDirectoryMixin:
    def make_temp_directory(self):
        temporary = tempfile.TemporaryDirectory(prefix="tmp_mlip_test_", dir=Path(__file__).parent)
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)


class NoStress(Calculator):
    implemented_properties = ["energy", "forces"]

    def calculate(self, atoms=None, properties=None, system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        self.results = {"energy": 0.0, "forces": np.zeros((len(atoms), 3))}


class ZeroCalculator(Calculator):
    implemented_properties = ["energy", "forces", "stress"]
    device = "cpu"

    def calculate(self, atoms=None, properties=None, system_changes=all_changes):
        super().calculate(atoms, properties, system_changes)
        self.results = dict(energy=0.0, forces=np.zeros((len(atoms), 3)), stress=np.zeros(6))


class MDExampleHarness(TemporaryDirectoryMixin):
    def setUp(self):
        self.root = self.make_temp_directory()
        self.input = self.root / "initial.traj"
        write(self.input, bulk("Cu", "fcc", a=3.6, cubic=True).repeat((2, 2, 2)))
        calculator = ZeroCalculator()
        calculator.device = "cpu"
        loader = patch("Process_MLIP.md_workflow.create_mlip_calculator", return_value=calculator)
        self.loader = loader.start()
        self.addCleanup(loader.stop)

    def run_example(self, config, stages=None, preview=False):
        with patch.multiple(example, INPUT=self.input, OUTPUT=self.root / "md",
                            STAGES=stages or [dict(name="equil", ensemble="nvt", steps=300),
                                              dict(name="final", ensemble="nvt", steps=300)],
                            MD_PARAMETERS=dict(temperature_K=300, timestep_fs=10,
                                               trajectory_interval=10),
                            PRE_RELAX=False, MSD_POSTPROCESS=config), \
                contextlib.redirect_stdout(io.StringIO()) as stream:
            example.main(["--preview"] if preview else [])
        return stream.getvalue()

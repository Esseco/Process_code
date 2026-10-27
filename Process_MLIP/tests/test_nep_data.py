import tempfile
import unittest
from pathlib import Path

import numpy as np
from ase import Atoms, units
from ase.io import read, write

from Process_MLIP import vasp_to_nep_xyz
from Process_MLIP.nep_data import split_nep_dataset, validate_nep_dataset


def _vasprun_xml(*, stress=True):
    basis = '<crystal><varray name="basis"><v>4 0 0</v><v>0 4 0</v><v>0 0 4</v></varray></crystal>'
    positions = '<varray name="positions"><v>0 0 0</v><v>0.5 0.5 0.5</v></varray>'
    stress_block = ('<varray name="stress"><v>10 2 3</v><v>2 20 4</v>'
                    '<v>3 4 30</v></varray>' if stress else '')
    return (
        '<modeling><kpoints><varray name="kpointlist"><v>0 0 0</v></varray>'
        '<varray name="weights"><v>1</v></varray></kpoints>'
        '<atominfo><array name="atoms"><set><rc><c>Li</c></rc><rc><c>O</c></rc>'
        '</set></array></atominfo><structure name="initialpos">' + basis + positions +
        '<varray name="selective"><v>F F F</v><v>T T T</v></varray></structure>'
        '<calculation><scstep><energy><i name="e_fr_energy">-10</i>'
        '<i name="e_0_energy">-9.9</i></energy></scstep>'
        '<energy><i name="e_fr_energy">-10</i><i name="e_0_energy">-9.9</i></energy>'
        '<structure>' + basis + positions + '</structure>'
        '<varray name="forces"><v>1 2 3</v><v>-1 -2 -3</v></varray>' +
        stress_block + '</calculation></modeling>'
    )


def _write_nep_fixture(path, count=4):
    frames = []
    for index in range(count):
        atoms = Atoms("LiO", positions=[[0, 0, 0], [2, 2, 2]],
                      cell=np.eye(3) * 4, pbc=True)
        atoms.info["energy"] = -10.0 - index
        atoms.info["virial"] = np.eye(3) * (index + 1)
        atoms.arrays["force"] = np.ones((2, 3)) * index
        frames.append(atoms)
    write(path, frames, format="extxyz", write_results=False)


class NepDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nep-data-test-")
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_vasp_to_nep_writes_standard_fields_and_virial(self):
        source = self.root / "vasprun.xml"
        source.write_text(_vasprun_xml(), encoding="utf-8")
        output = self.root / "train.xyz"
        self.assertEqual(vasp_to_nep_xyz(source, output), 1)
        frame = read(output, format="extxyz")
        self.assertAlmostEqual(frame.calc.results["energy"], -10.0)
        self.assertEqual(frame.arrays["force"].shape, (2, 3))
        expected_stress = -0.1 * units.GPa * np.array([[10, 2, 3], [2, 20, 4], [3, 4, 30]])
        np.testing.assert_allclose(frame.info["virial"], -expected_stress * 64)
        header = output.read_text(encoding="utf-8")
        self.assertIn("Properties=species:S:1:pos:R:3:force:R:3", header)
        self.assertIn("energy=", header)
        self.assertIn("virial=", header)

    def test_validation_and_deterministic_split(self):
        source = self.root / "all.xyz"
        _write_nep_fixture(source)
        report = validate_nep_dataset(source, expected_species=["Li", "O"], require_virial=True)
        self.assertEqual(report["frames"], 4)
        self.assertEqual(report["species"], ["Li", "O"])

        first = split_nep_dataset(source, self.root / "split1", seed=7)
        second = split_nep_dataset(source, self.root / "split2", seed=7)
        self.assertEqual(first["train_frames"], 4 * 0 + 4 - first["test_frames"])
        self.assertEqual((self.root / "split1" / "train.xyz").read_text(),
                         (self.root / "split2" / "train.xyz").read_text())
        self.assertEqual((self.root / "split1" / "test.xyz").read_text(),
                         (self.root / "split2" / "test.xyz").read_text())

    def test_missing_virial_and_output_protection(self):
        source = self.root / "vasprun.xml"
        source.write_text(_vasprun_xml(stress=False), encoding="utf-8")
        output = self.root / "train.xyz"
        with self.assertRaisesRegex(ValueError, "stress"):
            vasp_to_nep_xyz(source, output)
        self.assertFalse(output.exists())

        existing = self.root / "existing.xyz"
        _write_nep_fixture(existing, count=2)
        split_nep_dataset(existing, self.root / "split", train_fraction=0.5)
        (self.root / "split" / "keep.txt").write_text("keep")
        with self.assertRaises(FileExistsError):
            split_nep_dataset(existing, self.root / "split", train_fraction=0.5)

    def test_standard_stress_fallback_and_invalid_virial_are_checked(self):
        source = self.root / "stress.xyz"
        atoms = Atoms("Li", positions=[[0, 0, 0]], cell=np.eye(3) * 4, pbc=True)
        atoms.info["energy"] = -1.0
        atoms.info["stress"] = np.eye(3) * 0.1
        atoms.arrays["force"] = np.zeros((1, 3))
        write(source, atoms, format="extxyz", write_results=False)
        self.assertTrue(validate_nep_dataset(source, require_virial=True)["has_virial"])

        bad = self.root / "bad.xyz"
        atoms.info.pop("stress")
        atoms.info["virial"] = np.ones(6)
        write(bad, atoms, format="extxyz", write_results=False)
        with self.assertRaisesRegex(ValueError, "virial"):
            validate_nep_dataset(bad, require_forces=False, require_virial=True)


if __name__ == "__main__":
    unittest.main()

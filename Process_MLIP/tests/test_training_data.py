"""VASP -> MACE labels: real ASE XML parsing and extxyz round trips."""
import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from ase import Atoms, units
from ase.calculators.singlepoint import SinglePointCalculator
from ase.constraints import FixAtoms
from ase.io import read

from Process_MLIP import vasp_to_xyz


def xml_fixture(*, forces=True, stress=True):
    basis = '<crystal><varray name="basis"><v>4 0 0</v><v>0 4 0</v><v>0 0 4</v></varray></crystal>'
    positions = '<varray name="positions"><v>0 0 0</v><v>0.5 0.5 0.5</v></varray>'
    head = ('<modeling><kpoints><varray name="kpointlist"><v>0 0 0</v></varray>'
            '<varray name="weights"><v>1</v></varray></kpoints>'
            '<atominfo><array name="atoms"><set><rc><c>Li</c></rc><rc><c>O</c></rc>'
            '</set></array></atominfo><structure name="initialpos">' + basis + positions +
            '<varray name="selective"><v>F F F</v><v>T T T</v></varray></structure>')
    steps = []
    for free_energy in (-10.0, -11.0):
        energy = (f'<energy><i name="e_fr_energy">{free_energy}</i>'
                  f'<i name="e_0_energy">{free_energy + 0.1}</i></energy>')
        steps.append('<calculation><scstep>' + energy + '</scstep>' + energy +
                     '<structure>' + basis + positions + '</structure>' +
                     ('<varray name="forces"><v>1 2 3</v><v>-1 -2 -3</v></varray>' if forces else '') +
                     ('<varray name="stress"><v>10 2 3</v><v>2 20 4</v><v>3 4 30</v></varray>' if stress else '') +
                     '</calculation>')
    return head + ''.join(steps) + '</modeling>'


class VaspToXYZTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vasp-xyz-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "vasprun.xml"
        self.source.write_text(xml_fixture(), encoding="utf-8")
        self.output = self.root / "train.xyz"

    def test_xml_all_steps_preserve_labels_units_and_raw_forces(self):
        self.assertEqual(vasp_to_xyz(self.source, self.output), 2)
        frames = read(self.output, index=":", format="extxyz")
        self.assertEqual([a.info["REF_energy"] for a in frames], [-10.0, -11.0])
        np.testing.assert_allclose(frames[0].arrays["REF_forces"], [[1, 2, 3], [-1, -2, -3]])
        np.testing.assert_allclose(frames[0].info["REF_stress"],
                                  -0.1 * units.GPa * np.array([[10, 2, 3], [2, 20, 4], [3, 4, 30]]))
        self.assertEqual(frames[0].get_chemical_symbols(), ["Li", "O"])
        np.testing.assert_allclose(frames[0].cell.array, np.eye(3) * 4)
        self.assertTrue(frames[0].pbc.all())
        self.assertEqual(frames[0].constraints, [])
        self.assertIsNone(frames[0].calc)
        self.assertEqual(self.source.read_text(), xml_fixture())

    def test_directory_last_frame_and_explicit_zero_smearing_energy(self):
        self.assertEqual(vasp_to_xyz(self.root, self.output, index=-1, energy_type="energy"), 1)
        self.assertAlmostEqual(read(self.output).info["REF_energy"], -10.9)

    def test_multiple_files_and_compressed_xml(self):
        compressed = self.root / "vasprun.xml.gz"
        with gzip.open(compressed, "wt", encoding="utf-8") as handle:
            handle.write(xml_fixture())
        self.assertEqual(vasp_to_xyz([self.source, compressed], self.output, index=-1), 2)

    def test_missing_stress_is_explicitly_optional(self):
        self.source.write_text(xml_fixture(stress=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "stress"):
            vasp_to_xyz(self.source, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(vasp_to_xyz(self.source, self.output, include_stress=False), 2)
        self.assertNotIn("REF_stress", read(self.output).info)

    def test_missing_force_or_later_bad_frame_keeps_existing_output(self):
        self.output.write_text("keep me", encoding="utf-8")
        bad = "<v>nan -2 -3</v>".join(xml_fixture().rsplit("<v>-1 -2 -3</v>", 1))
        self.source.write_text(bad, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "finite"):
            vasp_to_xyz(self.source, self.output, overwrite=True)
        self.assertEqual(self.output.read_text(), "keep me")
        self.source.write_text(xml_fixture(forces=False), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "forces"):
            vasp_to_xyz(self.source, self.output, overwrite=True)
        self.assertEqual(self.output.read_text(), "keep me")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["train.xyz", "vasprun.xml"])

    def test_output_protection_and_empty_selection(self):
        self.output.write_text("keep me", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            vasp_to_xyz(self.source, self.output)
        with self.assertRaises(ValueError):
            vasp_to_xyz(self.source, self.source, overwrite=True)
        with self.assertRaisesRegex(ValueError, "No frames"):
            vasp_to_xyz(self.source, self.output, index="0:0", overwrite=True)
        self.assertEqual(self.output.read_text(), "keep me")
        self.assertEqual(vasp_to_xyz(self.source, self.output, overwrite=True), 2)

    def test_outcar_dispatch_uses_ase_reader(self):
        source = self.root / "OUTCAR"
        source.write_text("reader fixture", encoding="utf-8")
        atoms = Atoms("LiO", cell=[4]*3, positions=[[0, 0, 0], [2, 2, 2]], pbc=True)
        atoms.set_constraint(FixAtoms(indices=[0]))
        atoms.calc = SinglePointCalculator(atoms, energy=-9.9, free_energy=-10,
                                           forces=np.ones((2, 3)), stress=np.zeros(6))
        with patch("Process_MLIP.training_data.iread", return_value=iter([atoms])) as reader:
            self.assertEqual(vasp_to_xyz(source, self.output), 1)
        self.assertEqual(reader.call_args.kwargs["format"], "vasp-out")
        np.testing.assert_allclose(read(self.output).arrays["REF_forces"], np.ones((2, 3)))


if __name__ == "__main__":
    unittest.main()

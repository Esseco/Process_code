"""Regression checks using real pymatgen DOS objects and a stub XML reader."""

import tempfile
import gzip
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
from pymatgen.core import Lattice, Structure
from pymatgen.electronic_structure.core import Orbital, Spin
from pymatgen.electronic_structure.dos import CompleteDos, Dos
from pymatgen.io.vasp.inputs import Incar, Kpoints

from Process_Vasp.dos import read_dos, read_ipr_data


class ReadDosTests(unittest.TestCase):
    def setUp(self):
        structure = Structure(Lattice.cubic(4), ["Fe", "O"], [[0, 0, 0], [0.5]*3])
        density = {Spin.up: np.array([1., 2., 3.]), Spin.down: np.array([2., 3., 4.])}
        total = Dos(1., np.array([0., 1., 2.]), density)
        pdos = {site: {Orbital.s: density} for site in structure}
        self.run = SimpleNamespace(
            complete_dos=CompleteDos(structure, total, pdos),
            dos_has_errors=False, final_structure=structure,
            incar=Incar({"NEDOS": 3}), parameters={"SIGMA": .05},
            kpoints=Kpoints.gamma_automatic((2, 3, 4)), actual_kpoints=[[0, 0, 0]],
        )

    def test_defaults_and_csv_roundtrip(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder, patch("Process_Vasp.dos.Vasprun", return_value=self.run):
            Incar({"NEDOS": 301}).write_file(Path(folder)/"INCAR")
            result = read_dos(folder)
            self.assertEqual(result["NEDOS"], 301)
            self.assertEqual(result["kpoint_density"], 48)
            self.assertEqual(result["kpoint_mesh"], (2, 3, 4))
            self.assertEqual(result["df"].columns.tolist(), ["energy", "dos_up", "dos_down", "Fe_up", "Fe_down", "O_up", "O_down"])
            np.testing.assert_array_equal(result["df"]["energy"], [-1, 0, 1])
            self.assertFalse((Path(folder)/"dos.csv").exists())
            output = Path(folder)/"plot.csv"
            exported = read_dos(folder, output_csv=output)
            pd.testing.assert_frame_equal(pd.read_csv(output), exported["df"])

    def test_options_and_explicit_kpoints(self):
        self.run.kpoints = Kpoints(kpts=[[0, 0, 0]], num_kpts=1, style="Reciprocal", kpts_weights=[1])
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder, patch("Process_Vasp.dos.Vasprun", return_value=self.run):
            result = read_dos(folder, include_element=False, include_total=False, include_orbital=True, shift_fermi=False, mirror_spin_down=True)
            self.assertIsNone(result["kpoint_density"])
            self.assertEqual(result["NEDOS"], 3)
            np.testing.assert_array_equal(result["df"]["energy"], [0, 1, 2])
            np.testing.assert_array_equal(result["df"]["Fe_s_down"], [-2, -3, -4])
            self.assertNotIn("Fe_down", result["df"])

    def test_missing_projection(self):
        self.run.complete_dos.pdos = {}
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder, patch("Process_Vasp.dos.Vasprun", return_value=self.run):
            with self.assertRaisesRegex(ValueError, "Projected DOS"):
                read_dos(folder)
            self.assertIn("dos_up", read_dos(folder, include_element=False)["df"])

    def test_gzip_outputs(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            directory = Path(folder)
            for name, content in (("INCAR", "NEDOS = 401\n"), ("vasprun.xml", "stub"), ("PROCAR", "stub")):
                with gzip.open(directory / (name + ".gz"), "wt") as handle:
                    handle.write(content)
            procar = SimpleNamespace(
                weights=np.array([1.]),
                eigenvalues={Spin.up: np.array([[1.]])},
                data={Spin.up: np.ones((1, 1, 2, 1))},
            )
            with patch("Process_Vasp.dos.Vasprun", return_value=self.run) as xml_reader, patch("Process_Vasp.dos.Procar", return_value=procar) as procar_reader:
                result = read_dos(directory, read_ipr=True)
                self.assertEqual(result["NEDOS"], 401)
                self.assertEqual(Path(xml_reader.call_args.args[0]), directory / "vasprun.xml.gz")
                self.assertEqual(Path(procar_reader.call_args.args[0]), directory / "PROCAR.gz")
                np.testing.assert_allclose(result["df"]["ipr_up"], .5)
                ipr = read_ipr_data(directory, output_csv=directory / "ipr.csv", efermi=1.)
                self.assertEqual(ipr.loc[0, "ipr"], .5)
            self.assertFalse((directory / "vasprun.xml").exists())
            self.assertFalse((directory / "PROCAR").exists())


if __name__ == "__main__":
    unittest.main()

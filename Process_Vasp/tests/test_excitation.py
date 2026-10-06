"""Validate occupation changes and compressed restart input preparation."""
import gzip
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from pymatgen.core import Lattice, Structure
from pymatgen.electronic_structure.core import Spin
from pymatgen.io.vasp.inputs import Incar

from Process_Vasp.excitation import generate_excited_input


class ExcitationTests(unittest.TestCase):
    def test_generation_and_checks(self):
        structure = Structure(Lattice.cubic(4), ["Si"], [[0, 0, 0]])
        run = SimpleNamespace(
            converged_electronic=True, final_structure=structure,
            parameters={"NELECT": 4}, actual_kpoints=[[0, 0, 0]],
            actual_kpoints_weights=[1],
            eigenvalues={Spin.up: np.array([[[-2, 2], [-1, 2], [1, 0], [2, 0]]], dtype=float)},
        )
        charge = SimpleNamespace(structure=structure, data={"total": np.zeros((2, 3, 4))})
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temporary:
            root = Path(temporary)
            source = root / "ground"
            source.mkdir()
            for name, content in {
                "INCAR": b"ENCUT = 520\nISPIN = 1\n",
                "vasprun.xml": b"stub", "POTCAR": b"potcar",
                "WAVECAR": b"wave", "CHGCAR": b"charge",
                "KPOINTS": b"Gamma\n0\nGamma\n1 1 1\n0 0 0\n",
            }.items():
                with gzip.open(source / (name + ".gz"), "wb") as handle:
                    handle.write(content)
            with patch("Process_Vasp.excitation.Vasprun", return_value=run), patch("Process_Vasp.excitation.Chgcar.from_file", return_value=charge):
                target = root / "excited"
                report = generate_excited_input(source, target)
                incar = Incar.from_file(target / "INCAR")
                np.testing.assert_allclose(incar["FERWE"], [1, .5, .5, 0])
                self.assertEqual(report["valence_band"], 2)
                self.assertEqual(incar["NGYF"], 3)
                self.assertEqual(incar["ENCUT"], 520)
                self.assertEqual((target / "WAVECAR").read_bytes(), b"wave")
                self.assertTrue((source / "WAVECAR.gz").exists())
                with self.assertRaisesRegex(ValueError, "empty"):
                    generate_excited_input(source, target)
                run.actual_kpoints = [[0, 0, 0], [.5, 0, 0]]
                with self.assertRaisesRegex(ValueError, "single Gamma"):
                    generate_excited_input(source, root / "invalid")
                self.assertFalse((root / "invalid").exists())
                run.actual_kpoints = [[0, 0, 0]]
                run.eigenvalues = {
                    channel: np.array([[[-2, 1], [-1, 1], [1, 0], [2, 0]]], dtype=float)
                    for channel in (Spin.up, Spin.down)
                }
                polarized = root / "polarized"
                generate_excited_input(source, polarized, spin="down", valence_band=2, conduction_band=3)
                incar = Incar.from_file(polarized / "INCAR")
                np.testing.assert_allclose(incar["FERWE"], [1, 1, 0, 0])
                np.testing.assert_allclose(incar["FERDO"], [1, 0, 1, 0])
                run.eigenvalues[Spin.down][0, 2:, 0] = [.2, 2]
                auto = generate_excited_input(source, root / "auto")
                self.assertEqual(auto["spin"], "down")
                self.assertAlmostEqual(auto["channel_gaps_eV"]["down"], 1.2)
                both = generate_excited_input(source, root / "both", spin="both")
                self.assertEqual(set(both), {"up", "down"})
                up = Incar.from_file(root / "both" / "up" / "INCAR")
                down = Incar.from_file(root / "both" / "down" / "INCAR")
                np.testing.assert_allclose(up["FERWE"], [1, 0, 1, 0])
                np.testing.assert_allclose(up["FERDO"], [1, 1, 0, 0])
                np.testing.assert_allclose(down["FERWE"], [1, 1, 0, 0])
                np.testing.assert_allclose(down["FERDO"], [1, 0, 1, 0])
                # Equal gaps deterministically select up.
                run.eigenvalues[Spin.down][0, 2, 0] = 1
                self.assertEqual(generate_excited_input(source, root / "tie")["spin"], "up")
                # Invalid second channel must leave no first-channel files.
                run.eigenvalues[Spin.down][0, 2, 1] = .5
                with self.assertRaisesRegex(ValueError, "integer"):
                    generate_excited_input(source, root / "bad_both", spin="both")
                self.assertFalse((root / "bad_both").exists())


if __name__ == "__main__":
    unittest.main()

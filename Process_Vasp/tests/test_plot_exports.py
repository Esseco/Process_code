"""Check that exported band columns preserve plot coordinates and energy reference."""

import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from pymatgen.electronic_structure.core import Spin

from Process_Vasp.workflows.plot_exports import export_plot_data


class BandExportTests(unittest.TestCase):
    def test_band_csv_and_metadata(self):
        band = SimpleNamespace(
            distance=[0.0, 0.5],
            kpoints=[
                SimpleNamespace(frac_coords=[0, 0, 0], label="G"),
                SimpleNamespace(frac_coords=[0.5, 0, 0], label="X"),
            ],
            bands={Spin.up: np.array([[1.0, 2.0], [3.0, 4.0]])},
            efermi=1.5,
            is_metal=lambda: False,
            get_band_gap=lambda: {"energy": 1.0, "direct": True, "transition": "G-X"},
        )
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            root = Path(folder)
            with patch("Process_Vasp.workflows.plot_exports.Vasprun") as vasprun:
                vasprun.return_value.get_band_structure.return_value = band
                paths = export_plot_data("band", root, root)
            with (root / "band.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            metadata = json.loads((root / "band_metadata.json").read_text())
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[0]["label"], "G")
            self.assertEqual(rows[1]["k_distance_inv_angstrom"], "0.5")
            self.assertEqual(rows[0]["energy_minus_fermi_eV"], "-0.5")
            self.assertEqual(rows[2]["band_index"], "2")
            self.assertEqual(metadata["band_gap"]["energy_eV"], 1.0)
            self.assertEqual(paths, [str(root / "band.csv"), str(root / "band_metadata.json")])


if __name__ == "__main__":
    unittest.main()

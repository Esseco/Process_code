"""Portable plotting-data exports for completed atomate2 VASP stages."""

import csv
import json
from pathlib import Path

from monty.os.path import zpath
from pymatgen.electronic_structure.core import Spin
from pymatgen.io.vasp.outputs import Vasprun


def export_plot_data(stage, calculation_dir, task_dir):
    """Write DOS or band CSV and metadata; return the created paths.

    Energy values are in eV, and ``energy_minus_fermi_eV`` is E - E_F.
    Band path distance is in reciprocal angstroms. Existing CSVs are replaced
    when a completed calculation is exported again.
    """
    calculation_dir = Path(calculation_dir)
    task_dir = Path(task_dir)
    if stage == "dos":
        from Process_Vasp.results.dos import read_dos

        csv_path = task_dir / "dos.csv"
        result = read_dos(calculation_dir, output_csv=csv_path)
        metadata = {key: value for key, value in result.items() if key != "df"}
        metadata["energy_column"] = "energy = E - E_F (eV)"
        metadata["dos_units"] = "states/eV/cell"
        metadata_path = task_dir / "dos_metadata.json"
    elif stage == "band":
        run = Vasprun(
            zpath(calculation_dir / "vasprun.xml"),
            parse_dos=False,
            parse_eigen=True,
            parse_projected_eigen=False,
            parse_potcar_file=False,
        )
        band = run.get_band_structure(
            kpoints_filename=str(zpath(calculation_dir / "KPOINTS")),
            line_mode=True,
        )
        distances = band.distance
        if len(distances) != len(band.kpoints):
            raise ValueError("Band path distance and k-point counts differ")
        csv_path = task_dir / "band.csv"
        fieldnames = (
            "spin", "band_index", "kpoint_index", "k_distance_inv_angstrom",
            "kx_frac", "ky_frac", "kz_frac", "label", "energy_eV",
            "energy_minus_fermi_eV",
        )
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for spin in (Spin.up, Spin.down):
                if spin not in band.bands:
                    continue
                for band_index, energies in enumerate(band.bands[spin], start=1):
                    for index, (kpoint, energy) in enumerate(
                        zip(band.kpoints, energies, strict=True), start=1
                    ):
                        writer.writerow({
                            "spin": "up" if spin == Spin.up else "down",
                            "band_index": band_index,
                            "kpoint_index": index,
                            "k_distance_inv_angstrom": float(distances[index - 1]),
                            "kx_frac": float(kpoint.frac_coords[0]),
                            "ky_frac": float(kpoint.frac_coords[1]),
                            "kz_frac": float(kpoint.frac_coords[2]),
                            "label": kpoint.label or "",
                            "energy_eV": float(energy),
                            "energy_minus_fermi_eV": float(energy - band.efermi),
                        })
        gap = None
        if not band.is_metal():
            raw_gap = band.get_band_gap()
            gap = {
                "energy_eV": float(raw_gap["energy"]),
                "direct": bool(raw_gap["direct"]),
                "transition": raw_gap["transition"],
            }
        metadata = {
            "source": str(calculation_dir),
            "efermi_eV": float(band.efermi),
            "is_metal": bool(band.is_metal()),
            "band_gap": gap,
            "nkpoints": len(band.kpoints),
            "nbands_by_spin": {
                "up" if spin == Spin.up else "down": len(bands)
                for spin, bands in band.bands.items()
            },
            "energy_reference": "energy_minus_fermi_eV = E - E_F",
            "distance_unit": "1/angstrom",
        }
        metadata_path = task_dir / "band_metadata.json"
    else:
        raise ValueError(f"Unsupported plotting-data stage: {stage}")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return [str(csv_path), str(metadata_path)]

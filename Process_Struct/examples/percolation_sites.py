"""CCNB channel/site export example. Run in the ccnb environment from repo root.

Input: ordered structure, optional migrant element and probe radius in angstrom.
Output: original CCNB files, marker CIF, site/connection CSV and JSON summary.
No randomness in analysis; every run creates a unique directory, without overwrite.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.io.cif import CifBlock, CifFile

from Process_Struct import analyze_percolation
from Process_Struct.ccnb_net import read_channel_net

STRUCTURE_FILE = Path(
    r"E:\0-UCAS-Haild\Init_struct\Struct-Na-X\mp-1078217_NaFeF3.vasp"
)
MIGRANT = "Na"
PROBE_RADIUS_A = 0.5
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "percolation_outputs"


def export_sites(folder: Path, migrant: str | None):
    """Export channel NET sites and edges; retain every periodic connection."""
    sites, edges = read_channel_net(folder / "structure.net")
    with (folder / "interstitial_sites.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["channel_id", "dimension", "node_id", "label", "fx", "fy", "fz", "radius_A"])
        for row in sites:
            writer.writerow([row["channel_id"], row["dimension"], row["node_id"], row["label"],
                             *row["frac_coords"], row["radius_A"]])
    with (folder / "bottleneck_connections.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["channel_id", "dimension", "start", "end", "image_a", "image_b", "image_c",
                         "bottleneck_fx", "bottleneck_fy", "bottleneck_fz", "radius_A", "length_A"])
        for row in edges:
            writer.writerow([row["channel_id"], row["dimension"], row["start"], row["end"],
                             *row["image"], *row["bottleneck_frac_coords"],
                             row["bottleneck_radius_A"], row["length_A"]])

    structure = Structure.from_file(folder / "structure.cif")
    atoms = [(f"{site.specie.symbol}{i}", site.specie.symbol, site.frac_coords)
             for i, site in enumerate(structure) if site.specie.symbol != migrant]
    if {site.specie.symbol for site in structure}.intersection({"He", "Ne"}):
        raise ValueError("He/Ne markers conflict with actual atoms; choose other marker symbols.")
    # Folding/deduplication is for display only; the CSV retains original edge rows.
    for i, row in enumerate(sites):
        atoms.append((f"It{i}", "He", [x % 1.0 for x in row["frac_coords"]]))
    unique_bottlenecks = {}
    for row in edges:
        frac = [x % 1.0 for x in row["bottleneck_frac_coords"]]
        key = (tuple(round(x, 5) for x in frac), round(row["bottleneck_radius_A"], 5))
        unique_bottlenecks.setdefault(key, frac)
    for i, frac in enumerate(unique_bottlenecks.values()):
        atoms.append((f"Bn{i}", "Ne", frac))

    # Coincident markers are display layers, not physical atomic occupancy.
    groups = []
    for i, (_, _, frac) in enumerate(atoms):
        for group in groups:
            reference = atoms[group[0]][2]
            if all(abs((float(a) - float(b)) - round(float(a) - float(b))) < 1e-4
                   for a, b in zip(frac, reference)):
                group.append(i)
                break
        else:
            groups.append([i])
    occupancies = [1.0] * len(atoms)
    for group in groups:
        for index in group:
            occupancies[index] = 1.0 / len(group)

    data = {"_symmetry_space_group_name_H-M": "P 1",
            "_symmetry_Int_Tables_number": 1,
            "_symmetry_equiv_pos_as_xyz": ["x, y, z"]}
    for name, value in zip(("a", "b", "c", "alpha", "beta", "gamma"), structure.lattice.parameters):
        data[f"_cell_length_{name}" if name in {"a", "b", "c"} else f"_cell_angle_{name}"] = str(value)
    columns = ["_atom_site_label", "_atom_site_type_symbol", "_atom_site_fract_x",
               "_atom_site_fract_y", "_atom_site_fract_z", "_atom_site_occupancy"]
    for key in columns:
        data[key] = []
    for (label, symbol, frac), occupancy in zip(atoms, occupancies):
        for key, value in zip(columns, [label, symbol, *frac, occupancy]):
            data[key].append(str(value))
    block = CifBlock(data, [["_symmetry_equiv_pos_as_xyz"], columns], "channel_markers")
    (folder / "channel_sites_overlay.cif").write_text(
        str(CifFile({"channel_markers": block})), encoding="utf-8"
    )
    return sites, edges, len(unique_bottlenecks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structure", type=Path, default=STRUCTURE_FILE)
    parser.add_argument("--migrant", default=MIGRANT, help="Empty string keeps all atoms")
    parser.add_argument("--radius", type=float, default=PROBE_RADIUS_A, help="Probe radius in angstrom")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    if not args.structure.is_file():
        raise FileNotFoundError(args.structure)
    migrant = args.migrant.strip() or None
    result = analyze_percolation(args.structure, migrant=migrant,
                                cutoff_radius=args.radius, output_dir=args.output)
    folder = Path(result["output_directory"])
    sites, edges, unique_count = export_sites(folder, migrant)
    result.update(interstitial_count=len(sites), connection_record_count=len(edges),
                  unique_bottleneck_marker_count=unique_count)
    result["artifacts"] = sorted(str(p) for p in folder.iterdir() if p.is_file())
    summary = folder / "summary.json"
    result["artifacts"].append(str(summary))
    summary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("He/It = interstitial markers; Ne/Bn = bottleneck markers (visualization only)")
    print("CIF carries point positions; NET/CSV carry full periodic connectivity.")


if __name__ == "__main__":
    main()

"""Compact readers for the main results in ``vasprun.xml``."""

from pathlib import Path
from typing import Any, Literal

from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.entries.computed_entries import ComputedStructureEntry
from pymatgen.io.vasp.outputs import Vasprun

ReadField = Literal["e", "f", "s", "m"]


def _find_vasprun_file(init_dir: Path) -> Path:
    """Return the available plain or gzip-compressed vasprun file."""
    candidates = (init_dir / "vasprun.xml", init_dir / "vasprun.xml.gz")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Neither vasprun.xml nor vasprun.xml.gz was found in {init_dir}"
    )


def _corrected_energy_per_atom(structure: Any, energy: float) -> float:
    """Return the Materials Project corrected energy per atom."""
    entry = ComputedStructureEntry(
        structure,
        energy,
        parameters={
            "hubbards": {
                "Na": 0,
                "Mn": 3.9,
                "Fe": 5.3,
                "Co": 3.32,
                "Cr": 3.7,
                "Ni": 6.2,
                "V": 3.25,
                "O": 0,
            },
            "run_type": "GGA+U",
        },
    )
    processed = MaterialsProject2020Compatibility(check_potcar=False).process_entry(
        entry
    )
    corrected_energy = energy if processed is None else processed.energy
    return corrected_energy / structure.num_sites


def _normalise_fields(efsm: str) -> set[ReadField]:
    """Validate and normalize the requested energy/force/stress/magnetization fields."""
    fields = set(efsm.lower())
    invalid = fields.difference("efsm")
    if invalid:
        raise ValueError(f"Unsupported efsm field(s): {', '.join(sorted(invalid))}")
    return fields  # type: ignore[return-value]


def _step_data(step: dict[str, Any], fields: set[ReadField]) -> dict[str, Any]:
    """Return the requested values from one ionic step."""
    data: dict[str, Any] = {}
    if "e" in fields:
        raw_energy = float(step["e_0_energy"])
        structure = step["structure"]
        data.update(
            {
                "vasp_energy_per_atom": raw_energy / structure.num_sites,
                "corrected_energy_per_atom": _corrected_energy_per_atom(
                    structure, raw_energy
                ),
            }
        )
    if "f" in fields:
        data["forces"] = step.get("forces")
    if "s" in fields:
        data["stress"] = step.get("stress")
    if "m" in fields:
        data["magnetization"] = step.get("magnetization")
    return data


def read_vasp_output(
    init_dir: str | Path,
    last_step: bool = True,
    efsm: str = "e",
    read_dos: bool = False,
) -> dict[str, Any]:
    """Read selected results from one VASP calculation directory.

    Args:
        init_dir: Directory containing ``vasprun.xml`` or ``vasprun.xml.gz``.
        last_step: Read only the final ionic step when true; otherwise read all steps.
        efsm: Fields to read: ``e`` energy, ``f`` forces, ``s`` stress, and ``m`` magnetization.
        read_dos: Read band gap, CBM, VBM, and direct-gap information.

    Returns:
        A dictionary containing path, composition, atom count, and requested results.
    """
    init_dir = Path(init_dir)
    fields = _normalise_fields(efsm)
    vasprun = Vasprun(
        _find_vasprun_file(init_dir),
        parse_dos=read_dos,
        parse_eigen=read_dos,
        parse_projected_eigen=False,
        parse_potcar_file=False,
        exception_on_bad_xml=False,
    )
    structure = vasprun.final_structure
    result: dict[str, Any] = {
        "path": init_dir,
        "composition": structure.composition,
        "atom_num": structure.num_sites,
        "volume": structure.volume,
    }

    if last_step:
        result.update(_step_data(vasprun.ionic_steps[-1], fields))
    else:
        result["ionic_steps"] = [
            _step_data(step, fields) for step in vasprun.ionic_steps
        ]

    if read_dos:
        band_gap, cbm, vbm, is_direct = vasprun.eigenvalue_band_properties
        result.update(
            {"band_gap": band_gap, "cbm": cbm, "vbm": vbm, "direct": is_direct}
        )
    return result

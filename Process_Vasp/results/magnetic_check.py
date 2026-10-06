"""Read-only Fe/Mn local-moment diagnostics; never a magnetic ground-state proof."""
import math
from pathlib import Path

RANGES = {"Fe": (3.5, 4.5), "Mn": (3.0, 4.0)}


def check_layered_oxide_moments(elements, moments=None, *, is_layered_oxide=None,
                               noncollinear=False, total_moment=None):
    """Check supported elements' absolute scalar moments in mu_B, without writes.

    Layered identity must be supplied by the caller, not inferred from Fe/O alone.
    Negative collinear moments are valid. A warning is an empirical range miss,
    not proof of an excited state. Unsupported sites are never checked.
    """
    elements = list(elements)
    supported = sorted(set(elements) & set(RANGES))
    report = {"schema": "layered-fe-mn-moments-v1", "unit": "mu_B",
              "supported_elements": supported, "elements": elements,
              "expected_abs_ranges": {key: list(value) for key, value in RANGES.items()},
              "moments": None, "total_local_moment": total_moment,
              "is_layered_oxide": is_layered_oxide, "noncollinear": bool(noncollinear),
              "checked_atoms": 0, "reasonable_atoms": [], "anomalous_atoms": [], "heuristic_only": True}
    if not supported or is_layered_oxide is False or "O" not in elements:
        report.update(status="skipped", reason="no_supported_elements" if not supported else "not_layered_oxide")
        return report
    if noncollinear:
        report.update(status="unknown", reason="noncollinear_or_SOC_not_supported")
        return report
    try:
        values = [float(m) for m in moments]
        if len(values) != len(elements) or not all(math.isfinite(m) for m in values):
            raise ValueError("invalid shape or nonfinite moments")
    except (TypeError, ValueError, OverflowError):
        report.update(status="unknown", reason="missing_or_invalid_local_moments")
        return report
    report["moments"] = values
    if is_layered_oxide is not True:
        report.update(status="unknown", reason="layered_identity_unavailable")
        return report
    for index, (element, moment) in enumerate(zip(elements, values)):
        if element not in RANGES:
            continue
        report["checked_atoms"] += 1
        low, high = RANGES[element]
        atom = {"atom_index": index, "element": element,
                "moment": moment, "absolute_moment": abs(moment), "expected_abs_range": [low, high]}
        if not low <= abs(moment) <= high:
            report["anomalous_atoms"].append(atom)
        else:
            report["reasonable_atoms"].append(atom)
    report["status"] = "warning" if report["anomalous_atoms"] else "passed"
    return report


def check_dft_magnetic_moments(directory, *, structure=None, is_layered_oxide=None,
                              parameters=None):
    """Read the final collinear OUTCAR table (including gzip), then diagnose.

    No files are changed. The caller may supply the matching final Structure.
    Missing/invalid magnetization is unknown, never a fabricated zero/pass.
    """
    from monty.os.path import zpath
    from pymatgen.core import Structure
    root = Path(directory)
    if structure is None:
        structure = Structure.from_file(zpath(root / "POSCAR"))
    elements = [site.specie.symbol for site in structure]
    if not set(elements) & set(RANGES) or is_layered_oxide is False or "O" not in elements:
        return check_layered_oxide_moments(elements, is_layered_oxide=is_layered_oxide)
    if parameters and (_boolean(parameters.get("LNONCOLLINEAR", False)) or _boolean(parameters.get("LSORBIT", False))):
        return check_layered_oxide_moments(elements, is_layered_oxide=is_layered_oxide, noncollinear=True)
    raw = read_dft_magnetic_data(root, structure=structure, parameters=parameters)
    report = check_layered_oxide_moments(elements, raw.get("moments"), is_layered_oxide=is_layered_oxide,
        noncollinear=raw.get("noncollinear", False), total_moment=raw.get("total_local_moment"))
    report.update({key: raw[key] for key in ("source", "nupdown", "read_error") if key in raw})
    return report


def read_dft_magnetic_data(directory, *, structure=None, parameters=None):
    """Read final per-site moments for ALL elements, without accepting/rejecting spins.

    Units are mu_B. Scalar collinear or Cartesian vector noncollinear moments
    follow the Structure's atom order. Missing data are explicit, never zeros.
    No writes, phase identification, scientific filtering or VASP execution.
    """
    from monty.os.path import zpath
    from pymatgen.core import Structure
    from pymatgen.io.vasp.inputs import Incar
    from pymatgen.io.vasp.outputs import Outcar
    root = Path(directory)
    if structure is None:
        structure = Structure.from_file(zpath(root / "POSCAR"))
    elements = [site.specie.symbol for site in structure]
    raw = {"schema": "vasp-final-site-moments-v1", "unit": "mu_B", "elements": elements,
           "moments": None, "sites": [], "status": "unavailable", "noncollinear": False}
    try:
        if parameters is None:
            incar_path = Path(zpath(root / "INCAR"))
            parameters = Incar.from_file(incar_path) if incar_path.is_file() else {}
        outcar = Outcar(zpath(root / "OUTCAR"))
        values = [site["tot"] for site in outcar.magnetization]
        noncollinear = (bool(getattr(outcar, "noncollinear", False))
            or _boolean(parameters.get("LNONCOLLINEAR", False)) or _boolean(parameters.get("LSORBIT", False)))
        raw["noncollinear"] = noncollinear
        moments = [list(map(float, value.moment if hasattr(value, "moment") else value))
                   if noncollinear else float(value) for value in values]
        flattened = [component for value in moments for component in value] if noncollinear else moments
        if (len(moments) != len(elements) or not all(math.isfinite(m) for m in flattened)
                or noncollinear and any(len(value) != 3 for value in moments)):
            raise ValueError("missing, incomplete or nonfinite final magnetization table")
        raw.update(status="available", moments=moments,
            sites=[{"atom_index": index, "element": element, "moment": moment}
                   for index, (element, moment) in enumerate(zip(elements, moments))],
            total_local_moment=None if noncollinear else sum(moments),
            source="OUTCAR_final_local_projection", nupdown=parameters.get("NUPDOWN"))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        raw["read_error"] = f"{type(error).__name__}: {error}"
    return raw


def _boolean(value):
    if isinstance(value, str):
        return value.strip().upper() in {"T", "TRUE", ".TRUE.", "1"}
    return bool(value)

"""Prepare fixed-geometry, neutral Delta-SCF inputs from a converged run."""

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from monty.io import zopen
from monty.os.path import zpath
from pymatgen.electronic_structure.core import Spin
from pymatgen.io.vasp.inputs import Incar
from pymatgen.io.vasp.outputs import Chgcar, Vasprun


def generate_excited_input(
    ground_dir: str | Path,
    target_dir: str | Path,
    *,
    spin: str | None = "auto",
    valence_band: int | None = None,
    conduction_band: int | None = None,
) -> dict[str, Any]:
    """Prepare excitation inputs with spin='auto', 'up', 'down' or 'both'.

    Auto (also None) chooses the smallest same-spin band-edge gap; ties choose
    up. Explicit band indices do not change this channel-selection rule.
    Both creates independent up/ and down/ calculations below target_dir and
    returns their reports under those keys. It does not excite both channels
    in one calculation. Both requires ISPIN=2. All previous restrictions apply.
    """
    if spin not in (None, "auto", "up", "down", "both"):
        raise ValueError("spin must be 'auto', 'up', 'down' or 'both'")
    if spin != "both":
        return _generate_excited_input(ground_dir, target_dir, spin=spin,
                                      valence_band=valence_band, conduction_band=conduction_band)
    target = Path(target_dir).resolve()
    if target == Path(ground_dir).resolve():
        raise ValueError("Ground and target directories must differ")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Target directory must be absent or empty")
    # Validate both configurations before writing either one.
    for channel in ("up", "down"):
        _generate_excited_input(ground_dir, target / channel, spin=channel,
                                valence_band=valence_band, conduction_band=conduction_band,
                                _validate_only=True)
    return {channel: _generate_excited_input(
        ground_dir, target / channel, spin=channel,
        valence_band=valence_band, conduction_band=conduction_band,
    ) for channel in ("up", "down")}


def _generate_excited_input(
    ground_dir: str | Path,
    target_dir: str | Path,
    *,
    spin: str | None = None,
    valence_band: int | None = None,
    conduction_band: int | None = None,
    _validate_only: bool = False,
) -> dict[str, Any]:
    """Generate VASP inputs for a one-electron, same-spin vertical excitation.

    Supports collinear, insulating single-Gamma calculations only. Bands are
    1-based. Omit both bands to select the highest occupied and lowest empty
    state in the chosen spin channel. ISPIN=1 uses half occupations to transfer one electron with
    spin degeneracy; this is a spin-averaged configuration, not a pure singlet.
    Fractional ground occupations and degenerate automatic edge choices are
    rejected. Target must be absent or empty; source files are never changed.

    Requires INCAR, POTCAR, WAVECAR, CHGCAR, vasprun.xml and KPOINTS unless
    KSPACING was used. Compressed files are streamed into uncompressed inputs.
    Return metadata also written to excitation.json. No VASP is launched.
    """
    source = Path(ground_dir).resolve()
    target = Path(target_dir).resolve()
    if source == target:
        raise ValueError("Ground and target directories must differ")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Target directory must be absent or empty")
    if (valence_band is None) != (conduction_band is None):
        raise ValueError("Provide both valence_band and conduction_band, or neither")

    files = {}
    for name in ("INCAR", "POTCAR", "WAVECAR", "CHGCAR", "vasprun.xml"):
        path = Path(zpath(source / name))
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Required ground-state file missing or empty: {path}")
        files[name] = path
    run = Vasprun(files["vasprun.xml"], parse_dos=False, parse_eigen=True,
                  parse_projected_eigen=False, parse_potcar_file=False)
    if not run.converged_electronic:
        raise ValueError("Ground-state electronic calculation is not converged")
    incar = Incar.from_file(files["INCAR"])
    if run.parameters.get("LNONCOLLINEAR", False) or run.parameters.get("LSORBIT", False):
        raise ValueError("Noncollinear/SOC calculations are not supported")
    points = np.asarray(run.actual_kpoints, dtype=float)
    weights = np.asarray(run.actual_kpoints_weights, dtype=float)
    if points.shape != (1, 3) or not np.allclose(points, 0) or weights.shape != (1,) or not np.isclose(weights[0], 1):
        raise ValueError("Only a single Gamma point of weight 1 is supported; multi-k excitation requires a separate occupation strategy")
    eigen = run.eigenvalues
    polarized = Spin.down in eigen
    if not polarized and spin == "down":
        raise ValueError("ISPIN=1 has no separate down-spin channel")
    selected = Spin.down if spin == "down" else Spin.up
    capacity = 1.0 if polarized else 2.0
    nbands = eigen[Spin.up].shape[1]
    occupations = {}
    for channel, values in eigen.items():
        if values.shape != (1, nbands, 2):
            raise ValueError("Unexpected eigenvalue dimensions")
        occ = values[0, :, 1] / capacity
        if not np.all(np.isclose(occ, 0, atol=1e-5) | np.isclose(occ, 1, atol=1e-5)):
            raise ValueError("Ground occupations must be integer; fractional/metallic occupations are unsupported")
        occupations[channel] = np.rint(occ)
    channel_gaps = {}
    for channel, values in occupations.items():
        filled = np.flatnonzero(values == 1)
        vacant = np.flatnonzero(values == 0)
        if not len(filled) or not len(vacant):
            raise ValueError(f"Need occupied and empty states in {channel.name}; increase ground NBANDS")
        levels = eigen[channel][0, :, 0]
        gap = float(levels[vacant].min() - levels[filled].max())
        if not np.isfinite(gap) or gap <= 0:
            raise ValueError(f"Nonpositive or invalid band-edge gap in {channel.name}")
        channel_gaps["up" if channel == Spin.up else "down"] = gap
    if spin in (None, "auto"):
        spin = min(channel_gaps, key=channel_gaps.get) if polarized else None
        selected = Spin.down if spin == "down" else Spin.up
    energies = eigen[selected][0, :, 0]
    occupied = np.flatnonzero(occupations[selected] == 1)
    empty = np.flatnonzero(occupations[selected] == 0)
    if not len(occupied) or not len(empty):
        raise ValueError("Need occupied states and empty bands; increase ground-state NBANDS if necessary")
    if valence_band is None:
        vb = occupied[np.argmax(energies[occupied])]
        cb = empty[np.argmin(energies[empty])]
        if any(np.count_nonzero(np.isclose(energies[indices], energies[edge], atol=1e-4, rtol=0)) > 1
               for indices, edge in ((occupied, vb), (empty, cb))):
            raise ValueError("Degenerate band edges: explicitly select valence_band and conduction_band")
    else:
        if any(not isinstance(band, int) or isinstance(band, bool) or not 1 <= band <= nbands
               for band in (valence_band, conduction_band)):
            raise ValueError(f"Band indices must be integers in 1..{nbands}")
        vb, cb = valence_band - 1, conduction_band - 1
    if occupations[selected][vb] != 1 or occupations[selected][cb] != 0 or energies[cb] <= energies[vb]:
        raise ValueError("Choose an occupied valence state and a higher-energy empty conduction state")
    before = sum(capacity * values.sum() for values in occupations.values())
    if not np.isclose(before, float(run.parameters["NELECT"]), atol=1e-4):
        raise ValueError("Ground occupations do not reproduce NELECT")
    occupations[selected][vb] -= 1 / capacity
    occupations[selected][cb] += 1 / capacity

    kpoints_path = Path(zpath(source / "KPOINTS"))
    if not kpoints_path.is_file() and "KSPACING" not in incar:
        raise FileNotFoundError("Need ground KPOINTS or an INCAR KSPACING setting")
    charge = Chgcar.from_file(files["CHGCAR"])
    if charge.structure != run.final_structure:
        raise ValueError("CHGCAR structure differs from the final XML structure")
    grid = charge.data["total"].shape
    for tag in ("FERWE", "FERDO", "LPARD", "IBAND", "EINT", "NBMOD", "KPUSE", "LSEPB", "LSEPK"):
        incar.pop(tag, None)
    incar.update({"ISTART": 1, "ICHARG": 1, "NSW": 0, "IBRION": -1,
                  "ISMEAR": -2, "ALGO": "All", "LDIAG": False,
                  "LWAVE": True, "LCHARG": True, "NBANDS": nbands,
                  "NELECT": float(run.parameters["NELECT"]),
                  "ISPIN": 2 if polarized else 1,
                  "FERWE": occupations[Spin.up].tolist(),
                  **dict(zip(("NGXF", "NGYF", "NGZF"), map(int, grid)))})
    if polarized:
        incar["FERDO"] = occupations[Spin.down].tolist()
    report = {"ground_dir": str(source), "target_dir": str(target),
              "spin": spin or "spin_averaged", "valence_band": int(vb + 1),
              "conduction_band": int(cb + 1), "electrons_promoted": 1,
              "NELECT": before, "NBANDS": nbands, "fft_grid": list(grid),
              "ground_state_level_gap_eV": float(energies[cb] - energies[vb]),
              "channel_gaps_eV": channel_gaps,
              "note": "Fixed-geometry Delta-SCF inputs; verify final state occupations and actual NBANDS. Keep the ground-state functional and parallel settings. No excited-state convergence is guaranteed."}
    if _validate_only:
        return report
    target.mkdir(parents=True, exist_ok=True)
    try:
        for name in ("POTCAR", "WAVECAR", "CHGCAR"):
            with zopen(files[name], "rb") as src, (target / name).open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
        if kpoints_path.is_file():
            with zopen(kpoints_path, "rb") as src, (target / "KPOINTS").open("wb") as dst:
                shutil.copyfileobj(src, dst)
        run.final_structure.to(fmt="poscar", filename=target / "POSCAR")
        incar.write_file(target / "INCAR")
        (target / "excitation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        # Remove only the files this call created in the previously empty target.
        for name in ("INCAR", "POSCAR", "POTCAR", "KPOINTS", "WAVECAR", "CHGCAR", "excitation.json"):
            (target / name).unlink(missing_ok=True)
        raise
    return report

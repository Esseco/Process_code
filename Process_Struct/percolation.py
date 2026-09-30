"""Geometric percolation screening with the installed CCNB/CAVD library.

Run this module with the ``ccnb`` Python environment.
"""

from __future__ import annotations

import gc
import math
import shutil
import time
import warnings
from uuid import uuid4
from pathlib import Path
from typing import Any

from pymatgen.core import Element, Structure


def _load_structure(value: Structure | str | Path) -> Structure:
    if isinstance(value, Structure):
        return value
    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Structure file not found: {path}")
    return Structure.from_file(str(path))


def _analyze(
    structure: Structure,
    migrant: str | None,
    cutoff_radius: float,
    work_dir: Path,
    keep_files: bool,
    oxidation_states_guessed: bool,
) -> dict[str, Any]:
    from cavd import ConnStatus

    cif_path = work_dir / "structure.cif"
    structure.to(filename=str(cif_path), fmt="cif")

    if migrant is None:
        from monty.io import zopen
        from cavd.channel import Channel
        from cavd.get_Symmetry import get_labeled_vornet
        from cavd.local_environment import CifParser_new, get_local_envir_fromstru
        from cavd.netio import writeNETFile
        from cavd.netstorage import AtomNetwork, connection_values_list

        # Follow CAVD's ChannelCom path, retaining all atoms. Its VESTA
        # exporter is skipped because it can fail after channel calculation.
        with zopen(str(cif_path), "rt") as handle:
            parser = CifParser_new.from_string(handle.read())
        parsed_cif = parser.get_structures(primitive=False)[0]
        _, radii = get_local_envir_fromstru(parsed_cif)
        atom_network = AtomNetwork.read_from_CIF(
            str(cif_path), radii, True
        )
        voronoi_network, _, _, faces = (
            atom_network.perform_voronoi_decomposition(True)
        )
        network_with_faces = voronoi_network.add_facecenters(faces)
        symmetric_network, _ = get_labeled_vornet(
            network_with_faces, parser.get_sym_opt(), 0.01
        )
        prefix = str(cif_path.with_suffix(""))
        writeNETFile(prefix + "_origin.net", atom_network, symmetric_network)
        connection_values = [
            float(value)
            for value in connection_values_list(
                prefix + ".resex", symmetric_network
            )
        ]
        dimension, connected_axes = ConnStatus(
            connection_values, cutoff_radius, float("inf")
        )
        channels = Channel.findChannels(
            symmetric_network, atom_network, cutoff_radius,
            prefix + ".net",
        )
        channel_dimensions = [
            int(channel["dim"]) for channel in channels
        ]
        result: dict[str, Any] = {
            "mode": "geometric_voids",
            "percolation_dimension": int(dimension),
            "channel_dimensions": channel_dimensions,
            "connection_values_A": connection_values,
            "connection_values_by_axis_A": dict(zip("abc", connection_values)),
            "connected_axes": dict(zip("abc", map(bool, connected_axes))),
        }
    else:
        from ccnb import cal_channel_cavd

        # CCNB removes the specified mobile species from the framework.
        connection_values = [
            float(value)
            for value in cal_channel_cavd(
                str(cif_path),
                migrant,
                lower=cutoff_radius,
                upper=max(10.0, cutoff_radius),
                save_dir=work_dir,
            )
        ]
        dimension, connected_axes = ConnStatus(
            connection_values, cutoff_radius, float("inf")
        )
        result = {
            "mode": "migrant_removed",
            "percolation_dimension": int(dimension),
            "channel_dimensions": None,
            "connection_values_A": connection_values,
            "connection_values_by_axis_A": dict(zip("abc", connection_values)),
            "connected_axes": dict(zip("abc", map(bool, connected_axes))),
        }

    result.update(
        {
            "formula": structure.composition.reduced_formula,
            "oxidation_states_guessed": oxidation_states_guessed,
            "migrant": migrant,
            "cutoff_radius_A": cutoff_radius,
            "percolates": result["percolation_dimension"] > 0,
            "output_directory": str(work_dir) if keep_files else None,
            "artifacts": (
                sorted(str(path) for path in work_dir.iterdir() if path.is_file())
                if keep_files
                else []
            ),
        }
    )
    return result


def _remove_work_dir(work_dir: Path, root: Path) -> None:
    """Remove a temporary directory, retrying transient Windows file locks."""
    resolved_root = root.resolve()
    resolved_work_dir = work_dir.resolve()
    if not resolved_work_dir.is_relative_to(resolved_root):
        raise RuntimeError("Temporary analysis directory escaped the project.")

    delays = (0.0, 0.1, 0.25, 0.5, 1.0)
    last_error: OSError | None = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        if not work_dir.exists():
            return
        try:
            shutil.rmtree(work_dir)
            return
        except OSError as error:
            winerror = getattr(error, "winerror", None)
            transient_lock = isinstance(error, PermissionError) or winerror in {
                5, 32, 33
            }
            if not transient_lock:
                raise
            last_error = error
            gc.collect()

    if last_error is not None:
        raise last_error


def analyze_percolation(
    structure: Structure | str | Path,
    migrant: str | None = None,
    *,
    cutoff_radius: float,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Return geometric channel connectivity at a probe radius in Å.

    ``structure`` accepts a pymatgen Structure or any file format it can read.
    An empty ``migrant`` keeps all atoms and measures the original void network.
    A specified element is removed by CCNB before channel analysis. The
    returned dimension is 0, 1, 2, or 3; it is not a migration energy barrier.
    Generated files are retained under ``output_dir`` when that is provided.
    On Windows, transient locks on generated files are retried during cleanup;
    a persistent cleanup failure is returned in ``cleanup_warning`` together
    with the remaining temporary directory path.
    """
    try:
        radius = float(cutoff_radius)
    except (TypeError, ValueError) as error:
        raise ValueError("cutoff_radius must be a nonnegative number in Å.") from error
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("cutoff_radius must be a finite nonnegative number in Å.")

    parsed_structure = _load_structure(structure)
    if not parsed_structure.is_ordered:
        raise ValueError("CCNB/CAVD requires an ordered structure.")
    has_oxidation_states = [
        hasattr(site.specie, "oxi_state") for site in parsed_structure
    ]
    if any(has_oxidation_states) and not all(has_oxidation_states):
        raise ValueError("All sites must either have oxidation states or omit them.")
    oxidation_states_guessed = not all(has_oxidation_states)
    if oxidation_states_guessed:
        parsed_structure = parsed_structure.copy()
        try:
            parsed_structure.add_oxidation_state_by_guess()
        except Exception as error:
            raise ValueError(
                "Could not infer oxidation states required by CCNB/CAVD; "
                "provide a Structure with oxidation states assigned."
            ) from error
    migrant = migrant.strip() if migrant is not None else None
    migrant = migrant or None
    if migrant is not None:
        try:
            Element(migrant)
        except ValueError as error:
            raise ValueError(f"Invalid migrant element: {migrant!r}") from error
        if migrant not in parsed_structure.symbol_set:
            raise ValueError(f"{migrant} is absent from the input structure.")

    keep_files = output_dir is not None
    root = (
        Path(output_dir).expanduser().resolve()
        if keep_files
        else Path(__file__).resolve().parent
    )
    root.mkdir(parents=True, exist_ok=True)
    work_dir = root / f"ccnb_percolation_{uuid4().hex}"
    work_dir.mkdir()
    if keep_files:
        return _analyze(
            parsed_structure, migrant, radius, work_dir, True,
            oxidation_states_guessed,
        )
    try:
        result = _analyze(
            parsed_structure, migrant, radius, work_dir, False,
            oxidation_states_guessed,
        )
    except BaseException:
        try:
            _remove_work_dir(work_dir, root)
        except OSError as cleanup_error:
            warnings.warn(
                f"Could not remove temporary CCNB directory {work_dir}: "
                f"{cleanup_error}",
                RuntimeWarning,
                stacklevel=2,
            )
        raise

    try:
        _remove_work_dir(work_dir, root)
    except OSError as cleanup_error:
        result["cleanup_status"] = "failed"
        result["cleanup_warning"] = str(cleanup_error)
        result["output_directory"] = str(work_dir)
        try:
            result["artifacts"] = sorted(
                str(path) for path in work_dir.iterdir() if path.is_file()
            )
        except OSError:
            result["artifacts"] = []
    return result

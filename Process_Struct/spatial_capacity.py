"""CCNB interstitial-site capacity estimate; use the existing ccnb environment."""
from __future__ import annotations

import math
import time
from pathlib import Path
from uuid import uuid4
import warnings

import numpy as np
from pymatgen.core import Element, Structure

from .ccnb_net import read_channel_net
from .percolation import _load_structure, _remove_work_dir, analyze_percolation

FARADAY_OVER_3P6 = 26801.481145  # mAh per mole of electrons


def _pack_sites(lattice, sites, min_distance):
    """One radius-priority greedy pass without an N-by-N distance matrix."""
    if not sites:
        return []
    # Every occupied site repeats in adjacent cells. Check its own images too,
    # including non-axis translations in skew lattices.
    neighbors = lattice.get_points_in_sphere([[0, 0, 0]], [0, 0, 0], min_distance)
    if any(1e-8 < float(item[1]) < min_distance - 1e-8 for item in neighbors):
        raise ValueError(
            "The cell has a lattice translation shorter than min_site_distance_A; "
            "use a larger supercell to permit a partially occupied periodic pattern."
        )
    coords = np.asarray([site["frac_coords"] for site in sites]) % 1.0
    count = len(sites)
    priority = sorted(range(count), key=lambda i: (
        -sites[i]["radius_A"], sites[i]["node_id"], i
    ))
    available = np.ones(count, dtype=bool)
    chosen = []
    for site in priority:
        if not available[site]:
            continue
        chosen.append(site)
        available[site] = False
        remaining = np.flatnonzero(available)
        if len(remaining):
            # Only a 1-by-remaining row is needed. pymatgen handles the true
            # minimum image, including skew cells; no approximate distances.
            distances = lattice.get_all_distances(
                coords[site:site + 1], coords[remaining]
            )[0]
            available[remaining[distances < min_distance - 1e-8]] = False
    return [sites[i] for i in sorted(chosen)]


def estimate_spatial_capacity(
    structure: Structure | str | Path,
    mobile_ion: str = "Na",
    *,
    cutoff_radius: float = 0.8,
    min_site_distance_A: float = 2.0,
    output_dir: str | Path | None = None,
    verbose: bool = True,
) -> dict:
    """Estimate feasible loading of CCNB percolating-channel sites in mAh/g.

    Input: ordered Structure or readable structure file; Li/Na is removed by
    CCNB. First find channels at cutoff_radius (angstrom), then use only nodes
    in their 1D/2D/3D percolating components, with free radius >= cutoff_radius.
    Isolated voids and 0D components are excluded; no percolating channel means
    zero capacity. Repeated periodic positions are counted once. Bottleneck
    points are not storage sites; equivalent labels do not collapse different
    positions. Pair distances include periodic boundaries and must be >=
    min_site_distance_A (default 2 angstrom).

    One deterministic radius-priority greedy pass returns a feasible site count,
    using distance rows instead of a full matrix. It is NOT a proven
    maximum or an experimental reversible capacity. Each selected site holds
    one monovalent Li/Na. Default mass basis is framework + selected ions:
    Q = 26801.481145 * N / (M_framework + N * M_ion), using the input cell's
    composition and site count. Input-mass and framework-mass bases are also
    returned. Geometric percolation is required, but charge balance, site energy
    and migration barriers are not evaluated.

    Run in ccnb. No random seed is used. CCNB writes a unique temporary folder;
    default cleanup preserves the returned data on lock failure. output_dir
    retains a new unique folder each run; existing results are not overwritten.
    verbose prints elapsed CCNB and packing stages; set False to silence them.
    """
    if mobile_ion not in {"Li", "Na"}:
        raise ValueError("mobile_ion must be Li or Na.")
    radius = float(cutoff_radius)
    separation = float(min_site_distance_A)
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("cutoff_radius must be finite and nonnegative in angstrom.")
    if not math.isfinite(separation) or separation <= 0:
        raise ValueError("min_site_distance_A must be finite and positive.")
    parsed = _load_structure(structure)
    composition = parsed.composition.element_composition
    amounts = composition.get_el_amt_dict()
    initial_mobile_count = amounts.pop(mobile_ion, 0.0)
    framework_mass = sum(float(Element(element).atomic_mass) * amount
                         for element, amount in amounts.items())
    if framework_mass <= 0:
        raise ValueError("Structure must contain a nonempty framework.")

    # Reuse the existing CCNB adapter and its Windows file-lock cleanup policy.
    parent = (Path(output_dir).expanduser().resolve() if output_dir is not None
              else Path(__file__).resolve().parent)
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / f"ccnb_spatial_capacity_{uuid4().hex}"
    root.mkdir()
    result = None
    try:
        started = time.perf_counter()
        if verbose:
            print("空间容量：开始 CCNB 网络计算……", flush=True)
        percolation = analyze_percolation(
            parsed, migrant=mobile_ion, cutoff_radius=radius, output_dir=root,
        )
        ccnb_seconds = time.perf_counter() - started
        if verbose:
            print(f"空间容量：CCNB 完成，用时 {ccnb_seconds:.1f} 秒", flush=True)
        network_folder = Path(percolation["output_directory"])
        # This file is filtered by CCNB's channel search at the requested
        # cutoff. The original NET includes inaccessible/isolated voids.
        sites, _ = read_channel_net(network_folder / "structure.net")
        channel_dimensions = {}
        unique_sites = {}
        for site in sites:
            dimension = site["dimension"]
            if dimension not in {0, 1, 2, 3}:
                raise ValueError("CCNB channel NET lacks a valid dimensionality.")
            if dimension == 0:
                continue
            channel_dimensions[site["channel_id"]] = dimension
            if site["radius_A"] < radius:
                continue
            folded = np.asarray(site["frac_coords"], dtype=float) % 1.0
            # NET coordinates have finite precision. Canonicalize periodic
            # endpoints and repeated positions, not crystallographic labels.
            key = tuple(float(value) % 1.0 for value in np.round(folded, 6))
            previous = unique_sites.get(key)
            if previous is None or site["radius_A"] > previous["radius_A"]:
                unique_sites[key] = dict(site, frac_coords=folded.tolist())
        candidates = list(unique_sites.values())
        packing_started = time.perf_counter()
        if verbose:
            print(f"空间容量：筛选 {len(candidates)} 个候选位点……", flush=True)
        selected = _pack_sites(parsed.lattice, candidates, separation)
        packing_seconds = time.perf_counter() - packing_started
        if verbose:
            print(f"空间容量：保留 {len(selected)} 个位点，筛选用时 {packing_seconds:.1f} 秒", flush=True)
        count = len(selected)
        packed_mass = framework_mass + count * float(Element(mobile_ion).atomic_mass)
        electron_charge = FARADAY_OVER_3P6 * count
        result = {
            "capacity_mAh_g": electron_charge / packed_mass,
            "capacity_mAh_g_framework_mass_basis": electron_charge / framework_mass,
            "capacity_mAh_g_input_mass_basis": electron_charge / float(composition.weight),
            "site_count_per_cell": count,
            "candidate_count_per_cell": len(candidates),
            "selected_sites": selected,
            "mobile_ion": mobile_ion,
            "initial_mobile_count_per_cell": initial_mobile_count,
            "framework_mass_g_mol_cell": framework_mass,
            "packed_mass_g_mol_cell": packed_mass,
            "cutoff_radius_A": radius,
            "min_site_distance_A": separation,
            "method": "single_pass_radius_priority_greedy",
            "maximum_proven": False,
            "timings_seconds": {"ccnb": ccnb_seconds, "packing": packing_seconds},
            "candidate_network": "percolating_channels_only",
            "percolating_channel_count": len(channel_dimensions),
            "channel_dimensions": list(channel_dimensions.values()),
            "output_directory": str(network_folder) if output_dir is not None else None,
            "percolation_dimension": max(channel_dimensions.values(), default=0),
        }
        return result
    finally:
        if output_dir is None:
            try:
                _remove_work_dir(root, parent)
            except OSError as error:
                if result is not None:
                    result.update(cleanup_warning=str(error), output_directory=str(root))
                else:
                    warnings.warn(f"Temporary CCNB files remain at {root}: {error}")

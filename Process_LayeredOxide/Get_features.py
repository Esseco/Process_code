import numpy as np
from pymatgen.core import Structure
import pandas as pd
from pathlib import Path as p
from pymatgen.analysis.local_env import CrystalNN
from collections import defaultdict

def get_layer_spacing(structure:Structure, tol:float=0.5)->dict:
    lattice = structure.lattice
    a_vec, b_vec, c_vec = lattice.matrix
    n_vec = np.cross(a_vec, b_vec)
    n_hat = n_vec / np.linalg.norm(n_vec)

    proj = sorted(
        np.dot(site.coords, n_hat)
        for site in structure
        if site.specie.symbol == "O"
    )

    layers = [[proj[0]]]
    for z in proj[1:]:
        if abs(z - layers[-1][-1]) < tol:
            layers[-1].append(z)
        else:
            layers.append([z])

    z_mean = np.array([np.mean(l) for l in layers])
    c_proj = abs(np.dot(c_vec, n_hat))
    spacings = np.diff(np.r_[z_mean, z_mean[0] + c_proj])
    threshold = spacings.mean()
    Na = spacings[spacings > threshold]
    TM = spacings[spacings <= threshold]

    return {
        "Na_layer_avg": Na.mean() if Na.size else None,
        "TM_layer_avg": TM.mean() if TM.size else None,
        "Na_layers": Na.tolist(),
        "TM_layers": TM.tolist()
    }

def get_bond_lengths(structure:Structure)->dict:
    cnn = CrystalNN()
    bond_dict = defaultdict(list)
    for i, site in enumerate(structure):
        neighbors = cnn.get_nn_info(structure, i)
        for nn in neighbors:
            j = nn['site_index']
            if i < j:
                site_i = structure[i]
                site_j = structure[j]
                elem_i = site_i.specie.symbol
                elem_j = site_j.specie.symbol
                pair = "-".join(sorted([elem_i, elem_j]))
                dist = site_i.distance(site_j)
                bond_dict[pair].append(dist)
    return dict(bond_dict)

import numpy as np

def _cluster_periodic_1d(values, tol=0.05):
    """
    Cluster fractional coordinates on a periodic 1D circle [0, 1).

    Parameters
    ----------
    values : array-like
        Fractional z coordinates in [0, 1).
    tol : float
        Tolerance for grouping layers in fractional coordinate.

    Returns
    -------
    centers : np.ndarray
        Layer centers in fractional z.
    labels : np.ndarray
        Layer label for each input value.
    """
    values = np.mod(np.asarray(values, dtype=float), 1.0)
    n = len(values)

    if n == 0:
        return np.array([]), np.array([], dtype=int)

    order = np.argsort(values)
    z_sorted = values[order]

    # Find gaps on periodic circle.
    gaps = np.diff(z_sorted)
    wrap_gap = z_sorted[0] + 1.0 - z_sorted[-1]
    gaps_all = np.concatenate([gaps, [wrap_gap]])

    # Break at the largest gap, so a layer crossing 0/1 is not split.
    break_idx = int(np.argmax(gaps_all))

    if break_idx == n - 1:
        z_unwrapped = z_sorted.copy()
    else:
        z_unwrapped = np.concatenate([
            z_sorted[break_idx + 1:],
            z_sorted[:break_idx + 1] + 1.0
        ])

    original_indices_unwrapped_order = np.concatenate([
        order[break_idx + 1:],
        order[:break_idx + 1]
    ]) if break_idx != n - 1 else order

    # Cluster linearly after unwrapping.
    clusters = []
    current = [0]

    for i in range(1, n):
        if np.abs(z_unwrapped[i] - np.mean(z_unwrapped[current])) <= tol:
            current.append(i)
        else:
            clusters.append(current)
            current = [i]
    clusters.append(current)

    centers = []
    labels = np.empty(n, dtype=int)

    for label, inds in enumerate(clusters):
        center = np.mean(z_unwrapped[inds]) % 1.0
        centers.append(center)

        for ii in inds:
            original_idx = original_indices_unwrapped_order[ii]
            labels[original_idx] = label

    centers = np.array(centers)

    # Sort layers by z center.
    sort_layer = np.argsort(centers)
    remap = {old: new for new, old in enumerate(sort_layer)}

    centers_sorted = centers[sort_layer]
    labels_sorted = np.array([remap[x] for x in labels], dtype=int)

    return centers_sorted, labels_sorted


def row_factor(
    prim_struct,
    struct,
    species=("Fe", "Mn"),
    sigma_map=None,
    layer_tol=0.05,
    demean=True,
    normalize="n2",
    return_complex=False,
):
    """
    Calculate layer-resolved row-order structure factors at the three M points
    of the primitive triangular TM lattice.

    This is useful for detecting row-like / stripe-like Fe-Mn ordering
    in layered oxides.

    Parameters
    ----------
    prim_struct : pymatgen Structure
        Primitive reference structure. Its reciprocal lattice defines b1, b2.
        The first two reciprocal lattice vectors are assumed to span the TM layer.

    struct : pymatgen Structure
        Supercell or relaxed structure containing Fe and Mn.

    species : tuple[str, str]
        The two TM species to analyze. Default is ("Fe", "Mn").

    sigma_map : dict or None
        Mapping from element symbol to occupation variable.
        Default: {"Fe": +1.0, "Mn": -1.0}.

    layer_tol : float
        Tolerance for grouping TM atoms into layers, in fractional z of `struct`.

    demean : bool
        If True, subtract layer mean from sigma before calculating structure
        factors. This removes composition background when Fe:Mn is not exactly 1:1
        within each layer.

    normalize : {"n2", "n", "none"}
        Normalization of intensity |A|^2.
        - "n2": |A|^2 / n^2, bounded roughly by 0 to 1.
        - "n" : |A|^2 / n, useful as scattering-like normalization.
        - "none": raw |A|^2.

    return_complex : bool
        If True, return complex amplitudes as real/imag pairs.

    Returns
    -------
    dict
        {
            "M_cart": list of M-point Cartesian vectors,
            "layers": [
                {
                    "z": layer center,
                    "n": number of Fe/Mn atoms in layer,
                    "counts": {"Fe": ..., "Mn": ...},
                    "composition": {"Fe": ..., "Mn": ...},
                    "mean_sigma": ...,
                    "M1": intensity,
                    "M2": intensity,
                    "M3": intensity,
                    "sum": M1 + M2 + M3,
                    optionally "amp_M1": [real, imag], ...
                },
                ...
            ],
            "row_factor": average of layer sums,
            "row_factor_std": std of layer sums
        }

    Notes
    -----
    The phase is calculated as exp(i M · r), where M is from the primitive
    reciprocal lattice and r is the Cartesian coordinate in the supercell.
    """

    if sigma_map is None:
        sigma_map = {
            species[0]: 1.0,
            species[1]: -1.0,
        }

    valid_species = set(species)

    # ---------- M points from primitive reciprocal lattice ----------
    rec = np.asarray(prim_struct.lattice.reciprocal_lattice.matrix, dtype=float)

    if rec.shape != (3, 3):
        raise ValueError("Primitive reciprocal lattice matrix should be 3x3.")

    b1, b2 = rec[0], rec[1]

    M_list = [
        0.5 * b1,
        0.5 * b2,
        0.5 * (b1 + b2),
    ]

    # ---------- TM selection ----------
    coords = []
    frac_coords = []
    sigmas = []
    symbols = []

    for site in struct:
        sym = site.specie.symbol

        if sym in valid_species:
            if sym not in sigma_map:
                raise ValueError(f"Missing sigma value for species {sym}.")

            coords.append(site.coords)
            frac_coords.append(site.frac_coords)
            sigmas.append(float(sigma_map[sym]))
            symbols.append(sym)

    if len(coords) == 0:
        raise ValueError(f"No atoms with species {species} found in struct.")

    coords = np.asarray(coords, dtype=float)
    frac_coords = np.mod(np.asarray(frac_coords, dtype=float), 1.0)
    sigmas = np.asarray(sigmas, dtype=float)
    symbols = np.asarray(symbols)

    z = frac_coords[:, 2]

    # ---------- layer splitting ----------
    layer_centers, layer_labels = _cluster_periodic_1d(z, tol=layer_tol)
    n_layers = len(layer_centers)

    layer_results = []
    layer_scores = []

    # ---------- structure factor layer by layer ----------
    for layer_idx in range(n_layers):
        mask = layer_labels == layer_idx

        r_layer = coords[mask]
        sigma_layer_raw = sigmas[mask]
        symbols_layer = symbols[mask]
        n = len(sigma_layer_raw)

        if n == 0:
            continue

        counts = {
            sp: int(np.sum(symbols_layer == sp))
            for sp in species
        }

        composition = {
            sp: counts[sp] / n
            for sp in species
        }

        mean_sigma = float(np.mean(sigma_layer_raw))

        if demean:
            sigma_layer = sigma_layer_raw - mean_sigma
        else:
            sigma_layer = sigma_layer_raw.copy()

        m_dict = {
            "z": float(layer_centers[layer_idx]),
            "n": int(n),
            "counts": counts,
            "composition": composition,
            "mean_sigma": mean_sigma,
        }

        layer_sum = 0.0

        for i, M in enumerate(M_list, start=1):
            amp = np.sum(sigma_layer * np.exp(1j * (r_layer @ M)))
            intensity = np.abs(amp) ** 2

            if normalize == "n2":
                intensity /= n ** 2
            elif normalize == "n":
                intensity /= n
            elif normalize == "none":
                pass
            else:
                raise ValueError("normalize must be one of {'n2', 'n', 'none'}.")

            intensity = float(np.real_if_close(intensity))
            m_dict[f"M{i}"] = intensity
            layer_sum += intensity

            if return_complex:
                m_dict[f"amp_M{i}"] = [float(np.real(amp)), float(np.imag(amp))]

        m_dict["sum"] = float(layer_sum)

        layer_results.append(m_dict)
        layer_scores.append(layer_sum)

    if len(layer_scores) == 0:
        raise ValueError("No valid TM layers were found.")

    return {
        "M_cart": [M.tolist() for M in M_list],
        "n_layers": int(len(layer_results)),
        "layers": layer_results,
        "row_factor": float(np.mean(layer_scores)),
        "row_factor_std": float(np.std(layer_scores)),
        "settings": {
            "species": list(species),
            "sigma_map": dict(sigma_map),
            "layer_tol": layer_tol,
            "demean": demean,
            "normalize": normalize,
        },
    }


def get_na_o_cn(struct, cutoff=3.0, return_index=False):
    structure = struct

    na_indices = [
        i for i, site in enumerate(structure)
        if site.specie.symbol == "Na"
    ]

    na_sites = [structure[i] for i in na_indices]

    all_neighbors = structure.get_all_neighbors(
        r=cutoff,
        sites=na_sites,
        include_index=True,
    )

    results = {}

    for na_index, neighbors in zip(na_indices, all_neighbors):
        o_indices = [
            nn.index for nn in neighbors
            if nn.specie.symbol == "O"
        ]

        if return_index:
            results[na_index] = {
                "CN": len(o_indices),
                "O_index": o_indices,
            }
        else:
            results[na_index] = len(o_indices)

    return results

from pymatgen.core import Composition


def get_oxi_states(struct, init_oxi, redox_order):
    comp = struct.composition.get_el_amt_dict()
    oxi = init_oxi.copy()

    charge = sum(comp[e] * oxi[e] for e in comp)
    holes = -charge

    for el, target in redox_order:
        if holes <= 1e-8:
            break

        n = comp.get(el, 0)
        if n == 0:
            continue

        cap = n * (target - oxi[el])
        use = min(holes, cap)

        oxi[el] += use / n
        holes -= use

    if abs(holes) > 1e-6:
        raise ValueError(f"Not enough redox capacity, remaining holes = {holes}")

    return oxi
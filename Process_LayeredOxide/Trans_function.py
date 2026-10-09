import numpy as np
from pymatgen.core import Structure

def group_by_z(structure: Structure, species_list: list, tolerance=0.1) -> tuple:
    indices = [i for i, site in enumerate(structure) if site.specie.symbol in species_list]
    if not indices: return [], []

    z_coords = np.array([structure[i].frac_coords[2] for i in indices])
    sort_idx = np.argsort(z_coords)
    sorted_indices = np.array(indices)[sort_idx]
    sorted_z = z_coords[sort_idx]

    diffs = np.diff(sorted_z)
    split_indices = np.where(diffs > tolerance)[0] + 1
    groups = [list(g) for g in np.split(sorted_indices, split_indices)]
    
    if len(groups) > 1:
        gap = (sorted_z[0] + 1.0) - sorted_z[-1]
        if gap < tolerance:
            groups[0] = list(groups[-1]) + list(groups[0])
            groups.pop()

    layer_centers = []
    for g in groups:
        zs = np.array([structure[i].frac_coords[2] for i in g])
        if np.ptp(zs) > 0.5: 
            zs = np.where(zs > 0.5, zs - 1.0, zs)
        layer_centers.append(np.mean(zs) % 1.0)
    return groups, layer_centers


from Process_Struct import Octahedron
from pymatgen.analysis.local_env import  CrystalNN
import octadist as oc
import pandas as pd
import numpy as np
from pymatgen.core.periodic_table import Element

def sanitize_for_json(df):
    def convert(x):
        if isinstance(x, np.generic):
            return x.item()
        elif isinstance(x, np.ndarray):
            return x.tolist()
        elif hasattr(x, "item"):
            try:
                return x.item()
            except Exception:
                return x
        return x
    if hasattr(df, 'map'):
        return df.map(convert)
    else:
        return df.applymap(convert)

def analyze_octahedra_distortion(
    struct,
    TM_elements=["Fe", "Mn"],
    cutoff_O=2.5,
    cutoff_TM1=3.5,
    cutoff_TM2=5.5,
    ligands_max_dist=3.0
):

    cnn = CrystalNN()

    if TM_elements is None:
        TM_elements = [el.symbol for el in Element if el.is_transition_metal]
    TM_set = set(TM_elements)

    symbols = [site.specie.symbol for site in struct]
    TM_indices = [i for i, s in enumerate(symbols) if s in TM_set]

    if not TM_indices:
        return []

    all_neighbors = struct.get_all_neighbors(
        cutoff_TM2, sites=[struct[i] for i in TM_indices]
    )

    results = []

    for idx, (i, neighbors) in enumerate(zip(TM_indices, all_neighbors)):
        site = struct[i]
        O_neighbors = []
        TM_1NN = []
        TM_2NN = []

        for nn in neighbors:
            j = nn.index
            if j == i:
                continue

            dist = nn.nn_distance
            el_j = symbols[j]

            if el_j == "O":
                if dist <= cutoff_O:
                    O_neighbors.append(j)

            elif el_j in TM_set:
                if dist <= cutoff_TM1:
                    TM_1NN.append(j)
                elif dist <= cutoff_TM2:
                    TM_2NN.append(j)

        distortion_data = {}

        try:
            nn_info = cnn.get_nn_info(struct, i)
            o_neighbors_info = [
                n for n in nn_info if n['site'].specie.symbol == "O"
            ]

            if len(o_neighbors_info) >= 6:
                o_neighbors_info.sort(
                    key=lambda x: x['site'].distance(site)
                )
                o_neighbors_info = o_neighbors_info[:6]

                coords = [site.coords.tolist()] + [
                    n['site'].coords.tolist() for n in o_neighbors_info
                ]

                dist = oc.CalcDistortion(coords)

                octa = Octahedron(
                    core_site=site,
                    structure=struct,
                    ligands_max_distance=ligands_max_dist
                )

                distortion_data = {
                    "d_avg": dist.d_mean,
                    "Oct_vol": octa.volume,
                    "D_len": dist.zeta,
                    "D_tilt": dist.delta,
                    "D_ang": dist.sigma,
                    "D_tors": dist.theta,
                    "Q_elong": octa.calculate_quadratic_elongation(),
                    "Var_ang": octa.calculate_bond_angle_variance()
                }

                q_modes = octa.calculate_van_vleck_distortion_modes()
                for k, v in enumerate(q_modes, 1):
                    distortion_data[f"Q{k}"] = v

        except Exception as e:
            print(f"[Distortion Error] index {i}: {e}")

        results.append({
            "tm_index": i,
            "tm_element": site.specie.symbol,
            "O_neighbors": sorted(O_neighbors),
            "TM_1NN": sorted(TM_1NN),
            "TM_2NN": sorted(TM_2NN),

            **distortion_data
        })

    return results
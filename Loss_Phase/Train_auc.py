import numpy as np
import pandas as pd
from pathlib import Path as p
from pymatgen.core.structure import Structure, Composition
from pymatgen.entries.computed_entries import ComputedStructureEntry, ComputedEntry
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from pymatgen.analysis.phase_diagram import PhaseDiagram
from chgnet.utils import read_json

COMPAT = MaterialsProject2020Compatibility(check_potcar=False)

def correct_energy(structure, vasp_energy):
    try:
        atom_num = structure.num_sites
        params = {'hubbards': {'Na': 0, 'Mn': 3.9, 'Fe': 5.3, 'Co': 3.32, 'Ni': 6.2, 'O': 0}, 'run_type': 'GGA+U'}
        cse = ComputedStructureEntry(structure, energy=vasp_energy, parameters=params)
        COMPAT.process_entries(cse)
        return cse.energy / atom_num
    except Exception as e:
        print(f'Correction err: {e}')
        return 0

def load_json_data(init_dir: p, start_index: int = 5):
    '''
    init_dir.rglob('*.json')
    keys:"structures", "energies", "forces", "stresses", "magmoms", "formula", "TM_group", "Com_group", "path", "index", "Na_con", "Fe_con", "unit_num", "phase", "file_id"
    '''
    
    keys = ["structures", "energies", "forces", "stresses", "magmoms", "formula", "TM_group", "Com_group", "path", "index", "Na_con", "Fe_con", "unit_num", "phase", "file_id"]
    all_data = {k: [] for k in keys}
    last_step_data = {k: [] for k in keys}
    tm_group_map, com_group_map = {}, {}
    phase_mapping = {'O3': 'O3', 'P3': 'P3', 'OP2': 'OP2', 'O1': 'O1'}

    for file_id, file in enumerate(init_dir.rglob('*.json')):
        file_str = str(file)
        phase = next((v for k, v in phase_mapping.items() if k in file_str), 'OP')

        try:
            data = read_json(file)
            structures_raw = data.get("structure", [])
            if not structures_raw: continue
            
            s_init = Structure.from_dict(structures_raw[0])
            comp = s_init.composition
            fe_val, na_val, o_val = comp.get('Fe', 0), comp.get('Na', 0), comp.get('O', 0)
            inv_o = 2.0 / o_val if o_val != 0 else 0
            fe_con, na_con = fe_val * inv_o, na_val * inv_o
            unit_num = round(len(s_init) * inv_o, 2)
            formula = s_init.reduced_formula
            e_corr_per_atom = correct_energy(s_init, 0)
        
            tm_group = tm_group_map.setdefault(fe_con, len(tm_group_map))
            com_group = com_group_map.setdefault(formula, len(com_group_map))
            
            num_structures = len(structures_raw)
            start_idx = start_index if num_structures > 10 else 0
            
            for idx in range(start_idx, num_structures):
                struct_obj = Structure.from_dict(structures_raw[idx])
                energy = data["energy_per_atom"][idx] + e_corr_per_atom
                
                entry = {
                    "structures": struct_obj, "energies": energy,
                    "forces": data["force"][idx], "stresses": data["stress"][idx],
                    "magmoms": data["magmom"][idx], "formula": formula,
                    "path": file_str, "index": idx, "Na_con": na_con,
                    "Fe_con": fe_con, "unit_num": unit_num, "phase": phase,
                    "TM_group": tm_group, "Com_group": com_group,
                    "file_id": file_id  
                }

                for k, v in entry.items():
                    all_data[k].append(v)
                    if idx == num_structures - 1:
                        last_step_data[k].append(v)

        except Exception as e:
            print(f"Error processing {file}: {e}")

    print(f"Loaded {len(all_data['structures'])} total steps from {file_id + 1} files.")
    return all_data, last_step_data

def get_Ehull_from_tm(data_dict: dict, ref_energy: bool = False) -> dict:
    df = pd.DataFrame({
        'TM_group': data_dict['TM_group'],
        'Na_con': data_dict['Na_con'],
        'unit_num': data_dict['unit_num'],
        'energies': data_dict['energies']
    })

    all_ehull = np.zeros(len(df))
    all_ref = np.zeros(len(df)) if ref_energy else None

    for _, group in df.groupby('TM_group'):
        idx = group.index
        x = group['Na_con'].values.astype(float)
        unit_num = group['unit_num'].values.astype(float)
        e_fu = group['energies'].values * unit_num
        
        x_min, x_max = x.min(), x.max()
        if np.isclose(x_min, x_max):
            e_base = e_fu.min()
            e_form = e_fu - e_base
            e_ref_line = np.full_like(e_form, e_base)
        else:
            e_min = e_fu[np.isclose(x, x_min)].min()
            e_max = e_fu[np.isclose(x, x_max)].min()
            line_val = e_min + (e_max - e_min) * (x - x_min) / (x_max - x_min)
            e_form = e_fu - line_val
            e_ref_line = line_val

        unique_x = np.unique(x)
        pts = sorted({(xi, e_form[np.isclose(x, xi)].min()) for xi in unique_x})
        hull_pts = []
        for p_pt in pts:
            while len(hull_pts) >= 2:
                o, a = hull_pts[-2], hull_pts[-1]
                if (a[0] - o[0]) * (p_pt[1] - o[1]) - (a[1] - o[1]) * (p_pt[0] - o[0]) <= 0:
                    hull_pts.pop()
                else: break
            hull_pts.append(p_pt)
        
        hull_pts = np.array(hull_pts)
        e_hull_interp = np.interp(x, hull_pts[:, 0], hull_pts[:, 1]) if len(hull_pts) > 1 else hull_pts[0, 1]
        
        all_ehull[idx] = np.maximum(e_form - e_hull_interp, 0.0) / unit_num 
        if ref_energy:
            all_ref[idx] = (e_ref_line + e_hull_interp) / unit_num

    res = data_dict.copy()
    res["ehull"] = all_ehull.tolist()
    if ref_energy: res["ref_energies"] = all_ref.tolist()
    return res

def get_Ehull_from_com(data_dict: dict, ref_energy: bool = False) -> dict:
    df = pd.DataFrame({'Com_group': data_dict['Com_group'], 'energies': data_dict['energies']})
    all_ehull = np.zeros(len(df))
    all_ref = np.zeros(len(df)) if ref_energy else None
    
    for _, group in df.groupby('Com_group'):
        idx = group.index
        e_min = group['energies'].min()
        all_ehull[idx] = (group['energies'].values - e_min)
        if ref_energy: all_ref[idx] = e_min

    res = data_dict.copy()
    res["ehull"] = all_ehull.tolist()
    if ref_energy: res["ref_energies"] = all_ref.tolist()
    return res

def _even_sample_by_group(df, col, groups, target_n, is_numeric=False, random_seed=None):
    def get_subset(g):
        if is_numeric:
            return df[np.isclose(df[col].astype(float), float(g))]
        else:
            return df[df[col] == g]

    all_selected  = []
    remaining_n   = target_n
    remain_groups = list(groups)

    while remain_groups and remaining_n > 0:
        n     = len(remain_groups)
        base  = remaining_n // n
        extra = remaining_n % n

        quotas = {
            g: base + (1 if i < extra else 0)
            for i, g in enumerate(remain_groups)
        }

        exhausted = [g for g in remain_groups if len(get_subset(g)) < quotas[g]]

        if not exhausted:
            for g in remain_groups:
                subset = get_subset(g)
                all_selected.extend(
                    subset.sample(n=quotas[g], random_state=random_seed).index.tolist()
                )
            break
        else:
            for g in exhausted:
                subset = get_subset(g)
                all_selected.extend(subset.index.tolist())
                remaining_n  -= len(subset)
                remain_groups.remove(g)

    return all_selected


def subset_data(data, target_n, path_filter=None,
                phases=None, na_values=None,
                fixed_counts=None,
                random_seed=None):
    """
    Parameters
    ----------
    data          : dict
    target_n      : int
    path_filter   : str
    phases        : list
    na_values     : list
    fixed_counts  : dict
        e.g.
        {'OP2':100, 'O3':50}   {0.5:80, 0.7:120}

    random_seed   : int
    """

    df = pd.DataFrame(data)

    if path_filter:
        df = df[df['path'].str.contains(path_filter)]

    if df.empty:
        print("警告：过滤后数据集为空，返回空结果。")
        return pd.DataFrame().to_dict('list')

    rng = np.random.RandomState(random_seed)

    # ==========================================================
    # phase mode
    # ==========================================================
    if phases is not None:

        group_col = 'phase'
        groups = phases

    # ==========================================================
    # Na mode
    # ==========================================================
    elif na_values is not None:

        group_col = 'Na_con'
        groups = na_values

    # ==========================================================
    # random mode
    # ==========================================================
    else:

        final_df = df.sample(
            n=min(len(df), target_n),
            random_state=random_seed
        )

        print(f"Final Data Count: {len(final_df)}")
        return final_df.to_dict('list')

    # ==========================================================
    # grouped sampling
    # ==========================================================
    fixed_counts = fixed_counts or {}

    selected_idx = []

    remain_groups = []
    remain_target = target_n

    # -------------------------
    # 1. fixed sampling
    # -------------------------
    for g in groups:

        sub_df = df[df[group_col] == g]

        if g in fixed_counts:

            n_take = min(len(sub_df), fixed_counts[g])

            idx = sub_df.sample(
                n=n_take,
                random_state=random_seed
            ).index.tolist()

            selected_idx.extend(idx)

            remain_target -= n_take

        else:
            remain_groups.append(g)

    # -------------------------
    # 2. even sampling for remaining groups
    # -------------------------
    if remain_groups and remain_target > 0:

        per_group = remain_target // len(remain_groups)

        extra = remain_target % len(remain_groups)

        for i, g in enumerate(remain_groups):

            sub_df = df[df[group_col] == g]

            n_take = per_group

            if i < extra:
                n_take += 1

            n_take = min(len(sub_df), n_take)

            idx = sub_df.sample(
                n=n_take,
                random_state=random_seed
            ).index.tolist()

            selected_idx.extend(idx)

    final_df = df.loc[selected_idx]

    # ==========================================================
    # statistics
    # ==========================================================
    print(f"Final Data Count: {len(final_df)}")

    if 'phase' in final_df.columns:
        print(f"Phase 分布:\n{final_df['phase'].value_counts()}\n")

    if 'Na_con' in final_df.columns:
        print(
            f"Na_con 分布:\n"
            f"{final_df['Na_con'].value_counts().sort_index()}\n"
        )

    return final_df.to_dict('list')
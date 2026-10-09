import numpy as np
import pandas as pd
from pymatgen.core import Structure

def extract_data_from_mcjson(json_file, tar, select_num=1):

    df = pd.read_json(json_file)

    n = len(df)

    if select_num == 1:
        indices = [n - 1]
    else:
        indices = np.linspace(
            0,
            n - 1,
            min(select_num, n),
            dtype=int
        )
        indices = np.unique(indices)

    info_list = []

    sc = json_file.parts[-3]
    tar_dir = tar / sc
    tar_dir.mkdir(exist_ok=True, parents=True)

    for idx in indices:

        row = df.iloc[idx]

        s = Structure.from_dict(row['structure'])

        s_name = f"{json_file.parts[-1].split('_')[1]}-{idx}"

        save_path = tar_dir / f"{s_name}.vasp"

        s.sort().to(save_path, fmt='poscar')

        info_list.append({
            'path': str(json_file),
            'sc': sc,
            's_name': s_name,
            'step': idx,
            'c_e': row['energy_mean_per_atom'],
            'e_std': row['energy_std_per_atom'],
            'f_std_mean': row['force_uncertainty_per_atom'],
            'f_std_max': row['force_uncertainty_max']
        })

    return info_list
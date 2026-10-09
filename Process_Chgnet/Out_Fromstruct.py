from pymatgen.core.structure import Structure
from Process_VaspOut import get_Na_coord,get_lo_content
import numpy as np
from chgnet.model import CHGNet, StructOptimizer
from pathlib import Path as p

def out_from_struct(struct, energy, forces=None, magmoms=None, stress=None):
    st = struct
    na_con, fe_con = get_lo_content(st, ['Na', 'Fe'])
    
    res = {
        'com': str(st.composition),
        'atom_num': st.num_sites,
        'Na_con': na_con,
        'Fe_con': fe_con,
        'e':  energy,
        **get_Na_coord(st)
    }
    
    opts = {'f': forces, 'm': magmoms, 's': stress}
    res.update({k: np.array(v) for k, v in opts.items() if v is not None})
    return res

def chgnet_relax(struct:Structure, relaxer, model, include_f:bool=False,include_m:bool=False,include_traj:bool=False,fmax:float=0.02,steps:int=400)->dict:
    result = relaxer.relax(atoms=struct, fmax=fmax, steps=steps)
    final_structure = result["final_structure"]
    prediction = model.predict_structure(final_structure)
    res = {
        'struct':final_structure,
        'e':prediction['e'[0]],
    }
    if include_f:
        res.update({'f':str(prediction['f'[0]]).replace('\n',',')})
    if include_m:
        res.update({'m':str(prediction['m'[0]])})
    if include_traj:
        res.update({'traj':result['trajectory']})
    return res


def convert_traj_to_data(traj, include_f=False, include_s=False, include_m=False) -> dict:
    species = [atom.symbol for atom in traj.atoms]
    positions = traj.atom_positions
    cells = traj.cells
    n_atoms = len(species)
    energies_per_atom = np.array(traj.energies) / n_atoms
    
    results = {
        'steps': list(range(len(positions))),
        'struct': [],
        'e': energies_per_atom,
        'com': []
    }
    
    if include_f: results['f'] = []
    if include_s: results['s'] = []
    if include_m: results['m'] = []

    def format_array(arr):
        return [str(i).replace('\n',',') for i in arr]

    for i in range(len(positions)):
        ss = Structure(
            lattice=cells[i],
            species=species,
            coords=positions[i],
            coords_are_cartesian=True
        )
        results['struct'].append(ss)
        results['com'].append(str(ss.composition))
        
        if include_f:
            results['f'].append(format_array(traj.forces[i]))
        if include_s:
            results['s'].append(format_array(traj.stresses[i]))
        if include_m:
            results['m'].append(format_array(traj.magmoms[i]))
            
    return results

import numpy as np

def extract_stages_traj(data: dict, out_dir: p, path: str):
    '''
    data: traj
    out_dir: if not None, save struct to out_dir
    path: info
    '''
    total_steps = len(data['steps'])
    stages = {
        'early': (0, int(total_steps * 0.2)),
        'mid':   (int(total_steps * 0.4), int(total_steps * 0.6)),
        'late':  (int(total_steps * 0.8), total_steps)
    }

    selected_items = [] 

    for stage_name, (start, end) in stages.items():
        if end > start:
            n_pick = min(2, end - start)
            idxs = np.random.choice(np.arange(start, end), size=n_pick, replace=False)
            selected_items.extend([(idx, stage_name) for idx in idxs.tolist()])

    selected_items = sorted(selected_items, key=lambda x: x[0])

    new_dict = {key: [] for key in ['steps', 'e', 'com', 'f', 's', 'path', 'stage']}

    for idx, stage_name in selected_items:
        step_val = data['steps'][idx]
        struct = data['struct'][idx]

        if out_dir:
            filename = out_dir / f'{idx}.vasp'
            struct.to(filename=filename, fmt="POSCAR")

        new_dict['steps'].append(step_val)
        new_dict['e'].append(data['e'][idx])
        new_dict['com'].append(data['com'][idx])
        new_dict['path'].append(path)
        new_dict['stage'].append(stage_name)

        for key in ['f', 's']:
            if key in data:
                new_dict[key].append(data[key][idx])

    return new_dict


from pathlib import Path as p
import numpy as np
import json
from ase.calculators.singlepoint import SinglePointCalculator
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.core import Structure
from Process_VaspOut import correct_energy

def get_ase_from_json(file:p,is_force:bool=True,is_correct:bool=True)->list:
    '''
    read chgnet json return list
    default correct = True
    ase_atoms.info['REF_energy'] = vasp_energy 
    ase_atoms.arrays['REF_forces'] = vasp_force
    :param file: 说明
    :type file: p
    :return: 说明
    :rtype: list
    '''
    adapter = AseAtomsAdaptor()
    with open(file, 'r') as f:
        data = json.load(f)
    frames = []
    for struct_dict, energy, force in zip(data['structure'], 
                                     data['uncorrected_total_energy'], 
                                     data['force']):
        s  = Structure.from_dict(struct_dict)
        tar_e = correct_energy(s,energy) if is_correct else energy/s.num_sites
        ase_atoms = adapter.get_atoms(s)
        ase_atoms.info['REF_energy'] = tar_e
        if is_force:
            ase_atoms.arrays['REF_forces'] = np.array(force)
        frames.append(ase_atoms)
    return frames



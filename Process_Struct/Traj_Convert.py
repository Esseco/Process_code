from ase.calculators.singlepoint import SinglePointCalculator
from pymatgen.io.ase import AseAtomsAdaptor
from ase.io import read, write
import numpy as np

def save_traj_xyz(traj, save_name, include_e=True, include_f=False, include_s=False):
    energies  = getattr(traj, 'energies',      [None] * len(traj.atom_positions))
    forces    = getattr(traj, 'forces',         [None] * len(traj.atom_positions))
    stresses  = getattr(traj, 'stresses',       [None] * len(traj.atom_positions))

    atoms_list = []
    for pos, cell, e, f, s in zip(traj.atom_positions, traj.cells, energies, forces, stresses):
        frame = traj.atoms.copy()
        frame.set_positions(pos)
        frame.set_cell(cell)
        frame.calc = SinglePointCalculator(
            frame,
            energy  = e            if (include_e and e is not None) else None,
            forces  = np.array(f)  if (include_f and f is not None) else None,
            stress  = np.array(s)  if (include_s and s is not None) else None,
        )
        atoms_list.append(frame)
    write(save_name, atoms_list)


def traj_to_info(traj_file, include_e=True, include_f=False, include_s=False):
    atoms_list = read(traj_file, index=':')
    adaptor = AseAtomsAdaptor()
    
    results = {
        'structures': [adaptor.get_structure(a) for a in atoms_list]
    }
    if include_e:
        results['energies'] = [a.get_potential_energy() for a in atoms_list]
    if include_f:
        results['forces'] = [a.get_forces().tolist() for a in atoms_list]
    if include_s:
        results['stresses'] = [a.get_stress().tolist() for a in atoms_list]
    
    return results
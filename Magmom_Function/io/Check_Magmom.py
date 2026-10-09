import re
from pathlib import Path as p
from pymatgen.core.structure import Structure
from .Check_VaspOut import get_INCAR_NUPDOWN
from Process_Vasp.magnetism import read_magnetic_moments_outcar

def check_magnetic_moments(init_dir:p):
    '''
    check_magnetic_moments 的 Docstring
    
    :param init_dir: vasp_dir contains output
    :type init_dir: p
    :return: flag, round(total_magnetic_moment,1):Spin GS(1) or ES(0), if GS return total_magmom else return correct_magmom
    :rtype: tuple
    '''

    result = read_magnetic_moments_outcar(init_dir)
    if result == 0:
        raise ValueError("Missing or incomplete OUTCAR magnetization")
    elements, magnetic_moments,total_magnetic_moment = result
    comput_NUPDOWN = get_INCAR_NUPDOWN(init_dir)
    moments = magnetic_moments[-1]
    flag = 1
    if abs(total_magnetic_moment-comput_NUPDOWN)<10:
        for element, mag in zip(elements, moments):
            abmag = abs(mag)
            if element == 'Fe':
                if not (3.5 <= abmag <= 4.5):
                    total_magnetic_moment += 4.3-mag
                    flag=0
            elif element == 'Mn':
                if not (3 <= abmag <= 4):
                    total_magnetic_moment += 3.9-mag
                    flag=0
    else:
        for element, mag in zip(elements, moments):
            if element == 'Fe':
                if not (3.5 <= mag <= 4.5):
                    total_magnetic_moment = comput_NUPDOWN
                    flag=0
                    break
            elif element == 'Mn':
                if not (3 <= mag <= 4):
                    total_magnetic_moment = comput_NUPDOWN
                    flag=0
                    break

    return flag, round(total_magnetic_moment,1) 

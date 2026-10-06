"""Legacy scalar magnetization reader; not a vector/SOC moment interface."""
import re
from pathlib import Path as p
from monty.io import zopen
from monty.os.path import zpath
from pymatgen.core import Structure

def read_magnetic_moments_outcar(init_dir:p) -> tuple:
    '''
    read_magnetic_moments_outcar 的 Docstring
    
    :param init_dir: vasp_dir contains output
    :type init_dir: p
    :return: elements, magnetic_moments, total_magnetic_moment
    :rtype: tuple
    '''
    init_dir = p(init_dir)
    poscar_file = p(zpath(init_dir/'POSCAR'))
    outcar_file = zpath(init_dir/'OUTCAR')
    structure = Structure.from_file(poscar_file)
    elements = [str(site.specie) for site in structure]
    magnetic_moments = []
    total_magnetic_moment = 0.0 
    current_step = []
    reading_magnetization = False

    try:
        with zopen(outcar_file, 'rt', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                if re.search(r'magnetization\s*\((x|y|z)\)', line, re.IGNORECASE):
                    reading_magnetization = True
                    current_step = []
                    total_magnetic_moment = 0.0 
                    continue
                    
                if reading_magnetization:
                    if '---' in line or '# of ion' in line:
                        continue
                        
                    match = re.match(r'\s*(\d+)\s+[-.\d]+\s+[-.\d]+\s+[-.\d]+\s+([-.\d]+)', line)
                    if match:
                        current_step.append(float(match.group(2))) 
                        continue
                        
                    match_tot = re.match(r'\s*tot\s+([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)', line, re.IGNORECASE)
                    if match_tot:
                        total_magnetic_moment = float(match_tot.group(4)) 
                        
                        if current_step:
                            magnetic_moments = [current_step] 
                        
                        reading_magnetization = False
                        continue
                        
    except FileNotFoundError:
        print(f"OUTCAR not found: {outcar_file}")
        return 0

    if not magnetic_moments or len(magnetic_moments[0]) != len(elements):
        return 0
        
    return elements, magnetic_moments, total_magnetic_moment



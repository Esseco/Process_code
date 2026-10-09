from ..io import (
    read_magnetic_moments_outcar, 
    check_magnetic_moments, 
    update_incar, 
    copy_file, 
    get_INCAR_NUPDOWN, 
    detect_converge
)
from pathlib import Path as p

def InitDft_to_TarDft(init_dir: p, tar_dir: p, Update: bool = True, NSW: int=3):
    '''
    InitDft_to_TarDft 的 Docstring
    
    :param init_dir: vasp_initdir 
    :type init_dir: p
    :param tar_dir: vasp_tardir
    :type tar_dir: p
    :param Update: update file(Ture,False)
    :type Update: bool
    :param NSW: if ES set INCAR NSW
    :type NSW: int
    '''
    init_mag = read_magnetic_moments_outcar(init_dir)[2]
    converge = detect_converge(init_dir)
    NUPDOWN = get_INCAR_NUPDOWN(init_dir)
    mag_ok, cor_mag = check_magnetic_moments(init_dir)
    lsf_1, lsf_0 = init_dir / 'vasp.lsf', init_dir / 'vasplsf'

    if converge[2]: 
        return print(init_dir, 'serious err')
    if (tar_dir / 'POSCAR').exists(): 
        return print(tar_dir, 'exists')

    if not mag_ok:
        print(f"{init_dir} spin={mag_ok} finish={converge[0]} init_mag={init_mag} NUPDOWN={NUPDOWN} cor_mag={cor_mag}")
        if Update:
            update_incar(init_dir, init_dir, mag_ok, cor_mag, NSW)
            if lsf_0.exists(): lsf_0.rename(lsf_1)
    else:
        msg = f"check magmom ok, {'copy to ' + str(tar_dir) if converge[0] else 'not finish ' + str(init_dir)}"
        print(msg)
        if Update:
            if converge[0]:
                tar_dir.mkdir(exist_ok=True, parents=True)
                update_incar(init_dir, tar_dir, mag_ok, cor_mag)
                copy_file(init_dir, tar_dir)
            if lsf_1.exists(): lsf_1.rename(lsf_0)
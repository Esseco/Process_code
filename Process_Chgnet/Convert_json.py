from Magmom_Function.io import (
    check_magnetic_moments,
    detect_converge,
    update_incar,
)
from chgnet.utils import parse_vasp_dir
from pathlib import Path as p


def _rename_overwrite(src: p, dst: p) -> None:
    """Rename src → dst, removing dst first if it exists (Windows compat)."""
    if dst.exists():
        dst.unlink()
    src.rename(dst)


def _rm_lsf_marker(lsf: p, bak: p) -> None:
    """Rename lsf → bak to mark job as no longer queued."""
    if lsf.exists():
        _rename_overwrite(lsf, bak)
        print(f'  ✓ {lsf.name} → {bak.name}')


def _restore_lsf_marker(lsf: p, bak: p) -> None:
    """Rename bak → lsf to restore queue marker."""
    if bak.exists():
        _rename_overwrite(bak, lsf)
        print(f'  ✓ {bak.name} → {lsf.name}')


def vasp_to_chgnetJson(
    init_dir: p,
    tar_path: p,
    update: bool = True,
    check_converge: bool = True,
) -> int:
    """
    Convert VASP results to CHGNet JSON format.

    Returns:
        1 if conversion succeeded, 0 if skipped.
    """
    lsf = init_dir / 'vasp.lsf'
    bak = init_dir / 'vasplsf'

    # --- Already processed ---
    if tar_path.exists():
        _rm_lsf_marker(lsf, bak)
        return 0

    # --- Magnetic moments ---
    mag_ok, cor_mag = check_magnetic_moments(init_dir)

    if not mag_ok:
        if update:
            update_incar(init_dir, init_dir, mag_ok, cor_mag, NSW=100)
            _restore_lsf_marker(lsf, bak)
            print(f'{init_dir} magmom in ES, correct')
        print(f'{init_dir} magmom in ES')
        return 0

    # --- Convergence ---
    converged, *_ = detect_converge(init_dir)

    if not converged:
        if check_converge:
            _rm_lsf_marker(lsf, bak)
            print(f'{init_dir} not over')
            return 0
        print(f'{init_dir} not converged, converting anyway')

    # --- Convert ---
    parse_vasp_dir(base_dir=init_dir, save_path=tar_path)
    _rm_lsf_marker(lsf, bak)
    return 1

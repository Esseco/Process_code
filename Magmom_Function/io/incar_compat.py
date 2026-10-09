"""Legacy integer-spin signature adapted to the common INCAR editor."""
from pathlib import Path
import shutil
from Process_Vasp import update_incar as _update

def update_incar(init_dir, tar_dir, spin, NUPDOWN, NSW=3):
    """Legacy side effects retained: copy CONTCAR and set NSW/NUPDOWN.

    spin=0 copies CONTCAR to source POSCAR; spin=1 copies to target POSCAR.
    Prefer Process_Vasp.update_incar for new code without these implicit copies.
    """
    if spin not in (0, 1):
        raise ValueError("legacy spin must be 0 or 1")
    source, target = Path(init_dir), Path(tar_dir)
    if not (source / "CONTCAR").is_file():
        raise FileNotFoundError(source / "CONTCAR")
    updates = {"NSW": NSW if spin == 0 else 100}
    if spin == 0:
        updates["NUPDOWN"] = NUPDOWN
    _update(source, target, mode="Correct", updates=updates)
    shutil.copy2(source / "CONTCAR", (source if spin == 0 else target) / "POSCAR")

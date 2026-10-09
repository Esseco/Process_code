"""Legacy directory-based wrappers; Na-Fe-Mn assumptions are retained."""
from pathlib import Path
from monty.io import zopen
from monty.os.path import zpath
from pymatgen.core import Structure
from Process_Vasp.generation import get_INCAR_NUPDOWN as _estimate

def get_INCAR_NUPDOWN(init_dir):
    structure = Structure.from_file(zpath(Path(init_dir) / "POSCAR"))
    return round(_estimate(structure), 1)

def detect_converge(init_dir):
    """Legacy log heuristic: (finished, ionic_accuracy_seen, serious_error).

    Does not replace XML convergence validation or scheduler status.
    """
    with zopen(zpath(Path(init_dir) / "out"), "rt", encoding="utf-8") as handle:
        content = handle.read()
    runs = content.count("running on")
    finished = runs > 0 and content.count("Terminated at") == runs
    return int(finished), int(" reached required accuracy" in content), int(
        content.count("the old and the new charge density differ") > 10)

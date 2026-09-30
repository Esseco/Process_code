"""VASP input generation helpers."""

from pathlib import Path
import re
import json
from typing import Literal

from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.io.vasp.sets import MPRelaxSet

BASE_PATH = Path(__file__).parent
GPU_SCRIPT = BASE_PATH / "submit_gpu.sh"


def generate_atomate_input(
    directory: str | Path,
    structure: str | Path,
    calculation: Literal["relax", "static", "dos", "band"] = "relax",
    incar_settings: dict[str, dict] | None = None,
    kpoints_settings: dict[str, dict] | None = None,
    job_name: str | None = None,
    resume_from: dict[str, str] | None = None,
) -> Path:
    """Create a directly submittable atomate2 workflow from a .vasp or .cif.

    Settings are keyed by stage: ``relax``, ``static``, ``dos`` or ``band``.
    DOS and band workflows automatically run relax -> static -> non-SCF.
    Actual VASP inputs are written by atomate2 when each stage starts.
    ``static`` runs a single StaticMaker directly, without preceding relaxation.
    Stages run in ``runs/relax``, ``runs/static``, ``runs/dos`` or ``runs/band``.
    Repeated executions resume completed stages; retries use new attempt directories.
    ``resume_from`` explicitly adopts validated existing output directories by
    stage (paths are evaluated on the execution host); imports are used once.
    """
    source = Path(structure)
    if source.suffix.lower() not in {".vasp", ".cif"}:
        raise ValueError("structure must be a .vasp or .cif file")
    if not source.is_file():
        raise FileNotFoundError(source)
    if calculation not in {"relax", "static", "dos", "band"}:
        raise ValueError("calculation must be 'relax', 'static', 'dos', or 'band'")
    if job_name is not None and not re.fullmatch(r"[A-Za-z0-9_.-]+", job_name):
        raise ValueError("job_name may contain only letters, numbers, _, -, and .")

    # Validate the input structure before creating the task directory.
    Structure.from_file(source)
    config = {
        "calculation": calculation,
        "structure_file": "initial_structure" + source.suffix.lower(),
        "incar_settings": incar_settings or {},
        "kpoints_settings": kpoints_settings or {},
        "resume_from": resume_from or {},
    }
    for group in ("incar_settings", "kpoints_settings"):
        if not isinstance(config[group], dict) or any(
            stage not in {"relax", "static", "dos", "band"}
            or not isinstance(values, dict)
            for stage, values in config[group].items()
        ):
            raise ValueError(f"{group} must map stage names to dictionaries")
    if not isinstance(config["resume_from"], dict) or any(
        stage not in {"relax", "static", "dos", "band"}
        or not isinstance(path, str) or not path
        for stage, path in config["resume_from"].items()
    ):
        raise ValueError("resume_from must map stage names to nonempty directory strings")
    config_text = json.dumps(config, indent=2, ensure_ascii=False)

    script = GPU_SCRIPT.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    script = re.sub(r"(?m)^#SBATCH --job-name=.*$",
                    f"#SBATCH --job-name={job_name or calculation}", script)
    script = re.sub(r"(?m)^python3 1\.py\s*$", "python3 workflow.py", script)
    if "python3 workflow.py" not in script:
        raise ValueError("GPU script template does not contain the expected Python command")

    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / config["structure_file"]).write_bytes(source.read_bytes())
    (target / "workflow.json").write_text(config_text, encoding="utf-8")
    (target / "atomate_runner.py").write_bytes((BASE_PATH / "atomate_runner.py").read_bytes())
    (target / "workflow.py").write_text(_ATOMATE2_WORKFLOW, encoding="utf-8", newline="\n")
    (target / GPU_SCRIPT.name).write_text(script, encoding="utf-8", newline="\n")
    return target


_ATOMATE2_WORKFLOW = '''"""Resume the generated atomate2 workflow."""
from pathlib import Path
from atomate_runner import main

if __name__ == "__main__":
    main(Path(__file__).resolve().parent)
'''



def convert_dos_to_unix(file_path: Path) -> None:
    """Convert CRLF line endings to LF in one file."""
    try:
        content = file_path.read_bytes()
        if b"\r\n" in content:
            file_path.write_bytes(content.replace(b"\r\n", b"\n"))
    except OSError as exc:
        print(f"Failed to convert {file_path} to Unix line endings: {exc}")


def convert_files_in_directory(directory_path: str | Path) -> None:
    """Recursively convert files below a directory to Unix line endings."""
    for file_path in Path(directory_path).rglob("*"):
        if file_path.is_file():
            convert_dos_to_unix(file_path)


def generate_vasp_input(
    struct: Structure,
    tar_dir: str | Path,
    incar_set: dict,
    potcar_set: bool,
    lsfname: str,
    kpoints_set: Kpoints | None = None,
) -> None:
    """Generate INCAR, KPOINTS, optional POTCAR, and the LSF script."""
    target_dir = Path(tar_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    relax_set = MPRelaxSet(
        structure=struct,
        user_incar_settings=incar_set,
        user_kpoints_settings=kpoints_set,
    )
    relax_set.incar.write_file(target_dir / "INCAR")
    relax_set.kpoints.write_file(target_dir / "KPOINTS")
    if potcar_set:
        relax_set.potcar.write_file(target_dir / "POTCAR")

    template = (BASE_PATH / "vasp.lsf").read_text(encoding="utf-8")
    script = template.replace("#BSUB -J Na0", f"#BSUB -J {lsfname}")
    (target_dir / "vasp.lsf").write_text(script, encoding="utf-8", newline="\n")
    convert_files_in_directory(target_dir)


def get_INCAR_NUPDOWN(struct: Structure) -> float:
    """Estimate NUPDOWN from Na, Fe, and Mn composition."""
    na_num = struct.composition["Na"]
    fe_num = struct.composition["Fe"]
    mn_num = struct.composition["Mn"]
    oxidized = fe_num + mn_num - na_num
    fe3 = fe_num
    fe4 = 0
    if oxidized <= mn_num:
        mn4 = oxidized
        mn3 = mn_num - oxidized
    else:
        mn3 = 0
        mn4 = mn_num
        fe4 = oxidized - mn_num
        fe3 = fe_num - fe4
    return 3.2 * mn4 + 3.9 * (mn3 + fe4) + 4.3 * fe3

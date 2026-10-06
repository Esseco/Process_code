"""Utilities for editing and copying VASP input files."""

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
import shutil

DEFAULT_VASP_FILES: dict[str, str] = {
    "INCAR": "INCAR",
    "KPOINTS": "KPOINTS",
    "POTCAR": "POTCAR",
    "vasp.lsf": "vasp.lsf",
    "vasplsf": "vasp.lsf",
    "CONTCAR": "POSCAR",
}


def set_incar_tags(lines: Iterable[str], updates: Mapping[str, object]) -> list[str]:
    """Replace existing INCAR tags and append tags that are absent."""
    normalized = {key.upper(): value for key, value in updates.items()}
    found = dict.fromkeys(normalized, False)
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        key = stripped.split("=", 1)[0].strip().upper()
        if key in found:
            new_lines.append(f"{key} = {normalized[key]}\n")
            found[key] = True
        else:
            new_lines.append(line)

    new_lines.extend(
        f"{key} = {normalized[key]}\n" for key, present in found.items() if not present
    )
    return new_lines


def update_incar(
    init_dir: str | Path,
    tar_dir: str | Path,
    mode: str,
    spin: int | None = None,
    nupdown: float | None = None,
    updates: Mapping[str, object] | None = None,
) -> None:
    """Copy and update INCAR in ``Spin`` or ``Correct`` mode."""
    source = Path(init_dir) / "INCAR"
    target_dir = Path(tar_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)

    if mode.lower() == "spin":
        if spin is None:
            raise ValueError("Spin mode requires spin")
        incar_updates: dict[str, object] = {"NSW": 0}
        if spin == 0:
            if nupdown is None:
                raise ValueError("spin=0 requires nupdown")
            incar_updates["NUPDOWN"] = nupdown
    elif mode.lower() == "correct":
        if not updates:
            raise ValueError("Correct mode requires updates")
        incar_updates = dict(updates)
    else:
        raise ValueError("mode must be 'Spin' or 'Correct'")

    (target_dir / "INCAR").write_text(
        "".join(set_incar_tags(lines, incar_updates)), encoding="utf-8"
    )


def copy_vasp_files(
    init_dir: str | Path,
    tar_dir: str | Path,
    files: Mapping[str, str] | Sequence[str] | None = None,
) -> list[Path]:
    """Copy selected VASP files and return the created paths.

    ``files`` may be a source-to-destination mapping or a sequence of names.
    Missing files are optional and silently skipped. With the default mapping,
    ``vasplsf`` is accepted as a fallback for ``vasp.lsf`` and ``CONTCAR`` is
    copied as ``POSCAR``. Edit :data:`DEFAULT_VASP_FILES` to extend the defaults.
    """
    source_dir = Path(init_dir)
    target_dir = Path(tar_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    mapping = (
        DEFAULT_VASP_FILES
        if files is None
        else dict(files)
        if isinstance(files, Mapping)
        else {name: name for name in files}
    )

    copied: list[Path] = []
    destinations: set[Path] = set()
    for source_name, target_name in mapping.items():
        source = source_dir / source_name
        target = target_dir / target_name
        if source.is_file() and target not in destinations:
            shutil.copy2(source, target)
            copied.append(target)
            destinations.add(target)
    return copied


def copy_file(init_dir: str | Path, tar_dir: str | Path) -> None:
    """Backward-compatible copy helper using its original file selection."""
    copy_vasp_files(
        init_dir,
        tar_dir,
        {
            "POTCAR": "POTCAR",
            "vasp.lsf": "vasp.lsf",
            "vasplsf": "vasp.lsf",
            "KPOINTS": "KPOINTS",
        },
    )

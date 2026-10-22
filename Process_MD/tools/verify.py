"""Run checks with disposable data; --package also verifies a temporary wheel."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PROJECT = Path(__file__).resolve().parents[1]


def run(arguments: list[str], cwd: Path, environment: dict[str, str]) -> None:
    subprocess.run([sys.executable, *arguments], cwd=cwd, env=environment, check=True)


def check_package(root: Path, environment: dict[str, str]) -> None:
    source = root / "source"
    source.mkdir()
    for filename in ("pyproject.toml", "README.md"):
        shutil.copy2(PROJECT / filename, source / filename)
    shutil.copytree(PROJECT / "process_md", source / "process_md",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    wheels = root / "wheels"
    run(["-m", "pip", "wheel", ".", "--quiet", "--no-deps", "--no-build-isolation",
         "--no-index", "--no-cache-dir", "--wheel-dir", str(wheels)], source, environment)
    wheel, = wheels.glob("*.whl")
    installed = root / "installed"
    run(["-m", "pip", "install", "--quiet", "--target", str(installed), "--no-deps",
         "--no-index", "--no-compile", "--no-cache-dir", str(wheel)], root, environment)
    installed_path = os.pathsep.join(filter(None, (str(installed), environment.get("PYTHONPATH", ""))))
    installed_environment = dict(environment, PYTHONPATH=installed_path)
    code = (
        "from pathlib import Path; import sys; import process_md as p; "
        "from importlib.metadata import version; "
        "assert Path(p.__file__).resolve().is_relative_to(Path(sys.argv[1])); "
        "assert version('process-md') == '0.1.0'; "
        "assert p.diffusion_from_slope(6) == 0.0001; "
        "assert 'Process_MLIP' not in sys.modules; assert 'torch' not in sys.modules"
    )
    run(["-c", code, str(installed)], root, installed_environment)
    run([str(PROJECT / "examples" / "prepare_structure.py")], root, installed_environment)
    if subprocess.run([sys.executable, "-c", "import importlib.util; "
                        "raise SystemExit(importlib.util.find_spec('Process_MLIP') is None)"],
                       cwd=root, env=installed_environment, check=False).returncode == 0:
        run([str(PROJECT / "examples" / "short_md.py")], root, installed_environment)
    else:
        print("SKIP installed MD example: Process_MLIP is not importable")
    print(f"Wheel build, temporary installation and import verified: {wheel.name}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true", help="also build/install a disposable wheel")
    arguments = parser.parse_args()
    with TemporaryDirectory(prefix=".process_md_verify_", dir=PROJECT) as directory:
        root = Path(directory).resolve()
        assert root.parent == PROJECT
        temporary = root / "tmp"
        temporary.mkdir()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(temporary),
                           TMP=str(temporary), PIP_DISABLE_PIP_VERSION_CHECK="1")
        run(["-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(root / "pytest")],
            PROJECT, environment)
        if arguments.package:
            # Keep pip's hashed wheel paths below Windows MAX_PATH.
            with TemporaryDirectory(prefix=".p_", dir=PROJECT.parent) as pip_directory:
                assert Path(pip_directory).resolve().parent == PROJECT.parent
                check_package(root, dict(environment, TEMP=pip_directory, TMP=pip_directory))
    print(f"Verification temporary directory removed: {not root.exists()}", flush=True)


if __name__ == "__main__":
    main()

"""Verify with disposable data; optionally build/install disposable local wheels."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PROJECT = Path(__file__).resolve().parents[1]


def discover_library() -> Path | None:
    """Find Process_MD beside the workflow or through the user's PYTHONPATH."""
    candidates = [PROJECT.parent / "Process_MD"]
    for raw in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        if raw:
            path = Path(raw).resolve()
            candidates.extend((path, path / "Process_MD"))
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (candidate / "process_md").is_dir():
            return candidate
    return None


LIBRARY = discover_library()


def run(arguments: list[str], cwd: Path, environment: dict) -> None:
    subprocess.run([sys.executable, "-B", *arguments], cwd=cwd, env=environment, check=True)


def check_package(root: Path, environment: dict) -> None:
    wheels = root / "wheels"
    projects = [(PROJECT, "md_screening")]
    if LIBRARY is not None:
        projects.insert(0, (LIBRARY, "process_md"))
    for project, package in projects:
        source = root / package
        source.mkdir()
        for filename in ("pyproject.toml", "README.md"):
            shutil.copy2(project / filename, source / filename)
        shutil.copytree(project / package, source / package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        run(["-m", "pip", "wheel", ".", "--quiet", "--no-deps", "--no-build-isolation", "--no-index",
             "--no-cache-dir", "--wheel-dir", str(wheels)], source, environment)
    installed = root / "installed"
    run(["-m", "pip", "install", "--quiet", "--target", str(installed), "--no-deps", "--no-index",
         "--no-compile", "--no-cache-dir", *[str(path) for path in wheels.glob("*.whl")]], root, environment)
    # Remove development source paths; preserve the caller's old-library path.
    installed_environment = dict(environment, PYTHONPATH=os.pathsep.join(filter(None, (str(installed), os.environ.get("PYTHONPATH", "")))))
    code = (
        "from pathlib import Path; import sys; import md_screening as m; "
        "from importlib.metadata import version; "
        "assert Path(m.__file__).resolve().is_relative_to(Path(sys.argv[1])); "
        "assert version('md-screening-workflow') == '0.1.0'; "
        "assert m.ScreeningConfig().precheck_ps == 5; "
        "assert 'torch' not in sys.modules; assert 'Process_MLIP' not in sys.modules"
    )
    run(["-c", code, str(installed)], root, installed_environment)
    if subprocess.run([sys.executable, "-B", "-c", "import importlib.util; raise SystemExit(importlib.util.find_spec('Process_MLIP') is None)"],
                      cwd=root, env=installed_environment, check=False).returncode == 0:
        run([str(PROJECT / "examples/short_demo.py")], root, installed_environment)
    else:
        print("SKIP installed MD demo: Process_MLIP is not importable", flush=True)
    print("Disposable wheel build, installation and import verified.", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="store_true")
    arguments = parser.parse_args()
    with TemporaryDirectory(prefix=".md_screening_verify_", dir=PROJECT) as directory:
        root = Path(directory).resolve()
        assert root.parent == PROJECT
        temporary = root / "tmp"
        temporary.mkdir()
        source_paths = [str(PROJECT)] + ([str(LIBRARY)] if LIBRARY is not None else [])
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TEMP=str(temporary), TMP=str(temporary),
                           PYTHONPATH=os.pathsep.join(filter(None, (*source_paths, os.environ.get("PYTHONPATH", "")))),
                           PIP_DISABLE_PIP_VERSION_CHECK="1")
        run(["-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(root / "pytest")], PROJECT, environment)
        if arguments.package:
            # pip's hashed wheel paths can exceed Windows MAX_PATH under root/tmp.
            with TemporaryDirectory(prefix=".p_", dir=PROJECT.parent) as pip_directory:
                assert Path(pip_directory).resolve().parent == PROJECT.parent
                check_package(root, dict(environment, TEMP=pip_directory, TMP=pip_directory))
    print(f"Verification temporary directory removed: {not root.exists()}", flush=True)


if __name__ == "__main__":
    main()

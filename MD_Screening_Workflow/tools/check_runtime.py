"""Check this runtime's dependency closure and that its borrowed bases are unchanged."""
import hashlib
from importlib.metadata import distribution, distributions
import json
from pathlib import Path
import subprocess
import sys

from packaging.requirements import Requirement


PROJECT = Path(__file__).resolve().parents[1]


def main():
    if Path(sys.prefix).resolve() != PROJECT / ".venv":
        raise SystemExit("Run with this project's .venv/Scripts/python.exe")
    pending = [(name, frozenset()) for name in (
        "mace-torch", "gemdat", "kinisi", "pymatgen-analysis-diffusion", "md-screening-workflow")]
    pending.append(("process-md", frozenset(("mace", "analysis", "jumps", "uncertainty"))))
    visited, versions, errors = set(), {}, []
    while pending:
        name, extras = pending.pop()
        if (name.lower(), extras) in visited:
            continue
        visited.add((name.lower(), extras))
        installed = distribution(name)
        versions[installed.metadata["Name"]] = installed.version
        for declaration in installed.requires or ():
            requirement = Requirement(declaration)
            if requirement.marker and not any(requirement.marker.evaluate({"extra": extra}) for extra in extras | {""}):
                continue
            try:
                dependency = distribution(requirement.name)
            except ModuleNotFoundError:
                errors.append(f"{name}: missing {requirement}")
                continue
            if not requirement.specifier.contains(dependency.version, prereleases=True):
                errors.append(f"{name}: needs {requirement}; found {dependency.version}")
            pending.append((requirement.name, frozenset(requirement.extras)))
    if errors:
        raise RuntimeError("\n".join(errors))
    print(f"RUNTIME_DEPENDENCIES_OK: {len(versions)} packages", flush=True)
    from process_md import check_jump_backend, check_uncertainty_backend
    check_jump_backend()
    check_uncertainty_backend()
    print("GEMDAT_KINISI_APIS_OK", flush=True)
    before = json.loads((PROJECT / ".venv/base-environment-before.json").read_text(encoding="utf-8"))
    snapshot_code = "import importlib.metadata as m,json; print(json.dumps(sorted((d.metadata['Name'],d.version,str(d.locate_file(''))) for d in m.distributions()),sort_keys=True))"
    bases = {}
    for name in ("py1", "py-mace"):
        executable = Path(sys.base_prefix).parent / name / "python.exe"
        after = json.loads(subprocess.check_output([str(executable), "-B", "-c", snapshot_code],
                                                   cwd=PROJECT.parent, text=True))
        # Source-tree egg-info can appear after editable installation; base-site
        # and user-site distributions must remain byte-for-byte equal as records.
        original = [entry for entry in before[name]["packages"] if not Path(entry[2]).is_relative_to(PROJECT.parent)]
        current = [entry for entry in after if not Path(entry[2]).is_relative_to(PROJECT.parent)]
        if original != current:
            raise RuntimeError(f"{name} package metadata changed")
        bases[name] = dict(unchanged=True, package_count=len(current),
                           sha256=hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest())
    # The borrowed base has unrelated optional-package conflicts (e.g. SevenNet
    # needs a different e3nn); don't upgrade the MACE stack to silence those.
    check = subprocess.run([sys.executable, "-B", "-m", "pip", "check"], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base_check = subprocess.run([str(Path(sys.base_prefix) / "python.exe"), "-B", "-m", "pip", "check"],
                                cwd=PROJECT.parent, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    unexpected = set(check.stdout.splitlines()) - set(base_check.stdout.splitlines())
    if unexpected:
        raise RuntimeError("New dependency conflicts: " + "; ".join(sorted(unexpected)))
    result = dict(python=sys.executable, versions=versions, base_environments=bases,
                  full_pip_check_exit=check.returncode, full_pip_check=check.stdout.splitlines(),
                  conflicts_match_borrowed_base=True)
    (PROJECT / ".venv/runtime-check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("BASE_ENVIRONMENTS_UNCHANGED", bases, flush=True)
    print("FULL_PIP_CHECK_EXIT", check.returncode, "(unrelated inherited packages; see runtime-check.json)", flush=True)


if __name__ == "__main__":
    main()

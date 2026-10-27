"""Generate tiny Cu/Au EMT demo inputs; refuses to overwrite any existing directory."""
import argparse
from pathlib import Path

from ase.build import bulk
from ase.io import write
import yaml


def make_demo(directory, quick=False):
    """Create synthetic structures and YAML; EMT is only an end-to-end demonstration."""
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    copper = bulk("Cu", "fcc", a=3.6, cubic=True)
    gold = bulk("Au", "fcc", a=4.08, cubic=True)
    alloy = bulk("Cu", "fcc", a=3.85, cubic=True)
    alloy[0].symbol = "Au"
    structures = []
    for name, atoms in (("Cu", copper), ("Au", gold), ("Cu3Au", alloy),
                        ("Cu3Au_32", alloy.repeat((2, 2, 2)))):
        write(root / f"{name}.extxyz", atoms)
        structures.append(dict(id=name, path=f"{name}.extxyz"))
    config = dict(output_dir="results", seed=42,
                  models=[dict(id="emt_demo", type="emt", device="cpu")], structures=structures,
                  relax=dict(fmax=0.1, steps=2000, maxstep=0.2),
                  md=dict(temperature_K=800, timestep_fs=2, steps=20 if quick else 1000),
                  ehull=dict(reference_csv=None, tolerance_eV_per_atom=1e-6))
    path = root / "demo.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--quick", action="store_true", help="20 MD steps instead of 1000")
    args = parser.parse_args()
    print(make_demo(args.directory, args.quick))

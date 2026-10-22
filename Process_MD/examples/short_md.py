"""Check the existing MD adapter with eight LJ steps; no MLIP weights."""
from pathlib import Path
from tempfile import TemporaryDirectory

from ase.build import bulk
from ase.calculators.lj import LennardJones

from process_md import MDRunner


def main() -> None:
    atoms = bulk("Ar", "fcc", a=5.3, cubic=True)
    calculator = LennardJones(epsilon=0.0103, sigma=3.4, rc=8.0)
    workspace = Path.cwd().resolve()
    with TemporaryDirectory(prefix="process_md_example_", dir=workspace) as directory:
        root = Path(directory).resolve()
        assert root.parent == workspace
        result = MDRunner(calculator).run(
            atoms, temperature_K=100, duration_ps=0.005, equilibration_ps=0.003,
            timestep_fs=1, output_dir=root / "run", trajectory_interval=1, seed=42,
        )
        print(f"MD status: {result.status}; production steps: {result.steps_completed}")
        print("Used Process_MLIP NVT; this is an interface check, not MLIP validation.")
    print("Temporary example files removed.")


if __name__ == "__main__":
    main()

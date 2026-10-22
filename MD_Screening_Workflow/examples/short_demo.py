"""Disposable 7-step LJ demo; no weights, no scientific acceptance claim."""
from pathlib import Path
from tempfile import TemporaryDirectory

from ase.build import bulk
from ase.calculators.lj import LennardJones

from md_screening import ScreeningConfig, run_screening


def main() -> None:
    workspace = Path.cwd().resolve()
    with TemporaryDirectory(prefix="md_screening_demo_", dir=workspace) as directory:
        root = Path(directory).resolve()
        assert root.parent == workspace
        atoms = bulk("LiF", "rocksalt", a=5.3, cubic=True)
        result = run_screening(
            atoms, reference_sites=atoms,
            calculator=LennardJones(epsilon=0.0103, sigma=1.8, rc=3),
            output_dir=root / "case",
            config=ScreeningConfig(target_atoms=8, temperature_K=100, precheck_ps=0.002,
                                   check_interval_ps=0.004, max_production_ps=0.012,
                                   trajectory_interval=1, model_label="LJ interface check", stop_criteria=None,
                                   jump_analysis=False),
        )
        print(f"{result.status}: {len(result.check_reports)} checks; {result.md.steps_completed} MD steps")
        print(f"Transport: {result.last_check.transport_status}; no acceptance criteria applied.")
    print("Demo temporary files removed.")


if __name__ == "__main__":
    main()

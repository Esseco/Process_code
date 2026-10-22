"""Runnable foundation example; synthetic input, no MD or model loading."""
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from ase import Atoms
from ase.io import write

from process_md import MDConfig, get_structure_info, prepare_structure, save_csv, save_results


def main() -> None:
    # Synthetic geometry demonstrates I/O only; it is not a validated material.
    crystal = Atoms("LiO", scaled_positions=[[0, 0, 0], [0.5, 0.5, 0.5]],
                    cell=[4, 4, 4], pbc=True)
    workspace = Path.cwd().resolve()
    with TemporaryDirectory(prefix="process_md_example_", dir=workspace) as directory:
        root = Path(directory).resolve()
        assert root.parent == workspace
        write(root / "POSCAR", crystal, format="vasp")
        atoms = prepare_structure(root / "POSCAR", target_atoms=7)
        info = get_structure_info(atoms)
        config = MDConfig(temperature_K=800, duration_ps=50, equilibration_ps=5, seed=42)
        output = root / "preparation"
        save_results({"structure": info, "parameters": config}, output)
        save_csv([asdict(config)], output / "parameters.csv")
        print(f"Prepared {info.n_atoms} atoms; production plan: {config.production_steps} steps")
        print("Saved preparation JSON and CSV; no MD was run.")
    print("Temporary example files removed.")


if __name__ == "__main__":
    main()

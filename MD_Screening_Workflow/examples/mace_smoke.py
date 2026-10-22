"""Small real MACE-OMat run; compressed windows only test the integration."""
import argparse
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import time

from ase.build import bulk
from md_screening import ScreeningConfig, StopCriteria, run_screening
from process_md import save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--lattice-a", type=float, default=4.0)
    parser.add_argument("--threads", type=int, default=2)
    arguments = parser.parse_args()
    if not arguments.model_path.is_file() or arguments.output_dir.exists() or arguments.threads < 1:
        parser.error("Existing local weights, a new output directory and positive thread count are required")
    import torch
    torch.set_num_threads(arguments.threads)
    torch.set_num_interop_threads(1)
    atoms = bulk("LiF", "rocksalt", a=arguments.lattice_a, cubic=True)
    config = ScreeningConfig(
        target_atoms=len(atoms), temperature_K=800, precheck_ps=0.1,
        check_interval_ps=0.6, max_production_ps=1.8, timestep_fs=1,
        trajectory_interval=5, min_obs=1, fit_start_ps=1.0,
        model_path=arguments.model_path, device="cpu", configuration_id="LiF_real_MACE_smoke",
        framework_rdf_repeat=(2, 2, 2),
        stop_criteria=StopCriteria(min_production_ps=0.6, no_jump_stop_ps=0.6),
    )
    print("Real MACE-OMat / CPU / 8 atoms: 0.1 ps precheck, 0.6 ps checks, <=1.8 ps production.", flush=True)
    started = time.perf_counter()
    result = run_screening(atoms, output_dir=arguments.output_dir, config=config, reference_sites=atoms)
    report = result.last_check
    smoke = dict(
        status=result.status, elapsed_s=time.perf_counter()-started,
        n_atoms=len(atoms), lattice_a_A=arguments.lattice_a,
        model_sha256=sha256(arguments.model_path.read_bytes()).hexdigest(),
        steps_completed=result.md.steps_completed, md_status=result.md.status,
        total_time_ps=report.total_time_ps, production_time_ps=report.production_time_ps,
        framework_status=report.framework_status, framework=asdict(report.framework),
        jump_analysis=None if report.jumps is None else asdict(report.jumps),
        transport_status=report.transport_status, mobility_status=report.mobility_status,
        stop_metrics=report.stop_metrics, decision=asdict(report.decision),
        limitations=[
            "Compressed smoke windows do not replace the 5 ps + 10 ps production defaults.",
            "Eight atoms, min_obs=1 and a short trajectory cannot establish transport or size convergence.",
            "RDF periodic images improve small-cell diagnostics, not independent sampling or MD supercell size.",
            "The example lattice parameter is from a coarse MACE energy scan, not a converged thermal cell.",
        ],
    )
    save_json(smoke, result.output_dir / "smoke_summary.json")
    print(f"{result.status}; {result.md.steps_completed} steps; {smoke['elapsed_s']:.1f} s", flush=True)
    print(f"Framework={report.framework_status}, jumps={None if report.jumps is None else report.jumps.n_jumps}, action={report.decision.action}", flush=True)


if __name__ == "__main__":
    main()

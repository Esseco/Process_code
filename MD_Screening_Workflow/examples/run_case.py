"""Run one real case with a local MACE-OMat checkpoint and coarse stopping."""
import argparse
from pathlib import Path

from md_screening import ScreeningConfig, StopCriteria, run_screening


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--species", choices=("Li", "Na"), default="Li")
    parser.add_argument("--temperature-K", type=float, default=800,
                        help="NVT target and initial velocity temperature in K (default 800)")
    parser.add_argument("--max-production-ps", type=float, default=200,
                        help="production cap in ps, excluding 5 ps precheck; multiple of 10 (default 200)")
    parser.add_argument("--model-path", type=Path, help="or set PROCESS_MD_MACE_MODEL")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--enable-cueq", action="store_true")
    parser.add_argument("--enable-symmetrix", action="store_true")
    parser.add_argument("--symmetrix-use-kokkos", action="store_true")
    parser.add_argument("--symmetrix-species", nargs="+", default=None,
                        help="element symbols passed to Symmetrix model conversion")
    parser.add_argument("--hop-distance-A", type=float, default=None)
    parser.add_argument("--uncertainty", action="store_true", help="run kinisi once on an eligible estimate")
    parser.add_argument("--reference-sites", type=Path, required=True,
                        help="full-site reference, including vacancies, in the input cell")
    parser.add_argument("--no-jump-stop-ps", type=float, default=10, help="production no-jump+plateau window (default 10 ps)")
    arguments = parser.parse_args()
    if not arguments.structure.is_file() or (arguments.model_path is not None and not arguments.model_path.is_file()):
        parser.error("Structure and supplied model must be existing files")
    if arguments.output_dir.exists():
        parser.error("output_dir must not exist")
    if not arguments.reference_sites.is_file():
        parser.error("reference-sites must be an existing full-site structure")
    if arguments.enable_symmetrix and arguments.device == "cuda" and not arguments.symmetrix_use_kokkos:
        parser.error("CUDA Symmetrix requires --symmetrix-use-kokkos")
    config = ScreeningConfig(mobile_species=arguments.species, model_path=arguments.model_path,
                             temperature_K=arguments.temperature_K,
                             max_production_ps=arguments.max_production_ps,
                             device=arguments.device, configuration_id=arguments.structure.stem,
                             enable_cueq=arguments.enable_cueq,
                             enable_symmetrix=arguments.enable_symmetrix,
                             symmetrix_use_kokkos=arguments.symmetrix_use_kokkos,
                             symmetrix_species=None if arguments.symmetrix_species is None
                             else tuple(arguments.symmetrix_species),
                             hop_distance_A=arguments.hop_distance_A, uncertainty_on_stop=arguments.uncertainty,
                             stop_criteria=StopCriteria(no_jump_stop_ps=arguments.no_jump_stop_ps))
    print(
        f"MACE-OMat/{config.device}: {config.temperature_K:g} K; "
        f"{config.precheck_ps:g} ps framework precheck; "
        f"{config.check_interval_ps:g} ps production checks with GEMDAT; "
        f"production cap {config.max_production_ps:g} ps "
        f"(total cap {config.precheck_ps + config.max_production_ps:g} ps); "
        f"Symmetrix={arguments.enable_symmetrix}", flush=True,
    )
    result = run_screening(arguments.structure, output_dir=arguments.output_dir, config=config,
                           reference_sites=arguments.reference_sites)
    print(f"{result.status}: {result.output_dir / 'run.json'}")
    print(f"Check summaries: {result.output_dir / 'summary.csv'}")
    report = result.last_check
    if report is not None:
        print(f"Transport status: {report.transport_status}")
        if report.msd is not None:
            print(f"MSD last lag: {report.msd.msd_A2[-1]:.6g} A^2 "
                  f"at {report.msd.time_ps[-1]:.6g} ps")
            print(f"MSD curve: {result.check_reports[-1].parent / 'msd.csv'}")
        fit = report.transport
        print(f"D [cm^2/s]: {None if fit is None else fit.diffusion_cm2_s}")
        print(f"sigma_NE [S/cm]: {None if fit is None else fit.conductivity_NE_S_cm}")
        print(f"R^2: {None if fit is None else fit.r_squared}")
        if report.decision is not None:
            print(f"Decision: {report.decision.action}; {report.decision.reason}")


if __name__ == "__main__":
    main()

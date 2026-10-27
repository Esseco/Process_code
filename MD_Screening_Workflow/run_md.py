"""Edit the inputs/preset below, then python run_md.py (no automatic supercell)."""
import argparse
from pathlib import Path

try:
    from MD_Screening_Workflow import run_md
except ModuleNotFoundError as exc:
    if exc.name != "MD_Screening_Workflow":
        raise
    from md_screening import run_md  # installed package or source-local script


# Input is already the supercell that will run MD.
STRUCTURE_PATH = "POSCAR_SOC"
REFERENCE_SITES_PATH = "POSCAR_FULL"  # same cell/origin, including vacant ion sites
OUTPUT_DIR = None  # None: runs/<structure>_<timestamp>; an explicit path must be new

# Other defaults live in md_screening/presets.py and config.py.
# CUDA + Symmetrix, cell LBFGS/1000 steps, 5 ps precheck, 10 ps checks, 2 fs/20 fs.
PRESET = dict(
    temperature_K=800,
    max_production_ps=200,
    compress_trajectory=True,  # verified gzip archive after all MD/analysis completes
    model_path=None,  # local path, PROCESS_MD_MACE_MODEL, or sibling MLIP_model/mace/
    # mobile_species="Li",  # automatically Li/Na; specify if both are present
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, nargs="?", default=STRUCTURE_PATH)
    parser.add_argument("reference_sites", type=Path, nargs="?", default=REFERENCE_SITES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = run_md(args.structure, reference_sites=args.reference_sites,
                    output_dir=args.output, **PRESET)
    print(f"Status: {result.status}")
    print(f"Result: {result.output_dir / 'results/summary.json'}")
    if result.last_check is not None:
        fit = result.last_check.transport
        print(f"Transport: {result.last_check.transport_status}")
        print(f"D [cm^2/s]: {None if fit is None else fit.diffusion_cm2_s}")
        print(f"sigma_NE [S/cm]: {None if fit is None else fit.conductivity_NE_S_cm}")


if __name__ == "__main__":
    main()

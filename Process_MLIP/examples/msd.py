"""Export every saved NVT frame to MSD CSV using ASE's analysis.

From repository root, after editing INPUT/SPECIES:
    python -m Process_MLIP.examples.msd
No MLIP environment, model weights, fitting or plotting required.
"""
from pathlib import Path

from Process_MLIP import export_msd, fit_msd


# Select the NVT MD trajectory to analyze (not the static optimizer trajectory).
INPUT = Path("md_results/03_diffusion/md.traj")
OUTPUT = Path("md_results/03_diffusion/msd.csv")
SPECIES = "Na"                       # "Li", ["Na", "Li"], or None for all elements
FRAME_INTERVAL_FS = None              # infer from adjacent report.json
# For external trajectories without our MD report, fill the time BETWEEN
# SAVED FRAMES, e.g. MD dt=1 fs with interval=10 means FRAME_INTERVAL_FS=10.
UNWRAP = False                        # our MD saves unwrapped positions
# True only for trajectories whose coordinates were wrapped into the cell.
DRIFT_REFERENCE = None                # optionally "framework" to subtract framework COM motion
OVERWRITE = False

# Optional fitting of the exported CSV. Use the actual NVT temperature/volume.
TRANSPORT_FIT = {
    "enabled": False,
    "fit_start_ps": 2.0,
    "fit_end_ps": 8.0,
    "temperature_K": 800,
    "volume_A3": 1000.0,
    "ion_charge": 1,                  # or {"Na": 1, "Li": 1}, units e
    "output_json": Path("md_results/03_diffusion/transport.json"),
    "overwrite": False,
}


def main():
    """Export the entire trajectory, with frame zero as the MSD origin."""
    result = export_msd(INPUT, OUTPUT, species=SPECIES,
                        frame_interval_fs=FRAME_INTERVAL_FS, unwrap=UNWRAP,
                        drift_reference=DRIFT_REFERENCE, overwrite=OVERWRITE)
    print(f"MSD: {result['csv_file']}")
    print(f"Frames: {result['frame_count']}; species: {result['species']}")
    print(f"Time source: {result['time_source']}; MSD unit: angstrom^2")
    if TRANSPORT_FIT["enabled"]:
        options = {k: v for k, v in TRANSPORT_FIT.items() if k != "enabled"}
        fitted = fit_msd(OUTPUT, **options)
        print(f"Transport: {TRANSPORT_FIT['output_json']}")
        for row in fitted["results"]:
            print(f"{row['species']}: D={row['diffusion_cm2_s']:.6g} cm2/s; "
                  f"sigma_NE={row['conductivity_NE_S_cm']:.6g} S/cm")


if __name__ == "__main__":
    main()

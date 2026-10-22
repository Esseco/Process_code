"""Export multi-time-origin NVT MSD CSV using pymatgen-analysis-diffusion.

From repository root, after editing INPUT/SPECIES:
    python -m Process_MLIP.examples.msd
Requires the analysis package, no model weights or MLIP environment.
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
SKIP_FRAMES = 0                       # 跳过平衡段保存帧
NUMBER_OF_SEGMENTS = 1                # 各段独立做多起点平均；需足够长
MIN_OBS = 30                         # pymatgen max 模式采样阈值
OVERWRITE = False

# 拟合使用 pymatgen 原生默认值；手动选区间和电荷，填写实际 NVT 温度/体积。
TRANSPORT_FIT = {
    "enabled": False,
    "fit_start_ps": None,            # None: 最早正 lag；可填 ps
    "fit_end_ps": None,              # None: 最晚有效 lag；可填 ps
    "temperature_K": 800,
    "volume_A3": 1000.0,
    "ion_charge": 1,                  # or {"Na": 1, "Li": 1}, units e
    "diffusion_mode": "auto",         # "3d" 关闭，"2d"/"1d" 手动
    "axes": "xy",                     # 手动模式的 Cartesian 轴
    "anisotropy_threshold": 10,        # 拟合区间末端 MSD 分量倍率，>1
    "min_msd_A2": 1.0,                # 末端总 MSD 门槛，Å²；0 关闭
    "output_json": Path("md_results/03_diffusion/transport.json"),
    "overwrite": False,
}


def main():
    """Export native max-mode lag sampling; fit only an explicitly chosen range."""
    result = export_msd(INPUT, OUTPUT, species=SPECIES,
                        frame_interval_fs=FRAME_INTERVAL_FS, unwrap=UNWRAP,
                        drift_reference=DRIFT_REFERENCE, overwrite=OVERWRITE,
                        skip_frames=SKIP_FRAMES, number_of_segments=NUMBER_OF_SEGMENTS,
                        min_obs=MIN_OBS)
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

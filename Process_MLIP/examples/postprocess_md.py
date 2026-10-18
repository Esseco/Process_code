"""已有固定晶胞 NVT 轨迹：重算 MSD → 扩散系数 → Nernst–Einstein 电导率。

在项目根目录运行：python -m Process_MLIP.examples.postprocess_md
需要已有 pymatgen-analysis-diffusion；不加载模型。重复运行覆盖本示例的分析输出。
"""
from pathlib import Path
from ase.io import read
from Process_MLIP import export_msd, fit_msd


TRAJECTORY = Path("md_results/01_production/md.traj")
OUTPUT_DIR = TRAJECTORY.parent / "postprocess"
SPECIES = "Li"                      # "Na" 或元素列表
FIT_START_PS = None                  # None: 最早正 lag；可手动填 ps
FIT_END_PS = None                    # None: 最晚有效 lag；可手动填 ps
ION_CHARGE = 1                      # 电荷数；多元素如 {"Li": 1, "Na": 1}
TEMPERATURE_K = 600                  # 实际 NVT 温度；体积自动从轨迹读取
FRAME_INTERVAL_FS = None             # 自动读同目录 report.json；无报告时填保存帧间隔


def main():
    """复用项目后处理函数；只写 msd.csv 和 transport.json。"""
    volume = read(str(TRAJECTORY), index=0).get_volume()
    msd_csv = OUTPUT_DIR / "msd.csv"
    transport_json = OUTPUT_DIR / "transport.json"
    export_msd(TRAJECTORY, msd_csv, species=SPECIES,
               frame_interval_fs=FRAME_INTERVAL_FS, overwrite=True)
    result = fit_msd(msd_csv, species=SPECIES,
                     fit_start_ps=FIT_START_PS, fit_end_ps=FIT_END_PS,
                     temperature_K=TEMPERATURE_K, volume_A3=volume,
                     ion_charge=ION_CHARGE, output_json=transport_json, overwrite=True)
    print(f"MSD: {msd_csv}\nTransport: {transport_json}")
    for row in result["results"]:
        print(f"{row['species']}: D={row['diffusion_cm2_s']:.6g} cm²/s; "
              f"sigma_NE={row['conductivity_NE_S_cm']:.6g} S/cm")
    return result


if __name__ == "__main__":
    main()

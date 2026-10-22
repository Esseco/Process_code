"""扫描 模型/results/体系/阶段/md.traj，重算 MSD 并汇总为平铺 CSV。

运行：python -m Process_MLIP.examples.batch_postprocess_md
自动读取阶段 report.json；只覆盖分析 CSV 和汇总，不加载模型、不修改轨迹。
"""
from pathlib import Path
import json
import pandas as pd
from Process_MLIP import export_msd, fit_msd


INIT_DIR = Path("/data/home/lichaoyue/26-7-AEA/MLIP_MD_test")
OUTPUT_DIR = INIT_DIR / "00-final_results"
SUMMARY_CSV = INIT_DIR / "out.csv"
SPECIES = {"LCO": "Li", "NVP": "Na"}
FIT_START_PS = None                  # None: 最早正 lag；可手动填 ps
FIT_END_PS = None                    # None: 最晚有效 lag；可手动填 ps
ION_CHARGE = {"Li": 1, "Na": 1}     # 电荷数 z
DIFFUSION_MODE = "auto"              # "3d" 关闭检查，"2d"/"1d" 手动
AXES = "xy"                         # 手动模式的 Cartesian 轴
ANISOTROPY_THRESHOLD = 10            # 拟合区间末端 MSD 倍率，>1；Cartesian 轴
MIN_MSD_A2 = 1.0                    # 末端总 MSD 门槛，Å²；0 关闭


def main():
    """每个 NVT 阶段一行；失败也记录，避免一个任务中断整批。"""
    if not INIT_DIR.is_dir():
        raise NotADirectoryError(INIT_DIR)
    results = []
    for md_file in sorted(INIT_DIR.rglob("md.traj")):
        system_dir = md_file.parent.parent
        system = system_dir.name
        if system not in SPECIES or OUTPUT_DIR.resolve() in md_file.resolve().parents:
            continue
        method = system_dir.parent.parent.name
        stage = md_file.parent.name
        res = dict(method=method, system=system, stage=stage, trajectory=str(md_file))
        try:
            report = json.loads((md_file.parent / "report.json").read_text(encoding="utf-8"))
            params = report["parameters"]
            if params["ensemble"].lower() != "nvt":
                continue
            if report["status"] != "completed":
                raise ValueError("MD stage is not completed")
            temperature = params["temperature_K"]
            volume = report["final_state"]["volume_angstrom3"]
            res.update(temperature_K=temperature, volume_A3=volume,
                       time_fs=report["steps_completed"] * params["timestep_fs"],
                       steps=report["steps_completed"], steps_per_second=report["steps_per_second"])
            csv_path = OUTPUT_DIR / method / system / f"{stage}_msd.csv"
            species = SPECIES[system]
            export_msd(md_file, csv_path, species=species, overwrite=True)
            fitted = fit_msd(csv_path, species=species,
                             fit_start_ps=FIT_START_PS, fit_end_ps=FIT_END_PS,
                             temperature_K=temperature, volume_A3=volume,
                             diffusion_mode=DIFFUSION_MODE, axes=AXES,
                             anisotropy_threshold=ANISOTROPY_THRESHOLD,
                             min_msd_A2=MIN_MSD_A2,
                             ion_charge=ION_CHARGE[species])
            row = fitted["results"][0]
            res.update(status="completed", species=species, ion_charge=row["ion_charge"],
                       diffusion_cm2_s=row["diffusion_cm2_s"],
                       conductivity_NE_S_cm=row["conductivity_NE_S_cm"],
                       r_squared=row["r_squared"]["total"],
                       fit_start_ps=row["actual_fit_range_ps"][0],
                       fit_end_ps=row["actual_fit_range_ps"][1],
                       slope_floor_applied=row["pymatgen_slope_floor_applied"]["total"],
                       msd_csv=str(csv_path))
            res.update(anisotropy_status=row["anisotropy"]["status"],
                       anisotropy_threshold=ANISOTROPY_THRESHOLD,
                       min_msd_A2=MIN_MSD_A2, low_msd=row["low_msd"],
                       endpoint_total_msd_A2=row["anisotropy"]["endpoint_total_msd_A2"])
            for index, axis in enumerate("xyz"):
                res[f"D{axis}_m2_s"] = row["directional_diffusion_m2_s"][index]
                res[f"sigma_{axis}_S_cm"] = row["directional_conductivity_NE_S_cm"][index]
            reduced = row["reduced_dimensional"]
            res.update(reduced_dimension=None, reduced_axes=None,
                       reduced_diffusion_cm2_s=None, reduced_conductivity_NE_S_cm=None,
                       reduced_r_squared=None, reduced_slope_floor_applied=None)
            if reduced is not None:
                res.update(reduced_dimension=reduced["dimension"], reduced_axes=reduced["axes"],
                           reduced_diffusion_cm2_s=reduced["diffusion_cm2_s"],
                           reduced_conductivity_NE_S_cm=reduced["conductivity_NE_S_cm"],
                           reduced_r_squared=reduced["r_squared"],
                           reduced_slope_floor_applied=reduced["pymatgen_slope_floor_applied"])
        except Exception as exc:
            res.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            print(f"失败：{md_file}\n{res['error']}")
        results.append(res)
    if not results:
        raise ValueError("No matching LCO/NVP MD trajectories found")
    df = pd.DataFrame(results)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SUMMARY_CSV, index=False)
    print(f"汇总：{SUMMARY_CSV}")
    return df


if __name__ == "__main__":
    main()

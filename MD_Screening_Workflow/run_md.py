"""先填写下方两份结构路径，再运行 python run_md.py。支持 POSCAR、CIF、extxyz。"""
import argparse
from datetime import datetime
import os
from pathlib import Path

from ase.io import read
from MD_Screening_Workflow import ScreeningConfig, run_screening


# ===== 输入结构：在这里填写实际文件路径 =====
STRUCTURE_PATH = r"POSCAR_SOC"           # 当前SOC结构，用于实际MD
REFERENCE_SITES_PATH = r"POSCAR_FULL"    # 满位点参考，须与当前结构使用相同晶胞和原点

# ===== 计算参数 =====
TEMPERATURE_K = 800
MAX_PRODUCTION_PS = 200                 # 不含前5 ps初检，须为10的整数倍
MODEL_PATH = None                       # 可填模型路径；None时自动查找
MOBILE_SPECIES = None                   # 自动识别Li/Na；两者都有时填写"Li"或"Na"
DEVICE = "cuda"
ENABLE_SYMMETRIX = True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, nargs="?", default=STRUCTURE_PATH,
                        help="可选，覆盖顶部 STRUCTURE_PATH")
    parser.add_argument("reference_sites", type=Path, nargs="?", default=REFERENCE_SITES_PATH,
                        help="可选，覆盖顶部 REFERENCE_SITES_PATH")
    args = parser.parse_args()
    structure = args.structure.expanduser().resolve()
    if not structure.is_file():
        parser.error(f"结构文件不存在：{structure}")
    reference = args.reference_sites.expanduser().resolve()
    if not reference.is_file():
        parser.error(f"满位点参考结构不存在：{reference}")

    species = MOBILE_SPECIES
    if species is None:
        candidates = set(read(str(structure), index=0).get_chemical_symbols()) & {"Li", "Na"}
        if len(candidates) != 1:
            parser.error('无法唯一识别移动离子，请在脚本顶部设置 MOBILE_SPECIES="Li" 或 "Na"')
        species = candidates.pop()

    model = MODEL_PATH or os.environ.get("PROCESS_MD_MACE_MODEL")
    if not model:
        import Process_MLIP
        model = Path(Process_MLIP.__file__).resolve().parent.parent / "MLIP_model/mace/mace-omat-0-medium.model"
    model = Path(model).expanduser().resolve()
    if not model.is_file():
        parser.error(f"模型不存在：{model}；请设置顶部 MODEL_PATH 或环境变量 PROCESS_MD_MACE_MODEL")

    output = Path.cwd() / "runs" / f"{structure.stem}_{datetime.now():%Y%m%d_%H%M%S_%f}"
    config = ScreeningConfig(
        mobile_species=species, model_path=model, configuration_id=structure.stem,
        temperature_K=TEMPERATURE_K, max_production_ps=MAX_PRODUCTION_PS,
        device=DEVICE, enable_symmetrix=ENABLE_SYMMETRIX,
        symmetrix_use_kokkos=ENABLE_SYMMETRIX, timestep_fs=2, trajectory_interval=10,
    )
    print(f"{species} / {TEMPERATURE_K} K / {DEVICE} / Symmetrix={ENABLE_SYMMETRIX}", flush=True)
    print(f"结果目录：{output}", flush=True)
    result = run_screening(structure, reference_sites=reference, config=config, output_dir=output)
    print(f"结束状态：{result.status}\n汇总：{output / 'summary.csv'}")
    report = result.last_check
    if report is not None:
        fit = report.transport
        print(f"分析状态：{report.transport_status}")
        print(f"D [cm²/s]：{None if fit is None else fit.diffusion_cm2_s}")
        print(f"σ_NE [S/cm]：{None if fit is None else fit.conductivity_NE_S_cm}")
        print(f"R²：{None if fit is None else fit.r_squared}")
        if report.msd is not None:
            print(f"MSD 曲线：{result.check_reports[-1].parent / 'msd.csv'}")


if __name__ == "__main__":
    main()

"""Editable cluster MD example. Importing or --preview does not load models.

From repository root: python -m Process_MLIP.examples.mlip_md --preview
After editing paths/config: python -m Process_MLIP.examples.mlip_md
Use the cluster environment installed for the selected backend; no pip calls.
"""
import argparse
import json
import math
from numbers import Real
from pathlib import Path

from Process_MLIP import export_msd, fit_msd, model_config, run_mlip_md
from Process_MLIP.msd import _load_diffusion_analyzer, _msd_lags
from Process_MLIP.transport import _fit_window_mask, _load_pymatgen_fitter, _validate_dimension_options


# 路径与模型
INPUT = Path("initial.cif")            # 输入结构
OUTPUT = Path("md_results")           # 结果目录
MODEL_PRESET = "mace-mh1"              # mace-mh1 / sevennet-omni / chgnet / orb-v3
DEVICE = "cuda"                       # cuda / cuda:0 / cpu

# 只填写需覆盖的模型参数。
# model_path=None: 官方预训练；离线时填写本地路径。

MODEL_OVERRIDES = {
    "mace-mh1": {
        # 本地权重示例：
        # "model_path": "/absolute/path/to/mace-mh-1.model",
        "head": "omat_pbe",           # 任务头，如 matpes_r2scan
        "default_dtype": "float64",   # float32 / float64
        "enable_cueq": False,         # CuEq 加速
        "enable_symmetrix": False,    # Symmetrix，与 CuEq 互斥
        "symmetrix_use_kokkos": False, # Kokkos；目标由安装构建决定
        "symmetrix_species": None,    # 裁剪元素，如 ["Na", "O"]
        # OMat: head=None；CPU: device="cpu"。

        # Symmetrix JSON: head=None，symmetrix_species=None。
    },
    "sevennet-omni": {
        "model_path": None,           # 本地 checkpoint 或 None
        "modal": "mpa",               # 任务，如 omat24 / matpes_r2scan
        "enable_flash": False,        # FlashTP 加速
    },
    "chgnet": {
        "model_path": None,           # 本地 checkpoint 或 None
        "model_name": "0.3.0",        # 预训练版本；本地权重优先
    },
    "orb-v3": {
        "model_path": None,           # 本地权重须匹配 model_name
        "model_name": "orb-v3-conservative-inf-omat",
        "precision": "float32-highest",
        "compile": False,             # torch.compile
    },
}

# 预弛豫，与 MD 复用模型。


PRE_RELAX = {
    "enabled": True,                # 是否预弛豫
    "relax_cell": True,               # False: 仅原子；True: 原子+晶胞
    "optimizer": "FIRE",              # BFGS / FIRE / LBFGS（大写）
    "fmax": 0.05,                     # 收敛阈值，eV/Å
    "steps": 200,                    # 最大步数，非负整数
    "maxstep": 0.05,                 # 优化步幅上限，Å
    "exp_cell_factor": None,         # None: 晶胞变量按原子数缩放
    "require_convergence": True,      # 未收敛则停止 MD
}

# MD 公共参数；阶段参数优先。
MD_PARAMETERS = {
    "temperature_K": 800,            # 温度，K
    "timestep_fs": None,             # None: NVT=2 fs、NPT=1 fs；可填数值
    "tdamp_fs": 100.0,               # 温控阻尼，fs
    "pressure_bar": 1.0,              # NPT 压力，bar，正值为压缩
    "pdamp_fs": 1000.0,               # NPT 压控阻尼，fs
    "npt_cell_mode": "isotropic",    # isotropic: 等比；full: 全晶胞
    "tchain": 3,                      # 温控链长度
    "pchain": 3,                      # NPT 压控链长度
    "tloop": 1,                       # 温控积分子步数
    "ploop": 1,                       # NPT 压控积分子步数
    "seed": 42,                      # 随机种子
    "initialize_velocities": None,    # None: 缺少动量时初始化
    "remove_com": True,               # 初始化时移除质心运动
    "zero_rotation": False,           # 周期晶体保持 False
    "trajectory_interval": 10,       # 轨迹输出间隔，步
    "log_interval": 10,              # 日志输出间隔，步
    "measure_steps_per_second": True, # 记录 steps/s，不含加载和弛豫
    "overwrite": False,               # 是否覆盖已有结果
}

# 阶段按顺序运行；ensemble 可选 nvt / npt。
STAGES = [
    {"name": "production", "ensemble": "nvt", "steps": 5000},
]

# MD 完成后用 pymatgen 多时间起点平均导出 NVT MSD。

MSD_POSTPROCESS = {
    "enabled": False,
    "stage": "last_nvt",             # 最后 NVT 或阶段序号（从 1 起）
    "species": "Na",                 # 元素、元素列表；None 为全部
    "output_csv": None,              # None: 阶段目录/msd.csv
    "skip_frames": 0,                # 跳过平衡段保存帧
    "min_obs": 30,                   # pymatgen 最低采样量；越大，最大 lag 越短
    "drift_reference": None,         # "framework": 扣除框架质心漂移
    # 相对路径以 OUTPUT 为根目录。

    "overwrite": False,
}


# 拟合需开启 MSD；None 用全部有效 lag，可手动选扩散线性区。
# 时间单位 ps，含两端，至少 3 个采样点。
TRANSPORT_FIT = {
    "enabled": False,
    "fit_start_ps": None,             # None: 最早正 lag；可填 ps
    "fit_end_ps": None,               # None: 最晚有效 lag；可填 ps
    "ion_charge": 1,                  # 电荷数，或 {"Na": 1, "Li": 1}
    "diffusion_mode": "auto",         # "3d" 关闭，"2d"/"1d" 手动
    "axes": "xy",                     # 手动模式的 Cartesian 轴
    "anisotropy_threshold": 10,        # 拟合区间末端 MSD 分量倍率，>1
    "min_msd_A2": 1.0,                # 末端总 MSD 门槛，Å²；0 关闭
    "output_json": None,              # None: MSD 同目录/transport.json
    "overwrite": False,
}


def _prepare_msd_postprocess():
    """Check the selected NVT stage and destination before starting MD."""
    if type(MSD_POSTPROCESS.get("enabled", False)) is not bool:
        raise TypeError("MSD_POSTPROCESS enabled must be bool")
    if not MSD_POSTPROCESS.get("enabled", False):
        return None
    if type(MSD_POSTPROCESS.get("overwrite", False)) is not bool:
        raise TypeError("MSD_POSTPROCESS overwrite must be bool")
    modes = [str(stage.get("ensemble", MD_PARAMETERS.get("ensemble", "nvt"))).lower()
             for stage in STAGES]
    choice = MSD_POSTPROCESS.get("stage", "last_nvt")
    if choice == "last_nvt":
        candidates = [index for index, mode in enumerate(modes) if mode == "nvt"]
        if not candidates:
            raise ValueError("Automatic MSD export requires an NVT stage")
        index = candidates[-1]
    elif type(choice) is int and 1 <= choice <= len(STAGES):
        index = choice - 1
    else:
        raise ValueError("MSD stage must be last_nvt or a stage number starting from 1")
    if modes[index] != "nvt":
        raise ValueError("MSD target must be an NVT stage")
    if STAGES[index].get("steps", MD_PARAMETERS.get("steps", 1000)) < 1:
        raise ValueError("MSD target needs at least one MD step and two saved frames")
    stage_dir = Path(OUTPUT) / f"{index + 1:02d}_{STAGES[index].get('name') or modes[index]}"
    configured = MSD_POSTPROCESS.get("output_csv")
    if configured is None:
        destination = stage_dir / "msd.csv"
    else:
        destination = Path(configured)
        if not destination.is_absolute():
            destination = Path(OUTPUT) / destination
    if destination.is_symlink() or destination.is_dir():
        raise FileExistsError(destination)
    destination = destination.resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("MSD output_csv must have a .csv extension")
    log_paths = {(Path(OUTPUT) / f"{i + 1:02d}_{stage.get('name') or modes[i]}" / "md.csv").resolve()
                 for i, stage in enumerate(STAGES)}
    if destination in log_paths:
        raise ValueError("MSD output_csv must not overwrite an MD log")
    if destination.exists() and not MSD_POSTPROCESS.get("overwrite", False):
        raise FileExistsError(destination)
    _load_diffusion_analyzer()  # 开启后处理时，在加载模型前检查依赖和采样量。
    from ase.io import read
    symbols = read(str(INPUT), index=0).get_chemical_symbols()
    selected = MSD_POSTPROCESS.get("species")
    selected = [selected] if isinstance(selected, str) else selected
    selected = sorted(set(symbols)) if selected is None else selected
    if not selected or any(element not in symbols for element in selected):
        raise ValueError("MSD selected species must be present in the input structure")
    stage = STAGES[index]
    steps = stage.get("steps", MD_PARAMETERS.get("steps", 1000))
    dt = stage.get("timestep_fs", MD_PARAMETERS.get("timestep_fs"))
    dt = 2.0 if dt is None else dt
    interval = stage.get("trajectory_interval", MD_PARAMETERS.get("trajectory_interval", 10))
    skip = MSD_POSTPROCESS.get("skip_frames", 0)
    min_obs = MSD_POSTPROCESS.get("min_obs", 30)
    if type(skip) is not int or skip < 0 or type(min_obs) is not int or min_obs < 1:
        raise ValueError("MSD skip_frames must be nonnegative and min_obs positive integers")
    count = steps // interval + 1 - skip  # 不计非等间隔的强制末帧。
    grids = [_msd_lags(count, dt * interval, symbols.count(element), min_obs)
             * dt * interval / 1000 for element in selected]
    return index, destination, grids


def main(argv=None):
    """Preview configuration or run MD after editing the parameters above."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="print configuration without reading structures or loading models")
    args = parser.parse_args(argv)
    model = model_config(MODEL_PRESET, device=DEVICE, **MODEL_OVERRIDES[MODEL_PRESET])
    print(json.dumps(dict(input=str(INPUT), output=str(OUTPUT), model=model,
                          pre_relax=PRE_RELAX, common_md=MD_PARAMETERS, stages=STAGES,
                          msd_postprocess=MSD_POSTPROCESS,
                          transport_fit=TRANSPORT_FIT), indent=2, default=str))
    if args.preview:
        return
    if not INPUT.is_file():
        raise FileNotFoundError(f"Edit INPUT before running MD: {INPUT}")
    msd_target = _prepare_msd_postprocess()
    if type(TRANSPORT_FIT.get("enabled", False)) is not bool:
        raise TypeError("TRANSPORT_FIT enabled must be bool")
    fit_destination = None
    if TRANSPORT_FIT.get("enabled", False):
        if msd_target is None:
            raise ValueError("TRANSPORT_FIT requires MSD_POSTPROCESS enabled")
        if type(TRANSPORT_FIT.get("overwrite", False)) is not bool:
            raise TypeError("TRANSPORT_FIT overwrite must be bool")
        _validate_dimension_options(TRANSPORT_FIT.get("diffusion_mode", "auto"),
                                    TRANSPORT_FIT.get("axes", "xy"),
                                    TRANSPORT_FIT.get("anisotropy_threshold", 10),
                                    TRANSPORT_FIT.get("min_msd_A2", 1.0))
        _load_pymatgen_fitter()
        start, end = (TRANSPORT_FIT.get(key) for key in ("fit_start_ps", "fit_end_ps"))
        for grid in msd_target[2]:
            _fit_window_mask(grid, start, end)
        charge = TRANSPORT_FIT["ion_charge"]
        values = list(charge.values()) if isinstance(charge, dict) else [charge]
        if not values or any(isinstance(v, bool) or not isinstance(v, Real)
                             or not math.isfinite(v) or v == 0 for v in values):
            raise ValueError("ion_charge must contain finite nonzero charge numbers")
        configured = TRANSPORT_FIT.get("output_json")
        fit_destination = (msd_target[1].with_name("transport.json") if configured is None
                           else Path(configured))
        if configured is not None and not fit_destination.is_absolute():
            fit_destination = Path(OUTPUT) / fit_destination
        if fit_destination.suffix.lower() != ".json":
            raise ValueError("Transport output_json must have .json extension")
        # 禁止覆盖输入和计算报告。
        forbidden = {Path(INPUT).resolve(), msd_target[1].resolve(),
                     (Path(OUTPUT) / "run_report.json").resolve()}
        for i, stage in enumerate(STAGES):
            mode = stage.get("ensemble", "nvt")
            forbidden.add((Path(OUTPUT) / f"{i+1:02d}_{stage.get('name') or mode}" / "report.json").resolve())
        forbidden.add((Path(OUTPUT) / "00_relax" / "report.json").resolve())
        if fit_destination.resolve() in forbidden:
            raise ValueError("Transport output cannot overwrite simulation data")
        if (fit_destination.is_symlink() or fit_destination.is_dir()
                or (fit_destination.exists() and not TRANSPORT_FIT.get("overwrite", False))):
            raise FileExistsError(fit_destination)
    result = run_mlip_md(INPUT, model=model, output_dir=OUTPUT,
                         stages=STAGES, pre_relax=PRE_RELAX, **MD_PARAMETERS)
    if result["pre_relax_result"] is not None:
        relaxation = result["pre_relax_result"]
        print(f"Pre-relax converged: {relaxation['optimizer_converged']}; "
              f"steps: {relaxation['relax_steps_used']}; "
              f"structure: {relaxation['final_structure']}")
    print(f"Completed {result['total_steps']} steps, {result['elapsed_time_fs']} fs")
    if result["steps_per_second"] is not None:
        print(f"MD throughput: {result['steps_per_second']:.3f} steps/s")
    print(f"Report: {result['report_file']}")
    print(f"Final atoms with velocities: {result['stage_results'][-1]['final_structure']}")
    if msd_target is not None:
        index, destination, _ = msd_target
        exported = export_msd(result["stage_results"][index]["trajectory_file"], destination,
                               species=MSD_POSTPROCESS.get("species"),
                               skip_frames=MSD_POSTPROCESS.get("skip_frames", 0),
                               min_obs=MSD_POSTPROCESS.get("min_obs", 30),
                               drift_reference=MSD_POSTPROCESS.get("drift_reference"),
                               overwrite=MSD_POSTPROCESS.get("overwrite", False))
        print(f"MSD: {exported['csv_file']} (NVT stage {index + 1})")
        if fit_destination is not None:
            stage = STAGES[index]
            fitted = fit_msd(exported["csv_file"],
                             fit_start_ps=TRANSPORT_FIT.get("fit_start_ps"),
                             fit_end_ps=TRANSPORT_FIT.get("fit_end_ps"),
                             ion_charge=TRANSPORT_FIT["ion_charge"],
                             diffusion_mode=TRANSPORT_FIT.get("diffusion_mode", "auto"),
                             axes=TRANSPORT_FIT.get("axes", "xy"),
                             anisotropy_threshold=TRANSPORT_FIT.get("anisotropy_threshold", 10),
                             min_msd_A2=TRANSPORT_FIT.get("min_msd_A2", 1.0),
                             temperature_K=stage.get("temperature_K", MD_PARAMETERS.get("temperature_K", 300)),
                             volume_A3=result["stage_results"][index]["final_atoms"].get_volume(),
                             output_json=fit_destination,
                             overwrite=TRANSPORT_FIT.get("overwrite", False))
            print(f"Transport: {fit_destination}")
            for row in fitted["results"]:
                print(f"{row['species']}: D={row['diffusion_cm2_s']:.6g} cm2/s; "
                      f"sigma_NE={row['conductivity_NE_S_cm']:.6g} S/cm")


if __name__ == "__main__":
    main()

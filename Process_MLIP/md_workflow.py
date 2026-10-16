"""同一模型完成可选预弛豫及单阶段/连续阶段 MD。"""
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
import re

from .calculators import create_mlip_calculator
from .md import (_check_outputs, _copy_structure, _get_dynamics_class, _validate_atoms,
                 _validate_options, _write_json, run_md)
from .model_config import _resolve_model_config
from .pre_relax import _RELAX_FILES, _run_pre_relax, _validate_pre_relax


def run_mlip_md(structure, model="mace-mh1", output_dir="md_results", stages=None,
                *, pre_relax=None, **md_parameters):
    """预弛豫与 MD 共用模型；输出总报告、分阶段轨迹和最终结构。

    structure: 结构路径 / ASE Atoms / pymatgen Structure；model: 预设名或配置字典。
    stages=None: 单阶段；列表: 顺序衔接，参数优先级为阶段 > 公共 > 默认。
    衔接保留位置、晶胞和动量，控温/控压内部状态重置；非精确断点续跑。

    pre_relax=None/False: 不弛豫；True/字典: 开启，字典默认值如下：
      enabled=True；relax_cell=False（仅原子，True 为原子+晶胞）。
      optimizer="FIRE"（BFGS / FIRE / LBFGS，须大写）。
      fmax=0.05 eV/Å；steps=200（非负整数）；require_convergence=True（未收敛停止）。
      maxstep=0.05 Å；exp_cell_factor=None（FrechetCellFilter 按原子数缩放）。
    MD 默认：NVT、300 K、1000 步；步长 NVT=2 fs、NPT=1 fs，可显式覆盖。
    tdamp_fs=100，NPT pdamp_fs=1000；timestep_fs=None 按各阶段系综选择。
    NPT 晶胞：isotropic（默认）/ full；tchain/pchain=3，tloop/ploop=1。
    trajectory_interval/log_interval=10（步）；seed=42；overwrite=False。
    measure_steps_per_second=True 可记录吞吐，排除加载、弛豫与后处理。

    参考：pre_relax={"relax_cell": True, "optimizer": "FIRE", "steps": 200}，
    配合 temperature_K=600, steps=5000, trajectory_interval=1, log_interval=1。
    返回 final_atoms、stage_results、pre_relax_result、steps_per_second 和报告路径；
    elapsed_time_fs 为模拟时长。其余 MD 参数见 run_md。
    """
    config = _resolve_model_config(model)
    relaxation = _validate_pre_relax(pre_relax)
    common = _validate_options(md_parameters)
    if stages is None:
        stages = [{}]
    if not isinstance(stages, (list, tuple)) or not stages:
        raise ValueError("stages must be a nonempty list of parameter dicts")
    if Path(output_dir).is_symlink():
        raise FileExistsError(f"Output directory must not be a symlink: {output_dir}")
    root = Path(output_dir).resolve()
    if root.exists() and not root.is_dir():
        raise NotADirectoryError(root)
    summary_path = root / "run_report.json"
    if summary_path.is_symlink() or summary_path.is_dir() or (
            summary_path.exists() and not common["overwrite"]):
        raise FileExistsError(summary_path)
    atoms = _copy_structure(structure)
    prepared = []
    offset = common["time_offset_fs"]
    for index, stage in enumerate(stages):
        if not isinstance(stage, Mapping):
            raise TypeError("Each stage must be a parameter dict")
        stage = deepcopy(dict(stage))
        name = stage.pop("name", None)
        if name is not None and (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name)):
            raise ValueError("Stage name may contain only ASCII letters, numbers, '_' or '-'")
        if "time_offset_fs" in stage or "overwrite" in stage:
            raise ValueError("time_offset_fs and overwrite must be common parameters")
        parameters = dict(common, **stage)
        if "timestep_fs" not in stage and md_parameters.get("timestep_fs") is None:
            parameters["timestep_fs"] = None  # 按阶段系综选默认步长。
        if index > 0 and "initialize_velocities" not in stage:
            parameters["initialize_velocities"] = False
        parameters["time_offset_fs"] = offset
        parameters = _validate_options(parameters)
        # 后续阶段继承上一阶段动量。
        _validate_atoms(atoms, dict(parameters, initialize_velocities=True)
                        if index else parameters)
        _get_dynamics_class(parameters)
        destination = root / f"{index + 1:02d}_{name or parameters['ensemble']}"
        _check_outputs(destination, common["overwrite"])
        prepared.append(dict(output_dir=str(destination), parameters=parameters))
        offset += parameters["steps"] * parameters["timestep_fs"]
    if relaxation["enabled"]:
        _check_outputs(root / "00_relax", common["overwrite"], filenames=_RELAX_FILES)
        if relaxation["relax_cell"]:
            _validate_atoms(atoms, dict(prepared[0]["parameters"], ensemble="npt"))
    calculator = create_mlip_calculator(config)
    root.mkdir(parents=True, exist_ok=True)
    source = str(Path(structure).resolve()) if isinstance(structure, (str, Path)) else type(structure).__name__
    summary = dict(status="running", model=config, input_structure=source,
                   atom_count=len(atoms), stages=prepared,
                   stages_completed=0, stage_results=[], pre_relax_parameters=relaxation,
                   pre_relax_result=None)
    _write_json(summary_path, summary)
    results = []
    relax_result = None
    try:
        if relaxation["enabled"]:
            summary["active_stage"] = "pre_relax"
            _write_json(summary_path, summary)
            relax_result = _run_pre_relax(atoms, calculator, root / "00_relax", relaxation,
                                          overwrite=common["overwrite"], model_metadata=config)
            atoms = relax_result["final_atoms"]
            summary["pre_relax_result"] = {key: value for key, value in relax_result.items()
                                             if key != "final_atoms"}
            _write_json(summary_path, summary)
            if relaxation["require_convergence"] and not relax_result["optimizer_converged"]:
                raise RuntimeError("Pre-relaxation did not converge; increase steps or explicitly "
                                   "set require_convergence=False to continue into MD")
        for index, stage in enumerate(prepared):
            summary["active_stage"] = index + 1
            _write_json(summary_path, summary)
            result = run_md(atoms, calculator, stage["output_dir"],
                            model_metadata=config, **stage["parameters"])
            atoms = result["final_atoms"]
            results.append(result)
            summary["stages_completed"] = len(results)
            summary["stage_results"].append({key: value for key, value in result.items()
                                              if key != "final_atoms"})
            _write_json(summary_path, summary)
        summary.update(status="completed", total_steps=sum(r["steps_completed"] for r in results),
                       end_time_fs=offset, elapsed_time_fs=offset - common["time_offset_fs"])
        timed = [r for r in results if r["steps_completed"] > 0]
        summary["steps_per_second"] = (
            sum(r["steps_completed"] for r in timed)
            / sum(r["steps_completed"] / r["steps_per_second"] for r in timed)
            if timed and all(r["steps_per_second"] is not None for r in timed) else None)
        _write_json(summary_path, summary)
    except (Exception, KeyboardInterrupt) as exc:
        summary.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        _write_json(summary_path, summary)
        raise
    return dict(final_atoms=atoms, stage_results=results, pre_relax_result=relax_result,
                status="completed",
                total_steps=summary["total_steps"], elapsed_time_fs=summary["elapsed_time_fs"],
                steps_per_second=summary["steps_per_second"],
                end_time_fs=offset, report_file=str(summary_path), output_dir=str(root))

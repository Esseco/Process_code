"""Small human-facing summaries; detailed numerical reports stay in place."""
from datetime import datetime, timezone
from pathlib import Path

from ase.io import read, write
from process_md import save_csv, save_json


OUTPUT_GUIDE = """# MD 输出导航

优先查看 results/summary.json 或 results/summary.csv：
包含运行状态、D、σ_NE、R²、拟合区间和停止原因，未解析数值为 null/空白。
ready_for_screening 只表示设置的粗筛通过，不代表统计或尺寸收敛。

| 路径 | 内容 |
| --- | --- |
| parameters.json | 参数、SOC 输入与满位点参考来源 |
| run.log | UTC 流程阶段、检查时间、决定和错误 |
| prepared/ | 实际使用的结构、满位点参考、弛豫后结构 |
| relaxation/ | 原子/晶胞优化轨迹、日志、末结构与报告 |
| md/production/md.traj 或 md.traj.gz | 唯一连续轨迹，包含初检；默认直接入口结束后无损归档 |
| md/production/md.csv | 温度、能量等热力学量；time_fs 单位 fs |
| checks/000_precheck/ | 初检：结构诊断，不拟合生产 D |
| checks/001_production/ 等 | 累计生产 MSD、扩散拟合和跳跃分析 |
| results/summary.json、summary.csv | 最新/最终汇总；CSV 只有一行 |
| results/msd.csv | 最新生产 MSD（如有）；lag_time_ps 单位 ps |
| results/final_structure.extxyz | 最终积分结构（如有） |
| 根目录 summary.csv | 每次检查一行的历史记录 |
| run.json | 完整状态、参数和详细数据 |

D 单位 cm²/s，σ_NE 单位 S/cm。生产分析排除初检时间。
轨迹只保存一份；gzip 归档后先解压再单独分析，压缩失败保留原始轨迹。
results/ 另存小型汇总、末结构和最新 MSD。
结构异常和升温/降温/扩胞建议需要复核，不会自动执行调整。
当前不支持完整积分器 checkpoint 或严格 restart。
模型 stdout/stderr 留在终端或 Slurm 日志，run.log 记录流程事件。
"""


def initialize_outputs(root, metadata):
    """Write the output map and a resolved configuration once."""
    (root / "README.md").write_text(OUTPUT_GUIDE, encoding="utf-8")
    save_json(dict(config=metadata["config"], input_source=metadata["input_source"],
                   reference_source=metadata["reference_source"]),
              root / "parameters.json")


def record_progress(root, metadata, result):
    """Append a small workflow event; model stdout remains in the terminal."""
    report = result.last_check
    time = metadata.get("elapsed_time_ps", None if report is None else report.total_time_ps)
    phase = metadata.get("phase", None if report is None else report.phase)
    action = None if report is None or report.decision is None else report.decision.action
    archive = metadata.get("trajectory_archive", {})
    archive_error = archive.get("error") if archive.get("status") == "failed" else None
    reason = result.error or archive_error or (None if report is None or report.decision is None else report.decision.reason)
    line = (f"{datetime.now(timezone.utc).isoformat()} stage={metadata['stage']} "
            f"status={result.status} phase={phase} time_ps={time} action={action}")
    if reason:
        line += f" | {reason}"
    with (root / "run.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def write_summary(root, metadata, result):
    """Update a scalar summary; publish final structure/MSD after integration."""
    report = result.last_check
    fit = None if report is None else report.transport
    output = root / "results"
    output.mkdir(exist_ok=True)
    if result.status != "running" and result.check_reports:
        latest = result.check_reports[-1].parent / "msd.csv"
        if latest.is_file():
            (output / "msd.csv").write_bytes(latest.read_bytes())
    if result.status != "failed" and result.md is not None and result.md.final_structure is not None:
        source = Path(result.md.final_structure)
        if source.is_file():
            write(str(output / "final_structure.extxyz"), read(source, index=-1),
                  format="extxyz", write_results=False)
    def relative(path):
        if path is None or not Path(path).is_file():
            return None
        return Path(path).resolve().relative_to(root).as_posix()
    row = dict(
        status=result.status, ready_for_screening=result.status == "heuristic_ready",
        temperature_K=metadata["config"].temperature_K,
        total_time_ps=None if report is None else report.total_time_ps,
        production_time_ps=None if report is None else report.production_time_ps,
        framework_status=None if report is None else report.framework_status,
        transport_status=None if report is None else report.transport_status,
        mobility_status=None if report is None else report.mobility_status,
        diffusion_cm2_s=None if fit is None else fit.diffusion_cm2_s,
        conductivity_NE_S_cm=None if fit is None else fit.conductivity_NE_S_cm,
        r_squared=None if fit is None else fit.r_squared,
        fit_start_ps=None if fit is None else fit.fit_start_ps,
        fit_end_ps=None if fit is None else fit.fit_end_ps,
        n_jumps=None if report is None or report.jumps is None else report.jumps.n_jumps,
        action=None if report is None or report.decision is None else report.decision.action,
        reason=None if report is None or report.decision is None else report.decision.reason,
        error=result.error,
    )
    paths = dict(
        trajectory=relative(result.md.trajectory if result.md is not None and result.md.trajectory is not None
                            else root / "md/production/md.traj"),
        thermodynamics=relative(root / "md/production/md.csv"),
        latest_check=relative(result.check_reports[-1]) if result.check_reports else None,
        msd=relative(output / "msd.csv"),
        final_structure=relative(output / "final_structure.extxyz"),
        check_history=relative(root / "summary.csv"),
        full_state=relative(root / "run.json"),
    )
    save_json({**row, "files": paths, "trajectory_archive": metadata.get("trajectory_archive")},
              output / "summary.json", overwrite=True)
    save_csv([row], output / "summary.csv", overwrite=True)

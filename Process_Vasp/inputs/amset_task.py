"""Create a standalone CPU Slurm AMSET task; generation does not run calculations."""

import ast
import json
from pathlib import Path


def generate_amset_task(directory, *, workflow_root="..", source_dir=None, source_stage="dos",
                        doping=(-1e18, 1e18), temperatures=(300,),
                        relaxation_time=1e-14, interpolation_factor=10, nworkers=2):
    """Write an uploadable task with bundled helpers, config and Slurm script.

    Server workflow_root is relative to generated task location or absolute.
    Units and calculation semantics follow run_amset_postprocess. Generation uses
    only stdlib, requires an absent/empty target and does not access server data.
    Generated task requires AMSET/numpy, not an uploaded Py-Code installation.
    Edit partition/environment in submit_amset.sh for the target cluster. Output
    remains in this task's results/; resubmission reuses completed CRT requests.
    """
    target = Path(directory)
    if source_stage not in {"dos", "static"}:
        raise ValueError("AMSET source_stage must be dos or static")
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise FileExistsError(f"Task directory must be absent or empty: {target}")
    base = Path(__file__).resolve().parents[1]
    runner = (base / "workflows/atomate_runner.py").read_text(encoding="utf-8")
    nodes = ast.parse(runner).body
    helper = "import os\nimport json\nfrom contextlib import contextmanager\n\n"
    for node in nodes:
        if isinstance(node, ast.FunctionDef) and node.name in {"_save", "_lock"}:
            helper += ast.unparse(node) + "\n\n"
    target.mkdir(parents=True, exist_ok=True)
    files = {"checkpoint_utils.py": helper}
    files["amset_crt_local.py"] = (base / "workflows/amset_crt.py").read_text(encoding="utf-8").replace(
        "from .atomate_runner import _lock, _save", "from checkpoint_utils import _lock, _save")
    files["amset_postprocess_local.py"] = (base / "workflows/amset_postprocess.py").read_text(encoding="utf-8").replace(
        "from .amset_crt import run_amset_crt", "from amset_crt_local import run_amset_crt").replace(
        "from .atomate_runner import _save", "from checkpoint_utils import _save").replace(
        "from ..results.completed import get_completed_result", "from completed_local import get_completed_result")
    files["completed_local.py"] = (base / "results/completed.py").read_text(encoding="utf-8")
    files["postprocess.py"] = '''"""Run the task on the cluster, using paths relative to this file."""
import json
from pathlib import Path
from amset_postprocess_local import run_amset_postprocess

if __name__ == "__main__":
    task = Path(__file__).resolve().parent
    config = json.loads((task / "postprocess.json").read_text(encoding="utf-8"))
    root = Path(config.pop("workflow_root"))
    root = root if root.is_absolute() else task / root
    result = run_amset_postprocess(root, task / "results", **config)
    print("Results:", task / "results/transport_summary.csv")
'''
    files["postprocess.json"] = json.dumps(dict(workflow_root=str(workflow_root), source_dir=source_dir, source_stage=source_stage,
        doping=list(doping), temperatures=list(temperatures), relaxation_time=relaxation_time,
        interpolation_factor=interpolation_factor, nworkers=nworkers), indent=2)
    files["submit_amset.sh"] = (base / "templates/submit_amset.sh").read_text(encoding="utf-8").replace(
        "#SBATCH --cpus-per-task=2", f"#SBATCH --cpus-per-task={nworkers}")
    files["README.md"] = """# 超算 AMSET 后处理任务

把整个文件夹上传到原 VASP 任务目录下，和 runs 并列，例如 Full_TM/amset_postprocess。
postprocess.json 的 workflow_root 默认 ..，从父目录 workflow_state.json 自动读取已完成 DOS。
也可设置 source_dir 为相对 workflow_root 的实际 DOS 目录；不会选择路径能带或重跑 VASP。

编辑 submit_amset.sh 的 partition 和 conda 环境（默认沿用现有 python 环境，必须已安装 AMSET）。
然后进入本文件夹执行 sbatch submit_amset.sh。不要执行原 workflow.py。

结果在 results/transport_summary.csv 和 results/transport_properties.json。
包含电子/空穴输运有效质量 m*/m0、σ/τ、固定 τ 下的 CRT 迁移率和 μ/τ。
默认 τ=1e-14 s、300 K、电子/空穴各1e18 cm^-3；这些都能修改。
有效质量按 AMSET eff-mass 的输运定义从同一次 CRT 结果计算，不重复插值。
CRT 迁移率依赖人为设置的 τ，不是第一性原理散射迁移率。
相同成功计算重复提交会跳过；失败保留 attempt 并在重提时重新计算 AMSET。
当前代码未在超算或真实 AMSET 上运行验证，原 DOS 网格需自行确认输运收敛。
"""
    for name, content in files.items():
        with (target / name).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    return target

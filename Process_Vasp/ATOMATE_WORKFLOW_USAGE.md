# atomate2 断点续算

新生成任务包含 workflow.py、atomate_runner.py、workflow.json、结构文件及 submit_gpu.sh（64G）。上传整个任务目录；服务器只需已有的 atomate2 环境，不依赖本地 Process_Vasp 安装。

## 默认续算

再次 `sbatch submit_gpu.sh`，自动校验并跳过已完成阶段，从第一个缺失、未收敛或参数失效的阶段开始。workflow_state.json 原子保存阶段状态；即使任务被 kill 来不及标记完成，也会重新检查已有输出。OS 文件锁阻止两个提交同时操作一个任务目录（共享文件系统须支持文件锁）。

目录示例：

```text
runs/
  relax/attempt_001/
  static/attempt_001/   # 保留被终止的尝试
  static/attempt_002/   # 新尝试
  dos/attempt_001/
workflow_state.json
```

第一版实现阶段恢复：失败阶段从成功的前序结构和目录重新开始，不读取失败尝试的 WAVECAR/CHGCAR。Custodian 仍负责运行内部的错误修正。当前不会自动向 Slurm 重新提交，修改资源后需再次提交同一个脚本。

状态通过完整 vasprun.xml（或压缩文件）及收敛信息验证，要求 OUTCAR、CONTCAR；static 还要求 CHGCAR。relax 检查电子和离子收敛，其他阶段检查电子收敛。每次恢复会重新验证，损坏结果不会按已完成跳过。

## 修改参数

修改 workflow.json 对应阶段的 incar_settings/kpoints_settings，重新提交。改变 static 参数只重算 static 和后续阶段；改变 relax 或初始结构会使后续阶段全部失效。仅改变提交内存不会使已完成阶段失效。文件仍保留在各自 attempt 目录。

```json
"incar_settings": {
  "static": {"ENCUT": 600}
}
```

checkpoint 会记录各阶段路径、输入指纹、尝试编号和状态。文件夹保持原位；更换服务器路径后建议重新接入旧结果。默认不能识别所有外部变化（例如替换 VASP 版本、POTCAR 配置或修改环境），这些情况使用 `python workflow.py --fresh` 强制全部重算，新尝试不会覆盖旧文件。

## 接入旧任务，例如 relax 完成而 static 被终止

升级已有服务器任务时，先等待它停止；备份原 workflow.py、workflow.json、提交脚本。上传本次生成的 workflow.py 与 atomate_runner.py，保留原 workflow.json 和结构文件，并在原配置中加入：

```json
"resume_from": {
  "relax": "/服务器/原任务/job_数字目录"
}
```

也可以在生成新任务时指定：

```python
from Process_Vasp import generate_atomate_input

generate_atomate_input(
    directory=r"E:\tasks\continued_dos",
    structure=r"E:\structures\initial.cif",
    calculation="dos",
    incar_settings={"static": {"ENCUT": 520}},
    resume_from={"relax": "/server/old_task/job_12345"},
)
```

路径按服务器解析；相对路径以任务目录为基准。导入会检查结果完整及收敛，但无法证明旧 relax 与初始结构、所有期望参数相对应，用户需确认选对任务和方法。导入仅在该阶段没有 checkpoint 时使用；后续运行优先使用 checkpoint。需要重新选择导入源时使用新任务目录。static/dos/band 导入还会核对前一步结构。

将已有 submit_gpu.sh 的内存改为 64G，然后重新提交。新流程会导入优化结果，执行 static，再继续 dos。默认 static-only 任务仍只有 static，不会加 relax。

读取 DOS 时使用 workflow_state.json 中 dos 的 directory，例如 `read_dos("任务/runs/dos/attempt_001")`。

验证：断点恢复模拟测试通过，覆盖阶段失败重试、参数失效、kill 后完整结果恢复、旧目录导入和强制重算；DOS 与激发态测试通过。未运行真实 VASP，集群上仍需验证。

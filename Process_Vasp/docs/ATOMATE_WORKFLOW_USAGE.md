# atomate2 断点续算

新生成任务只包含 workflow.py、workflow.json、结构文件及 submit_gpu.sh（64G）。`workflow.py` 从 Process_Vasp 项目导入运行器；超算环境需能导入已上传的 Process_Vasp，并具有 atomate2 依赖。上传任务目录及项目后，提交 `submit_gpu.sh`。

## 默认续算

再次 `sbatch submit_gpu.sh`，自动校验并跳过已完成阶段，从第一个缺失、未收敛或参数失效的阶段开始。workflow_state.json 原子保存阶段状态；即使任务被 kill 来不及标记完成，也会重新检查已有输出。OS 文件锁阻止两个提交同时操作一个任务目录（共享文件系统须支持文件锁）。

升级旧版生成的任务时，运行器也会检查同一任务目录中 `runs/job_*` 的旧结果，即使曾经留下失败的新版检查点。候选必须有可解析且收敛的 `vasprun.xml`、对应阶段的 INCAR、匹配前一步的 POSCAR，以及完整输出；静态还需 WAVECAR 和 CHGCAR。验证通过的旧 relax 会直接接入，因此下一步从 static 开始，接着运行 DOS 或 band。找不到合格结果时会打印候选被拒绝的原因，再重新计算该阶段；升级前应保留服务器上的整个 `runs/` 目录。若旧任务的参数或结构不符合当前配置，不能自动当作完成结果。

目录示例：

```text
runs/
  relax/attempt_001/
  static/attempt_001/   # 保留被终止的尝试
  static/attempt_002/   # 新尝试
  dos/attempt_001/
workflow_state.json
```

失败阶段从成功的前序结构和目录重新开始。若 relax 失败且原参数未变，程序会尝试读取该阶段上一次尝试的有效 CONTCAR，从最后的几何构型重新弛豫；无效或空 CONTCAR 则使用初始结构。不读取失败尝试的 WAVECAR/CHGCAR。Custodian 仍负责运行内部的错误修正。当前不会自动向 Slurm 重新提交，修改资源后需再次提交同一个脚本。

失败时写出 `workflow_status.json` 和 `failure_report.txt`，注明阶段、尝试目录、可识别的停止原因、建议处理动作及 VASP 标准错误末尾，并在 Slurm 错误输出中打印。成功后 `workflow_status.json` 更新为 completed，旧的 `failure_report.txt` 保留作历史记录。若磁盘配额已满，报告文件自身可能无法写入，此时以 Slurm `err` 和阶段目录的 `std_err.txt` 为准。强制终止（如 SIGKILL）可能来不及写报告；再次提交会校验已有输出，不凭旧状态盲目跳过。

状态通过完整 vasprun.xml（或压缩文件）及收敛信息验证，要求 OUTCAR、CONTCAR；static 还要求 CHGCAR 和 WAVECAR。relax 检查电子和离子收敛，其他阶段检查电子收敛。每次恢复会重新验证，损坏结果不会按已完成跳过。

## 修改参数

修改 workflow.json 对应阶段的 incar_settings/kpoints_settings，重新提交。改变 static 参数只重算 static 和后续阶段；改变 relax 或初始结构会使后续阶段全部失效。仅改变提交内存不会使已完成阶段失效。文件仍保留在各自 attempt 目录。

```json
"incar_settings": {
  "static": {"ENCUT": 600}
}
```

checkpoint 会记录各阶段路径、输入指纹、尝试编号和状态。文件夹保持原位；更换服务器路径后建议重新接入旧结果。默认不能识别所有外部变化（例如替换 VASP 版本、POTCAR 配置或修改环境），这些情况使用 `python workflow.py --fresh` 强制全部重算，新尝试不会覆盖旧文件。

## 接入旧任务，例如 relax 完成而 static 被终止

升级已有服务器任务时，先等待它停止；备份原 workflow.py、workflow.json、提交脚本。上传项目和新生成的 workflow.py，保留原 workflow.json、结构文件和整个 runs/ 目录。同一目录下的旧 `runs/job_*` 会自动检查；只有旧结果位于别处时才需要在配置中加入：

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

路径按服务器解析；相对路径以任务目录为基准。导入会检查结果完整及收敛，但无法证明旧 relax 与初始结构、所有期望参数相对应，用户需确认选对任务和方法。无效或失败的 checkpoint 不阻止接入 `resume_from`；已验证完成的 checkpoint 优先使用。static/dos/band 导入还会核对前一步结构。

将已有 submit_gpu.sh 的内存改为 64G，然后重新提交。新流程会导入优化结果，执行 static，再继续 dos。默认 static-only 任务仍只有 static，不会加 relax。

读取 DOS 时使用 workflow_state.json 中 dos 的 directory，例如 `read_dos("任务/runs/dos/attempt_001")`。

## 自动导出绘图数据

生成任务时传入 `export_plot_data=True`，或在任务的 `workflow.json` 顶层加入 `"export_plot_data": true`。只有最终 DOS 或能带阶段通过收敛及输出完整性检查后才导出。关闭时设为 `false`。修改此开关后重新运行 `python3 workflow.py`，已完成的 VASP 阶段会跳过，只补导出；导出失败也不会把已完成计算标为失败，修复后可再次运行。重新导出覆盖任务根目录中的同名 CSV 和元数据文件。

DOS 任务在任务根目录写 `dos.csv` 与 `dos_metadata.json`。CSV 包含 `energy`（E−E_F，eV）、总 DOS 及各元素 DOS 的自旋列；原始 DOS 数值单位为 states/eV/cell，不做每原子归一化。该导出复用 `read_dos`，需要投影 DOS；生成器通常设置 `LORBIT=11`，若用户关闭投影输出，需关闭自动导出或重新计算。

能带任务写 `band.csv` 与 `band_metadata.json`。CSV 每行是一个自旋、能带和 k 点，含 `energy_eV`、`energy_minus_fermi_eV`、`k_distance_inv_angstrom`、分数 k 坐标及高对称点标签；能带编号和 k 点编号从 1 开始。元数据包括费米能级、是否为金属和可用时的带隙。没有随机种子；导出仅解析已完成结果，不启动新的 VASP 计算。

验证：断点恢复模拟测试通过，覆盖阶段失败重试、参数失效、kill 后完整结果恢复、旧目录导入和强制重算；DOS 与激发态测试通过。未运行真实 VASP，集群上仍需验证。

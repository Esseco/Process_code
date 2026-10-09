# AMSET 恒定弛豫时间后处理

## 接口

```python
from Process_Vasp import run_amset_crt

result = run_amset_crt(
    "/path/to/completed/dos", "/path/to/amset_crt",
    doping=[-1e18, 1e18], temperatures=[300], nworkers=1,
)
sigma_over_tau = result["sigma_over_tau_S_m_s"]
```

输入目录必须包含完整的 `vasprun.xml` 或 `vasprun.xml.gz`，来自均匀 k 点网格计算，不能使用高对称路径能带。输出目录必须独立，不能与输入互相嵌套。输入仅复制。示例的服务器路径来自当前 DOS 元数据；本地 Desktop/1/5 仅有任务元数据，不能直接用来计算。

浓度单位 cm⁻³，负号代表电子，正号代表空穴。温度 K，默认弛豫时间 1e-14 s。返回 σ 和 σ/τ 的笛卡尔 3×3 张量，外层依次是浓度、温度；σ/τ 单位 S·m⁻¹·s⁻¹。按返回的浓度顺序读取结果。CRT 不预测实际弛豫时间或真实迁移率。

## 环境与重复运行

使用安装了 AMSET 的环境，且 `amset` 位于 PATH。已有 atomate2 环境本次检查未发现 AMSET 安装，未新增依赖。接口调用 AMSET CLI，不使用默认的 VaspAmsetMaker 完整材料参数流程。导入不启动计算。

每次实际计算写入新的 `attempt_001` 等目录，含复制的 XML、settings.yaml、amset.log 及 AMSET 输出。根目录写 `amset_crt_state.json`、`amset_crt_result.json`，并复用项目的操作系统文件锁。输入文件内容及参数相同且已成功时，默认读取已完成输出；`resume=False` 强制新建 attempt。失败保留文件，下一次重做 AMSET 后处理；不从被中断的插值内部恢复。没有随机种子，无集群提交或 VASP 重跑。没有自动进行网格/插值收敛判断，completed 仅指成功运行和读取结果。

配置式入口先预览，再显式执行：

```text
python templates/run_task.py templates/configs/amset_crt.json
python templates/run_task.py templates/configs/amset_crt.json --run
```

先修改配置路径，并激活安装了 AMSET 的环境。独立示例在 `Process_Vasp/examples/amset_crt.py`。

## 有效质量

AMSET 有独立的 `amset eff-mass vasprun.xml` 命令，计算输运有效质量。新增 `run_amset_postprocess` 使用与官方 effmass.py 相同的定义从 CRT 张量导出质量：`m*/m0 = abs(n) e² inverse(σ/τ) / m0`，n 从 cm⁻³ 转为 m⁻³。同时导出调和平均 `3 / trace(inverse(m*/m0))`。此质量依赖温度和净掺杂浓度，不是特定带边沿某方向的曲率质量；双极输运时仍采用官方的绝对净掺杂定义。奇异或非正定电导率使质量为 null，并保留诊断。

## 可提交超算任务

```python
from Process_Vasp import generate_amset_task
generate_amset_task("amset_postprocess", workflow_root="..")
```

生成时不读取服务器结构、不启动模型、不提交计算。目标必须不存在或为空。上传整个生成文件夹到原任务目录，使目录成为 `Full_TM/amset_postprocess`，与 `Full_TM/runs` 并列。在这个文件夹执行 `sbatch submit_amset.sh`。任务自带 stdlib 辅助代码，不要求超算安装 Py-Code；计算环境须有 AMSET 和 numpy。

`postprocess.json` 的 `workflow_root` 相对该文件夹解析。默认从父目录 `workflow_state.json` 读取 completed 的 DOS 路径；若旧结果没有检查点，显式填写 `source_dir`（相对 workflow_root 或绝对路径）。不会自动寻找最新的任意 XML 或选择能带路径计算。

项目统一入口 `generate_followup_task(..., calculation="amset")` 也能生成这个任务。读取已有结果统一通过 get_completed_result；`source_stage="static"` 可复用已完成的均匀静态计算，仍需自行确认网格密度足够。见 [后续计算说明](FOLLOWUP_USAGE.md)。

`submit_amset.sh` 沿用用户原任务的 conda 初始化路径、python 环境和 v100m3 分区，使用单任务2 CPU、32 GB，不请求 GPU。上传后按超算实际可用 CPU 分区和已安装 AMSET 的环境修改这些项。原 partition 若强制要求 GPU，应换 CPU 分区。

输出在 `results/transport_properties.json`（完整张量、单位、诊断）和 `results/transport_summary.csv`（电子/空穴、温度、质量、σ/τ、CRT 迁移率的对角分量）。CRT 默认人为固定 τ=1e-14 s；`mobility_crt_cm2_V_s` 是 σ/(abs(n)e)，`mobility_over_tau_cm2_V_s2` 是其除以 τ 的值，不能当作预测的真实散射迁移率。

质量和迁移率复用同一次 CRT 插值，不单独再执行 eff-mass。成功后重提读取已有 CRT 结果并重导出表格；失败或改变输入/参数新建 attempt。CRT 的扫描完成状态和失败原因保存在 `results/crt/amset_crt_state.json`，外部进程日志在对应 attempt/amset.log。没有自动执行输运收敛测试。

配置模板 `templates/configs/amset_task.json` 可由 `templates/run_task.py` 预览和生成。生成任务的具体规格已写入自带 README。实现依据：[AMSET 官方 effmass.py](https://github.com/hackingmaterials/amset/blob/main/amset/tools/effmass.py)。

参考：[设置](https://hackingmaterials.lbl.gov/amset/settings/)、[输入](https://hackingmaterials.lbl.gov/amset/inputs/)、[更新记录](https://hackingmaterials.lbl.gov/amset/changelog/)。当前 DOS 元数据中的 3×5×1 网格尚未验证输运收敛；未运行真实 AMSET 计算。

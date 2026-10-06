# Process_Vasp

<!-- Manual project documentation -->

VASP 输入生成、计算结果读取和可恢复的 atomate2 工作流。默认 py1；运行生成的工作流使用已有 atomate2 环境。

## 按功能使用

| 功能 | 公开入口 | 输入 | 输出 | 独立模板 |
|---|---|---|---|---|
| DOS/元素分波/IPR | read_dos / read_ipr | 计算目录 | dict + DataFrame，可写 CSV | [dos_to_csv.py](examples/dos_to_csv.py) |
| 基态转激发态输入 | generate_excited_input | 基态目录和目标目录 | VASP 输入、excitation.json | [excited_inputs.py](examples/excited_inputs.py) |
| atomate2 任务生成 | generate_atomate_input | CIF/VASP 结构、分阶段参数 | 可上传的任务文件夹 | [create_workflow.py](examples/create_workflow.py) |
| 结果/状态读取 | read_vasp_output / read_vasp_status | 计算目录 | 结果或状态 dict | [read_results.py](examples/read_results.py) |
| Fe/Mn 磁矩诊断 | check_dft_magnetic_moments / check_layered_oxide_moments | OUTCAR 或局域磁矩、明确的层状体系标识 | 只读诊断 dict，μB | [磁矩说明](docs/MAGNETIC_CHECK.md) |
| 原始逐原子磁矩 | read_dft_magnetic_data | OUTCAR、对应结构 | 所有元素的原子索引/磁矩，μB；不筛选 | [磁矩说明](docs/MAGNETIC_CHECK.md) |
| INCAR/文件处理 | set_incar_tags / update_incar / copy_vasp_files | 输入文件/目录 | 修改或复制文件 | [API 参数索引](API.md) |

各功能可单独调用，不要求经过仓库统一 CLI。模板顶部集中放路径和参数，导入不会执行。先修改模板，再从仓库根目录运行，例如：

```text
python -m Process_Vasp.examples.dos_to_csv
python -m Process_Vasp.examples.excited_inputs
python -m Process_Vasp.examples.create_workflow
python -m Process_Vasp.examples.read_results
```

模板里的路径是示例，不会自动替换为真实数据。生成工作流只写任务文件，不提交；激发态只准备输入，不运行 VASP。DOS 模板不覆盖已有 CSV。

## 功能约定

- DOS 默认输出总 DOS 和元素 DOS，返回 result["df"]；轨道/IPR 可选。支持压缩输出。见 [DOS 说明](docs/DOS_USAGE.md)。
- 激发态支持单 Gamma 点整数占据，共线自旋；auto 选择较窄同通道带隙，both 生成两个独立计算。见 [激发态说明](docs/EXCITATION_USAGE.md)。
- 工作流默认跳过验证过的完成阶段，失败新建 attempt；可识别同一任务目录中旧版 `runs/job_*` 的已完成结果。例如旧 relax 完成后会从 static 开始。参数变化使受影响阶段及后续失效；失败时写出原因和建议处理动作。见 [断点续算说明](docs/ATOMATE_WORKFLOW_USAGE.md)。
- 工作流可设置 `export_plot_data=True`；DOS 完成后写出 `dos.csv`，能带完成后写出 `band.csv`，并分别保存费米能级等元数据。不重复运行已完成的 VASP 阶段。
- 结果里的能量修正具有特定 GGA+U/MP 假设；状态日志判断不能替代严格续算验证。见 [功能边界](docs/BOUNDARIES.md)。

## 目录与维护

根目录保留公开入口和项目导航，实际代码按功能归档：

```text
Process_Vasp/
├── input.py / output.py       # 稳定的输入、输出接口
├── __init__.py                # 包级接口及旧模块路径兼容
├── inputs/                    # 准备计算输入
│   ├── generation.py          # 常规 VASP / atomate2 任务文件生成
│   ├── incar.py               # INCAR 修改、输入文件复制
│   └── excitation.py          # 从基态准备激发态输入
├── results/                   # 读取已有计算结果
│   ├── reader.py              # 能量、结构及修正结果
│   ├── dos.py                 # DOS、元素/轨道分波及 IPR
│   ├── status.py              # 日志与计算状态
│   └── magnetism.py           # OUTCAR 标量磁矩
├── structures/structure.py    # 结构变换、NEB 端点、去重兼容入口
├── workflows/atomate_runner.py # atomate2 执行、检查点和续算
├── workflows/plot_exports.py   # DOS / 能带绘图数据导出
├── templates/                 # Slurm/LSF 脚本与 atomate2.yaml
├── examples/                  # 路径、参数集中配置的调用示例
├── tests/                     # 模拟数据回归测试
└── docs/                      # DOS、激发态、续算及功能边界说明
```

`__pycache__` 和原有 `tmp*` 目录保留原位，不属于功能入口。

### 导入兼容

以下调用都可以继续使用，参数和返回值不变：

```python
from Process_Vasp import read_dos, generate_atomate_input
from Process_Vasp.input import generate_excited_input
from Process_Vasp.output import read_vasp_output
from Process_Vasp.dos import read_dos  # 原模块路径兼容

# 阅读或维护实现时，直接定位新的功能目录。
from Process_Vasp.results.dos import read_dos
```

原来的 generation、incar、excitation、dos、reader、status、magnetism、structure、atomate_runner 模块路径均指向对应的新模块对象，旧调用和旧 mock.patch 路径共用实现。实际源文件路径已变；依赖根目录文件路径的外部脚本需按上表调整。测试模块现在位于 `Process_Vasp.tests`。

提交模板集中在 [templates](templates/README.md)。生成任务只包含结构、`workflow.json`、调用项目运行器的 `workflow.py` 和 `submit_gpu.sh`；运行逻辑留在 Process_Vasp 中。超算环境需能导入上传后的 Process_Vasp 项目。生成任务不提交计算；重复运行沿用项目运行器的检查点和 attempt 规则。

[API.md](API.md) 提供真实签名；[TASK_TEMPLATE.md](TASK_TEMPLATE.md) 记录具体任务规格。通用结构功能与磁矩工具是后续迁移候选，本轮保留兼容名称。

## 验证

py1：`python -m unittest Process_Vasp.tests.test_dos Process_Vasp.tests.test_excitation Process_Vasp.tests.test_layout`。

atomate2：`python -m unittest Process_Vasp.tests.test_atomate_directories`。

示例检查仅验证语法和安全导入，不读取示例路径。既有测试使用模拟数据，不代表真实 VASP 或集群运行已验证。

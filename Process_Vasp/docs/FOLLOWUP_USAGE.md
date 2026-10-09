# 从已完成任务继续计算

## 三个项目入口

```python
from Process_Vasp import run_workflow, get_completed_result, generate_followup_task
```

- `run_workflow(task_dir)`：执行原有 workflow.json，按检查点续跑原任务。需在安装 atomate2、VASP 已配置的执行环境使用；会启动未完成的 VASP 阶段。`fresh=True` 强制重做当前配置请求的阶段。
- `get_completed_result(task_dir, stage)`：只读解析指定阶段的 completed 检查点并验证结果，返回实际输出目录 Path。可传给 read_dos、read_vasp_output、generate_excited_input 等现有接口。validate 默认 True，需要 pymatgen；不会写文件或启动计算。
- `generate_followup_task(directory, previous_task, calculation, ...)`：准备后续任务，服务器运行时解析已有结果；生成阶段只写任务文件，不需要本地有超算 XML，不提交计算。

## 常用组合

| 后续 calculation | 默认 source_stage | 实际运行 |
|---|---|---|
| static | relax | 只做新的 static，读取已有弛豫结构 |
| dos | static | 只做新的非自洽 DOS，读取已有静态结构及 CHGCAR |
| band | static | 只做新的路径能带，读取已有静态结构及 CHGCAR |
| relax | relax | 以已完成弛豫结果为起点，做新的弛豫 |
| amset | dos | 只做 AMSET CRT，导出输运有效质量、σ/τ、CRT 迁移率 |

dos/band 若显式 `source_stage="relax"`，先补 static，再做 DOS/能带；不会重跑来源弛豫。amset 可显式选择 `source_stage="static"`，但输入必须是足够密的均匀 k 点结果。输运网格收敛不因复用结果而自动成立。

```python
# 从超算已经完成的静态任务生成 DOS 后续任务。
generate_followup_task(
    "new_dos", "/server/path/completed_task", "dos",
    source_stage="static", export_plot_data=True,
    kpoints_settings={"dos": {"reciprocal_density": 1000}},
)

# 同一接口生成 AMSET 后处理任务。
generate_followup_task(
    "new_amset", "/server/path/completed_task", "amset",
    amset_settings={"doping": [-1e18, 1e18], "temperatures": [300]},
)
```

上传 new_dos 后提交其 submit_gpu.sh；new_amset 使用 submit_amset.sh。VASP 后续任务调用项目中的运行器，超算需要更新后的 Process_Vasp 和 atomate2。AMSET 任务自动附带所需的辅助源码，只需 AMSET/numpy；按超算配置环境与 CPU 分区。

## 已有输出直接复用

```python
from Process_Vasp import get_completed_result, read_dos, generate_excited_input

dos_dir = get_completed_result("/server/path/task", "dos")
dos = read_dos(dos_dir)

static_dir = get_completed_result("/server/path/task", "static")
# 激发态输入的 Gamma 点/占据等原有适用限制仍然生效。
generate_excited_input(static_dir, "/server/path/new_excited_inputs")
```

没有检查点的旧任务可以显式传 `source_dir="runs/job_..."`，或把原始 VASP 输出目录直接作为 previous_task/task_dir。不会默认用最新目录猜测阶段，也不会从 band 结果冒充均匀 DOS。

## 路径、验证和副作用

生成函数的 previous_task 是执行服务器路径；相对路径以新任务目录为基准。source_dir 相对 previous_task。生成阶段不验证服务器是否存在该路径，运行时验证 XML、电子收敛、阶段 NSW，弛豫还检查离子收敛。只读读取 static 不要求 WAVECAR/CHGCAR；DOS/能带后续另要求 CHGCAR。没有随机种子。

新任务目录必须不存在或为空，原结果不改动。后续 VASP 状态写在新任务 workflow_state.json 中，并记录来源目录和依赖；源 XML 内容或配置改变会使相应后续阶段失效，重新计算写入新的 attempt，不删除旧 attempt。复用代表采纳已有结构和电子结果；不会证明来源计算参数符合新的精度要求。

原有 generate_atomate_input 和 resume_from 仍可使用。自动后续入口是独立配置路径，不改变原任务流程。当前新增功能未运行真实 VASP/AMSET 或提交超算，也未运行测试。

配置式生成：`python templates/run_task.py templates/configs/vasp_followup.json` 预览，加 `--run` 只生成任务。先填写任务的服务器路径。

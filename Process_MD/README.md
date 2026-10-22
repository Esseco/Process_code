# Process_MD

面向 MLIP-MD 的 Python 基础库。优先调用已有 `Process_MLIP`，用清晰的参数、结果对象和文件格式供其他项目复用。

## 当前能做什么

| 功能 | 状态与实现来源 |
|---|---|
| 读取结构、扩胞、结构信息 | 已实现，使用 ASE |
| SOC/组成与构型记录 | 已实现，记录匹配参考下的占位/脱出比例，不假设通用 SOC 定义 |
| MACE / CHGNet calculator | 已接通原 Process_MLIP 工厂，调用时才加载模型；保留原参数 |
| NVT 平衡与生产 MD | 已接通原 run_md；生产段可保持同一积分器分块推进与回调 |
| MSD 与扩散拟合 | 已接通原 export_msd / fit_msd 文件接口及诊断 |
| 参数/结果与 JSON/CSV | 已实现；明确单位，默认拒绝覆盖 |
| 结构化 calculate_msd / fit_diffusion | 已实现，返回 MSD/D_self/sigma_NE、窗口和数值诊断 |
| 骨架 MSD/RDF/配位诊断 | 已实现，复用 ASE 工具，不自动判决崩塌 |
| 尺寸/时间/温度证据 | 已实现几何、运行日志统计和两次传输估计比较，不内置审查阈值 |
| 跳距几何代理 | estimate_hop_distance，复用ASE最近同种移动离子距离，含周期像；不推断空位或允许路径 |
| 可选不确定性 | kinisi 2.1后验D/σ_NE区间；实际窗口、随机种子、数值状态及限制 |
| 可选跳跃识别 | GEMDAT原生位点/驻留过滤、事件、覆盖率；未知计数为None |
| 完整 checkpoint / 严格 resume | 尚未实现，显式报错 |

本库不包含自动升温/延时/扩胞、高通量调度、Agent 或数据库。

## 安装与环境

Python >=3.10，核心依赖为 ASE/NumPy。默认使用已有 **py1**，在本目录安装：

```powershell
python -m pip install -e ".[test]"
```

MD、模型加载和原始分析入口需要环境能导入原库：

```powershell
python -c "import Process_MLIP; print(Process_MLIP.__file__)"
```

当前 py1 已满足此条件。其他环境应沿用 Py-Code 的导入配置，将仓库根目录放入 PYTHONPATH；本库不硬编码机器路径、不自动修改 sys.path。Process_MLIP 当前没有独立 wheel 元数据，因此不声明不存在的 PyPI 包。

模型/分析依赖按需使用已有环境；缺少时可安装对应 extra：

```powershell
python -m pip install ".[chgnet]"
python -m pip install ".[analysis]"
```

额外的 `.[mace]` 和 `.[uncertainty]` 为可选依赖。本次不修改现有环境：本机 py1 无 MACE，已有 py-mace 可用 MACE；kinisi 2.1 依赖 NumPy>=2，应使用兼容环境而非直接升级 py1。缺失依赖会明确报错，不回退到其他模型或误差算法。

普通 `import process_md` 不导入 Process_MLIP、PyTorch 或扩散分析器。结构、数据对象、单位换算和序列化可以独立使用。

MACE 用法：`create_mace_calculator(model_path, device="cuda", head=None, default_dtype="float64")`，直接转发原工厂，保留CuEq/Symmetrix显式选项。例如 GPU Symmetrix 使用 `enable_symmetrix=True, symmetrix_use_kokkos=True`；CuEq 与 Symmetrix 互斥。单头MACE-OMat使用本地OMat权重，不混用MH-1预设。`estimate_hop_distance(atoms, species="Li")` 返回最近占据离子间距（Å），可供外部workflow设定位移尺度。

可选不确定性入口：

```python
from process_md import analyze_diffusion_uncertainty

interval = analyze_diffusion_uncertainty(
    production_frames, species="Li", frame_interval_ps=0.01,
    fit_start_ps=1, fit_end_ps=8, temperature_K=800,
    volume_A3=atoms.get_volume(), ion_charge=1,
)
print(interval.diffusion_median_cm2_s, interval.diffusion_lower_cm2_s, interval.diffusion_upper_cm2_s)
```

这里 `production_frames` 是已经截去热化段的均匀连续坐标轨迹/帧序列。原生 kinisi ASE 解析和 Bayesian 推断输出中位数及默认95%可信区间；最多60个 lag 限制分析开销，缺少数据/未解析以状态保存。`check_uncertainty_backend()` 可在运行MD前检查依赖/API。

kinisi 采用非选中原子的算术平均漂移，本库 WLS 框架漂移为质量加权，两种估计分别报告。σ_NE 区间由后验 D 在固定 N/V/T/电荷下传播；不含集体相关性、模型或有限尺寸误差，也未检查 MCMC 收敛。[kinisi 官方 API](https://kinisi.readthedocs.io/en/latest/analyze.html)

## 从哪里开始读

- **使用与 API**：本 README；公共导出在 `process_md/__init__.py`。
- **目录、复用关系、科学语义**：[ARCHITECTURE.md](docs/ARCHITECTURE.md)。
- **开发进度、后续顺序、验证记录**：[DEVELOPMENT.md](docs/DEVELOPMENT.md)。
- **模块 API、审查证据与后续扩展**：[MODULES.md](docs/MODULES.md)。
- **Codex 修改导航**：[AGENTS.md](AGENTS.md)。

```text
process_md/
  models.py          参数与结果 dataclass
  structure.py       结构准备
  state.py           组成状态与构型记录
  md/                calculator 与 MD 适配
  analysis/          扩散与骨架分析
  io/                JSON/CSV
examples/            两个最小示例
tests/unit/          独立工具与边界测试
tests/integration/   调用原库的测试
docs/                架构与开发记录
tools/verify.py      测试和临时打包检查
```

## 独立结构准备

```python
from process_md import MDConfig, get_structure_info, prepare_structure, save_results

atoms = prepare_structure("POSCAR", target_atoms=128)
config = MDConfig(temperature_K=800, duration_ps=50, timestep_fs=2,
                  equilibration_ps=5, trajectory_interval=10, seed=42)
save_results({"structure": get_structure_info(atoms), "parameters": config}, "preparation")
```

`target_atoms` 是下限，按完整输入晶胞数向上取整，使用 ASE 近立方超胞搜索；也可指定 `supercell_matrix`，二者互斥。自动扩胞要求 3D PBC，显式矩阵禁止混合周期/非周期向量。输入被复制，原始原子映射见 `atoms.arrays["process_md_source_index"]`；当前索引仍为 ASE 下标。多帧结构文件默认取首帧。

使用 `describe_alkali_state(atoms, mobile_species="Li", reference_mobile_atoms=...)` 可记录占位/脱出比例。参考数量必须与当前晶胞倍数和骨架归一化匹配；不同空位构型可用 configuration_id 区分。通用 SOC 构型生成与排序策略尚未实现。

## 复用现有 MD 和分析

```python
from process_md import MDRunner, create_chgnet_calculator, export_msd, fit_msd

calculator = create_chgnet_calculator(device="cpu", model_name="0.3.0")
result = MDRunner(calculator).run(
    atoms, temperature_K=800, duration_ps=50, timestep_fs=2,
    equilibration_ps=5, output_dir="run_001", trajectory_interval=10, seed=42,
)
msd_file = result.output_dir / "msd.csv"
export_msd(result.trajectory, msd_file, species="Li", unwrap=False)
transport = fit_msd(
    msd_file, fit_start_ps=10, fit_end_ps=40,
    temperature_K=800, volume_A3=atoms.get_volume(), ion_charge=1,
    species="Li", output_json=result.output_dir / "transport.json",
)
```

MD 使用原 NHC NVT；温度单位 K，时长 ps，步长 fs，输出间隔为步数。默认步长为 2 fs、每 10 步保存一帧，即 20 fs/帧。`duration_ps` 只计生产段且须对应整数步。`output_dir` 必须不存在；结果包含生产/平衡轨迹路径、生产步数、参数及状态。原阶段报告保留温度、能量、时间和错误等信息。

平衡段向生产段传递动量，温控器内部状态会重建。当前 **checkpoint_interval 必须为 None（默认）**；设置正值或调用 resume 会明确报错，轨迹末帧不充当严格 restart。

生产段可用 `segment_ps=10, on_segment=callback` 每 10 ps 回调；整个生产段保持同一个积分器，段间不重建温控器。回调前轨迹/日志已刷新；返回 None/False 继续、True 正常停止并记录实际步数。这里仅提供原语，不提供自动审查规则。总时长由 duration_ps 显式指定，例如 200。

此能力需要更新后的 Process_MLIP；本机已接通。对应的单文件补丁保留在 `tools/patches/process_mlip_segmented_md.patch`，供其他旧库副本审阅迁移，不会在安装/导入时自动应用。旧后端不支持时会在创建输出前明确报错。

原 MD 输出连续坐标，因此分析默认 `unwrap=False`；采样时间可由相邻 report.json 推断，显式指定时 `frame_interval_fs` 是保存帧间隔。原 `unwrap=True` 分支仍使用 ASE MIC；后续原生 pymatgen 解包扩展优先加入 Process_MLIP，本库直接调用，不另写算法。

`export_msd` 和 `fit_msd` 保留原有 dict/文件接口；结构化入口也已可用：

```python
from process_md import calculate_msd, fit_diffusion, validate_framework, summarize_md_log

msd = calculate_msd(result.trajectory, species="Li", frame_interval_ps=0.01)
transport = fit_diffusion(
    msd, fit_start_ps=msd.time_ps[0], fit_end_ps=msd.time_ps[-1],
    temperature_K=800, volume_A3=msd.volume_A3, ion_charge=1,
)
framework = validate_framework(result.trajectory, mobile_species=("Li",))
runtime = summarize_md_log(result.trajectory.with_name("md.csv"))
```

示例用全部正 lag 仅展示接口；它不自动识别扩散区间。wrapped 输入选择 `coordinate_mode="wrapped"`，使用 pymatgen 原生坐标重建。MSD 继续由旧 pymatgen 多起点实现计算，拟合继续由旧 fit_msd 执行。正 D 或高 R² 不证明长程扩散或尺寸收敛；不确定度明确标记未评估。

`validate_framework` 返回去骨架平移的 MSD、初末 RDF；需要配位指标时显式给出材料适用的 `coordination_cutoff_A`。`describe_cell`、`compare_transport` 和日志统计为扩胞/延时/升降温提供数值证据，具体阈值和动作留在后续审查层。详见模块文档。

## GEMDAT 与 kinisi

GEMDAT 为可选 `.[jumps]`，延迟导入；不替换已有pymatgen MSD/WLS。独立调用示例：

```python
from process_md import analyze_jumps, prepare_structure, save_json

jumps = analyze_jumps(
    "production_only.traj", species="Li", frame_interval_ps=0.01,
    min_residence_ps=0.2,
    # reference_sites=prepare_structure("all_sites.cif"),  # 同晶胞，含可能空缺的位点
)
save_json(jumps, "jumps.json")
```

默认位点是首帧占据位置；持续访问缺失位点会返回 `unmapped`，不能当作无跳跃。事件含原子/位点索引、相对本轨迹起点的ps时间、覆盖率和诊断。输入为生产轨迹、固定晶胞、均匀保存间隔；跨周期累计位移核对失败会报错。GEMDAT默认以非移动原子的算术平均去漂移，与旧MSD的质量加权约定分别记录。

`validate_framework(..., rdf_window_fraction=0.2, rdf_frames_per_window=5)` 可对轨迹前后各最多5帧的ASE RDF取平均，保留所选帧索引；默认None仍为原初末帧比较。基础库只返回数值，不决定融化或停止。

kinisi继续通过独立的 `analyze_diffusion_uncertainty(...)` 原生接口提供D/σ_NE后验区间；workflow可只在通过后调用一次，不每10ps运行MCMC。GEMDAT完整依赖解析可能引入kinisi/NumPy≥2，应在兼容环境安装，勿为此直接升级py1。当前py1无GEMDAT/kinisi；本机已在相邻workflow项目的专用`.venv`中安装兼容依赖，两套原环境保持不变，详见[环境说明](../MD_Screening_Workflow/environment/README.md)。

小晶胞可指定 `validate_framework(..., rdf_repeat=(2, 2, 2))`，仅为RDF快照增加周期像；骨架MSD、配位和MD原子数不变。周期像不增加独立样本，也不证明尺寸收敛；默认仍为 `(1, 1, 1)`。

## 结果与单位

```python
from process_md import diffusion_from_slope, save_csv

D = diffusion_from_slope(6.0, dimensions=3)  # 1e-4 cm²/s
save_csv([{"slope_A2_per_ps": 6.0, "diffusion_cm2_s": D}], "units.csv")
```

`D = slope/(2*d)`，`1 Å²/ps = 1e-4 cm²/s`。该函数只转换单位。JSON 保留 dataclass 单位字段名，`save_results` 使用 schema_version=1；CSV 只接受标量，None 为留白。默认拒绝覆盖和 NaN/Inf，先完成序列化/UTF-8 编码再写文件；报告工具不替代原子性 checkpoint。

## 示例与验证

```powershell
python examples/prepare_structure.py
python examples/short_md.py
python tools/verify.py --package
```

前两个示例结束后清理临时结果；short_md 通过原库运行八步 ASE LJ，仅用于接口检查。验证工具运行单元/集成测试，并可离线构建 wheel、临时安装、检查导入与示例，不修改当前环境的包。

py1最终检查为234 passed、12项可选依赖测试跳过；专用运行环境为246 passed，无跳过，含原生GEMDAT和kinisi集成。wheel、临时安装与示例通过。另用本地MACE-OMat对8原子LiF完成1.9 ps短测，结构/跳跃分析及预算停止正常，详见[短测记录](../MD_Screening_Workflow/environment/SMOKE_RESULT.md)。GPU、长时间MD、科学收敛与严格restart尚未验证。

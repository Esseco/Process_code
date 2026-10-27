# Process_MLIP

<!-- Manual project documentation -->

通用 ASE calculator 弛豫工具。默认 py1；具体模型由调用者选择已有专用环境，不在导入时加载模型。

新增独立 [Speed / Ehull Benchmark](benchmark/README.md)：分别比较结构弛豫和 MD 效率，
以及基于用户输入竞争相的标准组成凸包/DFT Ehull 误差。支持 YAML、多模型、阶段恢复及结果图表，
保留原有弛豫、MD 和训练接口。

现支持可配置的 MLIP 分子动力学：MACE / SevenNet / CHGNet / ORB，独立或连续 NVT/NPT。
使用 [完整 MD 示例](examples/mlip_md.py) 集中修改模型、加速与阶段参数；接口和超算说明见 [MD.md](MD.md)。
可选 `pre_relax` 在 MD 前只优化原子或同时优化晶胞；函数默认关闭，完整 MD 示例默认全弛豫（原子和晶胞）后直接运行 NVT，预弛豫与 MD 共用同一模型。
NPT 可选 `npt_cell_mode="isotropic"`（默认）或 `"full"`，温控/压控链和积分子步数可按阶段配置。
`timestep_fs=None` 时按阶段自动选步长：NVT 2 fs、NPT 1 fs；显式数值优先。
NVT 轨迹可直接用 `export_msd` 导出 MSD CSV，默认且仅使用 `pymatgen-analysis-diffusion` 的多时间起点平均；见 [MSD.md](MSD.md) 和 [后处理示例](examples/msd.py)。
原调用和 CSV 列保留；时间改为 lag time，采用 pymatgen 原生 `smoothed="max"` 采样，不再逐帧输出。分析环境需该包，导入项目或单独跑 MD 不需要加载它。
完整 MD 示例提供 `MSD_POSTPROCESS` 开关，运行结束后可自动导出指定元素、指定 NVT 阶段的 MSD。
`fit_msd` 独立读取 MSD CSV 拟合扩散系数和估算 Nernst–Einstein 离子导率；两个示例均提供 `TRANSPORT_FIT` 开关与拟合区间、电荷配置，详见 [MSD.md](MSD.md)。
扩散拟合直接沿用 pymatgen 原生默认算法、权重和斜率处理；保留手动区间和自设离子电荷，不增加拟合算法开关。
fit_start_ps/fit_end_ps 默认 None，按每个元素/分段拟合全部正 lag，也支持只设置一端；实际区间在 actual_fit_range_ps 中。全区间不会自动判断线性扩散区。
默认先保留三维拟合，再检查拟合区间末端 MSD 分量；超过 anisotropy_threshold=10 时补算一维或二维 D/导率。阈值可调，diffusion_mode="3d" 可关闭，"1d"/"2d" 配合 axes 可手动指定 Cartesian 方向。新结果写入 reduced_dimensional，原三维字段不变；该检查只是筛选，不证明扩散维数。规则与单位见 [MSD.md](MSD.md)。
末端总 MSD 小于 min_msd_A2=1.0 Å² 时跳过自动降维补算，保留三维结果并标记 low_msd；门槛可调，0 关闭过滤。手动降维不受此门槛限制；小 MSD 不自动归因为热振动。
已有轨迹的一次性重算可用 [精简独立示例](examples/postprocess_md.py)：顶部修改路径、元素、拟合区间、电荷和实际温度，体积自动读取。运行 `python -m Process_MLIP.examples.postprocess_md`；输出 postprocess/msd.csv 和 transport.json，重复运行覆盖这两个分析文件。
多模型 LCO/NVP 汇总见 [批处理示例](examples/batch_postprocess_md.py)：自动从各 NVT 阶段 report.json 读取温度、体积、时间、步数及速度，手动指定拟合区间和电荷，输出平铺 out.csv，失败任务保留错误记录。

## 代码分工

| 职责 | 文件 |
|---|---|
| 统一公开入口 | `__init__.py`，集中导出已有函数 |
| 模型配置与加载 | `model_config.py`、`calculators.py`，延迟加载模型 |
| 结构弛豫 | `MLIP_Relax.py` 是唯一 ASE 优化实现；`mace_relax.py`、`sevennet_relax.py` 保留模型专用入口 |
| 单阶段 MD | `md.py`，负责积分、输出和实际耗时统计 |
| 流程编排 | `md_workflow.py`、`pre_relax.py`，负责模型复用、弛豫及多阶段衔接 |
| 训练数据转换 | training_data.py：VASP 结果转为带参考标签的 MACE extxyz |
| 后处理 | `msd.py`、`transport.py`、`trajectory.py`，分别负责 MSD、扩散拟合和抽帧 |
| 内部共用代码 | `_md_support.py`：校验/状态/报告；`_relaxation.py`：单结构返回值适配 |
| 示例与测试 | `examples/` 放可修改脚本，`tests/` 放回归测试与共享夹具 |

原公开模块路径、函数签名和返回字段保持兼容。预弛豫与旧单结构接口的默认优化设置不同，
共用底层实现，但各自保留原默认值；MC 委员会和其他项目仍独立。

## 从轨迹提取结构

```python
from Process_MLIP import export_traj_frames

export_traj_frames("md.traj", "frames", frames=[0, 100, -1])
# 间隔抽帧：frames=slice(0, None, 100)；全部：frames=None；默认：末帧。
```

索引从 0 开始，不是时间或 MD 步号；-1 为末帧。多起点 MSD 的 `frame_index` 仅是 lag 参考索引，不能将该帧当作 MSD 的唯一终点。
默认输出 `frame_000000.vasp` 等文件，返回实际帧索引、文件路径和源轨迹总帧数。
支持 `format="vasp" / "cif" / "xyz" / "extxyz" / "traj"`；VASP/CIF 需完整晶胞。
不加载模型、不改变结构、不修改源轨迹，重复运行默认拒绝覆盖（可设 `overwrite=True`）。
VASP 保存几何结构；需保留动量等 ASE 数据时用 `traj`。弛豫、NVT、NPT 轨迹均可抽帧，
按各帧自身晶胞输出，不推断物理时间、不执行周期展开。无需随机种子，默认 py1 环境。
独立示例：[extract_frames.py](examples/extract_frames.py)。

## VASP 结果转为 MACE 微调数据

```python
from Process_MLIP import vasp_to_xyz

n_frames = vasp_to_xyz("calculation/vasprun.xml", "train.xyz")
# OUTCAR 或计算目录也可；默认全部离子步，index=-1 只导出末帧，index="::10" 间隔抽帧。
# 合并多个计算：vasp_to_xyz(["calc_1", "calc_2/OUTCAR"], "train.xyz")
```

输出为扩展 XYZ（后缀 .xyz 或 .extxyz 均可），返回实际写出的帧数。
REF_energy 为整胞能量（eV），REF_forces 为原始 DFT 力（eV/Å），
REF_stress 为 ASE 应力（3×3，eV/Å³，拉伸为正）；单位和 VASP 应力符号转换由 ASE 完成。
默认 energy_type="free_energy"，使用与力一致的 VASP 自由能；
需要零展宽外推能时显式设置 energy_type="energy"，同一数据集保持能量约定一致。
读取原始力时不施加固定原子约束，输出不携带计算器或约束，不加载模型或重新计算。

MACE 训练显式使用对应字段：
```text
--energy_key=REF_energy --forces_key=REF_forces --stress_key=REF_stress
```

目录优先读 vasprun.xml（支持 .gz），不存在才选 OUTCAR；不会把解析失败自动当作可跳过数据。
缺少能量、力、应力或遇到非有限值时明确报错；仅需能量与力可设置 include_stress=False。
默认拒绝覆盖，overwrite=True 才替换；转换失败保留原输出，临时文件自动清理。
默认 py1，无随机性，不修改 VASP 源文件。调用者负责检查电子收敛、DFT 参数一致性和选帧质量；
本函数不自动做收敛筛选、训练集划分、能量校正或模型训练。

## 独立模板

| 功能 | 输入 → 输出 | 模板 |
|---|---|---|
| 通用 calculator 弛豫 | ASE Atoms + calculator → 弛豫结构、能量、收敛与步数、轨迹 | [ase_relax.py](examples/ase_relax.py) |
| MACE 单结构弛豫 | 结构文件 + 模型 → 最终结构及报告 | [mace_relax.py](examples/mace_relax.py) |
| SevenNet-Omni 单结构弛豫 | 结构文件 + checkpoint + modal → 最终结构及报告 | [sevennet_relax.py](examples/sevennet_relax.py) |

通用模板需实现 make_calculator；MACE 模板使用 Process_MLIP.mace_relax 的公共实现。填写顶部路径后从根目录运行：

```text
python -m Process_MLIP.examples.ase_relax
python -m Process_MLIP.examples.mace_relax
```

两者独立，不要求统一 CLI；模板不覆盖已有输出，导入不执行计算。MACE 需要模型文件和兼容环境，通用模板不是开箱即用的科学模型。

## 原接口与返回值

```python
from Process_MLIP import MLIPRelaxer
result = MLIPRelaxer(atoms.copy(), calculator, fmax=0.05,
                     steps=200, optimizer="BFGS", relax_cell=False).relax(
    traj_file="relax.traj", log_file="relax.log", final_structure="final.extxyz")
```

原有 final_struct、energy、natoms、energy_per_atom、trajectory_file、log_file 保留。新增 optimizer_converged、relax_steps_used、force_max_ev_per_angstrom、energy_unit；能量 eV，力 eV/Å。达到步数上限仍返回结果，必须查看 optimizer_converged，不将函数结束视为收敛。

## 参数与限制

MLIPRelaxer 修改传入 Atoms，并设置 calculator；模板先复制。已有原子约束保留。固定晶胞时使用原子力判断，relax_cell=True 使用 FrechetCellFilter，收敛还涉及应力自由度，force_max 不能单独判定晶胞收敛。模型必须支持所需元素、能量/力以及晶胞弛豫所需应力。
MD 预弛豫默认 FIRE、`maxstep=0.05` Å；`exp_cell_factor=None` 按原子数缩放晶胞变量。两参数可在 `pre_relax` 中覆盖；旧脚本省略时自动采用新默认值。单独调用 MLIPRelaxer 的 `maxstep=None` 保持 ASE 优化器默认步幅。

底层 relax 默认会写轨迹/日志，直接调用会遵循 ASE 原写入规则；模板用独立目录。Atoms 不能直接写为普通 JSON，需显式转换或写结构文件。现有 MACE 接口与通用接口返回形式不同，暂不强行统一。

## 验证与边界

在仓库根目录用 py1 运行：

```bash
python -m unittest discover -s Process_MLIP/tests -t . -p "test_*.py"
```

单独运行弛豫测试：`python -m unittest Process_MLIP.tests.test_relax`。
测试按功能归并为 11 个文件，临时目录、替代 calculator 和示例夹具集中在 `tests/_support.py`；
公开 API 索引不包含测试。完整覆盖范围见 [tests/README.md](tests/README.md)。
测试使用 ASE/EMT 或模型替身，不代表真实模型、GPU 加速或材料性质已验证。

合并候选见 [BOUNDARIES.md](BOUNDARIES.md)，真实签名见 [API.md](API.md)。

## MACE 合并已完成

单结构 MACE 入口保存在 Process_MLIP/mace_relax.py，底层复用统一优化器；Process_AL_MC/relax.py 仍兼容导出同一函数。函数签名、默认值、模型 head 选择和报告字段保持不变；MC 类的委员会弛豫仍独立。

## MH-1 与 SevenNet-Omni

接口、环境、真实模型验证及调用示例见 [MODEL_COMPATIBILITY.md](MODEL_COMPATIBILITY.md)。
本机 MH-1 使用 `py-mace`，Omni 使用已有 `py1`；两环境的 e3nn 版本不同，勿混用。
两者当前均为 CPU PyTorch，调用时显式设置 `device="cpu"`。
`create_mace_calculator` / `create_sevennet_calculator` 也可接入原 `MLIPRelaxer`。

Symmetrix 加速通过 MACE 配置的 `enable_symmetrix=True` 开启，支持 OMat 权重转换或
预转换 JSON、元素裁剪与 Kokkos 选项，和 CuEq 互斥。完整配置见 [MD.md](MD.md)。

## NEP/GPUMD 双后端

`Process_MLIP` 支持 GPUMD NEP4。`model_config("nep", model_path=..., backend="cpu")` 使用 Calorine `CPUNEP`，适合本地 CPU 的单点、弛豫和短程 ASE MD；`backend="gpu"` 使用 `GPUNEP`，需要超算环境中的 GPUMD。后端显式选择，缺失依赖不会静默回退。

训练和微调任务使用 `prepare_nep_training()`、`train_nep()`、`fine_tune_nep()`；长时间、大体系 GPU MD 使用 `run_nep_md()` 直接生成 `model.xyz`、`run.in` 并调用 `gpumd`。`vasp_to_nep_xyz()` 生成标准 `energy`/`force`/`virial` extended XYZ，现有 `vasp_to_xyz()` 的 MACE `REF_*` 输出保持不变。

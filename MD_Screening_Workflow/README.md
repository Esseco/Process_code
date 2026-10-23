# MD_Screening_Workflow

复用 `Process_MD` 的简单、低成本 MLIP-MD 筛选。第一版处理**一个已生成的结构/SOC 构型、一个温度**，默认模型为 **MACE-OMat**。

默认：至少 200 原子、800 K NVT、**2 fs 积分步长，每 20 fs 保存一帧**，前 **5 ps** 骨架检查，随后每 **10 ps** 分析一次累计生产轨迹。全程使用同一积分器，不重置 thermostat。

## 输入当前结构和满位点参考运行

在`run_md.py`顶部填写`STRUCTURE_PATH`（当前SOC结构）和`REFERENCE_SITES_PATH`（满位点参考）。在配置好CUDA/Kokkos Symmetrix及分析依赖的环境中，从本项目目录运行：

```powershell
python run_md.py
```

`run_md.py`默认开启GPU Symmetrix，自动识别Li/Na，结果存入当前目录下`runs/结构名_时间戳/`。
也可用`python run_md.py POSCAR_SOC POSCAR_FULL`覆盖顶部两份路径。
模型优先使用顶部`MODEL_PATH`、其次环境变量`PROCESS_MD_MACE_MODEL`，否则查找与已有`Process_MLIP`并列的`MLIP_model/mace/mace-omat-0-medium.model`。
温度、生产时间上限等在脚本顶部修改；同时含Li和Na的结构需指定`MOBILE_SPECIES`。运行结束打印D、σ_NE、R²和MSD/汇总路径；未解析的数值显示None。

## 停止条件

默认粗筛要求一次检查同时满足：

| 条件 | 默认值 |
|---|---|
| 生产时间 | ≥10 ps，不含前 5 ps |
| 指定离子的 MSD | **>3d²**，单位 Å² |
| 拟合 R² | **>0.95** |

其中 `d` 是所提供满位点参考结构中**同种移动离子位点最近邻间距**，含周期镜像；作为跳距的几何近似自动识别。例如 `d=3 Å` 时，MSD 阈值为 **27 Å²**。已知跳距时用 `hop_distance_A` 手动覆盖。程序不推断迁移势垒或保证最近邻就是允许路径。参考近邻距离记录为`run.json`中的`reference_nearest_neighbor_A`。

MSD 指拟合窗口末端的多起点平均 MSD，使用选定 Cartesian 分量；它不是累计路径长度，也不是所有离子位移之和。只在实际可用的 lag 网格中拟合，原始斜率及 D/σ_NE 必须为正，不接受后端人为斜率下限。

满足后正常停止，状态为 `heuristic_ready`：可用于粗筛的 D/σ_NE 估计。**不要求多次连续合格、D 变化率或可信区间宽度**。最早总时间 15 ps 可停止。

另有两种成本保护，骨架失稳优先于传输通过：

| 情况 | 默认处理 |
|---|---|
| 骨架 MSD 大且持续增长，同时 RDF 明显变化 | 停止，`framework_unstable`，留待复核 |
| 生产满 **10 ps**，GEMDAT 无有效跳跃且 MSD 平台 | 停止，`needs_review`，建议 `raise_temperature` |
| 有少量跳跃但尚未通过，或位点映射不可靠 | 每 10 ps 继续检查，生产最多 **200 ps** |

无跳跃早停最早也是总时间 **15 ps**。这是用户选择的成本优先策略，可能漏掉慢扩散，不代表证明材料低导率。到上限返回 `budget_exhausted`，不写成可信 D=0；不自动升温。

R² 与位移阈值是成本优先的经验条件，不证明尺寸收敛、采样充分或骨架稳定。高 R² 不代表 D 的统计误差小：[He et al., 2018](https://doi.org/10.1038/s41524-018-0074-y)。这里采用的是用户确认的粗筛标准。

## 安装与模型

在兼容的 Python 环境中先让 `Process_MD` 项目根目录进入 `PYTHONPATH`，或从该目录做 editable 安装。Windows 本机示例：

```powershell
python -m pip install -e "E:/Py-Code/Process_MD[analysis,jumps]"
python -m pip install -e ".[test]"
```

还需能 `import Process_MLIP` 和 `import process_md`，且旧库 MD 接口有连续分段扩展。`Process_MD` 当前位于 `E:/Py-Code/Process_MD`；超算上使用对应的项目根路径。现有补丁在 `Process_MD/tools/patches/`，不自动应用。模型通过原库工厂加载，不复制加载/积分算法。

本机已配置专用 `.venv/Scripts/python.exe`，只读复用py-mace的模型栈，GEMDAT、kinisi和兼容的扩散分析依赖仅安装到新venv。两个本地项目已editable安装。**py1和py-mace的原安装清单均保持不变**；py1仍用于默认开发测试。[环境使用与边界](environment/README.md)包含版本约束、检查命令和现有基础环境的无关依赖告警。MACE可选依赖为`.[mace]`，CHGNet仍可显式注入。正式 workflow 默认设备为 CUDA；Symmetrix 需要单独安装其 CUDA/Kokkos 构建后显式开启。

权重使用本地路径，不下载，不回退到其他模型。官方模型名称见 [MACE foundation models](https://mace-docs.readthedocs.io/en/latest/guide/foundation_models.html)。

## Python API

```python
from md_screening import ScreeningConfig, StopCriteria, run_screening

result = run_screening(
    "POSCAR",
    reference_sites="POSCAR_FULL",
    output_dir="runs/material_A_SOC_50",  # 必须为新目录
    config=ScreeningConfig(
        mobile_species="Na",
        configuration_id="material_A_SOC_50",  # 只记录标签，不生成SOC构型
        model_path="/path/to/mace-omat-0-medium.model",
        device="cuda",
        enable_symmetrix=True,
        symmetrix_use_kokkos=True,
        # symmetrix_species=("Li", "P", "S", "Cl"),  # 可选元素裁剪
        # hop_distance_A=3.0,  # 可选；默认从满位点参考估计
        stop_criteria=StopCriteria(no_jump_stop_ps=10),  # 可改20；保留10ps/3d²/R²>.95
    ),
)
print(result.status, result.last_check.stop_metrics)
```

初始温度（同时为该次NVT的目标温度）和生产时间上限可在Python中通过
`ScreeningConfig(temperature_K=700, max_production_ps=100)`设置；本次运行保持该目标温度。
命令行示例：

```powershell
python examples/run_case.py POSCAR runs/material_A `
  --reference-sites POSCAR_FULL `
  --model-path "/path/to/mace-omat-0-medium.model" `
  --temperature-K 700 --max-production-ps 100 `
  --device cuda --enable-symmetrix --symmetrix-use-kokkos
```

`--max-production-ps`不含前5 ps初检，须为10 ps检查周期的整数倍；100 ps生产上限对应总计最多105 ps，满足停止条件可提前结束。
结束时终端打印最后一次检查的MSD末个lag值、D（cm²/s）、σ_NE（S/cm）、R²及结果路径。
完整MSD曲线在`checks/*_production/msd.csv`，每次检查的拟合窗口、诊断、D与σ_NE在`report.json`和`summary.csv`，`run.json`保留配置与最终状态。
未获得MSD或未解析到正扩散系数时，JSON数值为`null`、CSV为空，并保留原因；前5 ps结构检查就停止时没有生产MSD/D/σ。预算结束时已有的数值估计不等于粗筛通过。

必须传 `reference_sites="all_sites.cif"`，需与**扩胞前输入结构**使用同一晶胞与坐标原点；程序对两者应用相同扩胞矩阵。它应包含当前SOC中空缺的移动离子位点。GEMDAT直接使用这些位点，不从首帧或轨迹密度生成参考。程序检查晶胞/PBC、移动位点数及有效近邻距离，但不能自动证明参考位点完整或已正确对齐；需由调用方确认。若计算的本身是满位点态，两参数可指向同一结构文件。

也可以设置环境变量 `PROCESS_MD_MACE_MODEL` 指向已有权重。默认 `head=None`、float64，单头 OMat 不使用 MH-1 的任务预设。已有 ASE calculator 可通过 `calculator=...` 注入；模型路径配置仅在使用默认加载器时生效。`enable_cueq` 与 `enable_symmetrix` 互斥；GPU Symmetrix 必须同时设置 `symmetrix_use_kokkos=True`。

`stop_criteria=None` 且不传 reviewer 时恢复记录模式：诊断仍保存，运行至预算上限。`jump_analysis=False` 可关闭 GEMDAT 分析，`framework_criteria=None` 可关闭结构判据。传入 `reviewer(CheckReport)->Decision` 会替换默认自动决策，保留完整诊断。调整动作只保存请求和理由，暂不自动执行。自定义 accept 记录为 `accepted`。

## 单结构筛选流程

默认先把 SOC 结构扩胞到至少 200 个原子，再调用 `Process_MLIP` 的 ASE 预弛豫实现（默认原子与晶胞一起优化，LBFGS、`fmax=0.05 eV/Å`、最多 1000 步、`maxstep=0.05 Å`），然后进行 5 ps NVT 初检。弛豫不收敛时默认停止；可通过 `ScreeningConfig` 调整参数或关闭弛豫。初检通过后每 10 ps 检查结构、MSD、GEMDAT 跳跃和输运拟合，生产阶段最多 200 ps。

弛豫轨迹、日志和报告写入 `relaxation/`，弛豫后的结构写入 `prepared/relaxed_structure.extxyz`。完整位点参考结构不参与弛豫或 MD；若弛豫改变晶胞，程序按相同晶胞变形同步更新参考位点。

## GEMDAT 跳跃与平台检查

通过原生GEMDAT内位点区域与最小驻留时间过滤热振动，默认驻留 **0.2 ps**，可用 `jump_min_residence_ps` 调整。`jump_site_inner_fraction` 默认 **0.8**，控制位点内区相对于站点半径的大小；调大后更容易将弛豫后略有偏移的离子识别为原位点，但仍受站点半径限制。站点半径默认最近位点间距的0.45倍，可用 `jump_site_radius_A` 覆盖。若GEMDAT无法从内位点状态构造跳跃事件，结果会标为 `unmapped`、跳跃数记为未知，并提示检查阈值或参考位点对齐，不会误记为零跳跃。

只有可解析的零跳跃、总体覆盖≥95%、每离子覆盖≥80%，才参与无跳跃早停。参考遗漏中间位点造成的持续未映射、单一周期位点等为unknown，不能解释成零跳跃。骨架诊断、D和σ_NE仍使用当前SOC轨迹及其实际离子数；参考结构不参与MD。平台复用已有MSD的后半段：拟合总变化量/平均MSD≤0.2（分母下限0.05 Å²），不额外计算MSD。

GEMDAT与kinisi使用非移动原子的算术平均漂移；现有pymatgen/WLS路线为质量加权，报告保留差异。[GEMDAT跳跃说明](https://gemdat.readthedocs.io/en/latest/notebooks/jumps/)

## 可选不确定性

基础库提供 `analyze_diffusion_uncertainty(...)`，复用 [kinisi 的 ASE 解析与 Bayesian 分析](https://kinisi.readthedocs.io/en/latest/analyze.html)，输出 D 的后验中位数、95% 可信区间及相应 σ_NE 区间，包含实际拟合窗口、样本数、随机种子和诊断。

默认 **不运行 kinisi，也不以区间宽度限制停止**。设置 `uncertainty_on_stop=True` 可在粗筛通过后仅运行一次；缺少依赖会在 MD 前报错。也可 MD 结束后对生产轨迹单独调用基础库，减少 MD 检查时的开销。

可选依赖为 `.[uncertainty]`，使用 kinisi≥2.1,<3；其依赖 NumPy≥2，应放在兼容分析环境，避免升级现有 py1 破坏其他模型。kinisi 原生框架漂移是算术平均，本库 WLS 路线为质量加权；输出分别命名，不把 kinisi 后验区间当成 WLS 误差条。当前不检查 MCMC 收敛；区间不含模型误差或有限尺寸误差。

## 输出与骨架检查

```text
runs/case/
├── run.json                   # 配置、组成/标签、模型路径、跳距来源、状态及错误
├── prepared/structure.extxyz   # 扩胞结构及来源索引
├── md/production/             # 同一条完整连续轨迹、日志及末帧
├── checks/000_precheck/report.json
├── checks/001_production/      # 每次累计生产分析及msd.csv
└── summary.csv                # 各检查点指标、门槛、理由及可选kinisi结果
```

前5 ps及后续每个10 ps窗口复查骨架去平移MSD和ASE RDF；RDF仅平均前后各最多5帧。三个经验门槛**同时命中**才标记失稳：末四分之一窗口平均MSD>1 Å²，后半段两次相邻四分之一窗口的MSD均值增量均>0.2 Å²，RDF相对L1差>0.5。`FrameworkCriteria(...)` 可调整；不是通用熔化标准。

小晶胞可选`framework_rdf_repeat=(2,2,2)`，只对RDF快照扩展周期像，不增加MD原子数、独立采样或证明尺寸收敛；默认仍为`(1,1,1)`。

初始重排随后平台、整体平移或仅RDF变化不会单独触发。缺证据为 `insufficient_data`，通过为 `no_instability_detected`，不证明长期稳定。默认自动模式失稳时跳过昂贵分析并停止；记录/自定义模式继续保留分析。配位需显式cutoff，仅作辅助记录；NaN/Inf或计算/分析异常仍为 `failed`，保存记录并抛出。

生产 MSD 排除前 5 ps，保留边界帧；`fit_start_ps/fit_end_ps` 是 lag 时间。底层 `md/production/` 的原始轨迹仍包含前 5 ps，另做分析时须截取。D 单位 cm²/s，σ_NE 单位 S/cm；σ_NE 是 Nernst–Einstein 估计，不含离子相关修正。

没有严格跨进程 restart，末帧不是完整 checkpoint；不自动扩胞/变温、生成 SOC 或安排多温度外推。

## 开发入口

`md_screening/` 按 config、calculators、analysis、stopping、stability、review、workflow 分类；`tests/` 分 unit/integration；`examples/` 为最小使用例。详见 [架构说明](docs/ARCHITECTURE.md)。

```powershell
python tools/verify.py --package
python examples/short_demo.py
python examples/run_case.py POSCAR runs/case --reference-sites POSCAR_FULL --species Na --model-path /path/to/mace-omat-0-medium.model --device cuda
```

短 LJ 演示只跑 14 步并使用记录模式，不加载模型，不验证真实材料性质。验证临时产物结束后清理。

已有真实CPU MACE-OMat短测：[结果记录](environment/SMOKE_RESULT.md)。8原子LiF、1900步、总1.9 ps，约471秒；结构/跳跃分析运行成功，按短测预算结束。此测试压缩检查窗口，未改变正式5+10 ps默认值，也未强行触发低移动性早停。

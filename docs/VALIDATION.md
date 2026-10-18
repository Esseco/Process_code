# 验证与已知问题

2026-10-18：fit_msd 的 fit_start_ps/fit_end_ps 默认 None；每个元素/分段分别取全部正 lag，支持单端或双端手动边界。零 lag 不拟合；非有限/负数据、重复时间、越界和不足三点仍报错，未增加自动线性区识别。顶层 fit_range_ps 保留请求（可含 null），各结果 actual_fit_range_ps 记录实际区间。独立、批处理、MSD 和完整 MD 示例默认两端 None，预检查与核心拟合共用边界解析；批处理汇总仍输出实际时间范围。py1 完整 115 项测试 OK（原有 full MTK 缺失跳过 1 项），覆盖默认省略、双端 None、单端 None、多元素/分段不同范围、零 lag 排除、异常和示例完整流程；静态索引 15 项目/596 符号，preview 与 whitespace 检查通过。未调整模型环境或执行超算任务。

2026-10-18：新增 Process_MLIP/examples/batch_postprocess_md.py，沿用用户模型/results/LCO或NVP/阶段目录，自动读取各阶段 report.json 的温度、体积、步数和速度，按手动区间/电荷重算 MSD 与输运系数，输出一阶段一行的平铺 out.csv。跳过 NPT、区分阶段输出，失败记录错误不中断整批。py1 相关 14 项测试通过，含两个元素真实后端处理、报告自动读取和平铺结果/失败记录；静态索引 15 项目/596 符号。未修改模型环境，未访问用户超算数据。

2026-10-18：新增 Process_MLIP/examples/postprocess_md.py 精简独立后处理示例，顶部集中路径、元素、拟合区间、电荷、温度及外部轨迹保存间隔；体积从固定晶胞读取，复用 export_msd/fit_msd 原生 pymatgen 默认流程。重复运行只覆盖分析目录的 msd.csv、transport.json，不修改源轨迹。py1 相关 13 项 MSD/示例测试通过，包括真实后端完整链路、重复运行、区间/电荷传递与源文件保持；索引 15 项目/595 符号，whitespace 检查通过。未调整模型环境或运行超算。

### 2026-10-18 扩散系数采用 pymatgen 原生默认拟合

- fit_msd 原参数/调用保留，先按 fit_start_ps/fit_end_ps 截取 CSV 的 lag 区间，再调用 get_diffusivity_from_msd(msd, dt_fs)，不覆盖 smoothed 或权重等参数。总量和 x/y/z 都用原生默认值；方向结果按一维 Einstein 关系换算，保留 SI/常用单位。
- 按用户补充要求不添加 OLS 开关，不覆盖原生斜率正数下限。零/负/极小斜率可输出极小正 D，新增 pymatgen_slope_floor_applied 标记；原始加权斜率、截距和普通 R² 作诊断，不能把截断值解释为真实扩散。正 lag、至少三点及输出保护检查保留。
- 电导率仍使用调用者给定的电荷数、实际温度/体积和目标原子数进行 Nernst–Einstein 换算；不自动推定氧化态、不加入关联修正。两个示例保持手动区间和离子电荷配置，不增加算法参数。
- 已有 py1 / pymatgen-analysis-diffusion 2024.7.15：完整 108 项测试 OK（1 项原有 full MTK 实测跳过）。新增原生默认调用/裁剪/ps→fs/权重对照、方向系数、斜率下限和缺依赖测试；多元素多段、电荷/单位、JSON、独立及完整 MD 示例通过。静态索引 15 项目、594 符号，whitespace 检查通过。
- 未安装/升级依赖或调整模型环境；未执行真实 MLIP/GPU/超算或验证真实材料扩散与电导率收敛。

### 2026-10-18 pymatgen 多时间起点 MSD

- export_msd 移除 ASE 单起点统计，唯一后端为 pymatgen-analysis-diffusion DiffusionAnalyzer / smoothed="max"。既有调用与 CSV 列/单位保留，新增可选 min_obs=30；时间改为 lag，原生约 1 ps 起取样，不保证逐帧或零时刻输出。
- 保留连续坐标、ASE MIC 周期展开、框架质量加权漂移及独立分段。固定零位移参考位点阻止后端额外扣除漂移；不采用其自动拟合。短尾帧警告排除并记录，其他不等间隔报错；数据不足或缺依赖不回退、不写 CSV。
- 更新独立 MSD/完整 MD 示例、说明与 API 索引。完整 MD 示例在加载模型前检查依赖、原子数、采样范围和拟合窗口；八组/六组批任务原调用无需改动。
- py1（已有 pymatgen-analysis-diffusion 2024.7.15）：`python -m unittest discover -s Process_MLIP/tests -t . -p test_*.py -q`，102 项，OK，跳过已有缺失 full MTK 的 1 项。手工枚举随机轨迹所有位置对与真实后端比对，覆盖归一化、多元素/纯元素、斜晶胞、分段、漂移、尾帧、min_obs、缺依赖与输出保护；真实零力 MD→MSD→fit_msd 及独立/批量示例通过。
- 静态索引 15 项目、594 符号；完整 MD --preview 和本次变更 whitespace 检查通过。未安装/升级依赖或调整模型环境，未加载真实 MLIP、执行 GPU/超算任务或验证材料扩散收敛。

2026-10-15：完整 MD 示例新增 MSD_POSTPROCESS，默认关闭；全部 MD 阶段成功后复用 export_msd 自动导出指定 NVT 阶段/最后 NVT 的指定元素 MSD。元素、输出路径及覆盖策略可配置，预先拦截无 NVT、错误阶段、已有 CSV、零步及覆盖 MD 日志等情况；preview 不计算。新增 7 项示例集成测试，使用 EMT 真实短程 NVT/NPT；py-mace 65 项全部通过，py1 仅跳过已有缺失 full MTKNPT 的 1 项。未加载 MLIP 权重或调整模型环境。

2026-10-15：Process_MLIP 新增 export_msd，复用 ASE DiffusionCoefficient，默认导出整段固定晶胞 NVT 轨迹的逐帧、按元素 MSD（总量及 xyz 分量，Å²），不拟合 D 或电导率。可从同目录报告恢复真实时间轴，含末尾短间隔；默认保留本项目的连续坐标，外部 wrapped 轨迹使用 ASE find_mic 展开。新增 11 项解析轨迹/真实 EMT NVT 测试，验证 MSD 归一化、人数平均、周期/斜晶胞、时间轴、漂移修正及输出保护。py-mace 的全部 58 项回归测试通过；py1 的 58 项仅跳过已有的 1 项缺失 full MTKNPT 实测，其余通过。未加载模型或调整环境，未对真实材料扩散采样收敛性作验证。示例见 Process_MLIP/examples/msd.py。

2026-10-15：MD 新增 npt_cell_mode=isotropic/full，保留 NHC NVT 与 MTK NPT；开放 tchain=3、pchain=3、tloop=1、ploop=1。既有 py-mace 环境的 47 项测试全部通过，包括 EMT 实际柔性 MTK 晶胞形状变化；py1 运行同一 47 项，其中缺少 full MTKNPT 的 1 项真实积分测试明确跳过，其余通过。验证默认兼容、NVT/各向同性参数、full 模式分派、阶段覆盖、缺失实现加载前报错。未调整模型环境，未运行真实模型 GPU MD 或验证材料相变/热膨胀精度。示例与 Process_MLIP/MD.md 已更新。

2026-10-15：MD 新增可选 measure_steps_per_second，记录每阶段及整次流程 steps/s；只计积分和观察回调/输出，排除加载、预弛豫及最终导出，CUDA 在计时前后同步。py1 的 40 项测试通过，其中时钟替身验证计时计算、CUDA 同步调用顺序、零步/关闭计时及多阶段按总时间汇总；未验证真实 GPU 计时精度，未调整模型环境。

2026-10-15：run_mlip_md 新增可选 pre_relax（默认关闭），复用原 MLIPRelaxer 和同一 calculator，可仅优化原子或同时优化晶胞。py1 的 35 项回归测试通过。新增针对性 EMT 测试覆盖模型单次加载、优化结构传入 MD、初速度策略、非收敛默认停止/显式继续、失败报告和输出保护；含真实短程“晶胞弛豫 → NVT → NPT”。未调整本地模型环境；四模型真实 GPU/加速与材料科学精度未验证。完整示例的 PRE_RELAX 参数区和 Process_MLIP/MD.md 已更新。

2026-10-15：Process_MLIP 新增 model_config / run_mlip_md / run_md，支持 MACE、SevenNet、CHGNet、ORB 的配置式 NVT/NPT 与连续阶段；新增 CuEq、FlashTP 开关。py1 使用 ASE EMT 实际短程积分和替身模型接口验证，不加载四模型权重、不调整本地模型环境。覆盖独立 NVT/NPT、速度继承、单次加载、参数覆盖、压力动能项/单位、初末帧、输出保护、非有限数值和失败报告、四模型分派/加速开关。示例安全导入及 --preview 不导入 torch 或模型库。超算真实 GPU MD、CuEq/FlashTP/ORB 编译和科学精度未验证。详见 Process_MLIP/MD.md。

2026-10-15：Process_MLIP 新增 calculator 工厂及 SevenNet-Omni 单结构入口，修复旧 e3nn 导入与 PyTorch weights_only 默认值冲突，补装 py-mace 缺失的 orjson。py1 的 6 项单元测试通过。真实 Si 两原子晶胞：MH-1/omat_pbe 在 py-mace、Omni/mpa 在已有 py1 均完成 CPU 能量/力/应力计算和晶胞弛豫（均 2 步收敛，fmax=0.05 eV/Å）。py-mace 的 e3nn 0.4.4 不兼容 SevenNet，需分环境运行。官方 Omni 权重保存在 MLIP_model；未验证 CUDA、其他 head/modal 或用户材料精度。详情见 Process_MLIP/MODEL_COMPATIBILITY.md。

空间容量候选定义已按用户要求修正为先由 CCNB 截止半径筛选贯通通道，再从 `structure.net` 中 1D/2D/3D 分量选取位点；孤立间隙和 0D 分量不计入，无贯通通道返回 0。保留单次贪心和 2 Å 周期间距；本次仅改代码与静态索引，未运行计算验证。

位点容量随后按用户粗筛需求改为按自由半径排序的一次贪心筛选，取消多起点和完整距离矩阵，保持周期最小间距条件。未运行计算或性能测试，无法给出实测提速倍数；位点数可能低于原多起点结果。

2026-10-01：新增 `Process_Struct.estimate_spatial_capacity`，默认 CCNB 间隙自由半径 0.8 Å、所选离子位点间距至少 2 Å，确定性贪心装载数换算为 mAh/g。用户要求只改代码，因此未执行计算或新增测试；其最大装载数未获全局最优证明，详见 Process_Struct/SPATIAL_CAPACITY.md。

文档索引通过 AST 静态解析，未导入全部项目，不表示所有模块可运行。原项目目录、公开接口、模型及计算结果保持原位。

检查入口：

- py1：`python -m unittest Process_Vasp.tests.test_dos Process_Vasp.tests.test_excitation Process_Vasp.tests.test_layout`。
- atomate2：`python -m unittest Process_Vasp.tests.test_atomate_directories`。
- 文档索引：`python tools/project_catalog.py`。
- 配置预览：`python templates/run_task.py templates/configs/vasp_dos.json`。

VASP 测试使用模拟数据验证处理逻辑，尚未执行真实 VASP/集群任务。模板能力以已适配 recipe 为准。

2026-10-01：Process_Vasp 按 inputs/results/structures/workflows 归档实现，templates/docs/tests 分离。py1 的 8 个测试、atomate2 的 1 个测试通过；覆盖 DOS/压缩输出、激发态准备、旧模块与新模块对象一致性、模板路径、独立运行器复制和模拟断点恢复。首次沙箱执行因临时目录权限失败，随后用正常文件权限重跑通过；遗留临时目录保留原位。实际 VASP、POTCAR 生成和集群提交未验证。

已知问题：

- Process_Chgnet 部分模块引用已不存在的 Process_VaspOut。correct_energy/get_Na_coord/get_lo_content 需确认语义与单位再迁移。
- Magmom_Function/io/__init__.py 引用旧 Process_VaspInput，且相对导入越界。
- Example/DFT/Dos_csv.py 使用旧 export_dos_to_csv 和固定服务器路径，优先使用新 DOS 配置模板。
- Ehull_test 与 Loss_Phase/Loss_hull 的同名训练实现未自动合并。
- 一些原函数缺少输入/返回说明，API.md 标注缺失，不凭函数名编造科学语义。
- Process_Vasp 中此前 tmp* 测试目录存在权限问题，本次索引忽略临时目录，不删除内容。

未对全部模型训练、MC 采样、FAISS、通道批量任务、GUI 和历史示例运行测试。执行前先用小样本检查环境、模型、单位、随机种子及收敛条件。

Process_Struct/examples/percolation_sites.py 在已有 ccnb 环境对 NaFeF3 单结构实运行：0.5 Å 探针下 3D 连通，34 个间隙记录、96 条有向周期连接、48 个瓶颈标记；核对标记 CIF 回读与完整连接 CSV。1.0 Å 下无贯通通道，核对空位点表与框架 CIF。没有验证全数据集、空迁移元素分支的 NET 格式或实际迁移能垒。

2026-10-08：新增 Process_Vasp.run_amset_crt 和配置入口，调用 AMSET CRT 后处理，导出 σ/τ 张量并按输入内容/参数恢复已完成结果。仅更新实现及静态索引；未运行测试、真实 AMSET 或 VASP。已有 atomate2 环境未发现 AMSET 安装，未安装依赖。有效质量仅记录独立 AMSET 命令，未封装。

2026-10-08：新增 AMSET 超算独立任务生成和 DOS 检查点读取，质量采用官方 effmass.py 的输运定义从同次 CRT 结果导出，并输出固定 τ 下迁移率及 μ/τ。仅生成任务并更新静态索引；未运行测试、真实 AMSET 或超算提交。服务器 AMSET 安装、CPU 分区、原 DOS 网格收敛尚未验证。

2026-10-08：Process_Vasp 新增统一已完成结果解析 get_completed_result、后续任务生成 generate_followup_task、公开 run_workflow 续跑入口；原运行器支持 previous_result 配置，仅执行需要的新阶段，AMSET 也复用统一解析入口。更新静态索引；未运行测试、VASP/AMSET 或集群提交。服务器源结果在执行时验证，生成时不访问超算。

2026-10-09：加入 continue_task + 单 JSON 统一任务生成；服务器解析完成阶段及参数变更，执行 suffix 并保持原接口。AMSET 缺 DOS 时须显式 allow_vasp 和合适提交资源。仅代码/索引更新，未运行测试或真实计算。

### 2026-10-15 MSD transport fitting

- Added independent fit_msd: inclusive ps window, free-intercept NumPy OLS per species/segment, three-dimensional and directional diffusion, Nernst–Einstein conductivity and selected-species sum. Explicit K/Å³/charge-number inputs, SI and conventional units, R²/intercepts/sample diagnostics, optional protected JSON.
- Both MD and standalone MSD examples expose TRANSPORT_FIT (default off). MD reuses chosen NVT target temperature and volume; checks fit duration/sample count before loading a model. Analysis does not infer convergence, uncertainties or ion cross-correlations.
- py1: 72 tests, OK, one existing full-MTK skip (ASE class unavailable). Existing py-mace: 72 tests, OK. Added seven tests for analytic slopes/intercepts, irregular sampling, units, charge/multispecies sums, segments, malformed data/output protection, zero/negative slopes, real EMT NVT integration and preflight rejection.
- No dependency/environment changes or MLIP weights loaded. Real-material long-time diffusion/conductivity and GPU execution remain unverified. Existing ExpCellFilter deprecation warning remains unrelated.

### 2026-10-15 Symmetrix optional MACE backend

- Added enable_symmetrix, symmetrix_use_kokkos and symmetrix_species to MACE factory/presets and standalone relaxation; CuEq/Symmetrix mutually exclusive. Existing model reports preserve the effective configuration.
- Uses official symmetrix.Symmetrix and extract_mace_data. Supports preconverted JSON without Torch/MACE import, or temporary .model conversion with dtype restoration and cleanup; no source checkpoint edits. Example/docs explain OMat head=None, element selection, build-selected Kokkos device and upstream architecture restrictions.
- py1: 77 tests, OK (one existing missing full-MTK skip). py-mace: 77 tests, OK. Five added contract tests cover conversion, JSON, invalid combinations, failures, and EMT-substituted pre-relax/NVT/NPT reuse.
- User confirmed Symmetrix installed on the supercomputer, not this Windows machine. No environment modifications. Real Symmetrix model conversion/inference, OMat E/F/stress consistency, Kokkos/GPU and speedup remain unverified locally.

### 2026-10-15 Independent supercomputer benchmark folders

- Eight task folders each contain a full editable run_md.py (paths/model/optional all pre-relax/NVT/MSD/optional transport), submit.sh and README. Default 5000-step NVT and automatic entire-trajectory MSD export; identical seed/settings, no pre-relax for input consistency.
- Slurm scripts derived from user-provided 北京超算GPU.sh, retaining v100m3/1 GPU/32 GB/2 tasks/CUDA 12.8; bash source activation, per-job logs, environment mapping mace_cueq / sevennet_flash / python. Submission not performed.
- Two tests loop over all eight scripts: pure previews plus short real ASE EMT NVT and MSD export with model-loader replacement; check acceleration flags, Symmetrix element selection, reports and submission environments/LF. Full py1 suite: 79 tests, OK, 1 existing MTK skip. No real model/GPU/Slurm validation; local bash executable unavailable for shell syntax execution.
- Delivered eight task directories and root README/collector to C:/Users/Esseco/Desktop/1/2 with hash verification. Earlier generated flat scripts preserved in legacy_scripts after confirming unchanged hashes. No environment changes.

### 2026-10-15 Minimal benchmark parameters

- Reduced the eight task scripts to essential configuration; FIRE full-cell pre-relaxation, 600 K/5000-step NVT, MACE/Symmetrix float32, trajectory/log intervals both 1. SevenNet/CHGNet retain native precision without unsupported dtype arguments. Other settings use library defaults.
- Updated desktop copies with hash verification; Slurm scripts unchanged. Targeted tests cover all eight scripts and short EMT FIRE->NVT->MSD runs, including every-step MSD frame count; 2 tests OK. Real model/GPU execution remains unverified.


### 2026-10-15 Two-structure benchmark tasks

- Eight desktop tasks sequentially process LCO.vasp and NVP.vasp, each FIRE full relaxation -> 600 K/5000-step NVT -> MSD, every-step output. Results isolated under results/LCO and results/NVP. Model paths preserved by AST comparison; PROJECT_ROOT completed from the supplied model directory. Submission scripts unchanged.
- Full py1 suite: 79 tests, OK (one existing MTK skip), including short real EMT FIRE/NVT/MSD for 8 models times 2 structures. Desktop script syntax and structure readability verified. Production model/GPU/scheduler execution remains unverified.


### 2026-10-16 Trajectory frame extraction

- Added export_traj_frames and editable examples/extract_frames.py. ASE-based integer/list/slice/all selection, zero-based and negative indices, VASP/CIF/XYZ/extxyz/traj output, default overwrite prevention and source protection. Per-frame cell and atom order preserved; no models or randomness.
- Six added tests cover geometry/order and varying cells, negative/sliced/all selection, momenta roundtrip, formats, invalid selection, collisions, absent cell and empty input. Full py1 suite: 85 tests, OK (one existing full-MTK skip). Fresh import confirmed no MLIP/Torch import. Updated static API catalog. No production model/GPU run needed for frame extraction.


### 2026-10-18 Process_MLIP organization

- Moved 16 root-level test modules into tests/ and grouped into 10 responsibility-based files. Shared temporary-directory/calculator/example fixtures now in tests/_support.py; no test-to-test TestCase imports. All original 95 test identities retained exactly once; added 4 API/architecture/shared-optimizer compatibility checks. tests/public_api.json snapshots all 14 public signatures/defaults.
- Extracted unchanged MD helpers into _md_support.py and consolidated public exports. MACE/SevenNet single-structure wrappers now share _relaxation.py and MLIPRelaxer; retained historical LBFGS/default step behavior, copied inputs, output fields and legacy Process_AL_MC imports. Pre-relax defaults remain distinct and unchanged.
- Fresh verification: py1 99 tests OK, 1 existing full-MTK skip; existing py-mace 99 tests OK. AST comparison confirms unchanged MD/helper function bodies. Old/new fixed/full-cell EMT single-structure reports numerically identical at rtol/atol 1e-12. Fresh package import remains model-free. Examples parsed without execution. No dependency/environment/model changes, real GPU/model accuracy or performance not retested.
- README/module call map/test commands refreshed; MLIP public API catalog excludes tests. Unrelated in-progress VASP source/document changes preserved. Historical validation commands above retain their original test module locations for provenance.

### 2026-10-16 OMat/Symmetrix temperature and duration scans

- Added six standalone task folders for (500/700/900 K, 30 ps) and (700 K, 10/30/50/70 ps), deduplicating 700 K/30 ps. Each uses both LCO/Li-MSD and NVP/Na-MSD, FIRE full pre-relaxation, float32 Symmetrix/Kokkos and explicit 2 fs NVT; steps derived from requested duration. Reused user-provided paths and Slurm resource/environment settings. Delivered new folders and README_sym_scan.md to Desktop/1/2 without changing existing tasks/structures.
- Two tests verify all six configurations and 12 short model-substituted relaxation/NVT/MSD pipelines, output isolation, species and time grids. Full py1 suite: 95 tests OK (1 existing MTK skip). No real model/GPU/Slurm execution or stability/convergence claim for production temperatures/durations.

### 2026-10-16 Ensemble-dependent MD timestep

- timestep_fs=None now resolves to NVT 2 fs or NPT 1 fs per stage. Explicit common/stage values override; explicit stage None restores its ensemble default. Resolved values drive integration, CSV/report times, cumulative stage offsets and MSD inference. Other damping/default parameters unchanged.
- Added four tests covering direct runs, invalid values, multi-stage overrides/offsets, exact MSD time grid and automatic timestep in example transport preflight. Full py1 suite: 93 tests OK (1 existing full-MTK skip); existing py-mace: 93 tests OK. Updated example, docs and catalog. No environment changes; 2 fs is the requested configurable default, not material-specific accuracy validation.

### 2026-10-16 Full-cell relaxation stability

- Replaced deprecated ExpCellFilter in MLIPRelaxer with FrechetCellFilter, default extensive cell scaling (atom count); no silent fallback. Added keyword-only maxstep/exp_cell_factor to MLIPRelaxer and validated pre_relax options. MD preparation now defaults to FIRE with maxstep=0.05 Å; direct MLIPRelaxer keeps its optimizer/default ASE step behavior when maxstep=None. Effective filter and scaling recorded in preparation reports.
- Four new tests cover filter/default step forwarding, overrides across FIRE/BFGS/LBFGS, invalid settings before model load, and a 108-atom EMT full-cell trajectory (finite geometry/bounded volume/reduced energy). Fresh full suite: py1 89 tests OK, 1 existing full-MTK skip; py-mace 89 tests OK. No dependencies or model environments changed; the original MH1/GPU divergence and OOM remain unverified without its relaxation trajectory and cluster runtime.
- During verification fixed an intervening frame-export default Path(Trajectory) that prevented package import. output_dir=None is resolved to the actual input trajectory parent at call time; regression assertion added. Updated static catalog, README and MD examples/docs.

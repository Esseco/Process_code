# 验证与已知问题

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

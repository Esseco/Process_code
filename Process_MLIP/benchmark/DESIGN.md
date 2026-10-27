# MLIP Benchmark 设计与执行计划

2026-10-27；按用户后续修正：只实现标准组成凸包，不实现固定骨架脱嵌路径。

目标：复用 Process_MLIP 的延迟模型加载、MLIPRelaxer 和 run_md，独立运行
Speed / Ehull。保留现有目录和公开接口，不创建大小写冲突的第二个项目。

输入：YAML 配置，显式结构 ID/文件/帧索引、模型 ID/类型/设备/参数。
输出：分阶段 CSV/JSON、弛豫结构、日志、速度曲线、标准组成相图和误差报告。
默认：LBFGS + FrechetCellFilter，fmax=0.1 eV/Å，steps=2000，maxstep=0.2 Å；
Nose–Hoover chain NVT，800 K，2 fs，1000 steps，seed=42。
MD 从输入结构独立副本开始；不承接模型各自的弛豫结果。
加载/首次能量力应力预热、弛豫和 MD 分别记录。MD 计时复用现有 run_md 的
积分运行计时，包含其一致的观察器/轨迹开销。GPU 仅支持同进程 PyTorch CUDA
计时与 allocator 峰值；外部 GPU NEP 不伪报为 torch 测量。

Ehull：整胞原子计数 + 整胞 eV 能量传入 pymatgen PhaseDiagram；输出 eV/atom。
必须提供所有元素端元；不生成、不下载竞争相。某模型任何输入结构失败或未收敛，
该模型不生成不完整凸包。稳定点以配置 tolerance_eV_per_atom 判断。
DFT 参考为 ID,ehull_eV_per_atom CSV，仅评估 ID 交集，报告缺失/多余 ID 和覆盖率。
无交集/重复 ID/非有限或负参考值明确报错。输入组成一致的不同结构保留为独立相。
结果只相对于用户给定的竞争相集合，不证明全局热力学稳定性。

## 执行任务

- [x] 1. config.py / registry.py / storage.py：严格配置、延迟加载注册表、
  输入与 checkpoint 内容哈希、原子写入、按阶段恢复、环境记录。
- [x] 2. operations.py / runner.py：共享弛豫与测量、独立 Speed 阶段及失败隔离。
- [x] 3. ehull.py / plotting.py：标准凸包、ID 参考匹配、稳定点比较和图表。
- [x] 4. runner.py / __main__.py / examples：CLI、多模型与跨环境模型选择、
  README、示例、端到端测试及静态索引更新。

接口：load_config(path)->dict；register_model(type, factory)；
run_benchmark(config_path, mode, model_ids=None)->dict。
核心只消费 ASE calculator，不依赖模型类型分支。

验证：py1 下 TemporaryDirectory 管理所有测试文件，以 EMT 的真实短程弛豫/MD
和解析构造的二元相图测试归一化、同组成多相、缺端元、非收敛保护、失败隔离、
恢复与输入/checkpoint 变化拒绝复用。原有 MLIP 测试做回归。
不安装模型依赖、不加载真实权重、不提交任务、不自动 Git 提交。
独立模型 GPU/真实材料精度留待提供 checkpoint 和相应环境后实测。

决策：依用户 AGENTS 偏好，主代理直接执行，不启用强制 worktree、逐任务提交
或独立代理审查；在已有未提交改动基础上仅添加本任务文件与索引必要更新。

## 执行记录

- 配置→注册表→共享操作→结果持久化接口核对完成；主代理实现并自行审查，无模型切换或子代理。
- Speed 编排直接放在 runner.py，未额外创建只做转发的 speed.py。
- 首轮发现 pymatgen 相图 JSON 含 numpy.intc，改用 MontyEncoder；解析与真实相图测试通过。
- py1：新增 21 项 + 复用接口针对性回归 29 项，共 50 项通过。
- 原有完整套件：153 项，9 项失败、1 项跳过。旧测试将 __pycache__ 当作示例任务，
  另有旧预弛豫测试与当前默认 LBFGS/全晶胞行为不一致；独立进程不导入 benchmark
  仍复现两项代表性失败。本任务未修改旧测试或预弛豫默认行为。
- 原有 2026-10-18 的 tmp_mlip_test_ty_bxm46 和 2026-10-24 的示例 __pycache__
  均非本次产物，保留原状。新测试使用 TemporaryDirectory 自动清理。

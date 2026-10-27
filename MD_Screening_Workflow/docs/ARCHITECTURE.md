# 直接运行与输出整理

run_md.py → runner.run_md → workflow.run_screening → Process_MD → Process_MLIP/ASE。
presets.screening_preset 默认 target_atoms=None：使用输入超胞，旧低层默认值保持兼容。
reporting.py 生成 UTC 流程日志、参数、导航与 results/summary.json、summary.csv；末结构和最新 MSD 为小型导出，连续轨迹不复制。原 prepared/relaxation/md/checks 路径保持稳定。
未解析的 D/σ 保持 None，区分粗筛通过、预算耗尽、结构异常和失败。
完整说明见项目 README；实现记录见 MD_ENTRY_PLAN.md。

# 职责与扩展入口

第一版只有一个执行入口 `run_screening`，没有调度器、任务数据库或 Agent。

| 文件 | 负责什么 | 修改时的边界 |
|---|---|---|
| `md_screening/config.py` | 默认预算、模型、物种、拟合窗口及整数步边界 | 单位清晰；边界必须对齐保存帧 |
| `md_screening/calculators.py` | 默认本地MACE-OMat委托 | 不下载、不回退；支持外部calculator |
| `md_screening/stopping.py` | >=10ps、MSD>3d²、R²>0.95的粗筛 | 一次合格可停；没有额外收敛门槛 |
| `md_screening/stability.py` | 可调MSD持续增长+RDF联合告警 | 不测熔点，不单凭MSD或结构变形判断融化 |
| `md_screening/review.py` | CheckReport 数据、Decision 动作和理由 | 不内置材料阈值；continue 也用于请求更长时间 |
| `md_screening/analysis.py` | 预检查/累计生产分析，区分数据不足与错误 | 复用 Process_MD；不实现科学算法 |
| `md_screening/workflow.py` | 结构准备、一次连续 MD、调用 reviewer、持久化 | 所有调整请求只停止并记录 |
| `examples/` | 可运行的短演示、真实模型调用入口 | 模型文件显式提供；不自动下载 |

依赖方向是 `workflow → Process_MD → Process_MLIP / ASE / pymatgen-diffusion`。基础库不反向 import 本仓库。模型和旧库在运行时加载，普通 import 不加载 torch。

## 时间与状态

默认初始检查 2500 步、生产检查间隔 5000 步、生产预算 100000 步；积分步长为2 fs，轨迹每10步保存一帧（20 fs/帧）。以两种间隔步数的最大公约数进行底层分块，只在预检查结束或生产整数检查点分析。

从未重建积分器，前5 ps仍是完整轨迹的一部分。框架分析使用当前5/10 ps检查窗口、前后最多各5帧RDF平均；生产MSD和跳跃从预检查边界帧开始累计。`time_ps`拟合数组是lag时间，热力学日志则是总模拟时间。

- 默认 reviewer 缺省：应用粗筛，达到条件为 `heuristic_ready`；stop_criteria=None恢复仅记录。预算结束为 `budget_exhausted`，不推断导率低或统计已充分。
- 调用方 reviewer 返回 accept：已有生产 D 估计才允许，停止并记为 `accepted`；科学依据属于调用方。
- 其他停止动作：`needs_review`，保留请求与理由；不执行扩胞/变温/模型更换。
- 默认联合结构告警：`framework_unstable`，优先于传输通过；record-only/custom reviewer仍保留诊断和选择权。
- 默认无跳跃+平台：生产>=10ps、可靠位点映射时请求raise_temperature并停止。部分跳跃或unknown继续至预算，不能把缺失空位映射当作零跳跃。
- 数据不足：写检查报告，允许继续采样。轨迹损坏、错误参数、缺少依赖、reviewer 异常：写 `failed` 后抛出，不吞异常。

用Process_MD的ASE函数求满位点参考中最近同种移动位点间距，记录为跳距代理及来源；手动hop_distance_A优先。这个几何尺度不识别迁移势垒或允许路径。kinisi不确定性默认不运行，显式启用时通过后仅算一次，不阻止粗筛通过；输出单独的后验中位数和区间。

## 后续按需要补

1. 骨架/材料审查仍可作为 `reviewer(CheckReport) -> Decision` 校准和接入；粗筛阈值已由用户指定，不擅自加严。
2. 跨进程 checkpoint/restart 先补进 Process_MLIP/Process_MD 并验证完整状态，再给 workflow 增加恢复入口。当前停止不代表以后可以严格恢复。
3. SOC 构型生成、任务批量化、不同温度运行和外推放在本仓库扩展，数值通用工具留在基础库。不提前增加空类。

## 首次验证（2026-10-21）

使用 py1：`python -B tools/verify.py --package`，42 项测试通过；两个本地包的 wheel 构建、临时安装和新包独立导入通过，安装后的 14 步 LJ 例程通过。所有验证临时目录已清理。

有界只读核对未发现重要问题。没有运行真实 MLIP 权重、GPU、800 K 长 MD，也没有验证任何材料的稳定/扩散/尺寸收敛阈值。

## 粗筛与不确定性增量验证（2026-10-21）

最终py1检查 `tools/verify.py --package`：75项测试通过；两个本地wheel构建、临时安装、独立导入和短LJ示例通过。停止阈值/首个合格检查点、PBC跳距、模型选择、记录模式、自定义reviewer、可选不确定性只调用一次及失败留档均有覆盖。

MACE-OMat默认加载器另在已有py-mace环境对8原子结构执行一次真实能量/力调用，输出有限，未跑真实材料长MD。基础库kinisi在临时隔离target中完成181帧×20原子随机游走的真实后验与NE单位验证；临时依赖清理，原环境未改变。具体版本/数值记录在Process_MD/docs/DEVELOPMENT.md。该验证不检查MCMC收敛，也不验证材料阈值。

## GEMDAT 与联合结构告警增量（2026-10-21）

用户选择生产10ps无有效跳跃+平台早停，总时间最早15ps；有跳跃不足继续至生产200ps。联合结构规则是暂定经验告警，不宣称检测到熔点。默认RDF每次最多10帧；kinisi仍默认关闭，显式启用仅通过后一次。完整参考位点使用输入晶胞并共享扩胞矩阵。

最终py1 `tools/verify.py --package`：117 passed、1因缺GEMDAT跳过；两库wheel构建、临时安装、独立导入和14步LJ例程通过。新增结构联合/松弛平台、10ps时钟、少量跳跃预算、映射unknown、缺依赖提前失败、参考晶胞/PBC、记录模式与自定义reviewer优先测试。

原生最小target中单独验证GEMDAT→pymatgen MSD/WLS→TransportStopper真实接线：1 passed；原生跳跃另有11项通过，全部临时依赖/轨迹清理。一次只读审查发现“结构告警无条件跳过记录/自定义模式传输”的问题，已限定短路仅默认自动审查并补3项回归。没有再次审查循环；最终全套重新通过。

py1未永久安装GEMDAT/kinisi，依赖安装按README在兼容环境进行。没有真实材料长MD、GPU、阈值校准、MCMC收敛或严格restart验证。

## 兼容运行环境与真实短测（2026-10-22）

专用`.venv`已经安装完整GEMDAT/kinisi依赖，只读借用py-mace模型栈，py1和py-mace原安装清单未变。新环境两项目共367项测试通过（基础库246、workflow121），含原生GEMDAT和kinisi；wheel、临时安装及示例通过。基底原有无关可选包告警保留，未为消除告警而升级MACE所需e3nn。

`framework_rdf_repeat=(2,2,2)`仅扩展RDF快照周期像，用于小晶胞诊断，不改变MD规模。`examples/mace_smoke.py`使用8原子LiF、本地MACE-OMat、800 K、CPU，完成1.9 ps/1900步，四次结构/跳跃检查正常。0次有效跳跃且MSD平台判据未通过，所以继续到测试预算结束，结果为budget_exhausted。测试压缩时长仅用于接线验证，不改变正式默认参数。

保留一份实际短轨迹与检查报告；结果及限制见[短测记录](../environment/SMOKE_RESULT.md)，环境与重建方法见[环境说明](../environment/README.md)。无跳跃平台早停和结构失稳拒绝由原生合成轨迹/回归测试覆盖，本次不声称观察到真实扩散或熔化。

## 运行参数与结束摘要（2026-10-22）

`examples/run_case.py`通过`--temperature-K`和`--max-production-ps`转发已有配置，默认800 K、生产200 ps。上限不包含5 ps初检，且须对齐10 ps检查周期；温度为该次NVT目标值。终端输出最后一次检查的MSD、D、σ_NE、R²、状态和文件路径，继续复用已有检查JSON、MSD CSV及summary.csv，不重复计算。未解析数值保持None/null。

py1验证129 passed、1项原生GEMDAT因缺依赖跳过；覆盖CLI参数传递、估计/数据不足摘要，以及现有workflow的温度、时长和D/σ/MSD持久化。验证临时目录清理，本次未追加真实MD。

## 强制满位点参考（2026-10-22）

当前workflow API、run_md.py和run_case.py统一要求满位点参考结构。缺失时在创建结果目录前拒绝；GEMDAT分析调用显式参考，不再使用首帧占据位置。参考和当前SOC共用扩胞矩阵；检查PBC、晶胞和移动位点数。参考的最近邻距离以reference_nearest_neighbor_A保存，默认用于3d²阈值；实际MD、骨架诊断及NE导率粒子数仍来自当前SOC。调用方负责参考完整性和坐标原点对齐。

简洁调用为`python run_md.py POSCAR_SOC POSCAR_FULL`；满位点态本身可以把同一文件传两次。原始短测记录保持历史输入与参数，不改写旧结果。

# 独立 TM ordering 搜索

业务入口在本库，Agent 只封装配置、审批、输入准备与结果回收。与旧 `LayeredOxide_MCOrderingClass` 接口独立，旧调用仍可使用。

```python
from Process_AL_MC import plan_ordering_search, prepare_ordering_search, run_ordering_search

plan = plan_ordering_search(
    reference="/data/P2_full_Na_reference.vasp",
    phase="P2", tm_ratios={"Ni": 1, "Mn": 1}, na_content="2/3",
    max_det_H=12,
    model={"version": "main-v1", "model_path": "/models/main.model", "device": "cuda"},
    options={"workers": 3, "chains_per_H": 3, "seed": 42, "top_k": 5},
)
prepared = prepare_ordering_search(plan, "/data/search_P2_NiMn")
# 以下调用才加载模型并计算；在已确认的 MACE 环境中显式运行。
result = run_ordering_search(prepared["directory"])
```

`reference` 必须是有序、满 Na 的 NaTMO2 位点模板；目标 Na 可以为 0–1 的有理数，建议传字符串。TM 元素和比例任意配置。原子数无法满足整数组分的 H 会跳过。默认氧化态由 pymatgen 推断，可用 `oxidation_states={...}` 明确传入，各候选必须电中性。相与母结构由调用者选择。

范围参数二选一：`max_det_H=N` 枚举 det(H)≤N 的面内超胞；`h_matrices=[[a,b],[c,d]]` 只搜索该 H，也接受一个 3×3 矩阵或矩阵列表。每个精确 H 独立记录和排名，绝不按相同倍数合并。`min_distance` 默认 2 Å，要求最短周期矢量的一半达到此值；需要保留小超胞时显式调整。

准备阶段仅进行 H 枚举和有限 Ewald 初始化，不加载 MLIP、不提交作业。每个 H 从低静电能及少量多样性候选选默认 3 条链。若自动猜测给各 TM 相同电荷，Ewald 不区分这些 TM 排布；计划会记录这一点。

本地模型在计划时自动 SHA256；不可访问的远端模型必须提供 `sha256`，委员会模型通过 `model_checksums={路径:哈希}` 提供。执行前重新校验。`model_path` 始终为排序主模型，委员会只提供附加不确定性。参数、结构和模型共同绑定计划与历史。

满 Na 默认 `tm_only`，部分 Na 默认 `na_tm`。后者以默认 50% 概率交换 Na/空位或不同 TM，组分不变。排名按每个 H 的 TM 位点编码分组，保留搜索中观测到能量最低的 Na 伴随排布；这是有限搜索结果，不能宣称全局基态。计算去重使用联合 Na+TM 位点编码，在 SQLite 事务中先认领再计算，多条链共享历史；不使用 StructureMatcher。

所有参数在 `options` 中配置：`max_steps=1000`、`max_duplicate_trials=100`、`max_restarts=2`、`patience=10`、`energy_tol=0.001` eV/atom、`temperature=300` K、`fmax=0.05` eV/Å、`relax_steps=150`、`relax_cell=True`、`initial_pool_size=128`、`initial_exploration_fraction=0.1`。重复候选不调用 MLIP；达到连续重复上限会重新初始化，达到重启上限停止。每链包含初始化在内最多 `max_steps+1` 次 MLIP 评估，重启不重置此预算。Metropolis 使用总能差（每原子能差乘原子数）。每个并行工作线程独立加载模型，按 GPU 内存配置 `workers`。固定 seed 不保证 GPU 浮点完全确定性。

仅优化器报告收敛、最终力达标且氧配位层序识别为目标相的结果进入排名。相识别是保守几何检查，歧义结果归诊断；不支持的相标签也归诊断。显式 c 重复矩阵调整层数；混合 c 轴矩阵无法确定层序时不进入排名。

产物：`global_ranking.csv`、`matrices/<matrix_id>/ranking.csv`、对应 `top_structures.json`、全部联合候选 `all_joint_records.csv`、`diagnostics.csv`、POSCAR、位点编码、链停止原因与运行清单。能量为 eV/atom。结构路径相对结果目录，可将完整目录搬回本地；用 `inspect_ordering_search(directory)` 校验并读取。输入只写新目录或复用同一计划，拒绝覆盖其他计划。

中断后的历史可复用，但不保证随机链精确续跑；残留运行中记录不会超时自动重算。确认外部计算已结束后用 `reconcile_ordering_search` 显式登记证据并恢复待计算状态，已花费预算保留。此接口签名见 API.md。模型和输出目录不同时运行两个协调器。

CLI：`python -m Process_AL_MC.ordering request.json --output OUTPUT_DIR --prepare` 准备；显式 `--run` 执行。request 包含上例参数，`reference` 为路径。导入模块和计划不启动模型。

验证使用 py1、注入假评估器与合成结构，覆盖并发认领、组分、H、Ewald、模型绑定、排名、回收及审批边界；真实 MACE/GPU/HPC 计算未运行。

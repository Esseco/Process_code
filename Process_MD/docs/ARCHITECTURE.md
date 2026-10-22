# 架构与复用关系

## 定位

Process_MD 是供其他项目 import 的基础库。优先复用用户已有 Process_MLIP 与 ASE/pymatgen 的功能，不建立新的 MD/分析算法栈。调用方负责选择温度、时长、超胞和任务顺序。

## 目录职责

```text
Process_MD/
├── AGENTS.md                 # 给 Codex 的简短导航与约束
├── README.md                 # 给使用者的能力说明与 API 示例
├── pyproject.toml            # 安装与依赖
├── docs/
│   ├── ARCHITECTURE.md       # 本文：边界、复用、设计取舍
│   └── DEVELOPMENT.md        # 进度、后续任务、验证记录
├── examples/
│   ├── prepare_structure.py  # 结构/参数/结果保存；无模型
│   └── short_md.py           # 通过旧库运行极短 ASE LJ MD
├── tools/verify.py           # 临时目录内测试与可选打包验证
├── tests/
│   ├── conftest.py           # 最小合成结构夹具
│   ├── unit/                # 独立工具和接口边界
│   └── integration/         # 与旧库的真实调用验证
└── process_md/
    ├── __init__.py           # 稳定的顶层导出
    ├── models.py             # 参数/结果 dataclass，单位写入字段名
    ├── structure.py          # ASE 读结构、扩胞和索引映射
    ├── state.py              # SOC/组成记录与匹配参考下的占位比例
    ├── md/
    │   ├── calculators.py    # 调用旧模型工厂
    │   └── runner.py         # 调用旧 run_md；参数与结果适配
    ├── analysis/
    │   ├── trajectory.py     # 轨迹检查与现成坐标重建
    │   ├── diffusion.py      # MSD/D/sigma_NE 结果适配
    │   ├── framework.py      # 骨架 MSD/RDF/配位数值
    │   ├── jumps.py          # GEMDAT位点/驻留事件与映射质量，不做决策
    │   ├── uncertainty.py    # 可选kinisi原生后验与NE单位适配
    │   └── diagnostics.py    # 尺寸/时间/温度统计与比较
    └── io/results.py         # JSON/CSV，输出保护
```

`__init__.py` 只组织导出，不加载模型或旧库；`md`、`analysis`、`io` 各自公开少量函数。不设置 backend 注册器、抽象基类或工作流层。

## 已接通的复用映射

| Process_MD API | 实际实现 | 本库增加的职责 |
|---|---|---|
| `prepare_structure` | ASE read / make_supercell / find_optimal_cell_shape | 参数检查、输入副本、原始索引映射 |
| `create_chgnet_calculator` | Process_MLIP.calculators.create_chgnet_calculator | 延迟调用；显式 CPU 默认值 |
| `MDRunner.run` | Process_MLIP.md.run_md | ps → 整数步、平衡/生产两段、结果 dataclass、总结果记录 |
| `export_msd` | Process_MLIP.msd.export_msd | 保留原接口与返回数据，不复制算法 |
| `fit_msd` | Process_MLIP.transport.fit_msd | 保留原接口、拟合与诊断 |
| `calculate_msd/fit_diffusion` | 上述旧入口 | 临时文件适配为 dataclass，标记 NE 与未评估的不确定度 |
| `read_positions` | ASE / pymatgen Trajectory | 固定晶胞与输入检查，wrapped 重建使用原生工具 |
| `validate_framework` | ASE RDF / neighbor_list | 去骨架平移的位移指标和初末比较，不判决崩塌 |
| `analyze_jumps` | GEMDAT原生轨迹/Transitions/Jumps | 均匀采样/PBC核对、位点覆盖与事件单位适配，不判低导率 |
| `analyze_diffusion_uncertainty` | kinisi原生ASE/Bayesian | 后验区间/NE单位适配，不自写统计推断 |
| `diffusion_from_slope` | Einstein 关系的简单单位换算 | 指定维度，输出 cm²/s，不判定扩散可信性 |
| `save_json/save_csv/save_results` | 标准库 + dataclass/NumPy 序列化 | 默认拒绝覆盖，先校验和编码再写文件 |

旧源码位于本机 `E:/Py-Code/Process_MLIP`，这是核对记录而非代码中的配置。py1 已可直接导入该包；其他环境需通过现有仓库导入方式或 PYTHONPATH 提供它。核心结构/数据/序列化工具可在没有旧库时独立调用。旧库目前没有独立安装元数据，因此不虚构一个 PyPI 依赖名称。

## 数据与科学语义

- 结构使用 `ase.Atoms`，不包装另一套原子对象。输入被复制；元素、cell、PBC、arrays 和 info 保留，calculator 不转移。
- 目标原子数是下限：按完整输入晶胞数向上取整。自动近立方扩胞要求 3D PBC；部分 PBC 用显式矩阵，禁止周期/非周期向量混合。
- `process_md_source_index` 是原始输入索引，扩胞后重复正常；当前索引仍是 ASE 下标。
- 单位：时间 ps/fs，长度 Å，MSD Å²，D cm²/s。`duration_ps` 只指生产段，必须对应整数步。
- MD 使用旧 NHC NVT。同一 calculator 先平衡后生产，动量连续，温控器状态在阶段间重建；输出轨迹分开。默认 seed=42，步长=2 fs，每10步保存一帧（20 fs/帧）。
- `MDResult.steps_completed` 是生产步数；失败时为 None，阶段 report.json 保存后端能提供的进度。异常记录后继续抛出。
- 已有 `export_msd` 用 pymatgen 多起点平均；原 MD 保存连续坐标，因此默认 `unwrap=False`。原 `unwrap=True` 分支仍是 ASE MIC，本库不复制这段逻辑。
- 结构化 wrapped 入口通过 pymatgen Trajectory.to_displacements/to_positions 重建连续坐标，再复用旧 MSD。unwrapped 输入不二次解包。包装层负责固定晶胞、3D PBC、采样、原子顺序、单位与结果适配。
- `fit_msd` 沿用旧 pymatgen 拟合，返回斜率下限、low_msd 等诊断；不把原始正 D 或高 R² 当作可信扩散证据。拟合线性不证明超胞尺寸收敛。

## 当前边界

结构化分析和骨架数值已接通；严格 `resume` 仍抛出 NotImplementedError。审查阈值/动作、通用 SOC 构型生成、相关修正导率与多温度外推后续实现。详细模块与审查证据见 [MODULES.md](MODULES.md)。

原 run_md 的分段扩展保持同一个积分器，只提供块回调与调用方请求停止的原语，无内置筛选规则。分段与单次推进的状态一致已做测试。

原库没有完整 checkpoint。`checkpoint_interval` 必须为 None，设置正值会在开始前报错。后续须在原库保存积分器/温控器、位置/晶胞/动量、随机状态、步数和模型/版本，再用连续与分段恢复测试证明正确。`final.traj` 不作为严格 restart 回退。

## 现成工具核对

py1 中 ASE 3.25.0、CHGNet 0.4.0、pymatgen-analysis-diffusion 2024.7.15 可导入。已核对原生 pymatgen 三帧 wrapped 跨界探针：Li x 位移为 [0,2,4] Å，MSD 为 [0,4,16] Å²；这不代表新的结构化分析 API 已完成。模型权重推理未验证。

- [ASE 超胞工具](https://docs.ase-lib.org/_modules/ase/build/supercells.html)
- [pymatgen-diffusion 实现](https://materialsvirtuallab.github.io/pymatgen-analysis-diffusion/_modules/pymatgen/analysis/diffusion/analyzer.html)
- [CHGNet API](https://chgnet.lbl.gov/api)

# 模块、审查证据与后续扩展

## 边界

本库只提供模块；外部 MD_Screening_Workflow 已建立并调用本库。当前外部筛选配置为：实际 SOC 构型至少 200 原子、800 K、先观察 5 ps、之后每 10 ps 分析、生产时长最多 200 ps。它们不写死在模块里，也不是物理有效性的充分条件。

模块返回数据与诊断，不返回“必须扩胞/延时/升降温”的自动动作。外部workflow已加入用户指定的10ps/3d²/R²粗筛，后续的骨架判据、排序和任务调度仍由外部实现。

## 当前 API

| 需求 | API / 所在文件 | 返回的证据 | 不据此直接作出的判断 |
|---|---|---|---|
| SOC/组成记录 | describe_alkali_state / state.py | 实际离子数、匹配参考下占位/脱出比例、构型编号 | 通用 SOC 定义、最佳空位排序 |
| 扩胞与几何 | prepare_structure；describe_cell | 原子数、整数矩阵、晶胞向量/垂直高度、原始索引 | 单个尺寸已经收敛 |
| 跳距近似 | estimate_hop_distance | ASE含周期像的最近同种移动离子间距，Å | 缺失位点/允许迁移路径/势垒 |
| 跳跃事件 | analyze_jumps；check_jump_backend | GEMDAT驻留过滤、事件、位点覆盖与unknown诊断 | 零跳跃不是低导率证明；不自动识别缺失空位 |
| NVT/分段推进 | MDRunner.run / md/runner.py | 原子状态连续、生产步数、时间、已刷新的输出与回调 | 何时停止、升温或扩大 |
| 固定晶胞轨迹 | read_positions / analysis/trajectory.py | 连续坐标、输入/PBC/元素顺序检查 | 稀疏 wrapped 帧能否恢复多次穿胞 |
| MSD | calculate_msd / analysis/diffusion.py | 多起点 MSD、xyz 分量、原子数、帧数、观测时长 | 斜率线性已经进入长程扩散 |
| D 与导率 | fit_diffusion | 原窗口的 D_self、sigma_NE、R²、斜率及下限诊断 | 相关修正导率、统计/尺寸收敛 |
| 不确定性 | analyze_diffusion_uncertainty；check_uncertainty_backend | kinisi后验中位数/可信区间、sigma_NE区间、实际窗口与诊断 | 不含模型/尺寸误差，不把区间当作WLS误差条 |
| 骨架检查 | validate_framework / analysis/framework.py | 去平移 MSD 曲线、初末 RDF、显式 cutoff 的配位变化 | 仅凭单一数值判断崩塌/降温 |
| 温度运行状态 | summarize_md_log / analysis/diagnostics.py | 温度/能量/压力等已有日志列的均值、标准差、极值 | 一定要升温或降温 |
| 尺寸/时间/温度比较 | compare_transport | 两次估计的相对变化、缺失/未评估状态 | 自动通过、自动扩胞或停止 |
| 标准结果 | save_results / io/results.py | 参数、数值、路径、错误和诊断 | 把计算正常结束当作科学可信 |

## 分段 MD 的具体语义

原 Process_MLIP.run_md 现支持 segment_steps/on_segment；同一个 atoms/calculator/dyn 一直推进。Process_MD 使用 segment_ps 换算整数步。段长及生产终点须与轨迹输出间隔对齐，回调读取的是已同步轨迹和已刷新的日志；避免短尾帧被错误标记成均匀采样。

```python
result = runner.run(
    atoms, temperature_K=800, duration_ps=200,
    segment_ps=10, on_segment=inspect_segment,
    trajectory_interval=10, output_dir="run_001",
)
```

这是通用调用示意，不包含 inspect_segment 的审查实现。回调返回 None/False 继续，True 请求正常停止；此时 status='stopped'，steps_completed 为实际生产步数。段间不会重建积分器；平衡与生产阶段之间仍沿用旧库的温控器重建语义。

这与严格 checkpoint/resume 是不同能力。跨进程恢复仍未实现，仍拒绝把轨迹末帧当成严格 restart。

## 分析调用

```python
msd = calculate_msd(
    md_result.trajectory, species="Li", frame_interval_ps=0.01,
    axes="xyz", coordinate_mode="unwrapped",
)
transport = fit_diffusion(
    msd, fit_start_ps=10, fit_end_ps=40,
    temperature_K=800, volume_A3=msd.volume_A3, ion_charge=1,
)
framework = validate_framework(md_result.trajectory, mobile_species=("Li",))
runtime = summarize_md_log(md_result.trajectory.with_name("md.csv"))
```

frame_interval_ps 必须是实际均匀保存间隔，不是积分步长；默认 2 fs 每 10 步保存为 0.02 ps。短尾末帧/变步长不能假装均匀；调用方须按实际数据选择或使用旧入口的 report 时间检查。

原 MD 已保存连续坐标，默认不再解包；wrapped 输入调用 pymatgen Trajectory 的现成重建，再交给旧 export_msd 的 pymatgen 多起点算法。连续轨迹文件路径可以避免再写一份完整轨迹；内存或 wrapped 输入需要一次临时格式适配，结束即清理。

拟合继续使用 Process_MLIP.fit_msd，不重写 WLS。fit_diffusion 返回的 sigma_NE 单位为 S/cm；D 是 cm²/s。零/负斜率或上游斜率下限会得到 None，不保留人为的小正值。正斜率仍只是估计，uncertainty_status='not_evaluated'；R² 和多起点数量都不等于有效独立样本数。

## 三类审查将使用哪些证据

1. **尺寸不足**：至少需要受控尺寸比较，并保留晶胞基矢/整数矩阵和扩散方向。Cartesian x/y/z 分量不自动对应 a/b/c 扩胞方向。200 原子是成本起点，不是收敛证明。
2. **低扩散，考虑高温补充**：当前温度下未解析的扩散、模型/结构状态和高温相是否适用。高温数据不能直接等同于室温导率。
3. **统计不足，考虑延时**：实际观测时长、移动离子数、拟合窗口/累计结果变化、GEMDAT跳跃/覆盖率，以及可选kinisi后验区间。到200 ps未解析时，记录观测条件和未解析状态，不直接写D=0。

结构异常或模型问题作为单独诊断来源；瞬时热畸变、真实相变、固定体积不合适、步长问题和 MLIP 误差不能由一个骨架 MSD 阈值区分。诊断模块提供数据，后续审查再组合。

## 导率与外推

本轮沿用原库 Nernst–Einstein：sigma_NE = N q² D_self/(V k_B T)。N、V、T 使用当前 SOC 构型和实际模拟条件。sigma_NE 不默认包含离子间相关性。pymatgen-diffusion 已有集体电荷位移与相关导率能力，后续可以适配，不需要自行推导新的算法；需要另行报告方法和统计质量。[官方实现](https://materialsvirtuallab.github.io/pymatgen-analysis-diffusion/_modules/pymatgen/analysis/diffusion/analyzer.html)

多温度外推暂未实现。现有结果保留 T、V、离子数、组成标识和观测/拟合窗口，后续应按同一材料/SOC/构型/模型/相分组，复用成熟 Arrhenius 工具。单温度 800 K 不能提供受验证的室温外推。

统计不确定度受模拟时长、体系尺寸、缺陷/移动离子数量及估计方法影响，不能由 R² 单独决定。[Usler 等，J. Comput. Chem. 2023](https://doi.org/10.1002/jcc.27090)

# 通用模块补齐计划

目标：为后续低成本筛选 workflow 提供可独立调用的计算模块，不实现自动审查、升温、扩胞、停止判据或任务调度。

用户给定的后续初始策略是：按实际 SOC 结构扩胞到至少 200 原子，800 K，先检查 5–10 ps，再每 10 ps 分析，生产上限 200 ps。这些是外部 workflow 配置，不作为本库的物理收敛判据或算法默认值。

## 本轮模块与接口

1. `state.py`：`describe_alkali_state(atoms, mobile_species, reference_mobile_atoms=None, configuration_id=None)` 返回组成计数、占位/脱出比例和构型标识。不假定 SOC 的正反定义，不生成空位构型。
2. `analysis/trajectory.py`：`read_positions(trajectory, coordinate_mode='unwrapped') -> (first_atoms, positions_A)`。检查固定晶胞、3D PBC、原子顺序和有限数值。wrapped 输入交给 pymatgen Trajectory 的 to_displacements/to_positions，禁止自写 unwrap。
3. `analysis/diffusion.py`：接通结构化 calculate_msd 与 fit_diffusion；继续调用已有 export_msd/fit_msd，返回明确的 D_self 与 sigma_NE、拟合窗口和诊断。临时 CSV 只作为旧接口适配，不留下临时路径。
4. `analysis/framework.py`：接通骨架 MSD 曲线、ASE 初末 RDF、显式 cutoff 下配位变化；返回数值，不返回“稳定/崩塌”判决。
5. MD 分段能力：在已有 Process_MLIP.run_md 增加可选分块回调，保持同一个积分器；Process_MD 只适配时间与事件。保持旧调用兼容。严格跨进程 checkpoint/resume 单独留待后续。

## 数据约定

- 总 MSD 是所选 Cartesian 分量之和；D 的维度因子与 axes 对应。
- sigma_NE 是 Nernst–Einstein 估计，S/cm；不是默认包含相关修正的实验导率。没有拟合分辨能力时 D/sigma 可为 None；未实现统计误差时明确标注未评估。
- RDF/CN 只是诊断；热展宽、参考温度与 cutoff 会影响数值。
- 块回调只是计算原语，不内置阈值或审查类别。

## 验证

最小合成数据验证：wrapped/unwrapped 与斜晶胞、方向投影、D/NE 单位、零斜率诊断、SOC 计数、静态/平移/局部畸变骨架、连续/分块 MD 数值一致、回调停止及旧入口兼容。使用 py1，临时目录全部清理。真实 MLIP、200 原子/200 ps 运行及筛选有效性不在本轮测试范围。

## 进度

- [x] 组成状态和轨迹数据适配
- [x] 结构化 MSD/D/sigma_NE
- [x] 骨架诊断
- [x] 连续分段 MD 原语
- [x] 测试、打包与模块文档更新

最终验证：py1 下 154 项测试通过；wheel 构建、临时安装、导入与示例通过。旧库相关 29 项测试运行完毕，28 通过，1 项因 ASE 无 full MTKNPT 跳过。无真实模型/长 MD 测试，不声明筛选有效性或统计收敛。

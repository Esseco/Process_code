# 功能边界与迁移候选

Process_Vasp 按功能分目录；其他项目的功能边界与科学语义保持原有约定。

| 功能 | 当前归属 | 后续建议 |
|---|---|---|
| VASP 输入、INCAR、工作流 | inputs/generation.py / inputs/incar.py / workflows/atomate_runner.py | 保留 |
| 输出、DOS、IPR、激发态输入 | results/reader.py / results/dos.py / inputs/excitation.py / results/status.py | 保留 |
| 通用结构去重、去离子、结构变换 | structures/structure.py | 结构变换保持原接口；去重复用 Process_Struct |
| 磁矩 OUTCAR 读取 | results/magnetism.py | 旧 Process_Vasp.magnetism 导入兼容 |
| 磁矩判断与特定体系约束 | Magmom_Function | 与通用读取分离，保持体系参数显式 |
| CHGNet 训练 JSON | Process_Chgnet | 保留在数据转换项目，不并入 VASP 输入层 |

read_vasp_output 的 corrected_energy_per_atom 使用硬编码 GGA+U 参数和 MP 校正规则，不能视为任意方法的普适修正；原始 vasp_energy_per_atom 更适合需要自行确定校正方法的任务。

read_vasp_status 的 finished 依赖 out 日志格式，与 atomate_runner 的严格输出校验是两个入口，不将它替代续算收敛判断。

## 通用去重合并已完成

实现统一到 Process_Struct/deduplication.py；Process_Vasp 保留同名兼容入口，层状氧化物与表面直接复用公共实现。deduplicate 保留首次出现的结构副本，deduplicate_dict 跨所有键去重并省略空组，deduplicate_df 按能量升序保留指定数量；采用默认 StructureMatcher，可能匹配平移/缩放及等价晶胞，不能理解为逐坐标完全相等。

列表模板：[deduplicate_structures.py](../../Process_Struct/examples/deduplicate_structures.py)。DataFrame 原接口使用标签索引，建议输入索引唯一；n_keep 使用正整数。本轮保留这些旧行为，没有改匹配容差或能量基准。

# 合并候选与职责

- LOSlabProcessor、SurfaceFixer、表面配置保留本项目，分别承担生成、约束、配置处理。
- 表面配置依赖的通用去重/无序枚举后续与 Process_Struct 对比，迁移时保留兼容导出。
- Example/Surface 的有效调用逐项迁成此处独立模板；旧固定路径脚本本轮不移动。
- 固定层与 Process_MLIP 不能直接合并：约束生成属于结构前处理，弛豫项目接收已经带约束的 Atoms。
- 对称匹配与 Process_Struct.wyckoff 可共享对称工具，但上下表面配对与 Wyckoff 分组输出不同，不能直接互换。

本轮仅修复旧导入、完善说明和模板，不改变表面算法。

## 通用去重合并已完成

实现统一到 Process_Struct/deduplication.py；Process_Vasp 保留同名兼容入口，层状氧化物与表面直接复用公共实现。deduplicate 保留首次出现的结构副本，deduplicate_dict 跨所有键去重并省略空组，deduplicate_df 按能量升序保留指定数量；采用默认 StructureMatcher，可能匹配平移/缩放及等价晶胞，不能理解为逐坐标完全相等。

列表模板：[deduplicate_structures.py](../Process_Struct/examples/deduplicate_structures.py)。DataFrame 原接口使用标签索引，建议输入索引唯一；n_keep 使用正整数。本轮保留这些旧行为，没有改匹配容差或能量基准。

# 功能合并与拆分建议

| 当前功能 | 建议 | 状态 |
|---|---|---|
| Process_Vasp.structure 的 deduplicate/deduplicate_dict/deduplicate_df | 通用匹配去重迁入 Process_Struct，VASP 保留兼容导出 | 候选，未移动 |
| Na1_to_Nax、层序变换 | 比较 Process_LayeredOxide 的现有实现，体系相关逻辑归入该项目 | 候选，未合并 |
| Get_Oct_distortion 与 Get_structfeatures_all 的八面体逻辑 | 比较配体、周期边界、指标定义及缺失值，再抽公共内核 | 候选，不能因名称相近直接合并 |
| 理论计量容量与 Chemical_Capacity_Constraints | 保留两个入口，前者计量公式，后者化学约束估计 | 不直接合并 |
| percolation 与 channel_codes_optimized | 保留通用分析函数，批处理项目将来复用它；先比较输出和探针定义 | 待核对 |
| octadist | 保持第三方独立，仅调用其科学计算接口 | 保留 |

本轮只处理 Process_Struct 的说明与功能模板，不改变科学实现或其他项目接口。

## 通用去重合并已完成

实现统一到 Process_Struct/deduplication.py；Process_Vasp 保留同名兼容入口，层状氧化物与表面直接复用公共实现。deduplicate 保留首次出现的结构副本，deduplicate_dict 跨所有键去重并省略空组，deduplicate_df 按能量升序保留指定数量；采用默认 StructureMatcher，可能匹配平移/缩放及等价晶胞，不能理解为逐坐标完全相等。

列表模板：[deduplicate_structures.py](examples/deduplicate_structures.py)。DataFrame 原接口使用标签索引，建议输入索引唯一；n_keep 使用正整数。本轮保留这些旧行为，没有改匹配容差或能量基准。

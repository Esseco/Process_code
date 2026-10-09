# 合并候选与保留边界

| 功能 | 建议 | 理由 |
|---|---|---|
| group_by_z 与其他层聚类 | 先比较周期边界、分数/笛卡尔坐标和容差，再抽层聚类公共工具 | 同名不代表相同几何定义 |
| Get_features 与 Process_Struct 特征 | 通用键长/配位内核可复用；层序、Na/TM、氧层指标保留此处 | 体系假设不同 |
| VASP.structure 的 Na1_to_Nax | 比较脱钠、价态及无序处理后迁入层状体系工具 | 保留原导出兼容 |
| 形成能与 Process_Struct.Cal_eform | 统一输入单位约定后比较，不直接拼接 | 参考能与归一化不同 |
| 通用去重 | 后续由 Process_Struct 提供 | 当前 LO_O3TransClass 依赖 Process_Vasp.deduplicate，暂保留 |

本轮补说明和模板，未修复或更改旧相图算法。parse_composition、两点/共线凸包和部分层特征假设作为后续独立修复项。

## 通用去重合并已完成

实现统一到 Process_Struct/deduplication.py；Process_Vasp 保留同名兼容入口，层状氧化物与表面直接复用公共实现。deduplicate 保留首次出现的结构副本，deduplicate_dict 跨所有键去重并省略空组，deduplicate_df 按能量升序保留指定数量；采用默认 StructureMatcher，可能匹配平移/缩放及等价晶胞，不能理解为逐坐标完全相等。

列表模板：[deduplicate_structures.py](../Process_Struct/examples/deduplicate_structures.py)。DataFrame 原接口使用标签索引，建议输入索引唯一；n_keep 使用正整数。本轮保留这些旧行为，没有改匹配容差或能量基准。

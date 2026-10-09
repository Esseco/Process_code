# Process_Struct

<!-- Manual project documentation -->

结构分析工具，采用延迟导入；单独使用某项功能不要求安装所有可选依赖。默认 py1，通道分析使用已有 CCNB/CAVD 环境。

## 按功能选择

| 功能 | 公开入口 | 输入 → 输出 | 独立模板 |
|---|---|---|---|
| 理论容量 | theoretical_specific_capacity | 化学式、迁移离子 → mAh/g | [capacity.py](examples/capacity.py) |
| Wyckoff 分组 | get_wyckoff_sites | Structure、容差 → 分组列表 | [wyckoff_sites.py](examples/wyckoff_sites.py) |
| 八面体畸变 | analyze_octahedra_distortion / Octahedron | 有序氧化物结构 → 局域畸变记录 | [octahedra.py](examples/octahedra.py) |
| 结构特征 | StructureFeatureExtractor | Na/O 层状结构 → global/local 字典 | [structure_features.py](examples/structure_features.py) |
| 几何通道连通 | analyze_percolation | 结构、迁移元素、探针半径 → 通道结果 | [percolation.py](examples/percolation.py) |
| 通道位点导出示例 | analyze_percolation + 示例导出 | 结构、迁移元素、探针半径 → 标记 CIF、间隙与瓶颈 CSV | [percolation_sites.py](examples/percolation_sites.py) |
| 化学容量约束 | estimate_redox_capacity / estimate_mobile_ion_window | 化学组成及约束 → 容量与离子窗口 | [子项目说明](Chemical_Capacity_Constraints/README.md) |
| CCNB 位点容量 | estimate_spatial_capacity | 结构、离子、空隙半径、位点间距 → 可行位点数与 mAh/g | [位点容量说明](SPATIAL_CAPACITY.md) |
| 轨迹转换 | save_traj_xyz / traj_to_info | ASE 轨迹 → 文件/信息 | [参数索引](API.md) |
| 形成能 | calc_formation_energy | 组成和能量 DataFrame → 派生结果 | [参数索引](API.md) |

## 使用方式

模板顶部集中设置参数；从仓库根目录独立运行：

```text
python -m Process_Struct.examples.capacity
python -m Process_Struct.examples.wyckoff_sites
python -m Process_Struct.examples.octahedra
python -m Process_Struct.examples.structure_features
python -m Process_Struct.examples.percolation
python -m Process_Struct.examples.percolation_sites
```

除容量模板外，需要先修改输入路径。模板导入不会读取结构或启动分析。现有函数和参数保持兼容；每项可单独调用，不要求统一 CLI。

## 科学语义与限制

通道位点导出示例的参数、单位、输出、重复运行策略和验证记录见 [PERCOLATION_EXAMPLE.md](PERCOLATION_EXAMPLE.md)。在已有 ccnb 环境执行；标记 CIF 的 He/Ne 表示几何点位，完整周期连接保留在 NET/CSV 中。

- 理论容量按化学式中全部迁移离子可转移的计量计算，不是实验可逆容量；摩尔质量包含完整化学式。原函数的 pymatgen 单位对象附带 amu 标签，模板用 float 展示计算公式对应的 mAh/g。
- Wyckoff 分组依赖 symprec（Å）和 angle_tolerance（度）；返回包含 PeriodicSite，不能直接用普通 json.dump 写出整个对象。
- 八面体分析默认 O 配体及 Fe/Mn 中心；局部失败可能打印错误并返回缺少畸变字段的记录，需要检查完整性。
- StructureFeatureExtractor 当前无论特征选择如何都计算 Na/O 比值，不是任意材料的通用提取器；特征组使用列表，如 ["lattice"]，避免传单个组名字符串。
- 通道维数是几何连通性，不代表迁移能垒。CCNB/CAVD 依赖、氧化态和探针模型需要单独确认。
- 形成能/电压必须明确每原子、每化学式或离子归一化，不能混合不同能量基准。

## 功能边界

见 [BOUNDARIES.md](BOUNDARIES.md)。通用去重是与 Process_Vasp 的迁移候选；完整算法比较前不移动代码。octadist 保持第三方项目独立。

## 验证

容量模板已实运行；Wyckoff 使用合成结构核对分组。percolation_sites 示例在 ccnb 环境用 NaFeF3 核对了 0.5 Å 连通、1.0 Å 无通道情况，以及 CIF 回读和周期连接 CSV。其他示例的语法与导入检查不代表真实材料或模型计算已验证。真实签名见 [API.md](API.md)，具体任务记录见 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。

## 通用去重合并已完成

实现统一到 Process_Struct/deduplication.py；Process_Vasp 保留同名兼容入口，层状氧化物与表面直接复用公共实现。deduplicate 保留首次出现的结构副本，deduplicate_dict 跨所有键去重并省略空组，deduplicate_df 按能量升序保留指定数量；采用默认 StructureMatcher，可能匹配平移/缩放及等价晶胞，不能理解为逐坐标完全相等。

列表模板：[deduplicate_structures.py](examples/deduplicate_structures.py)。DataFrame 原接口使用标签索引，建议输入索引唯一；n_keep 使用正整数。本轮保留这些旧行为，没有改匹配容差或能量基准。

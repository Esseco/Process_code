# Process_face

<!-- Manual project documentation -->

表面 slab 生成、原子约束和表面配置处理。默认 py1；依赖 pymatgen、ASE、numpy，配置枚举还依赖现有 VASP 结构枚举工具。

## 独立功能模板

| 功能 | 公开入口 | 输入 → 输出 | 模板 |
|---|---|---|---|
| 单晶面 slab | LOSlabProcessor.generate_slabs | 体相、Miller 指数、厚度 → 终止面列表/文件 | [generate_slabs.py](examples/generate_slabs.py) |
| 固定底部区域 | SurfaceFixer.fix_bottom_distance | slab、距离 → selective_dynamics 结构 | [fix_bottom.py](examples/fix_bottom.py) |
| 对称等价原子 | get_symmetry_atom | 结构、零基原子编号 → partner 索引或 None | [symmetry_partners.py](examples/symmetry_partners.py) |
| 单元素表面配置 | sym_surface_remove_atoms_single | 带约束 slab → 配置文件 | [surface_configurations.py](examples/surface_configurations.py) |

从仓库根目录运行；先修改顶部参数：

```text
python -m Process_face.examples.generate_slabs
python -m Process_face.examples.fix_bottom
python -m Process_face.examples.symmetry_partners
python -m Process_face.examples.surface_configurations
```

模板导入不运行，文件输出拒绝覆盖。slab 生成只建模型，不启动优化；需后续单独生成 VASP/MLIP 输入。全部签名见 [API.md](API.md)。

## 参数与科学边界

- generate_slabs 的 min_slab_size/min_vacuum_size 单位 Å；实际厚度受晶面层间距影响，不保证精确等于输入。模板手动设定氧化态，用于极性判断，不能直接套默认字典到其他体系。
- process_and_save 批量流程使用内部默认厚度，并可能非化学计量对称化；与单晶面模板保留原始终止面不同。删除原子后需核对化学计量和能量参考。
- SurfaceFixer 的距离方法使用笛卡尔 z，fraction 方法使用分数 c；斜晶胞/斜表面不可视为相同方向。当前约束操作修改传入对象，并替换既有 ASE constraints 或 selective_dynamics；模板先复制。
- analyze_slab 返回底部/内部/顶部三类，不是晶体学实际层数。基于 CrystalNN 的表面识别是启发式，失败的 CN 被置零，需要检查。
- get_symmetry_atom 返回任意符合当前判据的等价原子，不保证上下表面配对；目前采用分数坐标距离且边界处理有限，不替代严格周期距离匹配。
- 表面配置算法通过 H 替换/无序枚举处理单元素终止面，依赖固定氧化态和试验数；不是通用吸附或空位算法，也不保证每次生成相同结果。未验证其完整科学结果。

## 本轮修复与合并边界

修复 Surface_atom_process.py 对不存在的 Process_VaspInput 引用，改用仓库现有 Process_Vasp 中同名入口。其他算法不改。见 [BOUNDARIES.md](BOUNDARIES.md)。

## 验证

包与四个模板安全导入；合成结构检查底部固定、原对象不变及 POSCAR selective_dynamics 写出读取。未验证真实表面生成、极性、非化学计量对称化或配置枚举。

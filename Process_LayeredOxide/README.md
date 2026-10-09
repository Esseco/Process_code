# Process_LayeredOxide

<!-- Manual project documentation -->

层状氧化物专用工具。默认 py1，主要依赖 pymatgen、numpy、pandas、scipy。保留原接口，不与通用结构项目直接混合。

## 独立功能模板

| 功能 | 入口 | 输入 → 输出 | 模板 |
|---|---|---|---|
| O3 层滑移相变 | LayerOxide_O3_Transformer | 兼容 O3 结构 → O1/P3/OP2 初始模型 | [convert_phase.py](examples/convert_phase.py) |
| 层间距与键长 | get_layer_spacing / get_bond_lengths | Structure → 字典 | [layer_features.py](examples/layer_features.py) |
| 端点形成能 | LayerOxidePhaseDiagram.process | x、eV/atom 表 → formula_e、formation_e | [phase_diagram.py](examples/phase_diagram.py) |
| 下凸包电压 | get_voltage | x、eV/化学式表、Na 参考 → 电压平台表 | [voltage.py](examples/voltage.py) |

先编辑顶部路径和参数，从仓库根目录独立运行：

```text
python -m Process_LayeredOxide.examples.convert_phase
python -m Process_LayeredOxide.examples.layer_features
python -m Process_LayeredOxide.examples.phase_diagram
python -m Process_LayeredOxide.examples.voltage
```

所有模板导入不会执行；写文件模板拒绝覆盖已有结果。真实参数见 [API.md](API.md)，具体任务记录用 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。

## 关键适用条件

- 相变是层滑移初始结构，不是优化后的稳定相；先确认输入层数、轴向、元素和堆垛。SC_matrix 表示坐标平移所参照的超胞，不应认为所有方法都会自动建立该超胞；OP2 方法另有加倍逻辑。
- 层间距按 O 层法向投影及间距大小分类，Na/TM 名称是几何分类，不是直接识别插层原子；没有 O 时不可用。
- 相图默认模型为 NaxTMO2；energy 输入 eV/atom，乘 x+3 得到 formula_e（eV/NaxTMO2），formation_e 是相对端点连线的 meV/NaxTMO2，不是对单质形成能。
- 现有 parse_composition=True 分支存在列名和静态方法参数问题，模板明确使用 False 并提供 Na_content，未改动算法。
- get_voltage 使用 μ_Na - dE/dx，应使用总能量或一致归一化能量与参考；不能直接将 meV formation_e 配上总能量 μ_Na。capacity_step 是 Δx，不是 mAh/g。
- 电压凸包目前不能直接处理只有两点或全部共线的输入；calc_ehull 分支需真实数据验证，不默认开启。

## 合并边界

见 [BOUNDARIES.md](BOUNDARIES.md)。本轮不移动其他项目代码，重复功能先比较定义。

## 验证

四个模板安全导入；合成数据检查端点形成能和电压下凸包；合成 O 层检查间距。未验证真实 O3 相变、配位判定或完整凸包分支。

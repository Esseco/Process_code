# 插层电极相图评价

计算逻辑集中在 [metrics.py](metrics.py)，仅依赖 NumPy 和 Python 标准库；
可从 `Process_Phasediagram` 导入，也可单独复制该文件使用。默认环境为 py1，
Python >= 3.11。两个函数确定性执行，不需要随机种子，不修改输入、不读写文件，
不加载模型或提交计算。相同输入可安全重复调用。

## 凸包形状误差

```python
from Process_Phasediagram import calculate_hull_error

pred_hull = [[0.0, 0.0], [0.25, -1.0], [1.0, 0.0]]
ref_hull = {"x": [0.0, 0.75, 1.0], "energy": [0.0, -1.0, 0.0]}
result = calculate_hull_error(pred_hull, ref_hull, return_curves=True)
print(result["hull_error"])      # 约 0.3333333333333333
print(result["integral_error"])  # 约 0.3333333333333333

# 可选：指定两条凸包均覆盖的子区间；端点可以不在输入顶点中。
partial = calculate_hull_error(pred_hull, ref_hull, x_range=(0.2, 0.8))
```

- 顶点支持 `(N, 2)` 数组/列表，或含一维 `x`、`energy` 列的字典；至少两点。
- 自动按 x 排序，重复 x（即使能量相同）、NaN/Inf、非下凸包均抛出 `ValueError`。
  不筛点、不重建凸包；允许共线点。下凸包要求相邻段斜率单调不减，仅允许
  64 倍机器精度的相对浮点舍入差。
- 默认范围为共同覆盖区间；无正宽度交集、无效区间或需要外推时报错。
- 各自减去评价区间端点的能量连线，然后在联合顶点网格上精确计算绝对积分；
  对段内交叉拆成两个三角形。能量零点与整体线性倾斜不会影响形状误差。
- 必须自行保证能量单位/归一化相同，例如 meV/TM；函数无法从数值推断单位。
  `hull_error` 与输入能量单位相同，`integral_error` 为能量单位乘组分单位。
- `return_curves=True` 额外返回 `x`、`pred_relative_energy`、
  `ref_relative_energy`，可直接用于分段线性绘图。默认只返回两项误差。
- 结果受浮点精度限制；仅用于已有计算参考凸包的情况。

## 容差相区间误差

```python
from Process_Phasediagram import calculate_phase_iou_error

ref_phases = {
    "O3": [(0.0, 0.3)],
    "P3": [(0.3, 0.6)],
    "OP2": [(0.6, 1.0)],
}
pred_phases = {
    "O3": [(0.0, 0.35)],
    "P3": [(0.35, 0.65)],
    "OP2": [(0.65, 1.0)],
}
result = calculate_phase_iou_error(
    pred_phases, ref_phases, x_range=(0.0, 1.0), delta=0.0,
)
print(result["phase_iou"])  # O3≈0.857143, OP2≈0.875, P3≈0.714286
print(result["mean_iou"])   # 约 0.815476
print(result["phase_error"])  # 约 0.184524
```

- `x_range` 必须提供，且满足有限的 `xmin < xmax`；组分区间及 `delta` 使用相同单位。
  `delta` 为非负有限标量，默认 0。
- 相标签为字符串。同一相可有多个不连续区间；两相共存区分别计入各相存在区间。
  每个原始区间必须满足有限的 `start < end`，即使它位于评价范围外也要通过检查。
- 先对两图所有区间分别左右扩展 `delta`，再裁剪到评价范围；原本在范围外的区间
  若扩展后进入范围，也会计入。合并同相重叠/相接区间，不重复计算长度。
- 对两图标签并集等权平均。只在一图出现的标签 IoU 为 0，包括该标签的区间裁剪后为空的情况。
- `[]` 表示空存在集合。标签在两图均有记录、但两边扩展和裁剪后均为空时 IoU 为 1；
  两图标签字典均为空时，平均值无定义，抛出 `ValueError`。
- 此指标严格采用“双侧区间扩展后的 IoU”。偏移小于 `delta` 并不保证 IoU 为 1；
  它不是边界偏移的硬容差判定。`delta` 改变的是扩展后存在区间的重合度。

## 验证

在仓库根目录使用 py1：

```text
python -B -m unittest discover -s tests -p test_phase_diagram_metrics.py -v
python -B -m doctest Process_Phasediagram/metrics.py
```

测试采用最小合成数据和解析预期值，无临时数据库、快照或正式数据副本。
覆盖一致性、凸包交叉、能量线性变换、插值端点、共同区间、窄相偏移、缺失相、
多段/重叠/共存区间、不同 delta、裁剪和输入异常。

# CompositionScreening

包目录：`E:\Py-Code\CompositionScreening`。默认使用 `py1` 环境，依赖 pymatgen 和本仓库的 `Process_Struct`。

在仓库根目录运行，或将 `E:\Py-Code` 加入 **PYTHONPATH** 后，可直接使用下面的导入方式。仅加入系统 `PATH` 不会让 Python 自动找到此包；修改环境变量后需重启终端或 Notebook 内核。

组分生成与理论容量初筛模块。当前版本支持一个 `X` 替代位点，例如
`Li-X-O2` 或 `LiXO2`。

```python
from CompositionScreening import screen_compositions

result = screen_compositions(
    "Li-X-O2",
    ["Ni", "Mn", "Fe", "Co"],
    n_elements=3,
    granularity=0.1,
    max_integer_coefficient=10,
    capacity_cutoff_mAh_g=100.0,
    return_details=True,
)
print(result["passed_count"])
```

纯 Li/Na/K-过渡金属氧化物会自动使用 `layered_oxide` 价态规则；也可以显式传入 `environment="layered_oxide"`。层状氧化物规则包括 Ti(+4)、V(+3/+4/+5)、Cr(+3/+4)、Mn(+3/+4)、Fe(+3/+4)、Co(+3/+4)、Ni(+2/+3/+4) 和 Cu(+2/+3)。

`n_elements` 指每次选择的元素数，且每个被选元素的比例必须大于 0；因此 `n=2` 只生成二元，`n=3` 只生成三元。`allowed_ranges={"Ni": (0.2, 0.6)}` 可限制所选元素在 X 中的比例，范围使用 0–1。整数比的最大系数默认是 10，等比例和整数比也必须满足范围限制。候选列表中的空字符串会被忽略，X 的真实元素比例始终归一化为 1。

返回 `generated_count`、`passed_count`、`failed_count`；设置 `return_details=True` 时还返回 `details` 列表。当前按理论容量上限大于等于阈值筛选。函数不写文件，无随机性。

如果只希望某些元素参与容量估算，可以传入 `active_elements=["Mn"]`；省略时会按现有价态规则把可变价阳离子都计入形式容量上限。

对于满 Li 配方无法电荷平衡的层状氧化物，默认会在固定 TM/O 骨架上反算允许的 Li 含量，并用不超过输入 Li 含量的最大中性值重算，例如 `Li1Ti0.1Mn0.9O2` 可调整为 `Li0.9Ti0.1Mn0.9O2`。可传 `adjust_mobile_ion=False` 关闭此行为。

生成规则：等比例和最大整数系数范围内的正整数比始终加入；其余比例在粒度网格上生成。比例候选通过现有
`Process_Struct.Chemical_Capacity_Constraints` 进行形式价态、电荷平衡和阳离子理论容量估算。结果是理论上限初筛，不代表实际可逆容量、结构稳定性或循环性能。

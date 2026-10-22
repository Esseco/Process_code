# 组分–形成能相图

```python
from Process_Phasediagram import plot_phase_diagram

fig, ax = plot_phase_diagram(
    df["Na_content"], df["eform"], df["phase"], df["is_stable"],
    phase_hulls=True,
    phase_styles={"O3": {"color": "#397CA5", "marker": "s"}},
    ylabel="Formation energy (meV / formula unit)",
)
fig.savefig("phase_diagram.png", dpi=300, bbox_inches="tight")
```

默认环境 py1。函数使用 NumPy 和 Matplotlib，不修改输入，不自动写文件或显示窗口，
不使用随机数。返回 figure/axes，由调用者保存、显示和关闭。

## 可修改的完整调用示例

编辑 [examples/plot_phase_diagram.py](examples/plot_phase_diagram.py) 顶部参数后，在仓库根目录执行：

```text
python -B -m Process_Phasediagram.examples.plot_phase_diagram
```

`INPUT_CSV=None` 使用明确标注的合成演示数据；设置 CSV 路径后使用真实数据。
顶部可改列名、图片路径、格式（PNG/PDF/SVG）、DPI、是否显示、各相凸包、
颜色和 marker、点大小、透明度、线宽、坐标轴标签和范围。
默认输出当前目录的 phase_diagram.png，拒绝覆盖；显式 `OVERWRITE=True` 才覆盖，
始终拒绝将输出指向输入 CSV。导入示例不读写文件或画图。

CSV 最小格式（单位由数据提供方保证）：

```csv
Na_content,eform,phase,is_stable
0,0,O3,True
0.5,-200,P3,True
1,0,O3,True
```

## 数据和样式约定

- 四列必须为等长非空一维数据。x/eform 为有限实数；相名为非空字符串；
  is_stable 为布尔值或数值 0/1，禁止缺失值和字符串标记。
- eform 原样绘制，不转换单位、不减端点参考能。若使用 LayerOxidePhaseDiagram
  的结果，可将 EFORM_COL 改为 formation_e，单位为 meV/NaₓTMO₂。
- 全局基态完全由 is_stable 决定，点较大、略透明（stable_alpha=0.95）、黑框，按 x 连接黑色实线。
  不校正或重新判断全局稳定性；调用者须保证标记正确。没有稳定点时不画总线，
  一个稳定点时仅画点；重复 x 的稳定点全显示，黑线只取其中最低能量。
- 默认 O3 蓝方块、P3 红上三角、P2 橙下三角、O2 紫圆、OP2 绿菱形、
  OP4 粉五边形、O1 灰六边形、X 棕 X。可通过 phase_styles 分别覆盖 color/marker，
  默认表可从 DEFAULT_PHASE_STYLES 查看。未知相名沿用 X 样式，保留自己的图例标签。
- phase_hulls=False 为默认值。开启后，每个相单独按组分选最低能，再用单调链提取
  下凸包，以相颜色虚线连接。各相凸包上的点更不透明，无黑框；全局基态样式优先。
  其他点较小且更透明。不画背景区间。
- 同组分同能量的并列点、下凸包边上的共线点均可强调；hull_atol 为绝对能量容差，
  默认 1e-10，与 eform 同单位，仅影响强调点判断。支持单点、两点、全共线及重复组分；
  单组分相只有点，无虚线段。各相仅在自身采样范围内连线，不外推。
- point_size/phase_hull_size/stable_size 为面积（pt²），默认分别为 28/50/85；
  各相凸包点比普通点稍大，全局基态仍最大。linewidth/edgewidth 为线宽（pt）；
  alpha 取 0–1，越小越透明。figsize 单位为英寸。传入 ax 可继续定制图形。
- xlim/ylim 默认 None，新建图自动确定坐标范围；可传入 (最小值, 最大值)。
  示例顶部 XLIM/YLIM 对应这两个参数。传入已有 ax 时，None 保留其现有范围设置。
- 绘制层级从低到高：普通结构点 → 各相凸包虚线 → 各相基态点 → 总凸包黑线 → 全局基态点。
- 默认 Arial（font_family 可改）、字号 13 pt（font_size 可改），仅保留左侧和底部主刻度。
  渲染机器需已安装相应字体；
  默认横轴用 mathregular 排版化学式下标，使其跟随 Arial 正文字体。

全局和各相凸包均基于输入的能量数据，不推断温度、熵或宏观相存在区间。

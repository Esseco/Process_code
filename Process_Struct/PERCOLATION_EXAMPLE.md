# 渗流通道与位点导出示例

任务记录采用 TASK_TEMPLATE.md 的字段；入口为 examples/percolation_sites.py。

- 目标：调用已有 analyze_percolation，保留 CCNB 网络并导出间隙与瓶颈标记。
- 输入：有序结构文件，迁移元素（默认 Na，空字符串保留全部原子），探针半径（Å）。默认固定路径指向已有 mp-1078217_NaFeF3.vasp，运行前检查路径。
- 环境：已有 ccnb 环境，含 CCNB/CAVD 和 pymatgen。
- 参数：示例探针半径 0.5 Å，只用于演示；指定迁移元素时从框架中移除此元素。未提供氧化态时由原接口猜测并在 summary.json 中记录。
- 随机性：分析没有随机种子；输出目录用 UUID 区分运行。
- 副作用：写入指定输出根目录下的唯一子目录；不启动 GUI、不提交外部计算。
- 重复运行：每次生成新目录，不覆盖或删除已有计算结果。
- 输出：CCNB 原始 structure.net、structure_origin.net、structure.resex，指定迁移元素时还会输出 structure.vesta；interstitial_sites.csv、bottleneck_connections.csv、channel_sites_overlay.cif、summary.json。

从 E:/Py-Code 根目录，在 ccnb 环境执行：

```text
python -m Process_Struct.examples.percolation_sites
python -m Process_Struct.examples.percolation_sites --structure "E:/structures/example.cif" --migrant Na --radius 0.5 --output "E:/results/channels"
```

也可在 Notebook 中复用现有接口和示例导出函数：

```python
from pathlib import Path
from Process_Struct import analyze_percolation
from Process_Struct.examples.percolation_sites import export_sites

result = analyze_percolation(
    structure, migrant="Na", cutoff_radius=0.5,
    output_dir=r"E:\Py-Code\percolation_outputs",
)
sites, connections, marker_count = export_sites(
    Path(result["output_directory"]), migrant="Na",
)
```

间隙 CSV 的 fx/fy/fz 是分数坐标，radius_A 是间隙半径。连接 CSV 保留起终点 ID、所属通道、周期平移、瓶颈分数坐标、瓶颈半径（Å）和段长（Å）；同一对位点的不同周期平移不能合并，反向连接也保留。一个连接段的瓶颈不等于控制整条渗流路径的全局临界瓶颈。

CIF 中 It/He 是间隙点，Bn/Ne 是瓶颈点，均为显示标记，不是实际元素。CIF 将坐标折回晶胞；瓶颈按坐标和半径保留 5 位小数去重，仅影响显示，原始 CSV/.net 不去重。He/Ne 如与实际元素冲突会报错，需要换标记。CIF 只携带点位，完整周期连接依靠 .net/CSV；不要将显示用 CIF 用于容量、能量或结构弛豫。

间隙点和瓶颈可能重合。示例以周期分数坐标容差 1e-4 分组，将重合显示记录的占位率分配为 1/记录数，使总和为 1；不移动坐标。此占位率仅用于显示，不具有化学意义。CIF 回读可能把重合的 He/Ne 作为同一个混合标记位点；CSV 保存两类点位的完整记录。pymatgen 回读时可能提示 He/Ne 没有电负性，不影响坐标显示。

无贯通通道时，structure.net 可以为空，导出为仅含框架的 CIF 和只有表头的 CSV；这不代表没有局部孤立孔隙。原始 structure_origin.net 保留未筛选的网络信息。

验证：指定 Na 的 NaFeF3 示例在 ccnb 环境实运行，0.5 Å 下为 3D，34 个间隙点、96 条有向连接、48 个去重瓶颈标记；核对 CIF 可回读、标记数及 CSV 周期连接行数。1.0 Å 下无贯通通道，核对空 CSV 和 8 个框架原子的 CIF。未验证全部材料、所有探针半径及空迁移元素分支的 NET 导出格式；维数和点位是几何结果，实际稳定性、能垒和离子迁移需另行评估。

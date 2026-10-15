# NVT 轨迹导出 MSD

`export_msd` 封装 ASE 自带 `ase.md.analysis.DiffusionCoefficient`，不重复实现 MSD 核心。
默认处理整段轨迹的所有保存帧，不裁剪、不分段，以首帧为起点，按元素分别平均：
MSD(t) = mean(|r_i(t) - r_i(0)|²)。仅导出 MSD，不拟合扩散系数或计算电导率。

```python
from Process_MLIP import export_msd

result = export_msd(
    "md_results/03_diffusion/md.traj",
    "md_results/03_diffusion/msd.csv",
    species="Na",  # 也可 "Li"、["Na", "Li"]、None（全部元素）
)
```

完整可编辑示例：[examples/msd.py](examples/msd.py)。修改 INPUT、OUTPUT、SPECIES 后运行：

```text
python -m Process_MLIP.examples.msd
```

## 集成到 MD 完整示例

[examples/mlip_md.py](examples/mlip_md.py) 中设置：

```python
MSD_POSTPROCESS = {
    "enabled": True,
    "stage": "last_nvt",         # 或从 1 开始的阶段序号
    "species": "Na",             # Li、元素列表，或 None（所有元素）
    "output_csv": None,          # 默认所选阶段目录内 msd.csv
    "overwrite": False,
}
```

全部 MD 阶段成功完成后，示例自动调用已有 export_msd，不加载新模型。
默认关闭，不改变原 MD 行为。开启时默认选最后一个 NVT 阶段，不会自动分析 NPT；
也不会自动区分哪个 NVT 是平衡段或生产段，需要按研究目的选择 stage。
output_csv 可填写自定义绝对路径，或相对 OUTPUT 的路径，例如 analysis/msd_na.csv。
目标阶段必须为 NVT、至少运行一步；无合适阶段、目标 CSV 已存在且不允许覆盖等问题，
会在 MD 开始前报错。MSD overwrite 与 MD overwrite 独立，不能将 MSD 写入任一阶段的 md.csv。
--preview 仅展示配置，不运行 MD 或后处理。

## CSV 内容

每行是一种元素在一帧的统计数据；多种元素分别输出，不混合平均。

| 字段 | 含义 |
|---|---|
| segment | 分段序号，默认整段为 1 |
| frame_index | 原轨迹中的保存帧索引，从 0 开始，不是 MD 积分步编号 |
| time_fs / time_ps | 距本段首帧的时间，fs / ps |
| species / atom_count | 元素及参与平均的原子数 |
| msd_x_A2 / msd_y_A2 / msd_z_A2 | 三个笛卡尔方向 MSD，Å² |
| msd_total_A2 | 上述三个分量之和，Å² |

xyz 是实际笛卡尔坐标轴，不自动等于晶体 a/b/c 方向或层间法向。
只有层面确实平行 xy 时，x+y 才能直接作为面内 MSD。

## 时间、周期边界与适用范围

- 优先从同目录、同一轨迹对应的已完成 `report.json` 自动恢复保存帧时间。
  默认末帧会被 MD 强制保存，间隔可能不足一个 trajectory_interval；仍按真实时间保留。
- 外部轨迹或没有可用报告时，显式传 `frame_interval_fs`。这是保存帧之间的时间，
  不是积分步长；例如 dt=1 fs、每 10 步保存，则填 10。显式参数按等间隔解释。
- 此接口针对固定晶胞 NVT `.traj`。不调用模型、不要求 calculator、不会修改源轨迹。
  检查每帧的晶胞、PBC 和元素序列；变胞轨迹会明确报错。
  原子索引必须保持对应关系；仅凭元素序列无法检测同种原子之间的重新编号。
- 当前 run_md 不执行 wrap，因此默认 unwrap=False，保留真实连续坐标，
  即使相邻保存帧位移超过半个晶胞，也不会错误地缩短成最小镜像位移。
- 外部 wrapped 轨迹用 unwrap=True，复用 ASE `find_mic` 逐帧展开，支持斜晶胞。
  这种重建要求保存间隔足够短，不能从稀疏 wrapped 帧恢复已丢失的跨胞次数。
- 默认不做漂移修正。`drift_reference="framework"` 可扣除未选中元素构成的框架的
  质量加权质心位移；必须存在未选中的框架原子。

静态结构弛豫的 relax.traj 记录优化迭代，没有物理 MD 时间，不能作为扩散时间序列。
这里“整段轨迹”指 NVT MD 轨迹，含首帧及最后一帧。

## ASE 复用与统计约定

MSD 数值由 ASE 的 `DiffusionCoefficient.calculate` 计算。
ASE 内部为 Einstein 斜率拟合储存的是 MSD/2，本封装乘 2 后导出常规定义的 MSD。
只把所选元素对应的原子交给 ASE，保证归一化人数正确。
CSV 使用准确的帧时间，不使用 ASE 内部均匀时间网格；其内部自动拟合结果不导出、也不采用，
因此尾部短间隔不会影响输出的 MSD 值或时间标签。
官方实现：[ASE analysis 源码](https://ase.gitlab.io/ase/_modules/ase/md/analysis.html)。

默认是单一起点的 MSD，不是所有重叠时间起点平均。需要时可用原 ASE 选项：
`skip_frames=...` 跳过初帧、`number_of_segments=...` 将剩余轨迹分成互不重叠的段。
每段以本段首帧为起点分别输出；保留帧数必须被段数整除，每段至少两帧，
不静默舍弃尾帧。不在同一文件中合并不同温度、不同 MD 阶段的轨迹。

只写指定 CSV，默认拒绝覆盖；overwrite=True 可显式覆盖，但禁止覆盖输入轨迹本身。
数据准备和 ASE 统计全部通过后才创建 CSV。返回值包含 CSV 路径、元素、帧数、时间来源等信息。
此功能不判断是否进入长时扩散区间，不能把整段 MSD 曲线自动等同于已收敛扩散系数。

## 扩散系数与离子导率拟合

独立函数直接读取上面生成的 MSD CSV，不加载模型或轨迹：

```python
from Process_MLIP import fit_msd
result = fit_msd(
    "md_results/03_diffusion/msd.csv",
    species="Na",                  # None 为 CSV 全部元素，也可列表
    fit_start_ps=2.0, fit_end_ps=8.0,
    temperature_K=800,
    volume_A3=1000.0,               # 实际固定 NVT 晶胞体积 Å³
    ion_charge=1,                   # 电荷数 z，Na+ 填 1，Mg2+ 填 2
    output_json="transport.json",  # 可不填，只返回 dict
)
```

拟合区间包含两端，必须位于每个选中分段的已有时间范围内，且至少含 3 个采样点。
使用真实 time_ps（包括不规则末帧），NumPy 普通最小二乘拟合 MSD = slope*t + intercept，
截距不强制为零。每个元素、每个 segment 分别拟合，不混合不同分段或温度。
分段 CSV 的时间从每段起点算起，拟合范围也按这个相对时间解释。

三维标量 D = slope_total/6，各笛卡尔方向 D_x/y/z = slope_x/y/z/2。
即使扩散主要局限在层内，三维标量仍是迹平均 (D_x+D_y+D_z)/3；
面内等效值在层面平行 xy 时可用 (D_x+D_y)/2，不能直接把 total 斜率除以 4。
Einstein 关系与自由截距线性拟合可参考 [ASE 官方实现](https://docs.ase-lib.org/_modules/ase/md/analysis.html)。

对每个元素，用 σ_NE = (N/V)*(z*e)^2*D/(k_B*T)。N 自动取 CSV atom_count，
多元素可传 ion_charge={"Na": 1, "Li": 1}，必须覆盖所有选中元素。
返回 results 中的 diffusion_m2_s、diffusion_cm2_s、directional_diffusion_m2_s（x/y/z），
conductivity_NE_S_m、conductivity_NE_S_cm，以及每项斜率、截距、R²、实际采样范围和点数。
conductivity_NE_sum_S_m 是每段所选元素的导率之和，不包含未选择的载流子。
Å²/ps 转 m²/s 乘 1e-8；S/m 转 S/cm 除 100。常数使用 SI 精确定义。

完全平坦曲线返回 D=0、R²=null；总斜率负值报错，不裁成正扩散。
方向斜率可能因噪声为负，保留原拟合值便于检查。R² 高不等于扩散充分收敛；
需要自己选择长时扩散线性区，检查足够多跳跃，并通过独立轨迹评估统计误差。
此接口不提供误差条，原有 MSD 是单起点/不重叠分段统计，采样点不能视为独立观测。
导率是忽略离子间交叉关联的 Nernst–Einstein 估算，不代表关联修正后的真实导率。

完整 MD 示例中，先开启 MSD_POSTPROCESS，再开启 TRANSPORT_FIT；后者自动使用选中
NVT 阶段的目标温度与最终晶胞体积，默认 JSON 写在 MSD CSV 旁边。
自定义相对 output_json 以 OUTPUT 为根目录。默认拟合 2–8 ps 仅为可修改占位示例，
短测试轨迹必须相应缩短拟合范围，生产扩散模拟通常需要显著更长的时间。
独立 examples/msd.py 中也有同名开关，但温度与体积需要手动填写。
默认禁止覆盖；显式 overwrite=True 可覆盖分析输出，但禁止覆盖输入 MSD CSV。

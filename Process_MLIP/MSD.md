# NVT 轨迹导出多时间起点 MSD

`export_msd` 仅使用 `pymatgen-analysis-diffusion` 的 `DiffusionAnalyzer`，
固定 `smoothed="max"`；旧 ASE 单起点后端已移除，无回退或后端选择开关。
原函数调用和 CSV 列名/单位保留，新增可选 `min_obs=30`。

```python
from Process_MLIP import export_msd

result = export_msd(
    "md_results/01_production/md.traj",
    "md_results/01_production/msd.csv",
    species="Na",              # "Li"、["Na", "Li"]、None（全部元素）
    skip_frames=0,             # 跳过平衡段保存帧
    min_obs=30,                # pymatgen 原生最低采样量控制
    drift_reference=None,      # "framework": 扣除未选中原子的质量加权质心漂移
)
```

MSD(n Δt) = mean_i,k(|r_i(k+n) - r_i(k)|²)。对每个 lag n，
使用段内所有可用起点 k，再对所选元素原子取平均；不同元素分别统计。
它与只参考第一帧的旧结果不同，也不是把每一步的位移平方累加。

## 环境与调用

精简完整流程见 [examples/postprocess_md.py](examples/postprocess_md.py)：从已有 NVT .traj
重算 MSD、扩散系数和电导率，顶部配置路径、元素、拟合区间、电荷及实际温度。
体积自动读取固定晶胞；默认同目录 report.json 推断保存帧时间，无报告时填写 FRAME_INTERVAL_FS。
在仓库根目录运行 `python -m Process_MLIP.examples.postprocess_md`，不加载模型。
仅覆盖 OUTPUT_DIR 中 msd.csv、transport.json，不修改原轨迹；拟合参数沿用 pymatgen 默认。

分析环境需要 pymatgen-analysis-diffusion；本地 py1 已装 2024.7.15，本次未安装或更新依赖。
只有调用 export_msd 时才导入该包，普通 Process_MLIP 导入、MD 和模型加载不受影响。
缺依赖时报明确错误；可在独立分析环境处理超算下载的轨迹，不要求更改模型环境。
不加载模型，不修改源轨迹/报告，无随机种子；只写指定 CSV，默认拒绝覆盖，显式 overwrite=True 可覆盖。
数据校验和统计成功后才创建 CSV。

完整后处理示例：[examples/msd.py](examples/msd.py)，修改输入/输出/元素后运行：

```text
python -m Process_MLIP.examples.msd
```

完整 MD 示例 [examples/mlip_md.py](examples/mlip_md.py) 的 MSD_POSTPROCESS 默认关闭；
开启后自动选择最后 NVT 或指定阶段，配置元素、输出路径、skip_frames、min_obs 和漂移选项。
相对输出路径以 OUTPUT 为根；MSD 覆盖开关与 MD 独立。--preview 只预览，不加载依赖或运行计算。
启用后在加载模型前检查分析依赖、原子数和可用 lag；开启拟合还会检查真实 lag 范围内是否有至少三点。
八模型和温度/时长扫描脚本保持原调用，更新项目后自动使用新后端。

## 原生 max 采样及分段

- 时间间隔从 int(1000 / 保存帧间隔_fs) 帧开始，约 1 ps；不自动输出零时刻。
  后续按 pymatgen 规则选取约 200 个 lag，不再每个保存帧输出一行。
- 每个元素的最大 lag 受 min_obs、原子数和段长共同限制；不同元素的 lag 网格可不同。
  min_obs 越大通常限制得越短。它不是滑动起点之间的间隔，也不表示窗口独立。
- 原生 DiffusionAnalyzer 会附带执行拟合，至少需要三点；本接口先检查，数据不足明确报错。
  应增加轨迹长度、减少分段，或在了解采样限制后调低 min_obs，不回退单起点计算。
- 保存帧间隔须 <= 1000 fs；更稀疏时原生 max 模式会产生零 lag 除零，因而明确拒绝。
- number_of_segments=1 默认整段；大于 1 时将保留帧等分成互不重叠的段，
  每段内部仍做多时间起点平均，分别输出，不合并段间结果。帧数须整除且各段采样充足。
- 不混合不同温度或不同 MD 阶段。跳过平衡帧后再分析，非平衡过程不能仅凭平均获得平衡态扩散。

## CSV 内容（列名不变）

| 字段 | 含义 |
|---|---|
| segment | 分段序号，从 1 起 |
| frame_index | 段首原轨迹索引 + lag 帧数；仅保留作兼容索引，不代表唯一位移终点 |
| time_fs / time_ps | 时间间隔 lag，fs / ps，不是绝对模拟时刻 |
| species / atom_count | 元素及真实参与平均的原子数 |
| msd_x_A2 / msd_y_A2 / msd_z_A2 | 笛卡尔 x/y/z 方向的多起点平均 MSD，Å² |
| msd_total_A2 | 三个方向之和，Å² |

每行代表一种元素在一个 lag 的统计；绘图仍直接用 time_ps 和 msd_total_A2。
frame_index 可定位相对段首具有该 lag 的帧，但 MSD 实际使用了多个位置对；不能再用它解释为单帧 MSD。
xyz 不自动等于晶格 a/b/c；只有层面平行 xy 时，x+y 才是面内 MSD。

## 时间、周期边界和漂移

- 自动从轨迹旁对应的已完成 report.json 读取时间。外部轨迹用 frame_interval_fs
  指定保存帧之间的时间，不是积分步长；例如 dt=1 fs、每 10 步输出，填 10。
- 多起点分析要求等间隔。报告中的强制末帧若不足一个保存间隔，明确警告并排除，
  返回 dropped_frame_indices；frame_count 为实际保留帧数。其余非等间隔数据报错。
  显式 frame_interval_fs 代表调用者保证等间隔，不用于掩盖真实不等间隔。
- 仅固定晶胞 NVT .traj；逐帧检查晶胞、PBC、元素顺序及有限坐标。
  原子身份须保持对应；同元素之间重排无法仅靠元素序列检测。
- run_md 不 wrap，默认 unwrap=False 保留连续坐标，包括大于半晶胞的真实位移。
  wrapped 外部轨迹用 unwrap=True，ASE find_mic 逐帧展开，支持斜晶胞；保存必须足够频繁。
- 默认不修正漂移。drift_reference="framework" 扣除所有未选中原子的质量加权质心位移；
  至少保留一个框架原子。多个选中元素共用这个框架，互不当作对方的框架。
- 为保持原调用的漂移语义，适配层把处理后的目标位移和一个固定零位移参考位点交给
  pymatgen，避免其默认框架处理再次扣除漂移；参考位点不计入 atom_count 或 MSD。
  后端必须的温度占位值只影响被丢弃的内部电导率计算，不影响导出的 MSD。

原生 MSD 统计直接复用 [pymatgen 官方实现](https://github.com/materialyzeai/pymatgen-analysis-diffusion/blob/main/src/pymatgen/analysis/diffusion/analyzer.py)。
不采用其自动拟合的扩散系数/电导率；沿用下方独立 fit_msd 的拟合区间、电荷和单位约定。
静态结构弛豫轨迹没有物理时间，不能作为扩散轨迹。

## 扩散系数与离子导率拟合

独立函数直接读取上面生成的 MSD CSV，不加载模型或轨迹：

```python
from Process_MLIP import fit_msd
result = fit_msd(
    "md_results/03_diffusion/msd.csv",
    species="Na",                  # None 为 CSV 全部元素，也可列表
    fit_start_ps=None, fit_end_ps=None,  # 默认全部有效 lag；也可省略
    temperature_K=800,
    volume_A3=1000.0,               # 实际固定 NVT 晶胞体积 Å³
    ion_charge=1,                   # 电荷数 z，Na+ 填 1，Mg2+ 填 2
    output_json="transport.json",  # 可不填，只返回 dict
)
```

拟合区间包含两端，默认 fit_start_ps=None、fit_end_ps=None，按每个元素、每个分段分别
使用最早到最晚的全部正 lag 数据。也支持只设置一端，例如 fit_start_ps=2、fit_end_ps=None，
或两端均手动设置。手动边界必须在对应数据覆盖范围内，且最终至少含 3 个采样点。
使用 CSV 的 lag time_ps，先解析/裁剪区间，再调用 pymatgen 的
get_diffusivity_from_msd(msd, dt_fs)，不覆盖其算法参数；默认 max 加权，权重为 1/lag，截距自由。
传入原生函数前 ps 转 fs，其返回的 cm²/s 再转 SI；不采用 DiffusionAnalyzer 自动全区间拟合结果。
零 lag 不参与加权拟合，None 起点会自动跳过零 lag；显式填 0 仍报错。
非有限、负值、重复时间等非法输入仍报错，不因 None 而静默清洗。
每个元素、每个 segment 分别拟合，不混合不同分段或温度。
分段 CSV 的时间是段内的 lag，拟合区间必须落在各元素实际输出的 lag 范围内。
顶层 fit_range_ps 保存请求边界（None 在 JSON 中为 null）；每项 actual_fit_range_ps
记录真正参与拟合的首末采样时间。默认全区间不代表自动识别扩散线性区。

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

扩散系数的总量和各方向全部调用 pymatgen 原生拟合，沿用其默认斜率下限 1e-15 Å²/fs。
因此负、零或很小的斜率会返回极小正 D；pymatgen_slope_floor_applied 按 x/y/z/total 标记触发下限的结果。
这不代表已观测到真实扩散。若分量触发下限，各方向 D 的迹平均可能与总 D 不再严格相等，这是原生截断的结果。
原 slope_A2_per_ps、intercept_A2 和 R² 用于诊断截断前的加权直线；负方向/负总斜率保留在诊断字段中。
完全平坦曲线 R²=null；fit_method="pymatgen" 和 fit_weighting="1/lag" 仅为返回元数据，不是可调参数。
原 r_squared 字段仍是该拟合直线的普通、非加权 R²，不是加权 R²。
方向斜率可能因噪声为负，保留原拟合值便于检查。R² 高不等于扩散充分收敛；
需要自己选择长时扩散线性区，检查足够多跳跃，并通过独立轨迹评估统计误差。
此接口不提供误差条，多时间起点窗口相互重叠，MSD 点不能视为独立观测。
不将 pymatgen 返回的回归标准差作为可靠的多起点 MSD 置信区间。
导率是忽略离子间交叉关联的 Nernst–Einstein 估算，不代表关联修正后的真实导率。

完整 MD 示例中，先开启 MSD_POSTPROCESS，再开启 TRANSPORT_FIT；后者自动使用选中
NVT 阶段的目标温度与最终晶胞体积，默认 JSON 写在 MSD CSV 旁边。
自定义相对 output_json 以 OUTPUT 为根目录。各示例默认两端 None；
正式分析可根据 MSD 曲线手动选择扩散线性区，生产扩散模拟通常需要显著更长的时间。
独立 examples/msd.py 中也有同名开关，但温度与体积需要手动填写。
默认禁止覆盖；显式 overwrite=True 可覆盖分析输出，但禁止覆盖输入 MSD CSV。

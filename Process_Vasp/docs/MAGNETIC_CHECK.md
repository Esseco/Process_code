# 层状氧化物 Fe/Mn 磁矩检查

默认 py1。新入口位于 `Process_Vasp.results.magnetic_check`，也可从 `Process_Vasp` 或 `Process_Vasp.output` 导入。

```python
from Process_Vasp import check_dft_magnetic_moments, check_layered_oxide_moments
report = check_dft_magnetic_moments(directory, is_layered_oxide=True)
report = check_layered_oxide_moments(
    ["Fe", "Mn", "O", "O"], [4.3, -3.9, 0.0, 0.0], is_layered_oxide=True)
```

调用方应由已知体系或相识别明确层状身份，不仅凭 Fe/Mn/O 组成猜测。Fe 的 |m| 范围为 3.5–4.5 μB，Mn 为 3.0–4.0 μB，含端点；沿用 Magmom_Function 的局域高自旋经验范围。负号可表示共线自旋方向，按绝对值检查。其他元素不检查，非层状/非氧化物或无 Fe/Mn 时 `skipped`；Na=0 仍可由调用方明确层状身份后检查。

目录接口只读最后一张共线 OUTCAR 局域投影磁矩表，支持压缩文件。可提供与 OUTCAR 匹配的最终 `structure` 和 XML `parameters`，否则读取 POSCAR/INCAR。返回 `passed`、`warning`、`unknown` 或 `skipped`，包含原子顺序、局域磁矩、零起始异常原子索引、元素及范围。缺失或非法数据、SOC/非共线计算无法判定，不填零。层状身份未确定时保留已读标量值并标 `unknown`。

局域投影之和 `total_local_moment` 不是包含间隙贡献的整体磁矩；NUPDOWN 若存在仅记录，不当作必须相等的约束。经验范围通过不是磁性基态证明，未通过也不能直接认定计算失败；不同价态、投影方式、泛函和磁性排列可能影响局域值。

无随机性，无输入修改、模型调用、VASP 执行或作业提交。重复运行仅返回诊断；项目可按结构和证据指纹复用。旧 `read_magnetic_moments_outcar` 和 Magmom_Function 的元组返回接口及其历史语义不改变。

## 原始数据与科学判断分离

`read_dft_magnetic_data(directory, *, structure=None, parameters=None)` 只读最后计算的全部元素局域磁矩，不判断范围或层状身份。返回原子顺序 `elements`、`moments` 和 `sites`（atom_index/element/moment），unit=mu_B、来源和读失败原因；共线保存标量，SOC/非共线保存能解析出的 xyz 矢量。无法解析则 available/unavailable 状态明确区分，不补零。此数据读取功能不限定 Fe/Mn；限定的是后续合理性判断。

PhaseDiagram 远端只保存原数据，回传不因磁矩异常拒收。Agent 的本地科学分析才检查层状 Fe/Mn 氧化物自旋：passed 才用于相图/微调/误差，异常或未知保留原始数据并暂缓科学使用。公共函数仍不自动改文件或任务，磁矩范围通过不等于已证明磁性基态。

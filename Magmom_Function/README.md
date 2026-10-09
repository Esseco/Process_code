# Magmom_Function

<!-- Manual project documentation -->

磁矩读取的兼容入口及 Na-Fe-Mn 专用磁性启发式。默认 py1。不是通用磁性基态判定项目。

## 功能模板

| 功能 | 推荐入口 | 模板 |
|---|---|---|
| 读 OUTCAR 局域磁矩 | Process_Vasp.read_magnetic_moments_outcar | [read_moments.py](examples/read_moments.py) |
| Na-Fe-Mn 经验检查 | Magmom_Function.io.check_magnetic_moments | [check_na_fe_mn.py](examples/check_na_fe_mn.py) |
| INCAR 修改 | 新代码用 Process_Vasp.update_incar/set_incar_tags | [VASP 参数说明](../Process_Vasp/API.md) |

编辑路径后从根目录运行 `python -m Magmom_Function.examples.read_moments` 或 `python -m Magmom_Function.examples.check_na_fe_mn`。模板只读文件，导入不执行。

## 已完成合并

OUTCAR 读取实现迁入 Process_Vasp/magnetism.py，旧路径导出同一函数；POSCAR/OUTCAR 支持压缩文件。Na-Fe-Mn NUPDOWN 估计复用 VASP 的组成函数，目录包装保留一位小数返回。

旧 INCAR 接口仍接受整数 spin、NUPDOWN、NSW，由兼容适配器调用公共编辑器。它保留 CONTCAR→POSCAR 的隐式复制：spin=0 写源目录，spin=1 写目标目录；新代码不要使用该旧接口做只读检查。utils.InitDft_to_TarDft 还会修改输入和重命名调度文件，属于历史批处理，不自动执行。

## 科学限制

读取器保留旧返回 `(elements, [moments], total)`，数据缺失返回 0；total 是 magnetization 表中局域投影之和，不保证等于包含间隙贡献的整体磁矩。解析最后匹配的 x/y/z 表，不能作为 SOC/非共线矢量读取器，数值格式支持有限。

经验检查使用 Fe/Mn 范围和特定 Na-Fe-Mn 价态假设；返回 flag 只是规则是否通过，不是基态/激发态的严格证明。缺失磁矩现在明确报 ValueError。

detect_converge 是旧 out 日志启发式，返回 finished、accuracy_seen、serious_error 三项；完整科学收敛请用 XML 校验，不将其与 Slurm 状态混用。

## 验证

包级 io/utils 导入和新旧读取函数身份检查通过；合成压缩 OUTCAR 验证局域表读取。未验证真实磁性体系或历史批处理。

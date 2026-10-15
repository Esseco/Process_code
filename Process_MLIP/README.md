# Process_MLIP

<!-- Manual project documentation -->

通用 ASE calculator 弛豫工具。默认 py1；具体模型由调用者选择已有专用环境，不在导入时加载模型。

现支持可配置的 MLIP 分子动力学：MACE / SevenNet / CHGNet / ORB，独立或连续 NVT/NPT。
使用 [完整 MD 示例](examples/mlip_md.py) 集中修改模型、加速与阶段参数；接口和超算说明见 [MD.md](MD.md)。
可选 `pre_relax` 在 MD 前只优化原子或同时优化晶胞；函数默认关闭，完整 MD 示例默认全弛豫（原子和晶胞）后直接运行 NVT，预弛豫与 MD 共用同一模型。
NPT 可选 `npt_cell_mode="isotropic"`（默认）或 `"full"`，温控/压控链和积分子步数可按阶段配置。
NVT 轨迹可直接用 `export_msd` 导出整段 MSD CSV，复用 ASE 内置分析；见 [MSD.md](MSD.md) 和 [后处理示例](examples/msd.py)。
完整 MD 示例提供 `MSD_POSTPROCESS` 开关，运行结束后可自动导出指定元素、指定 NVT 阶段的 MSD。
`fit_msd` 独立读取 MSD CSV 拟合扩散系数和估算 Nernst–Einstein 离子导率；两个示例均提供 `TRANSPORT_FIT` 开关与拟合区间、电荷配置，详见 [MSD.md](MSD.md)。

## 独立模板

| 功能 | 输入 → 输出 | 模板 |
|---|---|---|
| 通用 calculator 弛豫 | ASE Atoms + calculator → 弛豫结构、能量、收敛与步数、轨迹 | [ase_relax.py](examples/ase_relax.py) |
| MACE 单结构弛豫 | 结构文件 + 模型 → 最终结构及报告 | [mace_relax.py](examples/mace_relax.py) |
| SevenNet-Omni 单结构弛豫 | 结构文件 + checkpoint + modal → 最终结构及报告 | [sevennet_relax.py](examples/sevennet_relax.py) |

通用模板需实现 make_calculator；MACE 模板使用 Process_MLIP.mace_relax 的公共实现。填写顶部路径后从根目录运行：

```text
python -m Process_MLIP.examples.ase_relax
python -m Process_MLIP.examples.mace_relax
```

两者独立，不要求统一 CLI；模板不覆盖已有输出，导入不执行计算。MACE 需要模型文件和兼容环境，通用模板不是开箱即用的科学模型。

## 原接口与返回值

```python
from Process_MLIP import MLIPRelaxer
result = MLIPRelaxer(atoms.copy(), calculator, fmax=0.05,
                     steps=200, optimizer="BFGS", relax_cell=False).relax(
    traj_file="relax.traj", log_file="relax.log", final_structure="final.extxyz")
```

原有 final_struct、energy、natoms、energy_per_atom、trajectory_file、log_file 保留。新增 optimizer_converged、relax_steps_used、force_max_ev_per_angstrom、energy_unit；能量 eV，力 eV/Å。达到步数上限仍返回结果，必须查看 optimizer_converged，不将函数结束视为收敛。

## 参数与限制

MLIPRelaxer 修改传入 Atoms，并设置 calculator；模板先复制。已有原子约束保留。固定晶胞时使用原子力判断，relax_cell=True 使用 ExpCellFilter，收敛还涉及应力自由度，force_max 不能单独判定晶胞收敛。模型必须支持所需元素、能量/力以及晶胞弛豫所需应力。

底层 relax 默认会写轨迹/日志，直接调用会遵循 ASE 原写入规则；模板用独立目录。Atoms 不能直接写为普通 JSON，需显式转换或写结构文件。现有 MACE 接口与通用接口返回形式不同，暂不强行统一。

## 验证与边界

py1：`python -m unittest Process_MLIP.test_relax`。EMT 小样本验证未收敛标记、真实优化收敛、约束保留及能量归一化；不代表 MACE/CHGNet 科学准确性。两模板安全导入通过，未运行真实模型。

合并候选见 [BOUNDARIES.md](BOUNDARIES.md)，真实签名见 [API.md](API.md)。

## MACE 合并已完成

单结构 MACE 实现现在只保存在 Process_MLIP/mace_relax.py，Process_AL_MC/relax.py 仅兼容导出同一函数。函数签名、默认值、模型 head 选择、晶胞滤波器和报告保持不变；MC 类的委员会弛豫仍独立。

## MH-1 与 SevenNet-Omni

接口、环境、真实模型验证及调用示例见 [MODEL_COMPATIBILITY.md](MODEL_COMPATIBILITY.md)。
本机 MH-1 使用 `py-mace`，Omni 使用已有 `py1`；两环境的 e3nn 版本不同，勿混用。
两者当前均为 CPU PyTorch，调用时显式设置 `device="cpu"`。
`create_mace_calculator` / `create_sevennet_calculator` 也可接入原 `MLIPRelaxer`。

Symmetrix 加速通过 MACE 配置的 `enable_symmetrix=True` 开启，支持 OMat 权重转换或
预转换 JSON、元素裁剪与 Kokkos 选项，和 CuEq 互斥。完整配置见 [MD.md](MD.md)。

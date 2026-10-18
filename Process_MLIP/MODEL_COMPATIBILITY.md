# MACE-MH-1 / SevenNet-Omni 对接

2026-10-15 在本机真实权重验证。保留原 MACE 接口与 Process_AL_MC 兼容导出。

## 环境

| 模型 | 已验证环境 | 关键版本 | 任务 |
|---|---|---|---|
| MACE-MH-1 | py-mace | mace-torch 0.3.14、e3nn 0.4.4、torch 2.9.1+cpu | omat_pbe |
| SevenNet-Omni | py1（原已安装） | sevenn 0.12.0、e3nn 0.5.9、torch 2.9.1+cpu | mpa |

`py-mace` 虽已安装 sevenn 0.12.1，但 e3nn 0.4.4 不满足 SevenNet 的 >=0.5 要求，不能用于 Omni。
不要直接升级这个环境的 e3nn 来迁就 SevenNet：应分别运行两个模型。
本次仅在 py-mace 补装缺失的 orjson 3.13.0，未向 py1 安装依赖。
MACE 加载器在旧 e3nn 导入期间用 PyTorch `safe_globals([slice])` 兼容 constants.pt；
此上下文不会永久增加 allowlist。MACE 自身会设置 `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`，
checkpoint 仅使用可信来源。未修改模型库源码。

## 单结构调用

从仓库根目录、对应环境执行。输入可为结构路径、ASE Atoms、pymatgen Structure。

```python
# py-mace
from Process_MLIP import relax_structure_mace
report = relax_structure_mace(
    "initial.cif", "MLIP_model/mace-mh-1.model",
    device="cpu", head="omat_pbe", default_dtype="float64",
    fmax=0.05, steps=150, relax_cell=True,
    output_path="results/mace_relaxed.vasp",
)
print(report["optimizer_converged"], report["energy_per_atom"])
```

```python
# py1
from Process_MLIP import relax_structure_sevennet
report = relax_structure_sevennet(
    "initial.cif", "MLIP_model/checkpoint_sevennet_omni.pth",
    device="cpu", modal="mpa", fmax=0.05, steps=150, relax_cell=True,
    output_path="results/sevennet_relaxed.vasp",
)
print(report["optimizer_converged"], report["energy_per_atom"])
```

MH-1 文件名包含 mh1、mh-1、mh_1 时自动选 omat_pbe；重命名为其他名称的权重需显式传 head。
显式 head 优先，不强制改变用户选定的 DFT 任务。
SevenNet 默认 `model="7net-omni"`、`modal="mpa"`；也可传本地 checkpoint。
官方模型名首次使用可能下载到 SevenNet 包目录或其缓存；离线计算用已下载的本地路径。
本次权重来自官方发布：
[checkpoint_sevennet_omni.pth](https://github.com/MDIL-SNU/SevenNet/releases/download/v0.12.0.cp/checkpoint_sevennet_omni.pth)。
不向 SevenNet 强行传 MACE 的 float64 参数，沿用其模型 dtype。

可选任务参见 [SevenNet 官方说明](https://sevennet.readthedocs.io/en/latest/user_guide/pretrained.html)。
mpa、omat24、matpes_r2scan 等对应不同训练任务/DFT 设置，不能把不同任务的总能直接拼接计算相稳定性。
MACE 的 omat_pbe 和 Omni 的 mpa 也不等价。

## 接入原 MLIPRelaxer

```python
from Process_MLIP import MLIPRelaxer, create_sevennet_calculator
calc = create_sevennet_calculator(
    "MLIP_model/checkpoint_sevennet_omni.pth", device="cpu", modal="mpa")
result = MLIPRelaxer(atoms.copy(), calc, relax_cell=True).relax(
    traj_file=None, log_file=None)
```

MACE 可用 `create_mace_calculator(model_path, device="cpu", head="omat_pbe")`。
工厂仅在调用时导入模型依赖、加载权重；导入 Process_MLIP 不触发模型计算或下载。

## 输出、副作用与重复运行

两个单结构函数共用 LBFGS / FrechetCellFilter，复制输入 Atoms 并保留约束。
能量 eV、力 eV/Å；结构和晶胞长度 Å。报告含总能、每原子能、力、收敛与优化步数，
分别用 mace_head / sevennet_modal 记录任务。不写轨迹或日志。
给 output_path 时创建父目录并写 VASP 格式，重复运行会覆盖此文件；独立 examples 会拒绝覆盖。
无采样或随机种子参数；重复推断仍可能有设备/数值精度差异。
steps=0 仅求值，不保证收敛。达到步数上限后应读取 optimizer_converged；
晶胞弛豫含应力自由度，不能只看原子力判断收敛。

## 验证证据与边界

`python -m unittest Process_MLIP.tests.test_relax Process_MLIP.tests.test_calculators`
在 py1 的 6 项测试通过；EMT 替代模型覆盖旧导出、head 默认/覆盖、modal 透传、
晶胞优化、输入复制与无效参数。它们不代表科学准确性。

真实模型：ASE `bulk("Si", "diamond", a=5.43)`，2 原子，CPU。
两模型单点能量、力与 6 分量应力均为有限数值；随后 steps=5、fmax=0.05、relax_cell=True：

| 模型任务 | 优化步数 | 收敛 | 最终总能 eV | 最终最大力 eV/Å |
|---|---:|---|---:|---:|
| MH-1 / omat_pbe | 2 | True | -10.8513818991 | 2.09e-14 |
| Omni / mpa | 2 | True | -10.8330745697 | 2.67e-7 |

这些结果仅验证软件对接，不是不同模型精度的对比。
未验证 CUDA、其他 head/modal、大型体系或用户目标材料的精度。

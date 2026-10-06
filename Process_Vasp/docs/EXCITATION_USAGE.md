# 从基态生成激发态输入

```python
from Process_Vasp import generate_excited_input

# 默认 auto：自旋极化时选同通道带隙较小的一侧。
report = generate_excited_input(
    r"E:\calc\ground_static",
    r"E:\calc\excited_static",
)

# 自旋极化：明确指定通道；能带编号从 1 开始。
report = generate_excited_input(
    r"E:\calc\ground_static",
    r"E:\calc\excited_static_up",
    spin="up", valence_band=120, conduction_band=121,
)

# 两个独立激发态计算：目标目录下分别生成 up/ 和 down/。
reports = generate_excited_input(
    r"E:\calc\ground_static", r"E:\calc\excited_both", spin="both",
)
# reports["up"] 和 reports["down"] 是各自的报告。
```

需要基态文件夹中的 INCAR、POTCAR、WAVECAR、CHGCAR、vasprun.xml，以及 KPOINTS（若使用 INCAR 的 KSPACING 则可省略）。兼容单文件 gz/bz2 压缩。WAVECAR/CHGCAR 解压复制，不修改基态文件。

目标目录必须不存在或为空。生成 POSCAR、INCAR、POTCAR、WAVECAR、CHGCAR、KPOINTS（若基态存在）和 excitation.json。此函数只准备输入，不运行 VASP、不生成集群提交脚本。

第一版只支持单 Gamma 点且权重为 1、整数占据的共线基态。仅支持同自旋通道内转移一个电子。ISPIN=1 将目标价带/导带输入占据变为 0.5，代表自旋平均的单电子转移，不是严格纯单重态。自动选带遇到简并时拒绝生成，可明确指定两个能带编号。多 K 点、金属/分数占据、SOC/非共线暂不支持。

`spin="auto"`（默认，None 等价）比较两侧最高占据态到最低空态的能量差，选择较小者，相等时选 up。它比较的是本 Γ 点的同自旋带隙，不是跨自旋的整体带隙，也不是 ΔSCF 激发总能量。即使指定了两个能带编号，auto 仍按带边间隙选通道，然后验证指定编号；both 将同一组显式编号用于两侧，任一侧不合法就拒绝生成。报告中的 channel_gaps_eV 记录比较结果。

可用 up/down 强制选择；both 要求自旋极化，为两套分别激发一个电子的独立输入，不是在一次计算中同时激发两个电子。生成前先验证两侧。两套各有独立 WAVECAR/CHGCAR 副本，磁盘占用相应增加。

继承基态参数并固定原子位置，设置 ISMEAR=-2、ALGO=All、LDIAG=False、ISTART=1、ICHARG=1、NSW=0；实际 NBANDS 来自基态本征值，FFT 网格来自 CHGCAR。保持原来的 VASP 并行配置，避免 VASP 再次调整 NBANDS 导致占据数组长度不匹配。

提交前检查 excitation.json 和 INCAR 中的占据。运行后必须检查实际 NBANDS、最终占据、轨道性质与收敛情况；脚本不能保证指定态始终保持。参考 VASP 版本对 LDIAG 的支持：https://vasp.at/wiki/Delta_self-consistent_field 。

完成后在相同网格上计算 rho_excited - rho_ground；正值为积累，负值为耗尽。基态和激发态都必须来自对应的收敛自洽计算。

验证：py1 中运行 `python -m unittest Process_Vasp.test_excitation`。测试覆盖压缩文件复制、非自旋/自旋占据变化、参数继承及不支持输入的拒绝；使用模拟 XML/CHGCAR 数据，尚未运行真实 VASP。

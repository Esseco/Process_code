# MLIP 分子动力学

统一入口 `run_mlip_md` 支持 MACE、SevenNet、CHGNet、ORB。
内部只初始化一次模型，按顺序执行阶段。NVT 与 NPT 均可独立运行。
沿用你在超算准备的环境，不自动安装、升级依赖或选择 GPU 分区。

## 最简调用

```python
from Process_MLIP import model_config, run_mlip_md

result = run_mlip_md(
    structure="initial.cif",
    model=model_config("mace-mh1", model_path="/path/mace-mh-1.model",
                       enable_cueq=True),
    output_dir="md_results",
    stages=[
        dict(ensemble="nvt", temperature_K=800, steps=10000),
        dict(ensemble="npt", temperature_K=800, pressure_bar=1, steps=20000),
    ],
    timestep_fs=1.0, tdamp_fs=100, pdamp_fs=1000, seed=42,
)
final_atoms = result["final_atoms"]
```

独立 NPT：`run_mlip_md(..., ensemble="npt", temperature_K=800, steps=10000)`，
无需传 stages，也无需先跑 NVT。独立 NVT 同理。
输入支持文件路径、ASE Atoms、pymatgen Structure。Atoms 会复制，不修改调用方结构或速度。
预弛豫默认关闭，可按下节开启；函数不自动扩胞或设置 PBC，由调用者根据材料体系准备。

## 可选预弛豫

`run_mlip_md(..., pre_relax=None)` 或 False 不执行预弛豫，保留原来直接 MD 的行为。
True 使用默认原子位置弛豫；dict 可集中配置：

```python
PRE_RELAX = {
    "enabled": True,               # False 时跳过；省略 enabled 的 dict 默认开启
    "relax_cell": False,           # False 只优化原子；True 同时优化原子和晶胞
    "optimizer": "BFGS",           # BFGS / FIRE / LBFGS
    "fmax": 0.05,                  # eV/Å
    "steps": 200,
    "require_convergence": True,
}
result = run_mlip_md("initial.cif", model=model_config("mace-mh1"),
                     output_dir="prepared_md", pre_relax=PRE_RELAX,
                     ensemble="nvt", temperature_K=800, steps=10000)
```

预弛豫复用原有 MLIPRelaxer 实现，与全部 MD 阶段使用同一个 calculator，
不重新加载模型、不切换 head/modal、dtype 或加速设置。弛豫后的结构直接传入 MD。
静态弛豫不计入 MD 的模拟步数或 time_fs。

只弛豫原子时保持晶胞不变，不要求 calculator 支持应力。
同时弛豫晶胞时使用原 MLIPRelaxer 的 ExpCellFilter（可改变晶胞形状及体积），
要求完整 3D PBC、正体积右手晶胞和应力支持；目标是零外加静态压力，
与 MD 的 pressure_bar 独立。fmax 是 ASE 优化器阈值，晶胞滤波器还包括应力自由度，
不能仅根据最大原子力判定晶胞弛豫收敛。

require_convergence=True 时，步数耗尽仍不收敛会保留弛豫输出并停止整个流程，
不启动 MD。设置 False 可明确允许继续，报告仍保留 optimizer_converged=False。
弛豫失败或返回非有限数据时始终停止，不受此选项影响。
读取 result["pre_relax_result"] 获取优化步数、收敛、能量、最终结构及输出路径；
未启用时此值为 None。

预弛豫不会修改输入 Atoms，也不会重新分配已有 momenta。
没有初速度时，首段 MD 在弛豫结束后按 seed 初始化；有初速度时按原 MD 策略保留。
如希望弛豫后重新采样速度，设置首段 initialize_velocities=True。

## 模型预设

`model_config("预设名", **覆盖参数)` 返回独立的普通 dict。
此时不导入模型、不加载权重、不下载，也不检查路径是否存在；执行时才加载。
未知参数报错，避免把拼写错误静默忽略。

| 预设 | 默认权重/任务 | 默认精度 | 可选项 |
|---|---|---|---|
| mace-mh1 | 仓库 MLIP_model/mace-mh-1.model，head=omat_pbe | float64 | enable_cueq=False |
| sevennet-omni | 官方 7net-omni，modal=mpa | 沿用 checkpoint | enable_flash=False |
| chgnet | 官方 model_name=0.3.0 | 沿用模型 | model_path 可替换权重 |
| orb-v3 | orb-v3-conservative-inf-omat | float32-highest | compile=False |

全部预设默认 device="cuda"，可覆盖为 cuda:0、cpu 等后端支持的设备。
MACE 的 head、SevenNet 的 modal 必须与所需 DFT 设置一致；不同任务不能混用总能。
CHGNet 使用官方 ASE calculator，保留其应力从 GPa 到 eV/Å³ 的换算。
ORB 选择官方 pretrained 架构函数；传本地 model_path 时会作为 weights_path，
必须与 model_name 的架构一致。支持新版 model+adapter API 和旧版 model-only API。

```python
model = model_config("sevennet-omni", model_path="/weights/omni.pth",
                     modal="mpa", enable_flash=True)
model = model_config("chgnet", model_path="/weights/chgnet.pth.tar")
model = model_config("orb-v3", model_path="/weights/orb.ckpt", compile=False)
```

SevenNet/CHGNet/ORB 的 model_path=None 表示使用预训练加载器，可能涉及下载或缓存。
离线超算应提前准备权重，并显式填写本地路径。不提供不存在时换用其他模型的回退。

## 加速与超算

MACE 使用官方 `enable_cueq`，SevenNet 使用官方 `enable_flash`（FlashTP）。
开关默认关闭；显式开启时，所需库/版本/GPU 不满足而产生的错误直接向上传递，
包装层不捕获后静默切回其他模型或后端。
SevenNet 的 `SEVENNET_ENABLE_*` 环境变量可能覆盖 Python False；本加载器拒绝
与显式 FlashTP 选择冲突的环境变量，并提示 unset，避免记录配置与实际选择不一致。
示例使用单进程 ASE calculator；申请多张 GPU 不会自动获得多 GPU MD 加速。
ORB 的 compile 是官方 torch.compile 选项，首次编译可能额外耗时。

本地未安装、调整任何模型环境。CuEq、FlashTP、ORB 编译与四模型真实 GPU MD
需要在你的超算环境另行进行短程验证，不能由参数透传测试替代。

官方接口参考：
[MACE calculator](https://github.com/ACEsuit/mace/blob/main/mace/calculators/mace.py)、
[SevenNet calculator](https://github.com/MDIL-SNU/SevenNet/blob/main/sevenn/calculator.py)、
[CHGNet](https://github.com/CederGroupHub/chgnet)、
[ORB](https://github.com/orbital-materials/orb-models)。

## MD 参数与阶段衔接

参数优先级：阶段参数 > 公共参数 > 函数默认值。

| 参数 | 默认值 | 含义/单位 |
|---|---:|---|
| ensemble | nvt | nvt 或 npt，大小写均可 |
| temperature_K | 300 | 目标温度 K，必须 >0 |
| steps | 1000 | 本阶段积分步数，0 表示只求值/保存初态 |
| timestep_fs | 1 | 步长 fs |
| tdamp_fs | 100 | 温控阻尼时间 fs |
| pressure_bar | 1 | NPT 外压 bar，正值表示压缩 |
| pdamp_fs | 1000 | NPT 压控阻尼时间 fs |
| seed | 42 | 初速度随机数种子 |
| initialize_velocities | None | 初段无 momenta 时初始化，否则保留 |
| remove_com | True | 初始化时去除质心平动 |
| zero_rotation | False | 初始化时去除整体转动，仅允许非周期体系 |
| trajectory_interval / log_interval | 10 / 10 | 写出间隔，单位为步 |
| overwrite | False | 是否覆盖本函数已有输出 |
| time_offset_fs | 0 | 公共累计时间起点 fs |

NVT 使用 NoseHooverChainNVT；NPT 使用 IsotropicMTKNPT，改变体积但不独立改变晶胞形状。
此版本不支持原子约束，遇到约束报错；NPT 必须具有完整 3D PBC、正体积右手晶胞和应力支持。
需要包含这两个积分器的 ASE 版本（本地 ASE 已提供）。
NVT calculator 可不支持应力，此时 pressure_bar 列为空。
日志压力为 `-trace(stress)/3`，包含动能项，并换算成 bar；能量为 eV、体积为 Å³。

阶段衔接默认保留位置、晶胞及 momenta，不因改变目标温度而重新分配速度。
后续阶段只有自身显式设置 initialize_velocities=True 才会重新采样；
公共 initialize_velocities 仅决定首段初始化行为。
新阶段重建温控器与压控器辅助变量，不是严格的恒温/恒压状态断点续跑。
如果保留的初速度全零，会报错而不是静默启动零温动力学。
种子仅控制初速度；不同 GPU/模型精度下不保证逐位复现。
默认步长和阻尼时间是可调起点，不是对所有材料都已验证的物理参数。

## 输出与重复运行

根目录：run_report.json，记录模型配置、全部有效阶段参数、完成阶段及失败信息。
阶段目录：01_nvt、02_npt 等；可用阶段 name 指定后缀。
开启预弛豫后，另有 00_relax，保存 relax.traj、relax.log、final.traj、report.json。
根报告同时记录 pre_relax_parameters 和 pre_relax_result，未收敛不会冒充收敛。

- md.traj：含初帧、定间隔帧及末帧，即使步数不能被间隔整除。
- md.csv：step、累计 time_fs、温度、势能/动能/总能、压力、体积与最大原子力，字段名带单位。
- final.traj：最终结构、晶胞、momenta，可由 ASE read 读回后继续新阶段。
- report.json：有效参数、模型配置、软件版本、实际步数、状态及初末态统计。

默认拒绝覆盖；overwrite=True 只重写本函数拥有的文件，不清理其他文件或旧阶段目录。
不提供断点恢复。阶段文件记录局部 step，time_fs 在连续阶段中累计。
MD 正常结束不表示已达到热平衡；需要另行检查温度/压力/能量/结构统计。
运行中数值非有限或模型报错会终止，并把已创建的报告标记为 failed，保留已写轨迹。
结构/参数/模型加载的预检查失败可能不创建阶段报告。

## 完整示例与验证

编辑 [examples/mlip_md.py](examples/mlip_md.py) 顶部的 INPUT、OUTPUT、MODEL_PRESET、
MODEL_OVERRIDES、MD_PARAMETERS、STAGES。
预弛豫在同一文件的 PRE_RELAX 中修改。
从仓库根目录运行：

```text
python -m Process_MLIP.examples.mlip_md --preview
python -m Process_MLIP.examples.mlip_md
```

preview 不读取结构、不加载模型；完整运行只加载选中的一个模型。
已有 calculator 可直接使用 `run_md(structure, calculator, output_dir, **参数)`。

必要测试使用 py1、ASE EMT 与模型接口替身，不加载四模型权重：

```text
python -m unittest discover -s Process_MLIP -p "test_*.py"
```

覆盖 NVT/NPT 实际短程积分、压力单位与动能项、初末帧、随机种子、速度继承、
单次加载、参数覆盖、输出保护、失败报告、四后端分派及加速开关传递。
预弛豫另覆盖原子/晶胞优化、同一模型复用、MD 继承优化后结构、未收敛处理与初速度策略。

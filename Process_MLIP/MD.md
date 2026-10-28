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
函数的预弛豫默认关闭，可按下节开启；完整 `examples/mlip_md.py` 示例默认先全弛豫（原子和完整晶胞，`enabled=True, relax_cell=True`），收敛后直接运行一个 NVT 阶段。NVT 固定优化后的晶胞，不自动运行 NPT。函数不自动扩胞或设置 PBC，由调用者根据材料体系准备。

## 可选预弛豫

`run_mlip_md(..., pre_relax=None)` 或 False 不执行预弛豫，保留原来直接 MD 的行为。
True 使用默认原子位置弛豫；dict 可集中配置：

```python
PRE_RELAX = {
    "enabled": True,               # False 时跳过；省略 enabled 的 dict 默认开启
    "relax_cell": False,           # False 只优化原子；True 同时优化原子和晶胞
    "optimizer": "FIRE",           # FIRE / BFGS / LBFGS
    "fmax": 0.05,                  # eV/Å
    "steps": 200,
    "maxstep": 0.05,               # 优化步幅上限，Å
    "exp_cell_factor": None,       # None: 按原子数缩放晶胞变量
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
同时弛豫晶胞时使用 FrechetCellFilter（可改变晶胞形状及体积，需 ASE >= 3.23），
要求完整 3D PBC、正体积右手晶胞和应力支持；目标是零外加静态压力，
与 MD 的 pressure_bar 独立。fmax 是 ASE 优化器阈值，晶胞滤波器还包括应力自由度，
不能仅根据最大原子力判定晶胞弛豫收敛。
预弛豫默认 FIRE、maxstep=0.05 Å；exp_cell_factor=None 使用原子数缩放晶胞变量。
maxstep 对不同优化器的范数约束略有不同，不等于晶胞应变百分比上限。
这两项改善更新尺度，不能保证任意模型/初始结构收敛，也不直接修复 CUDA 显存或依赖问题。
报告包含实际 cell_filter、maxstep 和 exp_cell_factor；失败排查请保留 relax.traj。

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
| timestep_fs | None | 自动：NVT 2 fs、NPT 1 fs；显式数值可覆盖 |
| tdamp_fs | 100 | 温控阻尼时间 fs |
| pressure_bar | 1 | NPT 外压 bar，正值表示压缩 |
| pdamp_fs | 1000 | NPT 压控阻尼时间 fs |
| npt_cell_mode | isotropic | NPT 晶胞模式：isotropic / full |
| tchain | 3 | 温控链长度，正整数，NVT/NPT 均使用 |
| pchain | 3 | 压控器温控链长度，正整数，仅 NPT 使用 |
| tloop | 1 | 温控积分子步数，正整数，NVT/NPT 均使用 |
| ploop | 1 | 压控积分子步数，正整数，仅 NPT 使用 |
| seed | 42 | 初速度随机数种子 |
| initialize_velocities | None | 初段无 momenta 时初始化，否则保留 |
| remove_com | True | 初始化时去除质心平动 |
| zero_rotation | False | 初始化时去除整体转动，仅允许非周期体系 |
| trajectory_interval / log_interval | 10 / 10 | 写出间隔，单位为步 |
| overwrite | False | 是否覆盖本函数已有输出 |
| time_offset_fs | 0 | 公共累计时间起点 fs |
| measure_steps_per_second | False | 开启实际 MD steps/s 统计 |

比较运行速度时可设置 `measure_steps_per_second=True`，完整示例中已开启。
每阶段及整次流程的返回值/JSON 报告均包含 `steps_per_second`，关闭时或没有积分步数时为 None。
整次流程按总积分步数除以各段计时之和计算，不直接平均各段速度；
若任一有积分步数的阶段未开启计时，整次流程的速度为 None，已计时阶段仍各自保留速度。
计时仅包围 MD 积分运行，包含观察回调、日志及轨迹写出，
不包含模型加载、预弛豫、初始性质探测和最终结构导出；CUDA 在计时前后同步。
这不是纯模型推断速度测试，也没有额外的预热步数或剔除积分期间可能发生的编译。
比较时应使用相同初始结构/速度、精度、硬件及输出频率。

NVT 继续使用 NoseHooverChainNVT，固定晶胞。
NPT 可选择下列模式，目标外压均为标量 pressure_bar（静水压力）：

| npt_cell_mode | ASE 控制器 | 晶胞自由度 |
|---|---|---|
| isotropic（默认） | IsotropicMTKNPT | 等比例缩放体积，保持晶胞形状 |
| full | MTKNPT | 允许体积、不同晶轴及晶胞形状/角度变化 |

```python
STAGES = [
    dict(ensemble="nvt", temperature_K=800, steps=1000),
    dict(ensemble="npt", npt_cell_mode="full", temperature_K=800, steps=5000,
         tchain=3, pchain=3, tloop=1, ploop=1),
]
```

五项参数均可放在公共参数或各阶段中，仍然遵循阶段覆盖公共参数的规则。
npt_cell_mode、pchain、ploop 在 NVT 中不参与动力学；NVT 仍保持晶胞不变。
full 会开放剪切/角度自由度，并非仅改变三个晶轴长度；本接口未提供选定轴/角度约束。
温控/压控链长度及积分子步数严格要求正整数，不能用 0 关闭控制器。
默认 3/3/1/1 沿用 ASE 默认值，增加子步数不等于增加输出的物理 MD 步数。

此版本不支持原子约束，遇到约束报错；NPT 必须具有完整 3D PBC、正体积右手晶胞和应力支持。
所选模式必须由运行环境的 ASE 提供；缺少 MTKNPT 时，选择 full 会在模型加载及计算前报错，
不会安装依赖或静默退回 isotropic。本机 py1 缺少 full MTKNPT，已有 py-mace 的 ASE 3.27.0 提供该实现。
模式和链参数会写入有效 parameters，实际积分器类名记录在每阶段的 md_controller 字段。
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
python -m unittest discover -s Process_MLIP/tests -t . -p "test_*.py"
```

覆盖 NVT/NPT 实际短程积分、压力单位与动能项、初末帧、随机种子、速度继承、
单次加载、参数覆盖、输出保护、失败报告、四后端分派及加速开关传递。
预弛豫另覆盖原子/晶胞优化、同一模型复用、MD 继承优化后结构、未收敛处理与初速度策略。
控制器测试覆盖模式选择、链参数透传、默认向后兼容、参数校验、阶段覆盖与缺失实现报错。
真实 EMT 柔性晶胞积分测试会在支持 MTKNPT 的 ASE 中执行，不支持时明确跳过；
本次在已有 py-mace 环境完成了此实测，未加载模型权重或调整环境。

## MSD 后处理

固定晶胞 NVT 的 `.traj` 可用 `export_msd` 导出多时间起点平均 MSD CSV，后端仅使用 `pymatgen-analysis-diffusion`。
原调用和列名不变，time 为 lag，按原生 max 模式选取约 1 ps 起的时间间隔；短轨迹可能不足以分析。
见 [MSD.md](MSD.md) 和 [examples/msd.py](examples/msd.py)，无需重新加载模型。
完整 MD 示例也可通过 `MSD_POSTPROCESS` 开关在运行结束后自动导出所选 NVT 阶段的 MSD。
元素、阶段序号/最后 NVT、CSV 路径、跳帧、min_obs、框架漂移及覆盖策略均可在同一配置区修改。

## MACE 的 Symmetrix 后端（超算可选）

Symmetrix 是独立的 ASE calculator，不是 MACECalculator 的一个 CUDA 开关。
本项目按 [官方 ASE 接口](https://github.com/wcwitt/symmetrix/blob/main/symmetrix/source/symmetrix/symmetrix_calc.py)
接入，不安装依赖、不修改权重。配置默认关闭，不能和 CuEq 同时开启。

```python
from Process_MLIP import model_config, run_mlip_md
model = model_config(
    "mace",
    model_path="/cluster/models/mace-omat-0-medium.model",
    head=None,                         # OMat 单头；不要沿用 MH1 的 omat_pbe
    device="cpu",
    default_dtype="float64",
    enable_cueq=False,
    enable_symmetrix=True,
    symmetrix_use_kokkos=False,
    symmetrix_species=["Na", "Ni", "Mn", "O"],  # 改成体系真实元素
)
result = run_mlip_md(
    "initial.cif", model=model, output_dir="omat_symmetrix",
    pre_relax={"enabled": True, "relax_cell": False},
    stages=[{"ensemble": "nvt", "steps": 10000}],
    temperature_K=800, measure_steps_per_second=True,
)
```

完整 `examples/mlip_md.py` 的 MACE 配置区也提供以上开关。独立
`create_mace_calculator`、`relax_structure_mace` 同样接受这些参数。
预弛豫和连续 MD 只创建一次 Symmetrix calculator。

- `symmetrix_use_kokkos=False`：原生 CPU，实现要求 float64、device="cpu"。
- `True`：使用安装时编译的 Kokkos 目标，可能是 CPU OpenMP，也可能是 CUDA；
  float32/float64 均由官方接口处理。`device` 不会改变 Kokkos 的编译目标；必须和超算的
  构建匹配。当前封装仅接受 cpu/cuda，不接受 cuda:序号；GPU 可见性由运行环境设置。
- `.model` 输入会调用官方 `extract_mace_data`，并生成临时 JSON，初始化后清理；
  `run_mlip_md` 和 `relax_structure_mace` 在 `symmetrix_species=None` 时根据输入结构自动选择元素；
  benchmark 则选取本次结构的元素并集。直接调用 `create_mace_calculator` 时没有结构信息，
  因而 `symmetrix_species=None` 仍会转换所有训练元素，建议显式指定元素。
  转换不计入现有 MD steps/s。转换器可能用样条近似，正式生产前应对比标准 MACE 的
  能量、力和应力，并检查所需精度。
- 官方转换器对模型层数、球谐阶数和相互作用模块有兼容性限制，错误会直接传播；
  不静默改回标准 MACE，不保证任意 OMat/MH1 模型都支持。
- 超算重复运行建议先用官方工具导出 JSON，例如
  `symmetrix_extract_mace mace-omat-0-medium.model --atomic-numbers 8 11 25 28`，
  然后把 model_path 改为生成的 JSON，并设置 head=None、symmetrix_species=None。
  JSON 已固定元素与 head，运行时不能再选；此加载分支无需导入 Torch/MACE。
- 当前开发机没有安装 Symmetrix；测试使用 ASE EMT 替代验证传参与工作流，实际
  OMat 推理、Kokkos/GPU 和性能提升需要在已安装 Symmetrix 的超算上验证。

## NEP CPU/GPU 与原生 GPUMD MD

NEP 通过 `model_config("nep", model_path=..., backend="cpu"|"gpu")` 接入统一 `run_mlip_md`。CPU 后端为 Calorine `CPUNEP`，GPU 后端为 `GPUNEP`；缺失依赖或 GPUMD 可执行文件直接报错。长时间 GPU 运行使用 `run_nep_md()` 的原生 GPUMD 输出，保留 `thermo.out`、`dump.xyz` 等文件，不冒充 ASE `md.traj`。

```python
from Process_MLIP import run_nep_md
report = run_nep_md(
    "initial.cif", "/weights/nep.txt", "nep_gpu_run",
    parameters={"velocity": 800, "dump_thermo": 100,
                "dump_xyz": [100, "movie.xyz"],
                "ensemble": ["nvt_lan", 800, 800, 100], "run": 50000},
    executable="gpumd",
)
```

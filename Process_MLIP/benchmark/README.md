# MLIP Speed / Ehull Benchmark

这是 `Process_MLIP` 的独立 benchmark 子包。Windows 的大小写规则下，
`process_mlip` 与已有 `Process_MLIP` 是同一目录；保留原目录和原有接口。
仅复用模型加载、ASE 弛豫器和 MD；不引入训练、QBC、主动学习或 DFT 提交。

## 环境与运行

默认使用已有 `py1` 验证基础功能。运行真实模型时切换到该模型已有专用环境；
不要把所有模型依赖装到 py1。不执行自动安装或静默切换模型。
基础依赖见 `requirements.txt`；真实模型依赖按原项目 [模型兼容说明](../MODEL_COMPATIBILITY.md)。

在 `E:\Py-Code` 仓库根目录执行：

```powershell
# 生成可运行的合成 Cu/Au 演示；EMT 不是预训练 MLIP。
python -B -m Process_MLIP.benchmark.examples.make_demo E:\benchmark_demo --quick
python -B -m Process_MLIP.benchmark validate E:\benchmark_demo\demo.yaml
python -B -m Process_MLIP.benchmark speed E:\benchmark_demo\demo.yaml
python -B -m Process_MLIP.benchmark ehull E:\benchmark_demo\demo.yaml
```

不带 `--quick` 的演示生成 1000 步 MD 配置；`--quick` 明确改为 20 步，仅用于检查流程。
生成器拒绝覆盖现有目录。正式使用复制 [models.yaml](examples/models.yaml)，填写自己的路径、模型和结构。
配置里的相对路径均以 YAML 所在目录为基准。结构由 ASE 读取，支持 CIF、POSCAR、extxyz、traj 等；
每项 `index` 默认为 -1，明确选择一个帧；输入必须是无固定约束、满秩晶胞的三维周期结构。
结构 ID 和模型 ID 在各自列表内唯一（忽略大小写），只能使用文件安全的字母、数字、点、横线和下划线。

## YAML 配置

```yaml
output_dir: ./results
seed: 42
models:
  - id: my_mace
    type: mace
    device: cuda:0
    parameters:
      model_path: ./weights/mace.model
      head: omat_pbe
      default_dtype: float32
structures:
  - {id: Li, path: ./structures/Li.cif}
  - {id: Co, path: ./structures/Co.cif}
  - {id: O, path: ./structures/O.cif}
  - {id: LCO, path: ./structures/LiCoO2.cif}
relax: {fmax: 0.1, steps: 2000, maxstep: 0.2}
md: {temperature_K: 800, timestep_fs: 2, steps: 1000, tdamp_fs: 100,
     trajectory_interval: 10, log_interval: 10}
ehull: {reference_csv: null, tolerance_eV_per_atom: 0.000001}
```

`relax`、`md`、`ehull` 可以省略，采用上述默认值。温度 K、时间 fs、能量 eV，
力 eV/Å，距离 Å。MD 1000 × 2 fs = 2 ps。配置未知键、非有限数、非正步数等明确报错。
`validate` 仅校验配置/文件路径并输出解析配置，不加载模型、不创建计算结果；
结构元素支持性、应力和端元完整性在运行时检查。

Benchmark 可配置的模型精度默认 FP32：MACE 为 `default_dtype: float32`，
ORB 为 `precision: float32-highest`（保持最高 FP32 矩阵乘精度，不自动启用 TF32）。
显式配置优先；没有精度参数的现有 Adapter 沿用模型本身精度，不虚构参数或隐式转换权重。
Symmetrix 使用 FP32 需要 Kokkos；不支持时明确报错，不自动切换 FP64。

### 模型支持

| type | 当前状态 | parameters 要点 |
|---|---|---|
| mace | 复用现有工厂 | 本地 model_path、head、default_dtype、enable_cueq、enable_symmetrix |
| sevennet | 复用现有工厂 | model_path 或 model_name、modal、enable_flash |
| orb | 复用现有工厂 | model_name、可选 model_path、precision、compile |
| chgnet | 复用现有工厂 | model_name 或 model_path |
| nep | 复用现有 CPU 工厂 | model_path、backend: cpu |
| emt | ASE 演示/测试 | 仅 CPU，不用于评判 MLIP 科学精度 |
| grace / mattersim / nequip | 待实现 | 清楚报错，不以其他模型替代 |

模型可能按其官方库的命名预训练接口下载权重；建议正式复现采用本地 checkpoint。
参数沿用原 `model_config` 约定，不自动把不同 head/modal 的能量混用。
各 calculator 必须提供 ASE 标准 energy、forces、stress，含 free_energy 的需求由现有弛豫器/模型接口决定。
NEP 的外部 GPUMD GPU 后端不能用当前进程 torch 的计时/显存接口衡量，因此本版明确拒绝该组合。

## Speed：弛豫与 MD 分开比较

所有模型读取同一结构；原子数以读取的实际结构为准，不按文件名推断。

1. **加载**：每模型每次执行加载一次，在 `load.json` 与 `load.csv` 记录耗时及环境。
2. **预热**：每个待计算结构做一次能量、力、应力调用并清空 ASE 结果缓存。
   首次结构的预热反映该模型首次推理开销；不同尺寸的后续预热也单独记录。
3. **弛豫**：在输入副本上执行 LBFGS + FrechetCellFilter，优化原子和晶胞。
   记录独立总耗时、步数、收敛、最大原子力、力评估数、显存，保存轨迹、日志和优化结构。
   力评估数定义为 ASE 包装层未缓存的力请求数，不声称等于底层神经网络前向次数。
   计时含优化器轨迹/日志和末态属性提取，不含最终 extxyz 导出。
   晶胞自由度也参与收敛判定，不能只看最大原子力。
4. **MD**：从同一原始输入的新副本开始，与弛豫独立，固定晶胞 NHC NVT。
   所有模型用相同 seed 重建 Maxwell–Boltzmann 初速度并去除质心平动。
   仅计现有 `run_md` 的 `dyn.run` 耗时，包括统一的观察器、日志和轨迹开销；
   排除加载、预热、初始化、初始属性探测与最终导出。另存 `stage_wall_seconds` 供排查。
   输出实际步数、steps/s、模拟时间和异常。失败积分保留实际完成步数；
   当前底层接口不提供失败时精确积分耗时，`elapsed_seconds` 为 null，不以外层时间冒充。

CUDA 在计时开始和结束前同步，按阶段重置峰值计数。显存输出为同一进程
**torch allocator peak allocated/reserved MiB（含驻留模型）**，不是整卡显存，
不覆盖外部进程及非 PyTorch 内存。CPU 对应字段为 null。MD 峰值覆盖该阶段设置及运行，
时间字段只覆盖积分。800 K、2 fs 的默认参数是效率测试设置，不保证适合所有材料的稳定积分。

分别输出 `speed/relax.csv`、`speed/md.csv`、对应 JSON 和各指标随原子数变化的曲线。
同原子数不同结构保留各个数据点，不擅自平均；非收敛弛豫保留收敛标志，比较时应筛选。

## Ehull：仅使用你给的结构

每个模型独立对全部结构做同一全弛豫，用**整胞总能 eV + 整胞真实元素计数**构建
pymatgen `PhaseDiagram`，由库统一归一化，结果为 **eV/atom**。
不同大小超胞和同组成多态保留独立 ID，不把每原子能量误当整胞能传入。
不使用固定骨架、SOC 坐标或脱嵌路径；不做能量校正、元素化学势拟合或自动检索竞争相。

标准组成凸包要求所有元素都有用户提供的元素端元结构。例如 Li–Co–O 凸包至少需要
Li、Co、O 元素端元，加上需要比较的化合物和竞争相。缺端元时在加载模型前明确报错。
只提供不同 Li 含量的 Li–Co–O 化合物，不能在本模式中构建完整标准组成凸包。
所有输入结构都参与竞争；某结构失败或未收敛，则该模型不输出有效 Ehull 表。
输出相对于**输入竞争相集合**，缺少实际竞争相会低估 Ehull，端元齐全并不证明竞争相完备。

DFT 参考 CSV 格式：

```csv
id,ehull_eV_per_atom
LCO,0.012
```

设 `ehull.reference_csv` 后按 ID 精确匹配，不按化学式合并。参考为非负、有限的 eV/atom，
不再二次归一化。允许部分匹配，明确报告覆盖率、缺失/多余 ID；零交集、重复 ID 和非法值报错。
报告 MAE、RMSE、Bias（预测减参考），以及匹配集合内稳定 ID、TP/FP/FN/TN、precision/recall；
稳定判据为 `Ehull <= tolerance_eV_per_atom`，默认 1e-6。
没有 DFT 参考时照常输出预测凸包，但不生成伪造的误差指标。

保存 `ehull/<model>/ehull.csv/json`、`metrics.json`（有参考时）、`phase_diagram.json`、
相图 PNG 和按 ID 的 Ehull 对比图，及跨模型 `comparison.csv/json`。
相图 PNG 支持 1–4 元素；更高维保存完整相图 JSON 与 Ehull 图，并在状态报告说明绘图限制。
每个原始阶段的弛豫报告与结构保存在 `<mode>/<model>/<structure>/relax/`。

## 批量、恢复与跨环境

```powershell
# 同一个 YAML，分别在相应模型环境运行；其他模型的已保存结果参与最终汇总。
python -B -m Process_MLIP.benchmark speed benchmark.yaml --model my_mace
python -B -m Process_MLIP.benchmark speed benchmark.yaml --model sevennet_mpa
```

可重复指定 `--model`；不指定则尝试所有模型。各模型串行运行，避免彼此争抢 GPU。
单模型或单结构异常不终止其他计算，失败阶段保存错误/日志；正常失败退出码为 1，
配置/输入错误为 2。`summary.json` 中的失败计数覆盖当前已记录结果；未选择且从未计算的模型
不算失败；`status: partial` 和 `stages_missing` 明确说明整个配置尚未跑完。

重复运行默认按完整阶段恢复：成功阶段且末态结构哈希一致时跳过，失败阶段重跑。
不会从中断的 LBFGS Hessian 或 NHC thermostat 内部状态继续；中断阶段从输入重跑，
仅覆盖本 benchmark 拥有的该阶段文件。预热在每次重新加载模型后对待跑结构重做。
`manifest.json` 记录配置、输入/checkpoint/参考文件 SHA256 和实现源码 SHA256。
任一改变要求换新 `output_dir`，避免混用结果。各阶段存模型配置、软件版本、Python 路径、
GPU/驱动信息及 CUDA_VISIBLE_DEVICES；命名预训练权重未指定本地路径时无法由本项目哈希其下载缓存。

输出锁防止多进程同时写；如进程强杀留下 `.benchmark.lock`，先确认原任务已经退出再手动删除锁。
无 manifest 的非空目录拒绝使用。源结构、模型及其他项目数据不移动、不删除。

## 扩展与验证

```python
from Process_MLIP.benchmark import register_model
from Process_MLIP.benchmark.runner import run_benchmark

def load_my_model(config):
    # 延迟导入模型库，遵守 config['device']，返回 ASE calculator。
    from my_model import MyCalculator
    return MyCalculator(device=config['device'], **config['parameters'])

register_model('my_model', load_my_model)
run_benchmark('benchmark.yaml', 'speed')
```

只扩展工厂/Adapter，不修改 Benchmark 核心。自定义工厂实现不属于自动源码哈希范围，
应自行固定版本并在参数中明确 checkpoint；模型特定的单位/应力转换由 Adapter 负责。

```powershell
python -B -m unittest Process_MLIP.benchmark.tests.test_benchmark -v
```

测试使用 `TemporaryDirectory` 合成小结构并自动清理，不复制正式计算。
在临时目录受限的沙箱中，可将进程 `TMP`/`TEMP` 指向一个可写目录后运行。
覆盖真实 EMT 全弛豫/NVT/Ehull 流程、解析凸包、归一化、错误参考、恢复、失败重跑、
配置/checkpoint 变化、计时范围与 CUDA 接口顺序；CUDA 测试采用替身，不等于真实 GPU 验证。

# 弛豫 → NVT → MSD：八组超算脚本

每个编号文件夹包含约 40 行的 run_md.py 和 submit.sh。运行脚本顶部直接修改：
- PROJECT_ROOT：超算上的 Py-Code 根目录（包含 Process_MLIP）。
- STRUCTURES：依次读取八个文件夹同级的 LCO.vasp、NVP.vasp，每个模型都运行这两个结构。
- MODEL_PATH：自行填写相应模型路径，加速组和基线组使用相同权重。
- PRE_RELAX：默认 FIRE all 弛豫（原子+完整晶胞），未收敛则停止。
- MD：默认 600 K、2 fs、5000 步 NVT（10 ps）、seed=42，轨迹和日志每步输出；记录 steps/s。
- MSD：默认开启，species 字典指定 LCO 的 Li、NVP 的 Na。

进入对应文件夹执行 sbatch submit.sh 即可，一个任务顺序运行两个结构，不并发争抢 GPU。结果分别写在该文件夹 results/LCO/ 和 results/NVP/：
00_relax/ 保存弛豫轨迹和结构；01_nvt/ 保存 MD 轨迹、日志、最终结构；msd.csv 为 MSD。
每个结构内部模型只初始化一次，弛豫与 MD 共用；处理下一个结构时重新创建 calculator。steps/s 不包含弛豫、加载和 MSD 后处理。
MSD 默认仅用 pymatgen-analysis-diffusion 的 max 多时间起点平均，CSV 列保持不变，time 为 lag；运行后处理的环境需该包，也可关闭开关后在独立分析环境处理轨迹。本次不安装或修改模型环境。
不同模型独立弛豫后晶胞/位置可能不同；如需完全相同几何的速度对比，可统一设置 PRE_RELAX=False。

| 文件夹 | 环境 |
|---|---|
| 01_mace_mh1 | mace_cueq |
| 02_mace_omat | mace_cueq |
| 03_mace_omat_sym | mace_cueq |
| 04_sevennet_omni | sevennet_flash |
| 05_sevennet_omni_flash | sevennet_flash |
| 06_sevennet_nano6 | sevennet_flash |
| 07_sevennet_nano6_flash | sevennet_flash |
| 08_chgnet | python |

提交脚本沿用 北京超算GPU.sh 的 v100m3、1 GPU、32 GB、CUDA 12.8 等设置。
MACE 基线关闭 CuEq；Symmetrix 默认 Kokkos CUDA，CPU 安装需改 DEVICE="cpu"、symmetrix_use_kokkos=False。
不安装环境、不自动提交；不重复覆盖结果，重跑可更换 OUTPUT。八组用零力 calculator 验证弛豫/MD/真实 pymatgen MSD 衔接，真实模型与超算尚未运行。
根目录 collect_results.py 可汇总默认 results/ 的 steps/s。legacy_scripts/ 为以前的简化入口，保留备份。

MACE（含 Symmetrix）显式使用 float32；SevenNet/CHGNet 保持原生精度，没有添加不支持的 dtype 参数。其余省略参数沿用库默认值（例如 NVT 步长 2 fs、seed=42）。

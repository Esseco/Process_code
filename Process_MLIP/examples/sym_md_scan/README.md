# MACE-OMat + Symmetrix：温度与时长测试

六组独立任务，每组按顺序处理上一级 LCO.vasp 和 NVP.vasp。
每个结构执行 FIRE 全弛豫 → NVT → MSD；分别统计 LCO 的 Li、NVP 的 Na。
沿用原模型路径、float32、Kokkos、mace_cueq 环境和 V100 提交资源。

| 任务文件夹 | 温度 / K | NVT 时长 / ps | 步长 / fs | MD 步数 |
|---|---:|---:|---:|---:|
| sym_500K_30ps | 500 | 30 | 2 | 15000 |
| sym_700K_30ps | 700 | 30 | 2 | 15000 |
| sym_900K_30ps | 900 | 30 | 2 | 15000 |
| sym_700K_10ps | 700 | 10 | 2 | 5000 |
| sym_700K_50ps | 700 | 50 | 2 | 25000 |
| sym_700K_70ps | 700 | 70 | 2 | 35000 |

700 K / 30 ps 同时属于两组扫描，仅运行一次。时长只计 NVT，不包括弛豫。
每个文件夹都有 run_md.py、submit.sh 和 README.md；进入任务目录后 sbatch submit.sh。
run_md.py 顶部可修改 TEMPERATURE_K、DURATION_PS、TIMESTEP_FS；步数自动换算。
默认每步输出轨迹与日志，不覆盖已有结果。结果保存在各任务 results/LCO/、results/NVP/。
MSD 输出 msd.csv，MD 吞吐和实际模拟时间在 run_report.json 中。
MSD 自动使用 pymatgen-analysis-diffusion 的 max 多时间起点平均；CSV 列不变，time 为 lag，约从 1 ps 起取样。运行分析的环境需该包；也可先关闭 MSD，在独立分析环境处理轨迹，无需调整模型环境。

这些是相互独立的运行：不同温度/时长不续接旧轨迹，每组从同一输入结构重新弛豫。
900 K、2 fs 的稳定性及扩散收敛仍需检查实际轨迹；本地测试不代表生产模型验证。
使用已更新的 Process_MLIP（FrechetCellFilter、预弛豫默认 maxstep=0.05 Å）。
原始结构文件和旧八组任务不会被改动；只新增本次六个文件夹。

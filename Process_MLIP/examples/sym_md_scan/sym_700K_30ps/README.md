# sym_700K_30ps

每个结构先 FIRE 全弛豫，再运行 700 K、30 ps NVT（2 fs，15000 步），最后导出 MSD。
从上级读取 LCO.vasp / NVP.vasp，分别统计 Li / Na。
结果在本文件夹 results/LCO/ 和 results/NVP/。检查 run_md.py 路径后执行 sbatch submit.sh，使用 mace_cueq 环境。

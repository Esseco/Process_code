# 03_mace_omat_sym

编辑 run_md.py 顶部的库路径、结构路径、模型路径和参数，然后 sbatch submit.sh。
默认 FIRE all 弛豫（原子+完整晶胞）→ 600 K、5000 步 NVT（每步输出） → MSD，结果保存在 results/。
MSD 的 species=None 输出所有元素，可改 Na、Li 或元素列表。

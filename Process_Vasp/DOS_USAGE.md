# DOS 读取与 CSV 导出

输入文件夹需要 `vasprun.xml`。默认输出总 DOS 和各元素 DOS；需要 VASP 输出包含投影 DOS（例如 LORBIT=11）。开启 IPR 还需要 `PROCAR`。

支持 atomate2 的 `vasprun.xml.gz`、`INCAR.gz` 和 `PROCAR.gz`，直接读取，无需提前解压；原文件和压缩文件同时存在时优先读取原文件。也支持读取库可识别的 bz2 压缩文件。这里支持单文件压缩，不支持整个目录的 zip/tar 归档。

```python
from Process_Vasp import read_dos

result = read_dos(r"E:\calculations\FeO\dos")
print(result["NEDOS"], result["kpoint_mesh"], result["kpoint_density"])
df = result["df"]
df.to_csv(r"E:\calculations\FeO\dos\dos.csv", index=False)

# 也可以读取时直接导出，并开启每个元素的 s/p/d/f 轨道分波。
result = read_dos(
    r"E:\calculations\FeO\dos",
    output_csv=r"E:\calculations\FeO\dos\dos_spd.csv",
    include_orbital=True,
)
```

选项：`include_element=True`、`include_total=True`、`include_orbital=False`、`read_ipr=False`、`ipr_sigma=None`、`shift_fermi=True`、`mirror_spin_down=False`。这些是函数参数，没有图形界面。

`df` 仅包含数值列：`energy`（eV）、`dos_up/down`、`Fe_up/down` 等；轨道选项增加 `Fe_s_up/down` 等实际存在的轨道列。非自旋极化计算只有 up 列。默认能量为 E−E_F，自旋向下保留正值；镜像选项将向下 DOS 取负，IPR 保持不变。DOS 保留 pymatgen 读取的原始单位与数值，不做每原子归一化。

返回字典包含：

- `NEDOS`：优先读取文件夹中的 INCAR；缺失时读取 XML 记录的 INCAR。两者都未设置时为 None，不将默认参数冒充 INCAR 设置。DataFrame 的实际行数以 DOS 能量网格为准。
- `kpoint_mesh`：XML 记录的规则网格尺寸，例如 `(6, 6, 6)`。
- `kpoint_density`：KPPRA，定义为完整网格点数乘结构原子数。显式 K 点或线模式无法获得规则网格时为 None。
- `nkpoints`：XML 中实际计算的 K 点数，通常已做对称性约化，不能代替完整网格点数。
- `KSPACING`：INCAR 中的设置（若有），单位 Å⁻¹；与 KPPRA 是不同概念。
- `efermi`、`path`、`composition` 和 `df`。

接口变更：`read_dos` 现在返回 dict，原先直接接收 DataFrame 的调用应改为 `read_dos(folder)["df"]`。省略 `output_csv` 不再自动写入 dos.csv，需显式导出。

验证：在 py1 环境运行 `python -m unittest Process_Vasp.test_dos`。

# 本地 MACE / GEMDAT / kinisi 运行环境

使用 `MD_Screening_Workflow/.venv/Scripts/python.exe`，不切换全局PATH，不向py1安装包。

本机新venv以已有py-mace Python 3.12为基底，`--system-site-packages`只读复用PyTorch 2.9.1、MACE 0.3.14、e3nn 0.4.4和NumPy 2.2.6。新增包仅安装到.venv；因此它依赖原py-mace继续存在，并非完全独立的环境副本。正式workflow默认使用CUDA；当前这份验证环境本身是CPU版，不能执行GPU短测。py1仍是默认开发环境。

`requirements.txt`固定新增分析依赖；`constraints.txt`保护现有模型栈。旧pymatgen-analysis-diffusion 2024.7.15要求NumPy<2，与kinisi不兼容，本环境使用2025.11.15。Symmetrix不是当前requirements中的纯Python依赖；GPU路线需使用已编译CUDA/Kokkos的Symmetrix安装，并在配置中同时设置`enable_symmetrix=True`和`symmetrix_use_kokkos=True`。

## 重建与使用

以下在workflow目录运行；替换基础Python和模型路径为本机实际路径。不要对已有环境使用`--clear`。

```powershell
& 'C:\ProgramData\anaconda3\envs\py-mace\python.exe' -m venv --system-site-packages --without-pip .venv
& .\.venv\Scripts\python.exe -m pip --require-virtualenv install -r environment\requirements.txt -c environment\constraints.txt
# PYTHONPATH must contain the Process_MD project root, e.g. E:\Py-Code\Process_MD
& .\.venv\Scripts\python.exe -m pip --require-virtualenv install --no-deps --no-build-isolation -e 'E:\Py-Code\Process_MD' -e .
& .\.venv\Scripts\python.exe -B tools\check_runtime.py
& .\.venv\Scripts\python.exe -B examples\mace_smoke.py --model-path 'E:\Py-Code\MLIP_model\mace\mace-omat-0-medium.model' --output-dir runs\mace_omat_smoke
```

`--without-pip`复用基底的pip模块；`--require-virtualenv`保护误装基础环境。`PYTHONPATH`应包含`Process_MD`项目根目录（即包含`process_md/`和`pyproject.toml`的目录），父目录`E:\Py-Code`本身不够。若运行于临时目录受限的沙箱，给pip的TEMP/TMP指定项目内TemporaryDirectory，退出后清理。模型使用现有本地文件，不下载。旧Process_MLIP须可导入；本机由已有py-mace路径配置提供。

GPU Symmetrix 示例：

```powershell
& ".\.venv\Scripts\python.exe" examples\run_case.py `
  "D:\structures\POSCAR" "runs\material_A" `
  --reference-sites "D:\structures\POSCAR_FULL" `
  --species Li --device cuda --enable-symmetrix --symmetrix-use-kokkos
```

Windows editable构建可能超过260字符路径上限，必要时使用较短的系统临时路径并在结束后清理。`check_runtime.py`检查本路线93个依赖、GEMDAT/kinisi API、py1与py-mace原安装清单，写 `.venv/runtime-check.json`。完整`pip check`仍报告基础py-mace原有的可选包告警（boto3/botocore/mypy/sshtunnel缺依赖，SevenNet要求另一版e3nn）；工具验证没有新增告警。本环境供MACE路线，不为消除无关告警而升级模型栈。

## 短测的边界

使用已有ASE LiF示例的8原子晶体。晶格4.0 Å来自少量MACE能量扫描，不是精确优化。CPU设置2线程，真实1 fs步长；初检0.1 ps，每0.6 ps分析，生产最多1.8 ps、总计1.9 ps。缩短窗口只验证接口，正式默认5 ps+10 ps/200 ps保持不变。

小晶胞中的F-F距离超出默认RDF半径，因此只在RDF分析中重复周期像2×2×2，MD仍为8原子；不会增加独立采样或证明尺寸收敛。GEMDAT保留原生0.2 ps驻留过滤，kinisi不在每个MD检查点运行。

运行结果保留一份 `runs/.../smoke_summary.json`、完整短轨迹、检查报告与CSV。普通验证的临时目录会清理。基础环境安装清单指纹位于 `.venv/base-environment-before.json`，交付前复核py1及py-mace未变化。

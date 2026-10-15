# 同一结构的 8 组 MLIP NVT 速度对比

将本文件夹整体上传到超算；它需要已有的 Py-Code/Process_MLIP 库。
先修改 benchmark_config.py：PROJECT_ROOT、STRUCTURE、MODEL_PATHS。
所有组共用同一个结构文件，每组重新用 seed=42 初始化速度，800 K、1 fs、5000 步（5 ps）。
直接 NVT，不做弛豫；没有 MSD/导率后处理。输出间隔相同，默认不覆盖已有结果。

运行对应脚本时，先激活支持该模型/加速库的超算环境：

```bash
python 01_mace_mh1.py
python 02_mace_omat.py
python 03_mace_omat_sym.py
python 04_sevennet_omni.py
python 05_sevennet_omni_flash.py
python 06_sevennet_nano6.py
python 07_sevennet_nano6_flash.py
python 08_chgnet.py
```

每个脚本都支持 --preview，无需模型或 Process_MLIP 即可预览配置。
不自动激活环境、不安装依赖、不自动提交作业。可将对应 python 命令放入已有调度脚本。
建议逐个独占相同资源运行，避免相互争抢 CPU/GPU 影响 steps/s。

每组输出在 results/<case>/：run_report.json 和 01_nvt/ 下的轨迹、日志、最终结构与报告。
steps/s 包含 MD 内的输出和每步检查，排除模型加载、Symmetrix 转换与初始检查。
未单独去除首次 MD 内的编译开销；5000 步是本次统一对比长度，不代表扩散性质已经收敛。

汇总已运行结果（不会重新计算）：

```bash
python collect_results.py > comparison.csv
```

MACE 两个标准组关闭 CuEq，float64。MH1 使用 omat_pbe，OMat 使用单头默认值。
OMat 和 OMat+Symmetrix 共用同一个原始 .model 路径；Symmetrix 自动从结构提取元素列表。
Symmetrix 默认 Kokkos CUDA；必须与安装时的构建匹配。若是原生 CPU 安装，设置
SYMMETRIX_DEVICE="cpu"、SYMMETRIX_USE_KOKKOS=False。device 不会改变 Kokkos 编译目标。
跨 CPU/GPU 结果仅代表所用硬件配置下的吞吐，不应解释为纯后端加速比。
如需预转换 JSON，可在 runner 中为 Symmetrix 单独指定路径；普通 MACE 组仍需 .model。
SevenNet 每对共用相同 checkpoint；Nano 6.0 Å 对应 7net-6nano，单任务模型会忽略 modal。
FlashTP 组必须有匹配的安装/硬件/模型支持，失败会明确报错，不静默回退。
CHGNet 使用填写的本地 checkpoint。

验证范围：本地检查 8 个入口的预览、5000 步与配置/开关传递，未加载模型或执行真实超算作业。

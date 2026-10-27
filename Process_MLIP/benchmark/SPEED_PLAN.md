# LCO/NVP 多模型 Speed 测试准备

目标：对用户提供的 LCO（84/189/378/756 原子）和 NVP（120/240/480/720 原子），
按指定的模型清单分别重新计算全弛豫与 MD；旧结果只用于核验环境，不混入新表。

范围：LBFGS/Frechet 全弛豫 `fmax=0.1 eV/Å, steps=2000, maxstep=0.2 Å`；
NHC NVT `800 K, 2 fs, 1000 steps, seed=42`，从原始结构独立副本开始。
可配置精度默认 FP32；MACE-OMAT 指定 Symmetrix、SevenNet 指定 FlashTP，
记录实际后端；模型加载/预热、弛豫和 MD 分开计时。

执行顺序：

1. 在 registry 增加 MatterSim、GRACE 和 NequIP 官方 ASE Adapter；NequIP 使用
   单独编译好的 ASE 模型，不能把原始模型包直接冒充编译产物。支持 GRACE 模型目录
   的内容校验，保持现有模型 API 不变。验证配置、路径、异常和参数透传。
2. 在可准确测量不同后端之前，不把 PyTorch allocator 值称为 Kokkos/TensorFlow/GPUMD
   显存峰值。CUDA 同步、非 PyTorch GPU 设备选择和显存统计必须针对后端验证；
   缺能力时标记为不满足要求，不静默伪报。FlashTP 必须检查实际可用性，不接受回退。
3. 确认 NEP89 的 ASE/GPUMD 执行、全弛豫应力、同步、GPU 内存统计及服务器环境后再接入，
   不以 CPU 跑出结果冒充 GPU。GRACE、NequIP 需要独立环境及目标设备验证。
4. 在本机制作可审阅的结构清单、每模型配置和集群脚本；记录每个环境与已验证边界。
   不移动现有数据，目标为新任务目录；不覆盖已有权重或结果。上传/提交前依 electerm
   skill 提供具体文件及目标清单，取得用户明确批准。NEP89 直接引用服务器已有文件。
5. py1 使用模型替身和 ASE EMT 覆盖适配器分派、失败保护、原始输入独立性、
   输出与恢复；按需执行针对性回归。真实 GPU、编译及所有 15 模型必须另行实测。

约束：不变更原有公开接口、不把所有依赖安装进 py1、不在登录节点跑正式 GPU 计算；
新结构只用于 Speed，本次不执行 Ehull。不得把旧运行的速度当作本次结果。

# GRACE Speed 测量

只有 `type: grace` 的 GPU 测试使用 TensorFlow 测量路径；其他模型的计时和显存统计不变。
GRACE 使用 TensorFlow 同步执行，ASE calculator 将能量、力和应力转为 NumPy 后返回，
弛豫和 MD 分别计时。每阶段使用 TensorFlow `GPU:0` 的分配器统计，记录实际使用的
峰值 MiB（含驻留模型）；该值不是整卡或其他进程的显存峰值，reserved 字段为空。
每个进程必须仅看到一张 GPU；应通过调度器的 CUDA_VISIBLE_DEVICES 选择设备。

模型加载与每结构首次预热单独计时。结果需要在目标 GPU 和实际 TensorFlow 环境验证；
不自动回退到 PyTorch，也不在 Speed 模式中要求安装 pymatgen 或 monty。

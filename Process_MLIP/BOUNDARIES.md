# 合并候选

- Process_AL_MC/relax.py 的单结构 MACE 适配器适合迁入 Process_MLIP；迁移前比较模型 head、设备、应力、收敛报告与轨迹策略，原路径保留兼容导出。本轮模板先复用，不复制实现。
- Process_AL_MC 的 MC 排序、采样池、委员会和检查点仍属于采样项目，不并入弛豫工具。
- Process_Chgnet 的模型弛豫可成为独立 calculator 适配器；训练数据转换仍保留原项目。旧导入需先修复。
- Process_face 负责生成原子约束，本项目负责在弛豫中保留并执行约束，不重复实现固定层算法。
- 不为统一接口改变模型能量基准、默认 head、dtype 或晶胞优化方法。不同返回结构需经过兼容性设计后再整合。

本轮保留公开接口，仅增加输入校验、收敛报告和模板。

## MACE 合并已完成

单结构 MACE 实现现在只保存在 Process_MLIP/mace_relax.py，Process_AL_MC/relax.py 仅兼容导出同一函数。函数签名、默认值、模型 head 选择、晶胞滤波器和报告保持不变；MC 类的委员会弛豫仍独立。

# 项目边界

- Process_AL_MC/relax.py 的单结构 MACE 入口已兼容导出本项目实现；旧路径保留。
- Process_AL_MC 的 MC 排序、采样池、委员会和检查点仍属于采样项目，不并入弛豫工具。
- Process_Chgnet 的模型弛豫可成为独立 calculator 适配器；训练数据转换仍保留原项目。旧导入需先修复。
- Process_face 负责生成原子约束，本项目负责在弛豫中保留并执行约束，不重复实现固定层算法。
- 不为统一接口改变模型能量基准、默认 head、dtype 或晶胞优化方法。不同返回结构需经过兼容性设计后再整合。

保留公开接口、模型基准和各入口的默认参数。内部共享优化实现与校验，不强行统一不同返回结构。

## MACE 合并已完成

MACE/SevenNet 的模型包装分别保留在 mace_relax.py / sevennet_relax.py，
单结构结果适配集中在 _relaxation.py，ASE 优化由 MLIPRelaxer 统一执行。
Process_AL_MC/relax.py 仍兼容导出同一 MACE 函数；MC 类的委员会弛豫保持独立。

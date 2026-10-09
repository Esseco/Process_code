# Process_AL_PCA

<!-- Manual project documentation -->

局域结构特征的 PCA/FAISS 多样性筛选。

## 功能和使用条件

入口为 DiverseSelector_struct.select：df_pool/df_train 都是局域特征表，feature_cols 明确列出数值列；struct_col 指定结构分组，group_col 可限制组内比较。返回筛选 DataFrame；非结构分组时选的是局域行，不是完整结构。RobustScaler/PCA 使用训练与候选的联合特征空间；这适用于多样性选择，不应未经说明用于评估模型泛化。FAISS 距离是平方 L2，近似 IVF 的参数影响结果。sample_traj_xyz 返回结构列表及可选标签，缺失能量/力/应力可为 None。需要 faiss、sklearn、ASE 等专用依赖。

## 模板与参数

真实参数见 [API.md](API.md)，具体任务约定用 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。有 examples 时先填写其中顶部参数，每个功能独立运行。历史缺失依赖的入口不提供假定可运行的示例。

## 合并边界

Process_AL_PCA 的 PCA 筛选不与 MC 接受率合并；通用轨迹抽帧可与 Process_Struct 对比后抽公共内核。

## 验证状态

本轮完成源码审阅和说明；除另行列明的小功能检查外，未运行模型、训练、GUI 或集群计算。静态参数索引不等同运行验证。

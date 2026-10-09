# 功能项目整理结果

范围：功能小项目及内部子项目。测试项目、测试脚本、Codex 辅助脚本、诊断/缓存目录未纳入本轮整理。

## 最终导航

| 项目 | 主要职责 |
|---|---|
| [Process_Vasp](Process_Vasp/README.md) | VASP 输入/输出、DOS、激发态、可恢复 atomate2 工作流 |
| [Process_Struct](Process_Struct/README.md) | 去重、容量、对称性、畸变、特征和通道 |
| [Process_LayeredOxide](Process_LayeredOxide/README.md) | 层状相变、层特征、相图和电压 |
| [Process_face](Process_face/README.md) | 表面、约束和表面配置 |
| [Process_MLIP](Process_MLIP/README.md) | 通用 ASE 弛豫与单结构 MACE 适配 |
| [Process_AL_MC](Process_AL_MC/README.md) | MC 排序、委员会和候选池 |
| [Process_AL_PCA](Process_AL_PCA/README.md) | PCA/FAISS 多样性选择 |
| [Process_Chgnet](Process_Chgnet/README.md) | CHGNet 数据转换及历史模型工具 |
| [Magmom_Function](Magmom_Function/README.md) | Na-Fe-Mn 磁性规则和旧接口兼容 |
| [Process_folder](Process_folder/README.md) | 轻量目录/表格辅助 |
| [Loss_Phase](Loss_Phase/README.md) | 相稳定性训练及内部损失子项目 |
| [channel_codes_optimized](channel_codes_optimized/README.md) | 集群通道批处理 |
| [octadist](octadist/README.md) | 独立第三方畸变工具 |
| [Example](Example/README.md) | 分主题历史示例参考 |

子项目说明包括 Chemical_Capacity_Constraints、Loss_hull、Loss_rank、Magmom_Function/io 与 utils、octadist/src 与 logo、Example 各主题。第三方和无源码预留目录不强行模板化。

## 已完成实际合并

- MACE 单结构弛豫：Process_MLIP/mace_relax.py 唯一实现，Process_AL_MC 旧入口兼容。
- 结构去重：Process_Struct/deduplication.py 唯一实现，VASP 旧入口兼容，层状和表面复用。
- OUTCAR 磁矩读取：Process_Vasp/results/magnetism.py 唯一实现，旧磁矩路径兼容。
- Na-Fe-Mn NUPDOWN 估计：目录接口复用 VASP 组成接口。
- 旧磁矩 INCAR 编辑：适配器调用公共编辑器，保留旧参数和显式记录的复制副作用。

## 未盲目合并的部分

CHGNet 缺失的能量修正/结构特征来源、八面体指标差异、层聚类容差、训练损失、通道探针定义都需要独立科学核对。已有说明列出限制，未宣称其已修复。测试项目未比较或合并。

## 模板规则

各功能项目 examples/ 独立运行，顶部集中参数，导入不运行。原 Python 入口保留，不要求经仓库统一 CLI。模板不复制算法；模型、训练和集群依赖使用确认过的环境，默认 py1。

Process_Vasp 的实现进一步按 inputs、results、structures、workflows 分目录；提交模板放 templates，专题说明放 docs，测试放 tests。包级及 input/output 公开函数保持原接口，原平铺模块名通过模块别名兼容；导航见 [Process_Vasp](Process_Vasp/README.md)。

## 验证界限

本轮检查功能源码语法、说明链接、模板安全导入。此前已核对 MACE 兼容、结构去重、磁矩压缩读取及部分合成科学数据；未执行真实 VASP、模型训练、MC 长采样、FAISS 筛选或集群通道计算。文档补齐不等于这些科学功能全部可运行。

# Process_Chgnet

<!-- Manual project documentation -->

CHGNet 数据转换、预测和历史弛豫工具。

## 功能和使用条件

Convert_json 负责 VASP→训练 JSON；Out_Fromjson 读取并可预测；Json_To_AES 构建 ASE 数据；Out_Fromstruct 包含预测/轨迹处理。当前多个模块引用不存在的 Process_VaspOut（correct_energy/get_Na_coord/get_lo_content），包级导入不可假定可运行。旧转换器默认可能更新 INCAR、重命名调度文件；读取/转换不天然只读。能量修正必须确认原算法及每原子/总能量约定，不能简单替换名称相近的函数。

## 模板与参数

真实参数见 [API.md](API.md)，具体任务约定用 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。有 examples 时先填写其中顶部参数，每个功能独立运行。历史缺失依赖的入口不提供假定可运行的示例。

## 合并边界

单结构模型弛豫可归 Process_MLIP，训练数据转换保留此处。旧能量修正来源未核实，暂不做改变科学语义的合并。

## 验证状态

本轮完成源码审阅和说明；除另行列明的小功能检查外，未运行模型、训练、GUI 或集群计算。静态参数索引不等同运行验证。

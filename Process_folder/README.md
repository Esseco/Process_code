# Process_folder

<!-- Manual project documentation -->

目录和 CSV 字符串辅助工具。

## 功能和使用条件

ensure_dir 接收 Path，创建目录并返回该 Path。replace_hyphen 读取 CSV 并返回 DataFrame，不自动写回；除 e 和 exclude_cols 外的列转为字符串后把 - 替换为 _。它可能改变负数、日期和数值类型，只用于明确的文本字段。exclude_cols 支持字符串或列表，本轮修复字符串被逐字符展开的错误。

## 模板与参数

真实参数见 [API.md](API.md)，具体任务约定用 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。有 examples 时先填写其中顶部参数，每个功能独立运行。历史缺失依赖的入口不提供假定可运行的示例。

## 合并边界

保留轻量辅助工具，不让所有科学功能依赖统一大工具包。

## 验证状态

本轮完成源码审阅和说明；除另行列明的小功能检查外，未运行模型、训练、GUI 或集群计算。静态参数索引不等同运行验证。

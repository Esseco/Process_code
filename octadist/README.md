# octadist

<!-- Manual project documentation -->

第三方八面体畸变工具。

## 功能和使用条件

src 为科学计算与辅助实现，main.py/octadist_gui.py 为 GUI，octadist_cli.py 为命令行，logo 为界面资源。保持原第三方命名和来源，勿将 GUI 初始化放入批量科学任务。已有 Process_Struct 调用其畸变指标；具体依赖以实际源码为准。

## 模板与参数

真实参数见 [API.md](API.md)，具体任务约定用 [TASK_TEMPLATE.md](TASK_TEMPLATE.md)。有 examples 时先填写其中顶部参数，每个功能独立运行。历史缺失依赖的入口不提供假定可运行的示例。

## 合并边界

不合并第三方源码到个人算法项目；通过明确接口复用。

## 验证状态

本轮完成源码审阅和说明；除另行列明的小功能检查外，未运行模型、训练、GUI 或集群计算。静态参数索引不等同运行验证。

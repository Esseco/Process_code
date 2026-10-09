# Py-Code

逐项目整理后的功能导航与合并结果见 [FUNCTION_PROJECTS.md](FUNCTION_PROJECTS.md)。当前范围不包括测试项目和 Codex 辅助脚本；各功能优先使用本项目 examples。

材料计算工具与实验仓库：VASP、结构分析、层状氧化物、表面、MLIP、主动学习和训练。

默认环境为 **py1**；模型和工作流使用已有专用环境，不要求一个环境安装所有依赖。

- [项目导航](docs/PROJECTS.md)：各目录的用途、入口和说明。
- [机器可读索引](docs/project_catalog.json)：真实函数签名、文件位置和依赖线索。
- [功能模板](templates/README.md)：配置式运行及通用功能骨架。
- [Codex 协作规范](AGENTS.md)：项目边界和维护规则。
- [验证与已知问题](docs/VALIDATION.md)：运行验证范围和旧依赖问题。

常用入口：VASP DOS/激发态/可续算任务见 [Process_Vasp](Process_Vasp/README.md)；容量、畸变、连通性见 [Process_Struct](Process_Struct/README.md)；相变、电压见 [Process_LayeredOxide](Process_LayeredOxide/README.md)；表面见 [Process_face](Process_face/README.md)；模型弛豫见 [Process_MLIP](Process_MLIP/README.md) 和 [Process_AL_MC](Process_AL_MC/README.md)。

在根目录复制 templates/configs 对应 JSON，填写路径和参数：

```text
python templates/run_task.py your_config.json
python templates/run_task.py your_config.json --run
```

第一条仅预览，第二条执行；原 Python 导入方式保留。其他项目按各自 TASK_TEMPLATE.md 组织调用。

更新索引：`python tools/project_catalog.py`，只解析源文件，不启动计算。生成的项目 README/API/TASK_TEMPLATE 在该脚本中维护，专题文档保持独立。

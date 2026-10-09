# Py-Code 协作规范

如无明确说明，默认用 py1 环境。

先读 README.md、docs/PROJECTS.md，再读目标项目 README.md/API.md。机器可读索引为 docs/project_catalog.json，来自静态解析，不代表所有功能已验证。

保持原目录和公开接口。Example 是历史示例，先检查固定路径再运行。Loss_Phase 与 Ehull_test 是不同实验，不能仅凭同名文件合并。octadist 是第三方代码，保留来源、许可证和命名。缓存、诊断、模型和计算结果不搬移或删除。

新功能明确输入/输出、单位、随机种子、环境、副作用和重复运行策略。复用现有函数，分离配置、业务逻辑和 CLI。任务规格用项目 TASK_TEMPLATE.md；配置调用用 templates/run_task.py。不得为统一外观擅自更名或改变科学语义。

不将所有训练/模型依赖装入 py1。atomate2 测试使用已有 atomate2 环境，MACE/CHGNet/FAISS 使用确认过的专用环境。文档生成不得导入项目、加载模型、启动 GUI 或提交计算。

接口更新后运行 `python tools/project_catalog.py`。生成文档在脚本 PROJECTS 元数据中维护，专题说明独立维护。按修改运行必要测试，报告未验证项；验证范围见 docs/VALIDATION.md。

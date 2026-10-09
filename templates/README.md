# 功能模板

项目 TASK_TEMPLATE.md 定义任务规格。本目录提供配置入口和业务函数骨架。

| recipe | 原入口 | 环境 |
|---|---|---|
| vasp_dos | Process_Vasp.read_dos | py1 |
| vasp_excited | Process_Vasp.generate_excited_input | py1 |
| vasp_workflow | Process_Vasp.generate_atomate_input | py1 生成，atomate2 运行 |
| capacity | Process_Struct.theoretical_specific_capacity | py1 |
| wyckoff | Process_Struct.get_wyckoff_sites | py1，自动把结构路径转换为 Structure |
| mace_relax | Process_MLIP.mace_relax.relax_structure_mace | 已有 MACE 环境 |

复制 configs 中的 JSON，parameters 使用 API.md 中的真实参数名；路径按执行时工作目录解释，建议绝对路径。

```text
python templates/run_task.py your_config.json
python templates/run_task.py your_config.json --run
```

默认只预览，不导入业务包；--run 执行。DOS 不覆盖已有 CSV；workflow 不覆盖非空目录；激发态沿用原接口的空目录要求。MACE 按原函数写出结果，需先确认目标路径。

其余项目按任务模板组合 Python 调用，不通过 JSON 任意导入。新 recipe 需明确构建 Structure/Atoms/calculator 等对象的方式。不要把复杂模型对象直接当成 JSON 参数。

[function_template.py](function_template.py) 是可复制业务骨架，compute 需由具体功能实现，导入不会运行。它不是现成科学算法。

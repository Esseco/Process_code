# 提交与环境模板

| 文件 | 用途 | 谁使用 |
|---|---|---|
| submit_gpu.sh | Slurm GPU 提交模板 | generate_atomate_input；生成任务中仍叫 submit_gpu.sh |
| vasp.lsf | 常规 VASP 的 LSF 提交模板 | generate_vasp_input |
| vasp-NEB.lsf | NEB 的历史 LSF 模板 | 人工配置后使用 |
| 北京超算-vasp-GPU.sh | 北京超算的历史 GPU 脚本 | 人工配置后使用 |
| atomate2.yaml | VASP 启动命令配置示例 | 按实际执行环境配置 |

这些是配置文件，导入包不会执行它们。模板保留原集群路径、资源和命令；上传前需按实际服务器配置。工作流生成只写文件，不提交计算；重复生成写入同名任务文件，已有计算结果仍由运行器按检查点和 attempt 规则处理。

生成工作流可设置 `export_plot_data=True`；完成后由项目中的导出函数输出 DOS 或能带 CSV。任务目录无需复制运行器、导出器或 DOS 读取器；提交脚本只运行 `workflow.py`，超算环境需能导入 Process_Vasp。

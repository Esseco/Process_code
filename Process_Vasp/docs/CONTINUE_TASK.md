# 统一任务接口

```python
from Process_Vasp import continue_task
continue_task("config.json", directory="new_task")
```

只准备文件，不运行或提交。上传 new_task 后进入目录执行 `sbatch submit.sh`。超算须能导入更新后的 Process_Vasp；VASP 阶段需要 atomate2，AMSET 后处理需要 AMSET/numpy。任务含一个用户配置 workflow.json，可在提交前修改。生成目录须不存在或为空；不指定 directory 时生成 JSON 同级的 `<文件名>_task`。

## JSON

新计算填 structure_file（相对 JSON 所在目录），继续计算填 previous_task（超算绝对路径，或相对生成任务目录的路径），二者选一。

```json
{
  "previous_task": "/server/path/completed_task",
  "calculation": "dos",
  "incar_settings": {"dos": {"NEDOS": 3000, "ISMEAR": 0}},
  "kpoints_settings": {},
  "export_plot_data": true
}
```

calculation 支持 relax/static/dos/band/amset。执行时读取原任务检查点，从最新适用阶段开始补齐必要的前置步骤。新配置仅覆盖给出的 INCAR/KPOINTS 键，未提供的键继承原 workflow.json；比较原记录中的 overrides，不将其解释为所有实际 VASP 默认值。如果指定键没有原记录，保守地视为改变。修改某阶段参数，会重做该阶段及后续阶段。若全部完成且参数相同，直接复用。

可选 source_stage/source_dir 明确指定原始输出来源；source_dir 相对 previous_task，源结果必须通过阶段校验。显式选择的来源若被新配置改动而失效，会报错，请选择更早阶段。无检查点的原始输出建议明确 source_stage。源结果不修改；新计算、计划与状态在 execution/，CRT 后处理在 results/。重复提交按原有运行器检查点恢复，失败保留 attempt。无随机种子。

AMSET 示例见 examples/continue_amset.json。浓度 cm⁻³（负电子、正空穴），温度 K、relaxation_time s；输出为输运有效质量 m*/m0、σ/τ、指定 τ 下的 CRT 迁移率和 μ/τ，定义见 AMSET_CRT.md。默认只复用完成 DOS。需要新跑 DOS 时要求 amset_settings.allow_vasp=true，且必须将 submit.sh 改为配置了 VASP 的资源和环境；默认 AMSET CPU 脚本不具备运行 VASP 的条件。只做静态也能作为新 DOS 的前置来源，不将路径能带当均匀网格。

项目保留原有接口兼容；日常只使用 continue_task。生成阶段默认 py1，超算原任务文件和新任务源码应使用同版本项目。未运行测试、真实 VASP/AMSET 或集群提交。

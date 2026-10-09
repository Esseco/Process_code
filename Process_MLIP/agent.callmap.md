# Module: Process_MLIP

## Functions

### MLIPRelaxer.__init__
- type: method
- purpose: unknown
- inputs: ['atoms', 'calculator', 'fmax', 'steps', 'optimizer', 'relax_cell']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Process_MLIP\MLIP_Relax.py:8

### MLIPRelaxer._get_optimizer
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: ['MLIPRelaxer.relax']
- location: Process_MLIP\MLIP_Relax.py:27

### MLIPRelaxer.relax
- type: method
- purpose: unknown
- inputs: ['traj_file', 'log_file', 'final_structure']
- outputs: ['unknown']
- calls: ['MLIPRelaxer._get_optimizer', 'optimizer_class', 'run', 'ExpCellFilter']
- called_by: []
- location: Process_MLIP\MLIP_Relax.py:40

## Classes

### MLIPRelaxer
- methods: ['__init__', '_get_optimizer', 'relax']

## Entry Points

- MLIPRelaxer.__init__

## Call Graph Summary

子库 **Process_MLIP** 包含 **3** 个函数/方法，**1** 个类。

核心执行链路（从入口到关键逻辑）：
- MLIPRelaxer.relax → `MLIPRelaxer._get_optimizer, optimizer_class, run, ExpCellFilter`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
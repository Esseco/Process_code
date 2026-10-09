# Module: Process_folder

## Functions

### replace_hyphen
- type: function
- purpose: unknown
- inputs: ['df_f', 'exclude_cols']
- outputs: ['unknown']
- calls: ['read_csv']
- called_by: []
- location: Process_folder\Handle_Excel.py:3

### ensure_dir
- type: function
- purpose: unknown
- inputs: ['path']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Process_folder\Handle_File.py:3

## Entry Points

- unknown (无明确入口函数)

## Call Graph Summary

子库 **Process_folder** 包含 **2** 个函数/方法，**0** 个类。

核心执行链路（从入口到关键逻辑）：
- replace_hyphen → `read_csv`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
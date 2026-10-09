# Module: Process_Chgnet

## Functions

### vasp_to_chgnetJson
- type: function
- purpose: unknown
- inputs: ['init_dir', 'tar_path', 'Update', 'check_converge']
- outputs: ['unknown']
- calls: ['check_magnetic_moments', 'get_INCAR_NUPDOWN', 'detect_converge', 'parse_vasp_dir', 'update_incar']
- called_by: []
- location: Process_Chgnet\Convert_json.py:10

### get_ase_from_json
- type: function
- purpose: read chgnet json return list
- inputs: ['file', 'is_force', 'is_correct']
- outputs: ['unknown']
- calls: ['AseAtomsAdaptor', 'load', 'from_dict', 'get_atoms', 'correct_energy']
- called_by: []
- location: Process_Chgnet\Json_To_AES.py:9

### load_chgnet_json
- type: function
- purpose: model : object or None
- inputs: ['json_path', 'model', 'last_only', 'tasks', 'return_struct', 'energy_correction']
- outputs: ['unknown']
- calls: ['from_dict', 'predict_structure', 'correct_energy']
- called_by: []
- location: Process_Chgnet\Out_Fromjson.py:10

### out_from_struct
- type: function
- purpose: unknown
- inputs: ['struct', 'energy', 'forces', 'magmoms', 'stress']
- outputs: ['unknown']
- calls: ['get_lo_content', 'get_Na_coord']
- called_by: []
- location: Process_Chgnet\Out_Fromstruct.py:7

### chgnet_relax
- type: function
- purpose: unknown
- inputs: ['struct', 'relaxer', 'model', 'include_f', 'include_m', 'include_traj', 'fmax', 'steps']
- outputs: ['unknown']
- calls: ['relax', 'predict_structure']
- called_by: []
- location: Process_Chgnet\Out_Fromstruct.py:24

### convert_traj_to_data
- type: function
- purpose: unknown
- inputs: ['traj', 'include_f', 'include_s', 'include_m']
- outputs: ['unknown']
- calls: ['Structure']
- called_by: []
- location: Process_Chgnet\Out_Fromstruct.py:41

### extract_stages_traj
- type: function
- purpose: data: traj
- inputs: ['data', 'out_dir', 'path']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Process_Chgnet\Out_Fromstruct.py:83

## Entry Points

- unknown (无明确入口函数)

## Call Graph Summary

子库 **Process_Chgnet** 包含 **7** 个函数/方法，**0** 个类。

核心执行链路（从入口到关键逻辑）：
- vasp_to_chgnetJson → `check_magnetic_moments, get_INCAR_NUPDOWN, detect_converge, parse_vasp_dir, update_incar`
- get_ase_from_json → `AseAtomsAdaptor, load, from_dict, get_atoms, correct_energy`
- load_chgnet_json → `from_dict, predict_structure, correct_energy`
- out_from_struct → `get_lo_content, get_Na_coord`
- chgnet_relax → `relax, predict_structure`
- convert_traj_to_data → `Structure`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
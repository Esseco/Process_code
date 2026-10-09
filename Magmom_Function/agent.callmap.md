# Module: Magmom_Function

## Functions

### read_magnetic_moments_outcar
- type: function
- purpose: read_magnetic_moments_outcar 的 Docstring
- inputs: ['init_dir']
- outputs: ['unknown']
- calls: ['from_file', 'search', 'match', 'group']
- called_by: ['check_magnetic_moments', 'InitDft_to_TarDft']
- location: Magmom_Function\io\Check_Magmom.py:5

### check_magnetic_moments
- type: function
- purpose: check_magnetic_moments 的 Docstring
- inputs: ['init_dir']
- outputs: ['unknown']
- calls: ['read_magnetic_moments_outcar', 'get_INCAR_NUPDOWN']
- called_by: ['InitDft_to_TarDft']
- location: Magmom_Function\io\Check_Magmom.py:63

### get_INCAR_NUPDOWN
- type: function
- purpose: get_INCAR_NUPDOWN 的 Docstring
- inputs: ['init_dir']
- outputs: ['unknown']
- calls: ['from_file']
- called_by: ['check_magnetic_moments', 'InitDft_to_TarDft']
- location: Magmom_Function\io\Check_VaspOut.py:4

### detect_converge
- type: function
- purpose: detect_converge 的 Docstring
- inputs: ['init_dir']
- outputs: ['unknown']
- calls: ['read_text', 'count']
- called_by: ['InitDft_to_TarDft']
- location: Magmom_Function\io\Check_VaspOut.py:36

### update_incar
- type: function
- purpose: update_incar_struct 的 Docstring
- inputs: ['init_dir', 'tar_dir', 'spin', 'NUPDOWN', 'NSW']
- outputs: ['unknown']
- calls: ['readlines', 'writelines', 'lower']
- called_by: ['InitDft_to_TarDft']
- location: Magmom_Function\io\Correct_VaspInput.py:6

### copy_file
- type: function
- purpose: unknown
- inputs: ['init_dir', 'tar_dir']
- outputs: ['unknown']
- calls: []
- called_by: ['InitDft_to_TarDft']
- location: Magmom_Function\io\Correct_VaspInput.py:49

### InitDft_to_TarDft
- type: function
- purpose: InitDft_to_TarDft 的 Docstring
- inputs: ['init_dir', 'tar_dir', 'Update', 'NSW']
- outputs: ['unknown']
- calls: ['detect_converge', 'get_INCAR_NUPDOWN', 'check_magnetic_moments', 'read_magnetic_moments_outcar', 'update_incar', 'copy_file']
- called_by: []
- location: Magmom_Function\utils\Init_To_Tar.py:11

## Entry Points

- unknown (无明确入口函数)

## Call Graph Summary

子库 **Magmom_Function** 包含 **7** 个函数/方法，**0** 个类。

核心执行链路（从入口到关键逻辑）：
- InitDft_to_TarDft → `detect_converge, get_INCAR_NUPDOWN, check_magnetic_moments, read_magnetic_moments_outcar, update_incar`
- read_magnetic_moments_outcar → `from_file, search, match, group`
- update_incar → `readlines, writelines, lower`
- check_magnetic_moments → `read_magnetic_moments_outcar, get_INCAR_NUPDOWN`
- detect_converge → `read_text, count`
- get_INCAR_NUPDOWN → `from_file`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
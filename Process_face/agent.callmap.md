# Module: Process_face

## Functions

### SurfaceFixer.__init__
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: ['get_structure']
- called_by: []
- location: Process_face\Fix_atoms.py:10

### SurfaceFixer._get_cn
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['CrystalNN', 'get_cn']
- called_by: ['SurfaceFixer.analyze_slab']
- location: Process_face\Fix_atoms.py:37

### SurfaceFixer.analyze_slab
- type: method
- purpose: unknown
- inputs: ['target_cn']
- outputs: ['unknown']
- calls: ['SurfaceFixer._get_cn']
- called_by: ['SurfaceFixer.get_surface_atoms', 'SurfaceFixer.fix_center_layers']
- location: Process_face\Fix_atoms.py:56

### SurfaceFixer.get_symbol
- type: method
- purpose: unknown
- inputs: ['i']
- outputs: ['unknown']
- calls: []
- called_by: ['SurfaceFixer.get_surface_atoms']
- location: Process_face\Fix_atoms.py:74

### SurfaceFixer.get_surface_atoms
- type: method
- purpose: unknown
- inputs: ['target_cn', 'distance']
- outputs: ['unknown']
- calls: ['SurfaceFixer.analyze_slab', 'SurfaceFixer.get_symbol']
- called_by: []
- location: Process_face\Fix_atoms.py:83

### SurfaceFixer.fix_center_layers
- type: method
- purpose: unknown
- inputs: ['target_cn']
- outputs: ['unknown']
- calls: ['SurfaceFixer.analyze_slab', 'SurfaceFixer._apply_fix']
- called_by: []
- location: Process_face\Fix_atoms.py:133

### SurfaceFixer.fix_center_distance
- type: method
- purpose: unknown
- inputs: ['thickness']
- outputs: ['unknown']
- calls: ['SurfaceFixer._apply_fix']
- called_by: []
- location: Process_face\Fix_atoms.py:141

### SurfaceFixer.fix_center_fraction
- type: method
- purpose: unknown
- inputs: ['fraction']
- outputs: ['unknown']
- calls: ['SurfaceFixer._apply_fix']
- called_by: []
- location: Process_face\Fix_atoms.py:149

### SurfaceFixer._apply_fix
- type: method
- purpose: unknown
- inputs: ['fixed_indices']
- outputs: ['unknown']
- calls: ['FixAtoms']
- called_by: ['SurfaceFixer.fix_center_layers', 'SurfaceFixer.fix_center_distance', 'SurfaceFixer.fix_center_fraction']
- location: Process_face\Fix_atoms.py:162

### LOSlabProcessor.__init__
- type: method
- purpose: unknown
- inputs: ['structure', 'oxi_transformer', 'output_dir']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Process_face\Generate_StructFace_Class.py:8

### LOSlabProcessor.get_miller_indices
- type: method
- purpose: unknown
- inputs: ['max_index']
- outputs: ['unknown']
- calls: ['get_symmetrically_distinct_miller_indices', 'd_hkl']
- called_by: ['LOSlabProcessor.process_and_save']
- location: Process_face\Generate_StructFace_Class.py:17

### LOSlabProcessor.generate_slabs
- type: method
- purpose: unknown
- inputs: ['miller_index', 'min_slab_size', 'min_vacuum_size']
- outputs: ['unknown']
- calls: ['SlabGenerator', 'get_slabs']
- called_by: ['LOSlabProcessor.process_and_save']
- location: Process_face\Generate_StructFace_Class.py:23

### LOSlabProcessor.analyze_face
- type: method
- purpose: unknown
- inputs: ['slab_struct']
- outputs: ['unknown']
- calls: ['Slab', 'is_polar', 'is_symmetric', 'eye']
- called_by: ['LOSlabProcessor.process_and_save']
- location: Process_face\Generate_StructFace_Class.py:38

### LOSlabProcessor.process_and_save
- type: method
- purpose: unknown
- inputs: ['max_miller']
- outputs: ['unknown']
- calls: ['LOSlabProcessor.get_miller_indices', 'LOSlabProcessor.generate_slabs', 'LOSlabProcessor.analyze_face', 'nonstoichiometric_symmetrized_slab', 'make_supercell']
- called_by: []
- location: Process_face\Generate_StructFace_Class.py:58

### get_symmetry_atom
- type: function
- purpose: unknown
- inputs: ['struct', 'index_list']
- outputs: ['unknown']
- calls: ['SpacegroupAnalyzer', 'get_symmetry_operations', 'operate']
- called_by: []
- location: Process_face\Surface_atom_process.py:9

### sym_surface_remove_atoms_single
- type: function
- purpose: unknown
- inputs: ['struct', 'tar_dir', 'inter_atom', 'nstr', 'select_s']
- outputs: ['unknown']
- calls: ['remove_site_property', 'SurfaceFixer', 'get_surface_atoms', 'OxidationStateDecorationTransformation', 'replace_species', 'apply_transformation', 'gen_ESGS_structure', 'deduplicate', 'Fraction']
- called_by: []
- location: Process_face\Surface_atom_process.py:29

## Classes

### SurfaceFixer
- methods: ['__init__', '_get_cn', 'analyze_slab', 'get_symbol', 'get_surface_atoms', 'fix_center_layers', 'fix_center_distance', 'fix_center_fraction', '_apply_fix']

### LOSlabProcessor
- methods: ['__init__', 'get_miller_indices', 'generate_slabs', 'analyze_face', 'process_and_save']

## Entry Points

- SurfaceFixer.__init__, LOSlabProcessor.__init__

## Call Graph Summary

子库 **Process_face** 包含 **16** 个函数/方法，**2** 个类。

核心执行链路（从入口到关键逻辑）：
- sym_surface_remove_atoms_single → `remove_site_property, SurfaceFixer, get_surface_atoms, OxidationStateDecorationTransformation, replace_species`
- LOSlabProcessor.process_and_save → `LOSlabProcessor.get_miller_indices, LOSlabProcessor.generate_slabs, LOSlabProcessor.analyze_face, nonstoichiometric_symmetrized_slab, make_supercell`
- LOSlabProcessor.analyze_face → `Slab, is_polar, is_symmetric, eye`
- get_symmetry_atom → `SpacegroupAnalyzer, get_symmetry_operations, operate`
- SurfaceFixer._get_cn → `CrystalNN, get_cn`
- SurfaceFixer.get_surface_atoms → `SurfaceFixer.analyze_slab, SurfaceFixer.get_symbol`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
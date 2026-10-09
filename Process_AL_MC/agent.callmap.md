# Module: Process_AL_MC

## Functions

### extract_data_from_mcjson
- type: function
- purpose: unknown
- inputs: ['json_file', 'tar', 'select_num']
- outputs: ['unknown']
- calls: ['from_dict']
- called_by: []
- location: Process_AL_MC\Auc_code.py:5

### LayeredOxide_MCOrderingClass.__init__
- type: method
- purpose: unknown
- inputs: ['structure', 'mode', 'out_dir', 'temperature', 'max_steps', 'seed', 'pool_size', 'fmax', 'relax_steps', 'relax_cell', 'save_every', 'patience', 'energy_tol', 'tm_original_element', 'tm_ratios', 'na_remove_num', 'max_duplicate_trials', 'model_path', 'model_paths', 'main_model_index', 'initialize', 'full_na_structure']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._load_structure', 'LayeredOxide_MCOrderingClass._load_models', 'StructOptimizer', 'LayeredOxide_MCOrderingClass._save_settings']
- called_by: []
- location: Process_AL_MC\MC_sample.py:51

### LayeredOxide_MCOrderingClass._load_structure
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: ['from_file']
- called_by: ['LayeredOxide_MCOrderingClass.__init__']
- location: Process_AL_MC\MC_sample.py:199

### LayeredOxide_MCOrderingClass._save_vasp
- type: method
- purpose: unknown
- inputs: ['structure', 'path']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._prepare_tm', 'LayeredOxide_MCOrderingClass._prepare_na', 'LayeredOxide_MCOrderingClass._save_pool']
- location: Process_AL_MC\MC_sample.py:204

### LayeredOxide_MCOrderingClass._json_default
- type: method
- purpose: unknown
- inputs: ['obj']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Process_AL_MC\MC_sample.py:207

### LayeredOxide_MCOrderingClass._save_json
- type: method
- purpose: unknown
- inputs: ['data', 'path']
- outputs: ['unknown']
- calls: ['dump']
- called_by: ['LayeredOxide_MCOrderingClass._save_settings', 'LayeredOxide_MCOrderingClass._relax_and_evaluate', 'LayeredOxide_MCOrderingClass._save_pool', 'LayeredOxide_MCOrderingClass._save_checkpoint']
- location: Process_AL_MC\MC_sample.py:220

### LayeredOxide_MCOrderingClass._save_settings
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._save_json']
- called_by: ['LayeredOxide_MCOrderingClass.__init__']
- location: Process_AL_MC\MC_sample.py:224

### LayeredOxide_MCOrderingClass._build_occ_from_input_structure
- type: method
- purpose: Build Na/Vac occupation from:
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._prepare_na']
- location: Process_AL_MC\MC_sample.py:265

### LayeredOxide_MCOrderingClass._load_models
- type: method
- purpose: unknown
- inputs: ['model_path', 'model_paths']
- outputs: ['unknown']
- calls: ['load', 'from_file']
- called_by: ['LayeredOxide_MCOrderingClass.__init__']
- location: Process_AL_MC\MC_sample.py:310

### LayeredOxide_MCOrderingClass.prepare
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._prepare_tm', 'LayeredOxide_MCOrderingClass._prepare_na']
- called_by: ['LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:342

### LayeredOxide_MCOrderingClass._prepare_tm
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._save_vasp', 'LayeredOxide_MCOrderingClass._relax_and_evaluate', 'LayeredOxide_MCOrderingClass._tm_key', 'LayeredOxide_MCOrderingClass._update_pool', 'LayeredOxide_MCOrderingClass._species_from_ratios']
- called_by: ['LayeredOxide_MCOrderingClass.prepare']
- location: Process_AL_MC\MC_sample.py:348

### LayeredOxide_MCOrderingClass._prepare_na
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._structure_from_na_occ', 'LayeredOxide_MCOrderingClass._save_vasp', 'LayeredOxide_MCOrderingClass._relax_and_evaluate', 'LayeredOxide_MCOrderingClass._na_key', 'LayeredOxide_MCOrderingClass._update_pool', 'LayeredOxide_MCOrderingClass._build_occ_from_input_structure']
- called_by: ['LayeredOxide_MCOrderingClass.prepare']
- location: Process_AL_MC\MC_sample.py:464

### LayeredOxide_MCOrderingClass._species_from_ratios
- type: method
- purpose: unknown
- inputs: ['ratios', 'total']
- outputs: ['unknown']
- calls: ['floor']
- called_by: ['LayeredOxide_MCOrderingClass._prepare_tm']
- location: Process_AL_MC\MC_sample.py:559

### LayeredOxide_MCOrderingClass._tm_key
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._prepare_tm', 'LayeredOxide_MCOrderingClass._trial_tm']
- location: Process_AL_MC\MC_sample.py:582

### LayeredOxide_MCOrderingClass._na_key
- type: method
- purpose: unknown
- inputs: ['occ']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._prepare_na', 'LayeredOxide_MCOrderingClass._trial_na']
- location: Process_AL_MC\MC_sample.py:585

### LayeredOxide_MCOrderingClass._structure_from_na_occ
- type: method
- purpose: unknown
- inputs: ['occ']
- outputs: ['unknown']
- calls: ['remove_sites']
- called_by: ['LayeredOxide_MCOrderingClass._prepare_na', 'LayeredOxide_MCOrderingClass._trial_na']
- location: Process_AL_MC\MC_sample.py:588

### LayeredOxide_MCOrderingClass._relax_with_main_model
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._relax_and_evaluate']
- location: Process_AL_MC\MC_sample.py:606

### LayeredOxide_MCOrderingClass._predict_energy_force
- type: method
- purpose: unknown
- inputs: ['model', 'structure']
- outputs: ['unknown']
- calls: ['predict_structure']
- called_by: ['LayeredOxide_MCOrderingClass._evaluate_committee']
- location: Process_AL_MC\MC_sample.py:615

### LayeredOxide_MCOrderingClass._evaluate_committee
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._predict_energy_force']
- called_by: ['LayeredOxide_MCOrderingClass._relax_and_evaluate']
- location: Process_AL_MC\MC_sample.py:629

### LayeredOxide_MCOrderingClass._structure_to_json_dict
- type: method
- purpose: unknown
- inputs: ['structure']
- outputs: ['unknown']
- calls: ['as_dict']
- called_by: ['LayeredOxide_MCOrderingClass._make_traj_frame_json']
- location: Process_AL_MC\MC_sample.py:678

### LayeredOxide_MCOrderingClass._make_traj_frame_json
- type: method
- purpose: unknown
- inputs: ['step', 'structure', 'eval_data']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._structure_to_json_dict']
- called_by: ['LayeredOxide_MCOrderingClass._relax_and_evaluate']
- location: Process_AL_MC\MC_sample.py:681

### LayeredOxide_MCOrderingClass._get_traj_structures
- type: method
- purpose: Extract pymatgen structures from CHGNet TrajectoryObserver.
- inputs: ['trajectory']
- outputs: ['unknown']
- calls: ['get_chemical_symbols', 'Structure', 'get_structure']
- called_by: ['LayeredOxide_MCOrderingClass._relax_and_evaluate']
- location: Process_AL_MC\MC_sample.py:710

### LayeredOxide_MCOrderingClass._relax_and_evaluate
- type: method
- purpose: unknown
- inputs: ['structure', 'traj_dir']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._relax_with_main_model', 'LayeredOxide_MCOrderingClass._get_traj_structures', 'LayeredOxide_MCOrderingClass._evaluate_committee', 'LayeredOxide_MCOrderingClass._make_traj_frame_json', 'LayeredOxide_MCOrderingClass._save_json']
- called_by: ['LayeredOxide_MCOrderingClass._prepare_tm', 'LayeredOxide_MCOrderingClass._prepare_na', 'LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:784

### LayeredOxide_MCOrderingClass._trial
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._trial_na', 'LayeredOxide_MCOrderingClass._trial_tm']
- called_by: ['LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:824

### LayeredOxide_MCOrderingClass._trial_tm
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._choose_two_different_sites', 'LayeredOxide_MCOrderingClass._tm_key']
- called_by: ['LayeredOxide_MCOrderingClass._trial']
- location: Process_AL_MC\MC_sample.py:829

### LayeredOxide_MCOrderingClass._trial_na
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._na_key', 'LayeredOxide_MCOrderingClass._structure_from_na_occ']
- called_by: ['LayeredOxide_MCOrderingClass._trial']
- location: Process_AL_MC\MC_sample.py:851

### LayeredOxide_MCOrderingClass._choose_two_different_sites
- type: method
- purpose: unknown
- inputs: ['structure', 'indices']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._trial_tm']
- location: Process_AL_MC\MC_sample.py:871

### LayeredOxide_MCOrderingClass._accept
- type: method
- purpose: unknown
- inputs: ['trial_eval']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:884

### LayeredOxide_MCOrderingClass._should_stop
- type: method
- purpose: unknown
- inputs: ['step']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:895

### LayeredOxide_MCOrderingClass._summary_eval
- type: method
- purpose: unknown
- inputs: ['eval_data']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._save_checkpoint']
- location: Process_AL_MC\MC_sample.py:905

### LayeredOxide_MCOrderingClass._update_pool
- type: method
- purpose: unknown
- inputs: ['structure', 'eval_data', 'key', 'step', 'relax_traj']
- outputs: ['unknown']
- calls: []
- called_by: ['LayeredOxide_MCOrderingClass._prepare_tm', 'LayeredOxide_MCOrderingClass._prepare_na', 'LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:926

### LayeredOxide_MCOrderingClass._save_pool
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._save_json', 'LayeredOxide_MCOrderingClass._save_vasp']
- called_by: ['LayeredOxide_MCOrderingClass._save_checkpoint']
- location: Process_AL_MC\MC_sample.py:949

### LayeredOxide_MCOrderingClass._save_checkpoint
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass._save_json', 'LayeredOxide_MCOrderingClass._save_pool', 'LayeredOxide_MCOrderingClass._summary_eval']
- called_by: ['LayeredOxide_MCOrderingClass.run']
- location: Process_AL_MC\MC_sample.py:1003

### LayeredOxide_MCOrderingClass.run
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['LayeredOxide_MCOrderingClass.prepare', 'LayeredOxide_MCOrderingClass._save_checkpoint', 'LayeredOxide_MCOrderingClass._trial', 'LayeredOxide_MCOrderingClass._relax_and_evaluate', 'LayeredOxide_MCOrderingClass._accept', 'LayeredOxide_MCOrderingClass._update_pool', 'LayeredOxide_MCOrderingClass._should_stop']
- called_by: []
- location: Process_AL_MC\MC_sample.py:1028

## Classes

### LayeredOxide_MCOrderingClass
- methods: ['__init__', '_load_structure', '_save_vasp', '_json_default', '_save_json', '_save_settings', '_build_occ_from_input_structure', '_load_models', 'prepare', '_prepare_tm', '_prepare_na', '_species_from_ratios', '_tm_key', '_na_key', '_structure_from_na_occ', '_relax_with_main_model', '_predict_energy_force', '_evaluate_committee', '_structure_to_json_dict', '_make_traj_frame_json', '_get_traj_structures', '_relax_and_evaluate', '_trial', '_trial_tm', '_trial_na', '_choose_two_different_sites', '_accept', '_should_stop', '_summary_eval', '_update_pool', '_save_pool', '_save_checkpoint', 'run']

## Entry Points

- LayeredOxide_MCOrderingClass.__init__, LayeredOxide_MCOrderingClass.prepare, LayeredOxide_MCOrderingClass.run

## Call Graph Summary

子库 **Process_AL_MC** 包含 **34** 个函数/方法，**1** 个类。

核心执行链路（从入口到关键逻辑）：
- LayeredOxide_MCOrderingClass.run → `LayeredOxide_MCOrderingClass.prepare, LayeredOxide_MCOrderingClass._save_checkpoint, LayeredOxide_MCOrderingClass._trial, LayeredOxide_MCOrderingClass._relax_and_evaluate, LayeredOxide_MCOrderingClass._accept`
- LayeredOxide_MCOrderingClass._prepare_na → `LayeredOxide_MCOrderingClass._structure_from_na_occ, LayeredOxide_MCOrderingClass._save_vasp, LayeredOxide_MCOrderingClass._relax_and_evaluate, LayeredOxide_MCOrderingClass._na_key, LayeredOxide_MCOrderingClass._update_pool`
- LayeredOxide_MCOrderingClass._prepare_tm → `LayeredOxide_MCOrderingClass._save_vasp, LayeredOxide_MCOrderingClass._relax_and_evaluate, LayeredOxide_MCOrderingClass._tm_key, LayeredOxide_MCOrderingClass._update_pool, LayeredOxide_MCOrderingClass._species_from_ratios`
- LayeredOxide_MCOrderingClass._relax_and_evaluate → `LayeredOxide_MCOrderingClass._relax_with_main_model, LayeredOxide_MCOrderingClass._get_traj_structures, LayeredOxide_MCOrderingClass._evaluate_committee, LayeredOxide_MCOrderingClass._make_traj_frame_json, LayeredOxide_MCOrderingClass._save_json`
- LayeredOxide_MCOrderingClass.__init__ → `LayeredOxide_MCOrderingClass._load_structure, LayeredOxide_MCOrderingClass._load_models, StructOptimizer, LayeredOxide_MCOrderingClass._save_settings`
- LayeredOxide_MCOrderingClass._get_traj_structures → `get_chemical_symbols, Structure, get_structure`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
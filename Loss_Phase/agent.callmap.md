# Module: Loss_Phase

## Functions

### StructureDataHull.__init__
- type: method
- purpose: Initialize the dataset.
- inputs: ['structures', 'energies', 'forces']
- outputs: ['unknown']
- calls: ['CrystalGraphConverter']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:33

### StructureDataHull.from_vasp
- type: method
- purpose: Parse VASP output files into structures and labels and feed into the dataset.
- inputs: ['file_root']
- outputs: ['unknown']
- calls: ['parse_vasp_dir', 'cls']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:98

### StructureDataHull.__len__
- type: method
- purpose: Get the number of structures in this dataset.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:143

### StructureDataHull.__getitem__
- type: method
- purpose: Get one graph for a structure in this dataset.
- inputs: ['idx']
- outputs: ['unknown']
- calls: ['StructureDataHull.__getitem__', 'StructureDataHull.graph_converter']
- called_by: ['StructureDataHull.__getitem__']
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:148

### CIFData.__init__
- type: method
- purpose: Initialize the dataset from a directory containing CIFs.
- inputs: ['cif_path']
- outputs: ['unknown']
- calls: ['CrystalGraphConverter']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:209

### CIFData.__len__
- type: method
- purpose: Get the number of structures in this dataset.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:261

### CIFData.__getitem__
- type: method
- purpose: Get one item in the dataset.
- inputs: ['idx']
- outputs: ['unknown']
- calls: ['CIFData.__getitem__', 'from_file', 'CIFData.graph_converter']
- called_by: ['CIFData.__getitem__']
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:266

### GraphData.__init__
- type: method
- purpose: Initialize the dataset from a directory containing saved crystal graphs.
- inputs: ['graph_path']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:325

### GraphData.__len__
- type: method
- purpose: Get the number of graphs in this dataset.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:391

### GraphData.__getitem__
- type: method
- purpose: Get one item in the dataset.
- inputs: ['idx']
- outputs: ['unknown']
- calls: ['GraphData.__getitem__', 'from_file']
- called_by: ['GraphData.__getitem__']
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:395

### GraphData.get_train_val_test_loader
- type: method
- purpose: Partition the GraphData using materials id,
- inputs: ['train_ratio', 'val_ratio']
- outputs: ['unknown']
- calls: ['GraphData', 'DataLoader']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:443

### StructureJsonData.__init__
- type: method
- purpose: Initialize the dataset by reading JSON files.
- inputs: ['data', 'graph_converter']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:556

### StructureJsonData.__len__
- type: method
- purpose: Get the number of structures with targets in the dataset.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:617

### StructureJsonData.__getitem__
- type: method
- purpose: Get one item in the dataset.
- inputs: ['idx']
- outputs: ['unknown']
- calls: ['StructureJsonData.__getitem__', 'from_dict', 'StructureJsonData.graph_converter']
- called_by: ['StructureJsonData.__getitem__']
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:622

### StructureJsonData.get_train_val_test_loader
- type: method
- purpose: Partition the Dataset using materials id,
- inputs: ['train_ratio', 'val_ratio']
- outputs: ['unknown']
- calls: ['StructureJsonData', 'DataLoader']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:670

### collate_graphs
- type: function
- purpose: Collate of list of (graph, target) into batch data.
- inputs: ['batch_data']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:768

### get_train_val_test_loader
- type: function
- purpose: Randomly partition a dataset into train, val, test loaders.
- inputs: ['dataset']
- outputs: ['unknown']
- calls: ['DataLoader', 'SubsetRandomSampler']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:794

### get_loader
- type: function
- purpose: Get a dataloader from a dataset.
- inputs: ['dataset']
- outputs: ['unknown']
- calls: ['DataLoader']
- called_by: []
- location: Loss_Phase\Loss_hull\dataset_ehull_in.py:862

### TrainerHull.__init__
- type: method
- purpose: Initialize all hyper-parameters for trainer.
- inputs: ['model']
- outputs: ['unknown']
- calls: ['CombinedLossHull', 'determine_device', 'MultiStepLR', 'init', 'ExponentialLR', 'count', 'CosineAnnealingLR', 'CosineAnnealingWarmRestarts']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:43

### TrainerHull.train
- type: method
- purpose: Train the model using torch data_loaders.
- inputs: ['train_loader', 'val_loader', 'test_loader']
- outputs: ['unknown']
- calls: ['TrainerHull._train', 'TrainerHull._validate', 'TrainerHull.save', 'TrainerHull.save_checkpoint', 'load']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:253

### TrainerHull._train
- type: method
- purpose: Train all data for one epoch.
- inputs: ['train_loader', 'current_epoch', 'wandb_log_freq']
- outputs: ['unknown']
- calls: ['AverageMeter', 'perf_counter', 'TrainerHull.model', 'TrainerHull.criterion', 'TrainerHull.move_to']
- called_by: ['TrainerHull.train']
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:359

### TrainerHull._validate
- type: method
- purpose: Validation or test step.
- inputs: ['val_loader']
- outputs: ['unknown']
- calls: ['AverageMeter', 'perf_counter', 'TrainerHull.model', 'TrainerHull.criterion', 'write_json', 'TrainerHull.move_to']
- called_by: ['TrainerHull.train']
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:457

### TrainerHull.get_best_model
- type: method
- purpose: Get best model recorded in the trainer.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:620

### TrainerHull._init_keys
- type: method
- purpose: unknown
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['signature']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:633

### TrainerHull.save
- type: method
- purpose: Save the model, graph_converter, etc.
- inputs: ['filename']
- outputs: ['unknown']
- calls: ['save']
- called_by: ['TrainerHull.train', 'TrainerHull.save_checkpoint']
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:640

### TrainerHull.save_checkpoint
- type: method
- purpose: Function to save CHGNet trained weights after each epoch.
- inputs: ['epoch', 'mae_error', 'save_dir']
- outputs: ['unknown']
- calls: ['TrainerHull.save']
- called_by: ['TrainerHull.train']
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:651

### TrainerHull.load
- type: method
- purpose: Load trainer state_dict.
- inputs: ['path']
- outputs: ['unknown']
- calls: ['load', 'from_dict', 'cls', 'device']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:694

### TrainerHull.move_to
- type: method
- purpose: Move object to device.
- inputs: ['obj', 'device']
- outputs: ['unknown']
- calls: []
- called_by: ['TrainerHull._train', 'TrainerHull._validate']
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:717

### CombinedLossHull.__init__
- type: method
- purpose: Initialize the combined loss.
- inputs: ['unknown']
- outputs: ['unknown']
- calls: ['HuberLoss', 'MSELoss', 'L1Loss']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:748

### CombinedLossHull.forward
- type: method
- purpose: Compute the combined loss using CHGNet prediction and labels
- inputs: ['targets', 'prediction']
- outputs: ['unknown']
- calls: ['mae', 'CombinedLossHull.ehull_criterion', 'CombinedLossHull.criterion']
- called_by: []
- location: Loss_Phase\Loss_hull\trainer_ehull_in.py:810

### correct_energy
- type: function
- purpose: unknown
- inputs: ['structure', 'vasp_energy']
- outputs: ['unknown']
- calls: ['ComputedStructureEntry', 'process_entries']
- called_by: ['load_json_data']
- location: Loss_Phase\Train_auc.py:12

### load_json_data
- type: function
- purpose: init_dir.rglob('*.json')
- inputs: ['init_dir', 'start_index']
- outputs: ['unknown']
- calls: ['from_dict', 'correct_energy']
- called_by: []
- location: Loss_Phase\Train_auc.py:23

### get_Ehull_from_tm
- type: function
- purpose: unknown
- inputs: ['data_dict', 'ref_energy']
- outputs: ['unknown']
- calls: ['maximum']
- called_by: []
- location: Loss_Phase\Train_auc.py:84

### get_Ehull_from_com
- type: function
- purpose: unknown
- inputs: ['data_dict', 'ref_energy']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Train_auc.py:136

### _even_sample_by_group
- type: function
- purpose: unknown
- inputs: ['df', 'col', 'groups', 'target_n', 'is_numeric', 'random_seed']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Train_auc.py:152

### subset_data
- type: function
- purpose: Parameters
- inputs: ['data', 'target_n', 'path_filter', 'phases', 'na_values', 'fixed_counts', 'random_seed']
- outputs: ['unknown']
- calls: []
- called_by: []
- location: Loss_Phase\Train_auc.py:192

## Classes

### StructureDataHull
- methods: ['__init__', 'from_vasp', '__len__', '__getitem__']

### CIFData
- methods: ['__init__', '__len__', '__getitem__']

### GraphData
- methods: ['__init__', '__len__', '__getitem__', 'get_train_val_test_loader']

### StructureJsonData
- methods: ['__init__', '__len__', '__getitem__', 'get_train_val_test_loader']

### TrainerHull
- methods: ['__init__', 'train', '_train', '_validate', 'get_best_model', '_init_keys', 'save', 'save_checkpoint', 'load', 'move_to']

### CombinedLossHull
- methods: ['__init__', 'forward']

## Entry Points

- StructureDataHull.__init__, CIFData.__init__, GraphData.__init__, StructureJsonData.__init__, TrainerHull.__init__, TrainerHull.train, CombinedLossHull.__init__

## Call Graph Summary

子库 **Loss_Phase** 包含 **36** 个函数/方法，**6** 个类。

核心执行链路（从入口到关键逻辑）：
- TrainerHull.__init__ → `CombinedLossHull, determine_device, MultiStepLR, init, ExponentialLR`
- TrainerHull._validate → `AverageMeter, perf_counter, TrainerHull.model, TrainerHull.criterion, write_json`
- TrainerHull.train → `TrainerHull._train, TrainerHull._validate, TrainerHull.save, TrainerHull.save_checkpoint, load`
- TrainerHull._train → `AverageMeter, perf_counter, TrainerHull.model, TrainerHull.criterion, TrainerHull.move_to`
- TrainerHull.load → `load, from_dict, cls, device`
- CIFData.__getitem__ → `CIFData.__getitem__, from_file, CIFData.graph_converter`

## Notes

- 本分析基于 AST 静态分析，仅检测文件内直接函数调用。
- 动态调用（self.xxx、getattr、字典分发等）无法追踪。
- 外部库函数（chgnet、pymatgen、torch、ase 等）未纳入调用链。
- 不确定性信息均标注为 unknown。
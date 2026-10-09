# Loss_Phase 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `StructureDataHull`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 30 行。

```python
StructureDataHull
```

A simple torch Dataset of structures.

## `StructureDataHull.__init__`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 33 行。

```python
StructureDataHull.__init__(self, structures: list[Structure], energies: list[float], forces: list[Sequence[Sequence[float]]], *, stresses: list[Sequence[Sequence[float]]] | None=None, magmoms: list[Sequence[Sequence[float]]] | None=None, erefs=None, ehulls=None, structure_ids: list | None=None, graph_converter: CrystalGraphConverter | None=None, shuffle: bool=True)
```

Initialize the dataset.

Args:
    structures (list[dict]): pymatgen Structure objects.
    energies (list[float]): [data_size, 1]
    forces (list[list[float]]): [data_size, n_atoms, 3]
    stresses (list[list[float]], optional): [data_size, 3, 3]
        Default = None
    magmoms (list[list[float]], optional): [data_size, n_atoms, 1]
        Default = None
    structure_ids (list, optional): a list of ids to track the structures
        Default = None
    graph_converter (CrystalGraphConverter, optional): Converts the structures
        to graphs. If None, it will be set to CHGNet 0.3.0 converter
        with AtomGraph cutoff = 6A.
    shuffle (bool): whether to shuffle the sequence of dataset
        Default = True

Raises:
    RuntimeError: if the length of structures and labels (energies, forces,
        stresses, magmoms) are not equal.

## `StructureDataHull.from_vasp`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 98 行。

```python
StructureDataHull.from_vasp(cls, file_root: str, *, check_electronic_convergence: bool=True, save_path: str | None=None, graph_converter: CrystalGraphConverter | None=None, shuffle: bool=True)
```

Parse VASP output files into structures and labels and feed into the dataset.

Args:
    file_root (str): the directory of the VASP calculation outputs
    check_electronic_convergence (bool): if set to True, this function will
        raise Exception to VASP calculation that did not achieve
        electronic convergence.
        Default = True
    save_path (str): path to save the parsed VASP labels
        Default = None
    graph_converter (CrystalGraphConverter, optional): Converts the structures
        to graphs. If None, it will be set to CHGNet 0.3.0 converter
        with AtomGraph cutoff = 6A.
    shuffle (bool): whether to shuffle the sequence of dataset
        Default = True

## `CIFData`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 206 行。

```python
CIFData
```

A dataset from CIFs.

## `CIFData.__init__`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 209 行。

```python
CIFData.__init__(self, cif_path: str, *, labels: str | dict='labels.json', targets: TrainTask='efsm', graph_converter: CrystalGraphConverter | None=None, energy_key: str='energy_per_atom', force_key: str='force', stress_key: str='stress', magmom_key: str='magmom', shuffle: bool=True)
```

Initialize the dataset from a directory containing CIFs.

Args:
    cif_path (str): path that contain all the graphs, labels.json
    labels (str, dict): the path or dictionary of labels
    targets ("ef" | "efs" | "efm" | "efsm"): The training targets.
        Default = "efsm"
    graph_converter (CrystalGraphConverter, optional): Converts the structures
        to graphs. If None, it will be set to CHGNet 0.3.0 converter
        with AtomGraph cutoff = 6A.
    energy_key (str, optional): the key of energy in the labels.
        Default = "energy_per_atom"
    force_key (str, optional): the key of force in the labels.
        Default = "force"
    stress_key (str, optional): the key of stress in the labels.
        Default = "stress"
    magmom_key (str, optional): the key of magmom in the labels.
        Default = "magmom"
    shuffle (bool): whether to shuffle the sequence of dataset
        Default = True

## `GraphData`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 320 行。

```python
GraphData
```

A dataset of graphs. This is compatible with the graph.pt documents made by
make_graphs.py. We recommend you to use the dataset to avoid graph conversion steps.

## `GraphData.__init__`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 325 行。

```python
GraphData.__init__(self, graph_path: str, *, labels: str | dict='labels.json', targets: TrainTask='efsm', exclude: str | list | None=None, energy_key: str='energy_per_atom', force_key: str='force', stress_key: str='stress', magmom_key: str='magmom', shuffle: bool=True)
```

Initialize the dataset from a directory containing saved crystal graphs.

Args:
    graph_path (str): path that contain all the graphs, labels.json
    labels (str, dict): the path or dictionary of labels.
        Default = "labels.json"
    targets ("ef" | "efs" | "efm" | "efsm"): The training targets.
        Default = "efsm"
    exclude (str, list | None): the path or list of excluded graphs.
        Default = None
    energy_key (str, optional): the key of energy in the labels.
        Default = "energy_per_atom"
    force_key (str, optional): the key of force in the labels.
        Default = "force"
    stress_key (str, optional): the key of stress in the labels.
        Default = "stress"
    magmom_key (str, optional): the key of magmom in the labels.
        Default = "magmom"
    shuffle (bool): whether to shuffle the sequence of dataset
        Default = True

## `GraphData.get_train_val_test_loader`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 443 行。

```python
GraphData.get_train_val_test_loader(self, train_ratio: float=0.8, val_ratio: float=0.1, *, train_key: list[str] | None=None, val_key: list[str] | None=None, test_key: list[str] | None=None, batch_size=32, num_workers=0, pin_memory=True)
```

Partition the GraphData using materials id,
randomly select the train_keys, val_keys, test_keys by train val test ratio,
or use pre-defined train_keys, val_keys, and test_keys to create train, val,
test loaders.

Args:
    train_ratio (float): The ratio of the dataset to use for training
        Default = 0.8
    val_ratio (float): The ratio of the dataset to use for validation
        Default: 0.1
    train_key (List(str), optional): a list of mp_ids for train set
    val_key (List(str), optional): a list of mp_ids for val set
    test_key (List(str), optional): a list of mp_ids for test set
    batch_size (int): batch size
        Default = 32
    num_workers (int): The number of worker processes for loading the data
        see torch Dataloader documentation for more info
        Default = 0
    pin_memory (bool): Whether to pin the memory of the data loaders
        Default: True

Returns:
    train_loader, val_loader, test_loader

## `StructureJsonData`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 551 行。

```python
StructureJsonData
```

Read structure and targets from a JSON file.
This class is used to load the MPtrj dataset.

## `StructureJsonData.__init__`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 556 行。

```python
StructureJsonData.__init__(self, data: str | dict, graph_converter: CrystalGraphConverter, *, targets: TrainTask='efsm', energy_key: str='energy_per_atom', force_key: str='force', stress_key: str='stress', magmom_key: str='magmom', shuffle: bool=True)
```

Initialize the dataset by reading JSON files.

Args:
    data (str | dict): file path or dir name that contain all the JSONs
    graph_converter (CrystalGraphConverter): Converts pymatgen.core.Structure
        to CrystalGraph object.
    targets ("ef" | "efs" | "efm" | "efsm"): The training targets.
        Default = "efsm"
    energy_key (str, optional): the key of energy in the labels.
        Default = "energy_per_atom"
    force_key (str, optional): the key of force in the labels.
        Default = "force"
    stress_key (str, optional): the key of stress in the labels.
        Default = "stress"
    magmom_key (str, optional): the key of magmom in the labels.
        Default = "magmom"
    shuffle (bool): whether to shuffle the sequence of dataset
        Default = True

## `StructureJsonData.get_train_val_test_loader`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 670 行。

```python
StructureJsonData.get_train_val_test_loader(self, train_ratio: float=0.8, val_ratio: float=0.1, *, train_key: list[str] | None=None, val_key: list[str] | None=None, test_key: list[str] | None=None, batch_size=32, num_workers=0, pin_memory=True)
```

Partition the Dataset using materials id,
randomly select the train_keys, val_keys, test_keys by train val test ratio,
or use pre-defined train_keys, val_keys, and test_keys to create train, val,
test loaders.

Args:
    train_ratio (float): The ratio of the dataset to use for training
        Default = 0.8
    val_ratio (float): The ratio of the dataset to use for validation
        Default: 0.1
    train_key (List(str), optional): a list of mp_ids for train set
    val_key (List(str), optional): a list of mp_ids for val set
    test_key (List(str), optional): a list of mp_ids for test set
    batch_size (int): batch size
        Default = 32
    num_workers (int): The number of worker processes for loading the data
        see torch Dataloader documentation for more info
        Default = 0
    pin_memory (bool): Whether to pin the memory of the data loaders
        Default: True

Returns:
    train_loader, val_loader, test_loader

## `collate_graphs`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 768 行。

```python
collate_graphs(batch_data: list)
```

Collate of list of (graph, target) into batch data.

Args:
    batch_data (list): list of (graph, target(dict))

Returns:
    graphs (List): a list of graphs
    targets (Dict): dictionary of targets, where key and values are:
        e (Tensor): energies of the structures [batch_size]
        f (Tensor): forces of the structures [n_batch_atoms, 3]
        s (Tensor): stresses of the structures [3*batch_size, 3]
        m (Tensor): magmom of the structures [n_batch_atoms]

## `get_train_val_test_loader`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 794 行。

```python
get_train_val_test_loader(dataset: Dataset, *, batch_size: int=64, train_ratio: float=0.8, val_ratio: float=0.1, return_test: bool=True, num_workers: int=0, pin_memory: bool=True)
```

Randomly partition a dataset into train, val, test loaders.

Args:
    dataset (Dataset): The dataset to partition.
    batch_size (int): The batch size for the data loaders
        Default = 64
    train_ratio (float): The ratio of the dataset to use for training
        Default = 0.8
    val_ratio (float): The ratio of the dataset to use for validation
        Default: 0.1
    return_test (bool): Whether to return a test data loader
        Default = True
    num_workers (int): The number of worker processes for loading the data
        see torch Dataloader documentation for more info
        Default = 0
    pin_memory (bool): Whether to pin the memory of the data loaders
        Default: True

Returns:
    train_loader, val_loader and optionally test_loader

## `get_loader`

源文件：[Loss_hull/dataset_ehull_in.py](Loss_hull/dataset_ehull_in.py)，第 862 行。

```python
get_loader(dataset, *, batch_size: int=64, num_workers: int=0, pin_memory: bool=True)
```

Get a dataloader from a dataset.

Args:
    dataset (Dataset): The dataset to partition.
    batch_size (int): The batch size for the data loaders
        Default = 64
    num_workers (int): The number of worker processes for loading the data
        see torch Dataloader documentation for more info
        Default = 0
    pin_memory (bool): Whether to pin the memory of the data loaders
        Default: True

Returns:
    data_loader

## `TrainerHull`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 40 行。

```python
TrainerHull
```

A trainer to train CHGNet using energy, force, stress and magmom.

## `TrainerHull.__init__`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 43 行。

```python
TrainerHull.__init__(self, model: CHGNet | None=None, *, targets: TrainTask='ef', energy_loss_ratio: float=1, force_loss_ratio: float=1, stress_loss_ratio: float=0.1, mag_loss_ratio: float=0.1, ehull_loss_ratio: float=0, ehull_T: float=0.03, optimizer: str='Adam', scheduler: str='CosLR', criterion: str='MSE', epochs: int=50, starting_epoch: int=0, learning_rate: float=0.001, print_freq: int=100, torch_seed: int | None=None, data_seed: int | None=None, use_device: str | None=None, check_cuda_mem: bool=False, wandb_path: str | None=None, wandb_init_kwargs: dict | None=None, extra_run_config: dict | None=None, **kwargs)
```

Initialize all hyper-parameters for trainer.

Args:
    model (nn.Module): a CHGNet model
    targets ("ef" | "efs" | "efsm"): The training targets. Default = "ef"
    energy_loss_ratio (float): energy loss ratio in loss function
        Default = 1
    force_loss_ratio (float): force loss ratio in loss function
        Default = 1
    stress_loss_ratio (float): stress loss ratio in loss function
        Default = 0.1
    mag_loss_ratio (float): magmom loss ratio in loss function
        Default = 0.1
    optimizer (str): optimizer to update model. Can be "Adam", "SGD", "AdamW",
        "RAdam". Default = 'Adam'
    scheduler (str): learning rate scheduler. Can be "CosLR", "ExponentialLR",
        "CosRestartLR". Default = 'CosLR'
    criterion (str): loss function criterion. Can be "MSE", "Huber", "MAE"
        Default = 'MSE'
    epochs (int): number of epochs for training
        Default = 50
    starting_epoch (int): The epoch number to start training at.
    learning_rate (float): initial learning rate
        Default = 1e-3
    print_freq (int): frequency to print training output
        Default = 100
    torch_seed (int): random seed for torch
        Default = None
    data_seed (int): random seed for random
        Default = None
    use_device (str, optional): The device to be used for predictions,
        either "cpu", "cuda", or "mps". If not specified, the default device is
        automatically selected based on the available options.
        Default = None
    check_cuda_mem (bool): Whether to use cuda with most available memory
        Default = False
    wandb_path (str | None): The project and run name separated by a slash:
        "project/run_name". If None, wandb logging is not used.
        Default = None
    wandb_init_kwargs (dict): Additional kwargs to pass to wandb.init.
        Default = None
    extra_run_config (dict): Additional hyper-params to be recorded by wandb
        that are not included in the trainer_args. Default = None

    **kwargs (dict): additional hyper-params for optimizer, scheduler, etc.

Raises:
    NotImplementedError: If the optimizer or scheduler is not implemented
    ImportError: If wandb_path is specified but wandb is not installed
    ValueError: If wandb_path is specified but not in the format
        'project/run_name'

## `TrainerHull.train`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 253 行。

```python
TrainerHull.train(self, train_loader: DataLoader, val_loader: DataLoader, test_loader: DataLoader | None=None, *, save_dir: str | None=None, save_test_result: bool=False, train_composition_model: bool=False, wandb_log_freq: LogFreq=LogEachBatch)
```

Train the model using torch data_loaders.

Args:
    train_loader (DataLoader): train loader to update CHGNet weights
    val_loader (DataLoader): val loader to test accuracy after each epoch
    test_loader (DataLoader):  test loader to test accuracy at end of training.
        Can be None.
        Default = None
    save_dir (str): the dir name to save the trained weights
        Default = None
    save_test_result (bool): Whether to save the test set prediction in a JSON
        file. Default = False
    train_composition_model (bool): whether to train the composition model
        (AtomRef), this is suggested when the fine-tuning dataset has large
        elemental energy shift from the pretrained CHGNet, which typically comes
        from different DFT pseudo-potentials.
        Default = False
    wandb_log_freq ("epoch" | "batch"): Frequency of logging to wandb.
        'epoch' logs once per epoch, 'batch' logs after every batch.
        Default = "batch"

Raises:
    ValueError: If model is not initialized

## `TrainerHull.get_best_model`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 620 行。

```python
TrainerHull.get_best_model(self)
```

Get best model recorded in the trainer.

Returns:
    CHGNet: the model with lowest validation set energy error

## `TrainerHull.save`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 640 行。

```python
TrainerHull.save(self, filename: str='training_result.pth.tar')
```

Save the model, graph_converter, etc.

## `TrainerHull.save_checkpoint`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 651 行。

```python
TrainerHull.save_checkpoint(self, epoch: int, mae_error: dict, save_dir: str)
```

Function to save CHGNet trained weights after each epoch.

Args:
    epoch (int): the epoch number
    mae_error (dict): dictionary that stores the MAEs
    save_dir (str): the directory to save trained weights

## `TrainerHull.load`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 694 行。

```python
TrainerHull.load(cls, path: str)
```

Load trainer state_dict.

Args:
    path (str): path to the saved model

Returns:
    Trainer: the loaded trainer

## `TrainerHull.move_to`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 717 行。

```python
TrainerHull.move_to(obj: Tensor | list[Tensor], device: torch.device)
```

Move object to device.

Args:
    obj (Tensor | list[Tensor]): object(s) to move to device
    device (torch.device): device to move object to

Raises:
    TypeError: if obj is not a tensor or list of tensors

Returns:
    Tensor | list[Tensor]: moved object(s)

## `CombinedLossHull`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 745 行。

```python
CombinedLossHull
```

A combined loss function of energy, force, stress and magmom.

## `CombinedLossHull.__init__`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 748 行。

```python
CombinedLossHull.__init__(self, *, target_str: str='ef', criterion: str='MSE', ehull_T: float=0.03, is_intensive: bool=True, energy_loss_ratio: float=1, force_loss_ratio: float=1, stress_loss_ratio: float=0.1, mag_loss_ratio: float=0.1, ehull_loss_ratio: float=0.0, delta: float=0.1)
```

Initialize the combined loss.

Args:
    target_str: the training target label. Can be "e", "ef", "efs", "efsm" etc.
        Default = "ef"
    criterion: loss criterion to use
        Default = "MSE"
    is_intensive (bool): whether the energy label is intensive
        Default = True
    energy_loss_ratio (float): energy loss ratio in loss function
        Default = 1
    force_loss_ratio (float): force loss ratio in loss function
        Default = 1
    stress_loss_ratio (float): stress loss ratio in loss function
        Default = 0.1
    mag_loss_ratio (float): magmom loss ratio in loss function
        Default = 0.1
    delta (float): delta for torch.nn.HuberLoss. Default = 0.1

## `CombinedLossHull.forward`

源文件：[Loss_hull/trainer_ehull_in.py](Loss_hull/trainer_ehull_in.py)，第 810 行。

```python
CombinedLossHull.forward(self, targets: dict[str, Tensor], prediction: dict[str, Tensor])
```

Compute the combined loss using CHGNet prediction and labels
this function can automatically mask out magmom loss contribution of
data points without magmom labels.

Args:
    targets (dict): DFT labels
    prediction (dict): CHGNet prediction

Returns:
    dictionary of all the loss, MAE and MAE_size

## `correct_energy`

源文件：[Train_auc.py](Train_auc.py)，第 12 行。

```python
correct_energy(structure, vasp_energy)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `load_json_data`

源文件：[Train_auc.py](Train_auc.py)，第 23 行。

```python
load_json_data(init_dir: p, start_index: int=5)
```

init_dir.rglob('*.json')
keys:"structures", "energies", "forces", "stresses", "magmoms", "formula", "TM_group", "Com_group", "path", "index", "Na_con", "Fe_con", "unit_num", "phase", "file_id"

## `get_Ehull_from_tm`

源文件：[Train_auc.py](Train_auc.py)，第 84 行。

```python
get_Ehull_from_tm(data_dict: dict, ref_energy: bool=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `get_Ehull_from_com`

源文件：[Train_auc.py](Train_auc.py)，第 136 行。

```python
get_Ehull_from_com(data_dict: dict, ref_energy: bool=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `subset_data`

源文件：[Train_auc.py](Train_auc.py)，第 192 行。

```python
subset_data(data, target_n, path_filter=None, phases=None, na_values=None, fixed_counts=None, random_seed=None)
```

Parameters
----------
data          : dict
target_n      : int
path_filter   : str
phases        : list
na_values     : list
fixed_counts  : dict
    e.g.
    {'OP2':100, 'O3':50}   {0.5:80, 0.7:120}

random_seed   : int


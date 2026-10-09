# Process_Chgnet 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `vasp_to_chgnetJson`

源文件：[Convert_json.py](Convert_json.py)，第 31 行。

```python
vasp_to_chgnetJson(init_dir: p, tar_path: p, update: bool=True, check_converge: bool=True)
```

Convert VASP results to CHGNet JSON format.

Returns:
    1 if conversion succeeded, 0 if skipped.

## `get_ase_from_json`

源文件：[Json_To_AES.py](Json_To_AES.py)，第 9 行。

```python
get_ase_from_json(file: p, is_force: bool=True, is_correct: bool=True)
```

read chgnet json return list
default correct = True
ase_atoms.info['REF_energy'] = vasp_energy 
ase_atoms.arrays['REF_forces'] = vasp_force
:param file: 说明
:type file: p
:return: 说明
:rtype: list

## `load_chgnet_json`

源文件：[Out_Fromjson.py](Out_Fromjson.py)，第 10 行。

```python
load_chgnet_json(json_path, model=None, last_only: bool=True, tasks: str='e', return_struct: bool=False, energy_correction: bool=True, include_el: bool=False)
```

model : object or None
    ML model with:
        model.predict_structure(struct)
    If None -> only load VASP results

last_only : bool
tasks : str efsm
Returns
-------
dict or list[dict]

## `out_from_struct`

源文件：[Out_Fromstruct.py](Out_Fromstruct.py)，第 7 行。

```python
out_from_struct(struct, energy, forces=None, magmoms=None, stress=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `chgnet_relax`

源文件：[Out_Fromstruct.py](Out_Fromstruct.py)，第 24 行。

```python
chgnet_relax(struct: Structure, relaxer, model, include_f: bool=False, include_m: bool=False, include_traj: bool=False, fmax: float=0.02, steps: int=400)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `convert_traj_to_data`

源文件：[Out_Fromstruct.py](Out_Fromstruct.py)，第 41 行。

```python
convert_traj_to_data(traj, include_f=False, include_s=False, include_m=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `extract_stages_traj`

源文件：[Out_Fromstruct.py](Out_Fromstruct.py)，第 83 行。

```python
extract_stages_traj(data: dict, out_dir: p, path: str)
```

data: traj
out_dir: if not None, save struct to out_dir
path: info


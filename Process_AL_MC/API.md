# Process_AL_MC 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `extract_data_from_mcjson`

源文件：[Auc_code.py](Auc_code.py)，第 5 行。

```python
extract_data_from_mcjson(json_file, tar, select_num=1)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/extract_trajectory.py](examples/extract_trajectory.py)，第 6 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/na_vacancy_ordering.py](examples/na_vacancy_ordering.py)，第 12 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/read_trace.py](examples/read_trace.py)，第 5 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/tm_ordering.py](examples/tm_ordering.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayeredOxide_MCOrderingClass`

源文件：[MC_sample.py](MC_sample.py)，第 16 行。

```python
LayeredOxide_MCOrderingClass
```

MLIP relaxation and MC ordering for layered Na-TM-O systems.

Supported modes are ``TM_MC_random``, ``TM_MC_input``,
``Na_MC_input``, and ``Relax``. Models can be loaded when the object is
created; the structure, mode, output directory, and run parameters can be
supplied later to :meth:`run`.

Committee:
    - one main model performs relaxation
    - all models evaluate each relaxed structure
    - MC accept/reject uses committee mean energy per atom

Output:
    settings.json
    trace.json
    status.json
    initial_unrelaxed.vasp
    initial_relaxed.vasp
    initial_relax_traj.json
    pool/
        rank_XXX_step_YYYY.vasp
        rank_XXX_step_YYYY_relax_traj.json
        pool_summary.json

## `LayeredOxide_MCOrderingClass.__init__`

源文件：[MC_sample.py](MC_sample.py)，第 67 行。

```python
LayeredOxide_MCOrderingClass.__init__(self, structure=None, mode=None, out_dir=None, temperature=300, max_steps=1000, seed=0, pool_size=50, fmax=0.05, relax_steps=150, relax_cell=True, save_every=100, patience=10, energy_tol=0.001, tm_original_element=None, tm_ratios=None, na_remove_num=0, max_duplicate_trials=100, model_path=None, model_paths=None, main_model_index=0, model_type='chgnet', device='cpu', mace_head=None, mace_default_dtype='float64', initialize='random', full_na_structure=None, save_relax_traj=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayeredOxide_MCOrderingClass.prepare`

源文件：[MC_sample.py](MC_sample.py)，第 477 行。

```python
LayeredOxide_MCOrderingClass.prepare(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayeredOxide_MCOrderingClass.run`

源文件：[MC_sample.py](MC_sample.py)，第 1213 行。

```python
LayeredOxide_MCOrderingClass.run(self, structure=None, mode=None, out_dir=None, **options)
```

Configure and execute one MC or relaxation run.

Args:
    structure: Structure file path or pymatgen ``Structure``.
    mode: One of ``TM_MC_random``, ``TM_MC_input``,
        ``Na_MC_input``, or ``Relax``.
    out_dir: Directory in which to save the run outputs.
    **options: Optional run parameters such as ``max_steps``,
        ``tm_ratios``, ``full_na_structure``, and ``patience``.

Returns:
    For ``Relax`` and ``Na_MC_input`` without a valid Na/Vac swap, the
    relaxed structure, final committee evaluation, and relaxation
    trajectory. Other MC runs return ``None``.


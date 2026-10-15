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

源文件：[MC_sample.py](MC_sample.py)，第 17 行。

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

源文件：[MC_sample.py](MC_sample.py)，第 72 行。

```python
LayeredOxide_MCOrderingClass.__init__(self, structure=None, mode=None, out_dir=None, temperature=300, max_steps=1000, seed=0, pool_size=50, fmax=0.05, relax_steps=150, relax_cell=True, save_every=100, patience=10, energy_tol=0.001, tm_original_element=None, tm_ratios=None, na_remove_num=0, max_duplicate_trials=100, model_path=None, model_paths=None, main_model_index=0, model_type='chgnet', device='cpu', mace_head=None, mace_default_dtype='float64', initialize='random', full_na_structure=None, save_relax_traj=False, occupation_history_scope=None, occupation_history_seed=None, occupation_reference_file=None, min_improvement=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayeredOxide_MCOrderingClass.prepare`

源文件：[MC_sample.py](MC_sample.py)，第 503 行。

```python
LayeredOxide_MCOrderingClass.prepare(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayeredOxide_MCOrderingClass.run`

源文件：[MC_sample.py](MC_sample.py)，第 1259 行。

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

## `pack_occupation`

源文件：[occupation_history.py](occupation_history.py)，第 14 行。

```python
pack_occupation(occupation)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `site_layout`

源文件：[occupation_history.py](occupation_history.py)，第 24 行。

```python
site_layout(structure)
```

Hash ordered reference sites once, never relaxed coordinates or symmetry.

## `encode_snapshot`

源文件：[occupation_history.py](occupation_history.py)，第 34 行。

```python
encode_snapshot(scope, site_count, basis, records)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `decode_snapshot`

源文件：[occupation_history.py](occupation_history.py)，第 44 行。

```python
decode_snapshot(data)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReferenceOccupations`

源文件：[occupation_history.py](occupation_history.py)，第 65 行。

```python
ReferenceOccupations
```

Optional per-run reference; the caller owns cross-run persistence.

## `ReferenceOccupations.__init__`

源文件：[occupation_history.py](occupation_history.py)，第 68 行。

```python
ReferenceOccupations.__init__(self, scope, site_count, basis, *, seed=None, reference_file=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReferenceOccupations.add`

源文件：[occupation_history.py](occupation_history.py)，第 95 行。

```python
ReferenceOccupations.add(self, bits)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReferenceOccupations.write_delta`

源文件：[occupation_history.py](occupation_history.py)，第 103 行。

```python
ReferenceOccupations.write_delta(self, path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReferenceOccupations.close`

源文件：[occupation_history.py](occupation_history.py)，第 111 行。

```python
ReferenceOccupations.close(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[ordering/__main__.py](ordering/__main__.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `plan_ordering_search`

源文件：[ordering/api.py](ordering/api.py)，第 14 行。

```python
plan_ordering_search(reference, *, phase, tm_ratios, na_content, max_det_H=None, h_matrices=None, oxidation_states=None, model=None, options=None)
```

Plan fixed-composition H searches and cheap Ewald seeds without MLIP calls.

``na_content`` is Na per O2, ``tm_ratios`` are relative counts, H is exact,
Ewald energies are in eV and MC/ranking energies are eV/atom. A full-Na
reference fixes site numbering. Exactly one H scope selector is required.

## `prepare_ordering_search`

源文件：[ordering/api.py](ordering/api.py)，第 45 行。

```python
prepare_ordering_search(plan, output_dir)
```

Save immutable inputs and a portable runner; no model load or submission.

## `run_ordering_search`

源文件：[ordering/api.py](ordering/api.py)，第 101 行。

```python
run_ordering_search(directory, *, evaluator=None, evaluator_factory=None)
```

Run bounded concurrent chains, reusing completed observations on rerun.

Passing an evaluator enables fake-backend validation. Without one, the
configured main model loads here in its dedicated environment. Interrupted
running claims require explicit reconciliation; no timer silently retries.
History resumes are supported; exact stochastic chain continuation is not
claimed. The output directory has one coordinator and parallel chain workers.

## `inspect_ordering_search`

源文件：[ordering/api.py](ordering/api.py)，第 214 行。

```python
inspect_ordering_search(directory, *, expected_plan_id=None)
```

Inspect completed portable results without loading a model or executing MC.

## `reconcile_ordering_search`

源文件：[ordering/api.py](ordering/api.py)，第 258 行。

```python
reconcile_ordering_search(directory, matrix_id, occupation_key, *, verified_not_running, note)
```

Release one checked failed/interrupted claim; preserve evaluation budgets.

## `digest`

源文件：[ordering/common.py](ordering/common.py)，第 10 行。

```python
digest(value)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `file_digest`

源文件：[ordering/common.py](ordering/common.py)，第 16 行。

```python
file_digest(path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `freeze_model`

源文件：[ordering/common.py](ordering/common.py)，第 24 行。

```python
freeze_model(model)
```

Fingerprint accessible files; remote files require supplied SHA256 values.

## `write_json`

源文件：[ordering/common.py](ordering/common.py)，第 54 行。

```python
write_json(path, value)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `occupation_key`

源文件：[ordering/common.py](ordering/common.py)，第 64 行。

```python
occupation_key(occupation)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `tm_key`

源文件：[ordering/common.py](ordering/common.py)，第 69 行。

```python
tm_key(occupation)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `options`

源文件：[ordering/common.py](ordering/common.py)，第 73 行。

```python
options(values=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `identify_phase`

源文件：[ordering/evaluation.py](ordering/evaluation.py)，第 9 行。

```python
identify_phase(structure, target_phase, H=None)
```

Conservative oxygen-triangle check; ambiguous classifications remain X.

## `MACEOrderingEvaluator`

源文件：[ordering/evaluation.py](ordering/evaluation.py)，第 59 行。

```python
MACEOrderingEvaluator
```

One existing main model per worker; optional committee metrics do not rank.

## `MACEOrderingEvaluator.__init__`

源文件：[ordering/evaluation.py](ordering/evaluation.py)，第 62 行。

```python
MACEOrderingEvaluator.__init__(self, model, config)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `write_csv`

源文件：[ordering/export.py](ordering/export.py)，第 35 行。

```python
write_csv(path, rows)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `export_results`

源文件：[ordering/export.py](ordering/export.py)，第 53 行。

```python
export_results(plan, root, stores, chains)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore`

源文件：[ordering/history.py](ordering/history.py)，第 12 行。

```python
OccupationStore
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.__init__`

源文件：[ordering/history.py](ordering/history.py)，第 13 行。

```python
OccupationStore.__init__(self, path, identity)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.transaction`

源文件：[ordering/history.py](ordering/history.py)，第 38 行。

```python
OccupationStore.transaction(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.claim`

源文件：[ordering/history.py](ordering/history.py)，第 52 行。

```python
OccupationStore.claim(self, key, tm_key, occupation, owner, *, budget=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.complete`

源文件：[ordering/history.py](ordering/history.py)，第 70 行。

```python
OccupationStore.complete(self, key, owner, result)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.fail`

源文件：[ordering/history.py](ordering/history.py)，第 79 行。

```python
OccupationStore.fail(self, key, owner, error)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.records`

源文件：[ordering/history.py](ordering/history.py)，第 86 行。

```python
OccupationStore.records(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.count_completed`

源文件：[ordering/history.py](ordering/history.py)，第 94 行。

```python
OccupationStore.count_completed(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.calls`

源文件：[ordering/history.py](ordering/history.py)，第 98 行。

```python
OccupationStore.calls(self, owner)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `OccupationStore.reconcile`

源文件：[ordering/history.py](ordering/history.py)，第 103 行。

```python
OccupationStore.reconcile(self, key, *, verified_not_running, note)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `normalize_H`

源文件：[ordering/planning.py](ordering/planning.py)，第 14 行。

```python
normalize_H(value)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `select_matrices`

源文件：[ordering/planning.py](ordering/planning.py)，第 32 行。

```python
select_matrices(reference, *, max_det_H=None, h_matrices=None, min_distance=2)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `build_structure`

源文件：[ordering/planning.py](ordering/planning.py)，第 80 行。

```python
build_structure(matrix, occupation)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `random_occupation`

源文件：[ordering/planning.py](ordering/planning.py)，第 96 行。

```python
random_occupation(matrix, rng)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `initialize`

源文件：[ordering/planning.py](ordering/planning.py)，第 131 行。

```python
initialize(matrix, config, supplied_charges)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `make_plan`

源文件：[ordering/planning.py](ordering/planning.py)，第 196 行。

```python
make_plan(reference, *, phase, tm_ratios, na_content, max_det_H=None, h_matrices=None, oxidation_states=None, model=None, search_options=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `trial`

源文件：[ordering/search.py](ordering/search.py)，第 13 行。

```python
trial(occupation, matrix, config, rng)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `run_chain`

源文件：[ordering/search.py](ordering/search.py)，第 33 行。

```python
run_chain(plan, matrix, initial, chain_index, root, store, evaluator)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。


# Process_Vasp 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `main`

源文件：[examples/amset_crt.py](examples/amset_crt.py)，第 9 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/create_workflow.py](examples/create_workflow.py)，第 14 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/dos_to_csv.py](examples/dos_to_csv.py)，第 10 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/excited_inputs.py](examples/excited_inputs.py)，第 12 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/followup.py](examples/followup.py)，第 8 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/read_results.py](examples/read_results.py)，第 10 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `generate_amset_task`

源文件：[inputs/amset_task.py](inputs/amset_task.py)，第 8 行。

```python
generate_amset_task(directory, *, workflow_root='..', source_dir=None, source_stage='dos', doping=(-1e+18, 1e+18), temperatures=(300,), relaxation_time=1e-14, interpolation_factor=10, nworkers=2)
```

Write an uploadable task with bundled helpers, config and Slurm script.

Server workflow_root is relative to generated task location or absolute.
Units and calculation semantics follow run_amset_postprocess. Generation uses
only stdlib, requires an absent/empty target and does not access server data.
Generated task requires AMSET/numpy, not an uploaded Py-Code installation.
Edit partition/environment in submit_amset.sh for the target cluster. Output
remains in this task's results/; resubmission reuses completed CRT requests.

## `continue_task`

源文件：[inputs/continue_task.py](inputs/continue_task.py)，第 7 行。

```python
continue_task(config, directory=None)
```

Prepare a task from a JSON path or dict; never run or submit calculations.

JSON selects calculation and exactly one of structure_file/previous_task.
Local structure_file is relative to the JSON; previous_task is a server path,
relative to the generated task when not absolute. Default target is a sibling
<config-stem>_task. Requires an absent/empty target. Writes workflow.json,
workflow.py, submit.sh and optionally initial structure. No random seed.
Execution uses the installed Process_Vasp project and atomate2/AMSET as needed.

## `generate_excited_input`

源文件：[inputs/excitation.py](inputs/excitation.py)，第 16 行。

```python
generate_excited_input(ground_dir: str | Path, target_dir: str | Path, *, spin: str | None='auto', valence_band: int | None=None, conduction_band: int | None=None)
```

Prepare excitation inputs with spin='auto', 'up', 'down' or 'both'.

Auto (also None) chooses the smallest same-spin band-edge gap; ties choose
up. Explicit band indices do not change this channel-selection rule.
Both creates independent up/ and down/ calculations below target_dir and
returns their reports under those keys. It does not excite both channels
in one calculation. Both requires ISPIN=2. All previous restrictions apply.

## `generate_followup_task`

源文件：[inputs/followup.py](inputs/followup.py)，第 8 行。

```python
generate_followup_task(directory, previous_task, calculation, *, source_stage=None, source_dir=None, incar_settings=None, kpoints_settings=None, job_name=None, export_plot_data=False, amset_settings=None)
```

Generate relax/static/dos/band/amset from a completed task or raw run.

previous_task and source_dir are execution-host paths; relative previous_task
is relative to the new task, source_dir is relative to previous_task. No
source files are read during generation. Defaults: static <- relax;
dos/band <- static; relax <- relax; amset <- dos. Explicit source_stage=relax
for dos/band schedules static then the requested non-SCF calculation.
AMSET can use a verified uniform static calculation via source_stage=static.
Writes an absent/empty task directory, never submits. Existing public
generate_atomate_input remains unchanged. Existing source results are read
only; completed new stages are reused on resubmission. No random seed.

## `generate_atomate_input`

源文件：[inputs/generation.py](inputs/generation.py)，第 16 行。

```python
generate_atomate_input(directory: str | Path, structure: str | Path, calculation: Literal['relax', 'static', 'dos', 'band']='relax', incar_settings: dict[str, dict] | None=None, kpoints_settings: dict[str, dict] | None=None, job_name: str | None=None, resume_from: dict[str, str] | None=None, export_plot_data: bool=False)
```

Create a directly submittable atomate2 workflow from a .vasp or .cif.

Settings are keyed by stage: ``relax``, ``static``, ``dos`` or ``band``.
DOS and band workflows automatically run relax -> static -> non-SCF.
Actual VASP inputs are written by atomate2 when each stage starts.
``static`` runs a single StaticMaker directly, without preceding relaxation.
Stages run in ``runs/relax``, ``runs/static``, ``runs/dos`` or ``runs/band``.
Repeated executions resume completed stages; retries use new attempt directories.
``resume_from`` explicitly adopts validated existing output directories by
stage (paths are evaluated on the execution host); imports are used once.
``export_plot_data`` writes DOS or band CSV and metadata after the final
stage succeeds. It can be enabled later without repeating VASP calculations.

## `convert_dos_to_unix`

源文件：[inputs/generation.py](inputs/generation.py)，第 102 行。

```python
convert_dos_to_unix(file_path: Path)
```

Convert CRLF line endings to LF in one file.

## `convert_files_in_directory`

源文件：[inputs/generation.py](inputs/generation.py)，第 112 行。

```python
convert_files_in_directory(directory_path: str | Path)
```

Recursively convert files below a directory to Unix line endings.

## `generate_vasp_input`

源文件：[inputs/generation.py](inputs/generation.py)，第 119 行。

```python
generate_vasp_input(struct: Structure, tar_dir: str | Path, incar_set: dict, potcar_set: bool, lsfname: str, kpoints_set: Kpoints | None=None)
```

Generate INCAR, KPOINTS, optional POTCAR, and the LSF script.

## `get_INCAR_NUPDOWN`

源文件：[inputs/generation.py](inputs/generation.py)，第 146 行。

```python
get_INCAR_NUPDOWN(struct: Structure)
```

Estimate NUPDOWN from Na, Fe, and Mn composition.

## `set_incar_tags`

源文件：[inputs/incar.py](inputs/incar.py)，第 17 行。

```python
set_incar_tags(lines: Iterable[str], updates: Mapping[str, object])
```

Replace existing INCAR tags and append tags that are absent.

## `update_incar`

源文件：[inputs/incar.py](inputs/incar.py)，第 42 行。

```python
update_incar(init_dir: str | Path, tar_dir: str | Path, mode: str, spin: int | None=None, nupdown: float | None=None, updates: Mapping[str, object] | None=None)
```

Copy and update INCAR in ``Spin`` or ``Correct`` mode.

## `copy_vasp_files`

源文件：[inputs/incar.py](inputs/incar.py)，第 76 行。

```python
copy_vasp_files(init_dir: str | Path, tar_dir: str | Path, files: Mapping[str, str] | Sequence[str] | None=None)
```

Copy selected VASP files and return the created paths.

``files`` may be a source-to-destination mapping or a sequence of names.
Missing files are optional and silently skipped. With the default mapping,
``vasplsf`` is accepted as a fallback for ``vasp.lsf`` and ``CONTCAR`` is
copied as ``POSCAR``. Edit :data:`DEFAULT_VASP_FILES` to extend the defaults.

## `copy_file`

源文件：[inputs/incar.py](inputs/incar.py)，第 111 行。

```python
copy_file(init_dir: str | Path, tar_dir: str | Path)
```

Backward-compatible copy helper using its original file selection.

## `get_completed_result`

源文件：[results/completed.py](results/completed.py)，第 7 行。

```python
get_completed_result(task_dir, stage, *, source_dir=None, validate=True, require_uniform=False)
```

Return a completed relax/static/dos/band directory without modifying it.

Prefer the named completed checkpoint; relative directories use task_dir.
A raw VASP directory can be passed as task_dir or explicitly source_dir.
validate checks electronic convergence, ionic convergence for relax, NSW
semantics and rejects line-mode k points for DOS or require_uniform=True.
This excludes explicit path mode, not a full grid completeness proof. No wavefunction/charge
files required for read-only reuse; downstream calculations check theirs.
Requires pymatgen only when validate=True. No random seed or file writes.

## `read_dos`

源文件：[results/dos.py](results/dos.py)，第 24 行。

```python
read_dos(init_dir: str | Path, output_csv: str | Path | None=None, read_ipr: bool=False, include_orbital: bool=False, ipr_sigma: float | None=None, *, include_element: bool=True, include_total: bool=True, shift_fermi: bool=True, mirror_spin_down: bool=False)
```

Read DOS and calculation metadata; optionally export the numeric table.

Args:
    init_dir: Directory containing ``vasprun.xml`` or ``vasprun.xml.gz``.
        Compressed INCAR and PROCAR are also read directly.
    output_csv: Destination CSV path. None means no file is written.
    read_ipr: Whether to add Gaussian-broadened IPR columns from ``PROCAR``.
    include_orbital: Whether to include the s/p/d/f PDOS of every element.
    ipr_sigma: Gaussian broadening width in eV for the IPR. Defaults to the
        ``SIGMA`` value in ``vasprun.xml``.
    include_element: Include element-projected DOS (enabled by default).
    include_total: Include total DOS.
    shift_fermi: Use E - E_F instead of absolute energy (eV).
    mirror_spin_down: Negate down-spin DOS for mirrored plots; IPR is unchanged.

Returns:
    Dict with ``NEDOS``, ``kpoint_density`` (KPPRA = full mesh size times
    atom count), ``kpoint_mesh``, ``nkpoints``, ``KSPACING``, ``efermi``,
    ``path``, ``composition``, and ``df``. Density is None when no regular
    mesh is available (e.g. explicit or line-mode k-points). ``NEDOS`` is
    read from INCAR when present, otherwise from the recorded XML input.
    ``df`` contains only numeric plotting columns; export with
    ``result['df'].to_csv('dos.csv', index=False)``.

## `read_ipr_data`

源文件：[results/dos.py](results/dos.py)，第 219 行。

```python
read_ipr_data(init_dir: str | Path, output_csv: str | Path | None=None, efermi: float | None=None)
```

Read atom-projected inverse participation ratios from ``PROCAR``.

Args:
    init_dir: Directory containing ``PROCAR`` and, when ``efermi`` is omitted,
        ``vasprun.xml``.
    output_csv: Destination CSV path. Defaults to ``ipr.csv`` in the input directory.
    efermi: Fermi energy used as the energy zero. When omitted, it is read from
        ``vasprun.xml``.

Returns:
    A DataFrame containing energy, spin, k-point, band, and IPR columns.

## `read_ipr`

源文件：[results/dos.py](results/dos.py)，第 280 行。

```python
read_ipr(init_dir: str | Path, output_csv: str | Path | None=None, efermi: float | None=None)
```

Read IPR data from ``PROCAR``, export it to CSV, and return it.

## `check_layered_oxide_moments`

源文件：[results/magnetic_check.py](results/magnetic_check.py)，第 8 行。

```python
check_layered_oxide_moments(elements, moments=None, *, is_layered_oxide=None, noncollinear=False, total_moment=None)
```

Check supported elements' absolute scalar moments in mu_B, without writes.

Layered identity must be supplied by the caller, not inferred from Fe/O alone.
Negative collinear moments are valid. A warning is an empirical range miss,
not proof of an excited state. Unsupported sites are never checked.

## `check_dft_magnetic_moments`

源文件：[results/magnetic_check.py](results/magnetic_check.py)，第 56 行。

```python
check_dft_magnetic_moments(directory, *, structure=None, is_layered_oxide=None, parameters=None)
```

Read the final collinear OUTCAR table (including gzip), then diagnose.

No files are changed. The caller may supply the matching final Structure.
Missing/invalid magnetization is unknown, never a fabricated zero/pass.

## `read_dft_magnetic_data`

源文件：[results/magnetic_check.py](results/magnetic_check.py)，第 80 行。

```python
read_dft_magnetic_data(directory, *, structure=None, parameters=None)
```

Read final per-site moments for ALL elements, without accepting/rejecting spins.

Units are mu_B. Scalar collinear or Cartesian vector noncollinear moments
follow the Structure's atom order. Missing data are explicit, never zeros.
No writes, phase identification, scientific filtering or VASP execution.

## `read_magnetic_moments_outcar`

源文件：[results/magnetism.py](results/magnetism.py)，第 8 行。

```python
read_magnetic_moments_outcar(init_dir: p)
```

read_magnetic_moments_outcar 的 Docstring

:param init_dir: vasp_dir contains output
:type init_dir: p
:return: elements, magnetic_moments, total_magnetic_moment
:rtype: tuple

## `read_vasp_output`

源文件：[results/reader.py](results/reader.py)，第 82 行。

```python
read_vasp_output(init_dir: str | Path, last_step: bool=True, efsm: str='e', read_dos: bool=False)
```

Read selected results from one VASP calculation directory.

Args:
    init_dir: Directory containing ``vasprun.xml`` or ``vasprun.xml.gz``.
    last_step: Read only the final ionic step when true; otherwise read all steps.
    efsm: Fields to read: ``e`` energy, ``f`` forces, ``s`` stress, and ``m`` magnetization.
    read_dos: Read band gap, CBM, VBM, and direct-gap information.

Returns:
    A dictionary containing path, composition, atom count, and requested results.

## `read_vasp_status`

源文件：[results/status.py](results/status.py)，第 44 行。

```python
read_vasp_status(init_dir: str | Path)
```

Read calculation status without modifying VASP input files.

Args:
    init_dir: VASP calculation directory.

Returns:
    Completion, convergence, ionic-step, and detected-error information.

## `deduplicate`

源文件：[structures/structure.py](structures/structure.py)，第 13 行。

```python
deduplicate(struc_lst: list)
```

Load the optional structure toolkit only when deduplication is used.

## `deduplicate_dict`

源文件：[structures/structure.py](structures/structure.py)，第 20 行。

```python
deduplicate_dict(struc_dict: dict)
```

Deduplicate a structure dictionary with the shared implementation.

## `deduplicate_df`

源文件：[structures/structure.py](structures/structure.py)，第 27 行。

```python
deduplicate_df(df: pd.DataFrame, n_keep: int, struct_col: str='struct', energy_col: str='energy_mean_per_atom')
```

Deduplicate a table with the shared implementation.

## `gen_ESGS_structure`

源文件：[structures/structure.py](structures/structure.py)，第 39 行。

```python
gen_ESGS_structure(disordered_structure: Structure, nstr: int)
```

gen_ESGS_structure 的 Docstring

:param disordered_structure: disorderd struct
:type disordered_structure: Structure
:param nstr: generate nstr structs
:type nstr: int
:return: struct_lsit
:rtype: list

## `generate_neb_endpoints`

源文件：[structures/structure.py](structures/structure.py)，第 62 行。

```python
generate_neb_endpoints(fully_intercalated_structure: Structure, deintercalated_structure: Structure, mobile_ion: str, mode: str='random', num_paths_per_ion: int=1, indices: int | Iterable[int] | None=None, random_num: int=3, max_distance: float=5.0, dedu: bool=False, match_tol: float=0.6, overlap_tol: float=0.5, seed: int | None=None)
```

Generate NEB endpoints for hops into vacancies of a deintercalated structure.

In ``select`` mode, ``indices`` are mobile-ion indices in the
deintercalated structure. In ``random`` mode, ``random_num`` unique
ion-vacancy pairs are sampled without replacement.

## `check_layer_equal`

源文件：[structures/structure.py](structures/structure.py)，第 223 行。

```python
check_layer_equal(structure: Structure, element: str='Na', target_layers: int=3, EL_Equal: bool=True)
```

check_layer_equal 的 Docstring

:param structure: Struct
:type structure: Structure
:param element: consider Element
:type element: str
:param target_layers:element layer >= target_layers
:type target_layers: int
:param EL_Equal: if Each Layer element Equal(0,1)
:type EL_Equal: bool
:return: if equal and len (0,1)
:rtype: bool

## `build_redox_disordered_structure`

源文件：[structures/structure.py](structures/structure.py)，第 278 行。

```python
build_redox_disordered_structure(struct, na_num_now)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `remove_oxi`

源文件：[structures/structure.py](structures/structure.py)，第 317 行。

```python
remove_oxi(struct)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `Na1_to_Nax`

源文件：[structures/structure.py](structures/structure.py)，第 329 行。

```python
Na1_to_Nax(struct, tar_dir, interval=3, nstr=3, tar_layer=None, equal_num=None, select_num=None, dedu=False, is_Na0=False, phase=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StageDirectoryTests`

源文件：[tests/test_atomate_directories.py](tests/test_atomate_directories.py)，第 13 行。

```python
StageDirectoryTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StageDirectoryTests.test_invalid_legacy_relax_stops_before_recalculation`

源文件：[tests/test_atomate_directories.py](tests/test_atomate_directories.py)，第 14 行。

```python
StageDirectoryTests.test_invalid_legacy_relax_stops_before_recalculation(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StageDirectoryTests.test_completed_legacy_relax_starts_with_static`

源文件：[tests/test_atomate_directories.py](tests/test_atomate_directories.py)，第 28 行。

```python
StageDirectoryTests.test_completed_legacy_relax_starts_with_static(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StageDirectoryTests.test_failed_relax_uses_valid_contcar_and_reports_quota_error`

源文件：[tests/test_atomate_directories.py](tests/test_atomate_directories.py)，第 71 行。

```python
StageDirectoryTests.test_failed_relax_uses_valid_contcar_and_reports_quota_error(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `StageDirectoryTests.test_restart_parameters_import_and_kill_window`

源文件：[tests/test_atomate_directories.py](tests/test_atomate_directories.py)，第 110 行。

```python
StageDirectoryTests.test_restart_parameters_import_and_kill_window(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 20 行。

```python
ReadDosTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests.setUp`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 21 行。

```python
ReadDosTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests.test_defaults_and_csv_roundtrip`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 33 行。

```python
ReadDosTests.test_defaults_and_csv_roundtrip(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests.test_options_and_explicit_kpoints`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 47 行。

```python
ReadDosTests.test_options_and_explicit_kpoints(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests.test_missing_projection`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 57 行。

```python
ReadDosTests.test_missing_projection(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ReadDosTests.test_gzip_outputs`

源文件：[tests/test_dos.py](tests/test_dos.py)，第 64 行。

```python
ReadDosTests.test_gzip_outputs(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ExcitationTests`

源文件：[tests/test_excitation.py](tests/test_excitation.py)，第 17 行。

```python
ExcitationTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ExcitationTests.test_generation_and_checks`

源文件：[tests/test_excitation.py](tests/test_excitation.py)，第 18 行。

```python
ExcitationTests.test_generation_and_checks(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayoutTests`

源文件：[tests/test_layout.py](tests/test_layout.py)，第 16 行。

```python
LayoutTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayoutTests.test_legacy_modules_are_same_objects`

源文件：[tests/test_layout.py](tests/test_layout.py)，第 17 行。

```python
LayoutTests.test_legacy_modules_are_same_objects(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayoutTests.test_workflow_uses_project_runner_and_template`

源文件：[tests/test_layout.py](tests/test_layout.py)，第 29 行。

```python
LayoutTests.test_workflow_uses_project_runner_and_template(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `LayoutTests.test_vasp_generation_finds_lsf_template`

源文件：[tests/test_layout.py](tests/test_layout.py)，第 46 行。

```python
LayoutTests.test_vasp_generation_finds_lsf_template(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_ranges`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 14 行。

```python
test_ranges(moments, status, count)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_applicability`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 24 行。

```python
test_applicability(elements, layered, expected)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_missing_not_pass`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 29 行。

```python
test_missing_not_pass(moments)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_reader_compressed_and_last_table`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 33 行。

```python
test_reader_compressed_and_last_table(tmp_path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_soc_and_skip_dont_read`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 46 行。

```python
test_soc_and_skip_dont_read(tmp_path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_actual_outcar_final_table`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 56 行。

```python
test_actual_outcar_final_table(tmp_path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_raw_reader_retains_unsupported_elements`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 67 行。

```python
test_raw_reader_retains_unsupported_elements(tmp_path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `test_raw_reader_retains_vector`

源文件：[tests/test_magnetic_check.py](tests/test_magnetic_check.py)，第 77 行。

```python
test_raw_reader_retains_vector(tmp_path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BandExportTests`

源文件：[tests/test_plot_exports.py](tests/test_plot_exports.py)，第 17 行。

```python
BandExportTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BandExportTests.test_band_csv_and_metadata`

源文件：[tests/test_plot_exports.py](tests/test_plot_exports.py)，第 18 行。

```python
BandExportTests.test_band_csv_and_metadata(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `run_amset_crt`

源文件：[workflows/amset_crt.py](workflows/amset_crt.py)，第 46 行。

```python
run_amset_crt(source_dir, output_dir, *, doping=(-1e+18, 1e+18), temperatures=(300,), relaxation_time=1e-14, interpolation_factor=10, nworkers=1, resume=True)
```

Calculate sigma/tau from an existing uniform-grid vasprun.xml[.gz].

Doping is cm^-3 (negative electrons, positive holes), temperatures K,
relaxation_time seconds. Returned tensors have shape (ndoping, nT, 3, 3)
and sigma/tau units S m^-1 s^-1. Requires an environment with AMSET CLI.
Writes isolated attempt directories, logs, settings and a JSON checkpoint;
copies the source XML, never runs VASP. Identical successful requests are
reused; failures/changed requests create another attempt. No random seed.
Resume is at completed-calculation level, not inside AMSET interpolation.

## `main`

源文件：[workflows/amset_crt.py](workflows/amset_crt.py)，第 128 行。

```python
main()
```

CLI with the same default electron/hole CRT settings as the Python API.

## `run_amset_postprocess`

源文件：[workflows/amset_postprocess.py](workflows/amset_postprocess.py)，第 61 行。

```python
run_amset_postprocess(workflow_root, output_dir=None, *, source_dir=None, source_stage='dos', doping=(-1e+18, 1e+18), temperatures=(300,), relaxation_time=1e-14, interpolation_factor=10, nworkers=1, resume=True)
```

Read a completed DOS task and export transport masses and CRT mobility.

workflow_root contains workflow_state.json; source_stage selects dos/static.
source_dir optionally overrides
the DOS path (relative to workflow_root). Default output is root/amset_results.
Units: doping cm^-3 (electrons negative), temperature K, tau s; mass in m_e,
mobility cm²/(V s), sigma/tau S/(m s). Tensor axes match run_amset_crt.
Requires AMSET and numpy; no random seed. Copies XML and writes only to the
independent output subtree; no VASP runs/submission or source modification.
Reuses completed CRT calculations by content/parameter fingerprint; derived
properties can be regenerated without recomputing AMSET. Invalid mass tensors
are null with a diagnostic; CRT success does not imply numerical convergence.

## `run_workflow`

源文件：[workflows/atomate_runner.py](workflows/atomate_runner.py)，第 281 行。

```python
run_workflow(root, *, fresh=False)
```

Resume valid stages, retry interrupted stages, invalidate changed dependencies.

## `main`

源文件：[workflows/atomate_runner.py](workflows/atomate_runner.py)，第 467 行。

```python
main(root)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `execute_task`

源文件：[workflows/continue_runner.py](workflows/continue_runner.py)，第 69 行。

```python
execute_task(task_dir)
```

Execute generated task on cluster. Writes plans/checkpoints; may run VASP.

Original results are read only. AMSET prefers a completed DOS; absent DOS is
generated from available static/relax results via atomate2 before transport.
AMSET-only submission scripts require VASP resources/modules to be configured
if missing precursor calculations need to run. No automatic job submission.

## `export_plot_data`

源文件：[workflows/plot_exports.py](workflows/plot_exports.py)，第 12 行。

```python
export_plot_data(stage, calculation_dir, task_dir)
```

Write DOS or band CSV and metadata; return the created paths.

Energy values are in eV, and ``energy_minus_fermi_eV`` is E - E_F.
Band path distance is in reciprocal angstroms. Existing CSVs are replaced
when a completed calculation is exported again.


# Process_MLIP 参数索引

源码静态索引；保留原有函数名。类构造和公开方法分别列出。默认值不代表适用于所有体系。

## `create_mace_calculator`

源文件：[calculators.py](calculators.py)，第 20 行。

```python
create_mace_calculator(model_path, *, device='cuda', head=None, default_dtype='float64', enable_cueq=False, enable_symmetrix=False, symmetrix_use_kokkos=False, symmetrix_species=None)
```

Load a local MACE checkpoint. MH-1 filenames default to omat_pbe.

Only load trusted checkpoints: MACE deserializes Python model objects.
Pass head explicitly for renamed multihead weights or other DFT tasks.

## `create_sevennet_calculator`

源文件：[calculators.py](calculators.py)，第 97 行。

```python
create_sevennet_calculator(model='7net-omni', *, device='cpu', modal='mpa', enable_flash=False)
```

Load SevenNet-Omni by official name or trusted local checkpoint.

Named models may download weights through SevenNet on first use. Local
paths must exist. modal selects the DFT task (mpa, omat24, etc.); do not
combine energies from different tasks. No dtype conversion is applied.

## `create_chgnet_calculator`

源文件：[calculators.py](calculators.py)，第 130 行。

```python
create_chgnet_calculator(model_path=None, *, device='cuda', model_name='0.3.0', model=None)
```

Load CHGNet pretrained version, trusted local checkpoint, or loaded model.

The official calculator converts stress from GPa to ASE eV/Å³. Only one
of model_path and model may be supplied; no dependencies are installed.

## `create_orb_calculator`

源文件：[calculators.py](calculators.py)，第 149 行。

```python
create_orb_calculator(model_path=None, *, device='cuda', model_name='orb-v3-conservative-inf-omat', precision='float32-highest', compile=False)
```

Load an ORB pretrained architecture, optionally with local weights.

Supports the official model+adapter API and the older model-only API.
model_path must match model_name's architecture. No fallback model is used.

## `create_mlip_calculator`

源文件：[calculators.py](calculators.py)，第 175 行。

```python
create_mlip_calculator(model='mace-mh1')
```

Build exactly one calculator from a preset name or model_config dict.

## `make_calculator`

源文件：[examples/ase_relax.py](examples/ase_relax.py)，第 13 行。

```python
make_calculator()
```

Replace with a calculator compatible with the material and environment.

## `main`

源文件：[examples/ase_relax.py](examples/ase_relax.py)，第 18 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/extract_frames.py](examples/extract_frames.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/mace_relax.py](examples/mace_relax.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/benchmark_runner.py](examples/md_benchmark/benchmark_runner.py)，第 20 行。

```python
main(case)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/01_mace_mh1/run_md.py](examples/md_benchmark/tasks/01_mace_mh1/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/02_mace_omat/run_md.py](examples/md_benchmark/tasks/02_mace_omat/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/03_mace_omat_sym/run_md.py](examples/md_benchmark/tasks/03_mace_omat_sym/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/04_sevennet_omni/run_md.py](examples/md_benchmark/tasks/04_sevennet_omni/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/05_sevennet_omni_flash/run_md.py](examples/md_benchmark/tasks/05_sevennet_omni_flash/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/06_sevennet_nano6/run_md.py](examples/md_benchmark/tasks/06_sevennet_nano6/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/07_sevennet_nano6_flash/run_md.py](examples/md_benchmark/tasks/07_sevennet_nano6_flash/run_md.py)，第 21 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/md_benchmark/tasks/08_chgnet/run_md.py](examples/md_benchmark/tasks/08_chgnet/run_md.py)，第 22 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/mlip_md.py](examples/mlip_md.py)，第 168 行。

```python
main(argv=None)
```

Preview configuration or run MD after editing the parameters above.

## `main`

源文件：[examples/msd.py](examples/msd.py)，第 37 行。

```python
main()
```

Export the entire trajectory, with frame zero as the MSD origin.

## `main`

源文件：[examples/sevennet_relax.py](examples/sevennet_relax.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `relax_structure_mace`

源文件：[mace_relax.py](mace_relax.py)，第 8 行。

```python
relax_structure_mace(structure, model_path, *, output_path=None, device='cuda', head=None, default_dtype='float64', enable_cueq=False, enable_symmetrix=False, symmetrix_use_kokkos=False, symmetrix_species=None, fmax=0.05, steps=150, relax_cell=True)
```

Relax one structure and return final energy, forces, and optimizer facts.

``structure`` may be a path, ASE ``Atoms``, or pymatgen ``Structure``.
No trajectory or per-step files are written. If ``output_path`` is given,
only the final structure is written there.

## `run_md`

源文件：[md.py](md.py)，第 188 行。

```python
run_md(structure, calculator, output_dir, *, ensemble='nvt', temperature_K=300.0, steps=1000, timestep_fs=None, tdamp_fs=100.0, pressure_bar=1.0, pdamp_fs=1000.0, initialize_velocities=None, seed=42, remove_com=True, zero_rotation=False, trajectory_interval=10, log_interval=10, overwrite=False, time_offset_fs=0.0, model_metadata=None, measure_steps_per_second=False, npt_cell_mode='isotropic', tchain=3, pchain=3, tloop=1, ploop=1)
```

Run one NHC NVT or MTK NPT stage with an ASE calculator.

Positions/cell use Å; energies eV, temperature K, time/damping fs, pressure
bar (positive compression). Input atoms are copied. initialize_velocities
None initializes only when momenta are absent; False preserves velocities;
True samples Maxwell-Boltzmann momenta using seed. COM removal/rotation
options apply only to initialization. Constraints are not supported.
npt_cell_mode selects isotropic volume scaling or full flexible-cell MTK.
tchain/tloop control the thermostat; pchain/ploop apply only to NPT.
Chain lengths and integration substeps must be positive integers.
timestep_fs=None selects 2 fs for NVT or 1 fs for NPT; explicit values override.

Writes md.traj, md.csv, final.traj (with momenta), report.json. Existing
owned files require overwrite=True; unrelated files are never removed.
No exact thermostat/barostat restart is provided. Returns final_atoms,
output paths, final thermodynamic state and actual completed step count.
measure_steps_per_second times dyn.run (including observers/output), with
CUDA synchronization. Loading, pre-relaxation, property probes and final
export are excluded. steps_per_second is None when off or steps is zero.

## `run_mlip_md`

源文件：[md_workflow.py](md_workflow.py)，第 14 行。

```python
run_mlip_md(structure, model='mace-mh1', output_dir='md_results', stages=None, *, pre_relax=None, **md_parameters)
```

预弛豫与 MD 共用模型；输出总报告、分阶段轨迹和最终结构。

structure: 结构路径 / ASE Atoms / pymatgen Structure；model: 预设名或配置字典。
stages=None: 单阶段；列表: 顺序衔接，参数优先级为阶段 > 公共 > 默认。
衔接保留位置、晶胞和动量，控温/控压内部状态重置；非精确断点续跑。

pre_relax=None/False: 不弛豫；True/字典: 开启，字典默认值如下：
  enabled=True；relax_cell=False（仅原子，True 为原子+晶胞）。
  optimizer="FIRE"（BFGS / FIRE / LBFGS，须大写）。
  fmax=0.05 eV/Å；steps=200（非负整数）；require_convergence=True（未收敛停止）。
  maxstep=0.05 Å；exp_cell_factor=None（FrechetCellFilter 按原子数缩放）。
MD 默认：NVT、300 K、1000 步；步长 NVT=2 fs、NPT=1 fs，可显式覆盖。
tdamp_fs=100，NPT pdamp_fs=1000；timestep_fs=None 按各阶段系综选择。
NPT 晶胞：isotropic（默认）/ full；tchain/pchain=3，tloop/ploop=1。
trajectory_interval/log_interval=10（步）；seed=42；overwrite=False。
measure_steps_per_second=True 可记录吞吐，排除加载、弛豫与后处理。

参考：pre_relax={"relax_cell": True, "optimizer": "FIRE", "steps": 200}，
配合 temperature_K=600, steps=5000, trajectory_interval=1, log_interval=1。
返回 final_atoms、stage_results、pre_relax_result、steps_per_second 和报告路径；
elapsed_time_fs 为模拟时长。其余 MD 参数见 run_md。

## `MLIPRelaxer`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 7 行。

```python
MLIPRelaxer
```

Relax ASE Atoms with an explicitly supplied calculator.

Modifies the supplied Atoms and retains its constraints. Energies are eV,
fmax is eV/Å. Cell relaxation also tests filter stress degrees of freedom.
maxstep=None uses the ASE optimizer default; positive values limit optimizer
steps (Å for atom variables). FrechetCellFilter scales cell variables by
exp_cell_factor, defaulting to atom count; no direct strain bound is imposed.

## `MLIPRelaxer.__init__`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 17 行。

```python
MLIPRelaxer.__init__(self, atoms, calculator, fmax=0.05, steps=200, optimizer='BFGS', relax_cell=False, *, maxstep=None, exp_cell_factor=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MLIPRelaxer.relax`

源文件：[MLIP_Relax.py](MLIP_Relax.py)，第 64 行。

```python
MLIPRelaxer.relax(self, traj_file='relax.traj', log_file='relax.log', final_structure=None)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `model_config`

源文件：[model_config.py](model_config.py)，第 23 行。

```python
model_config(preset='mace-mh1', **overrides)
```

Return an independent dict of model defaults with explicit overrides.

Presets: mace-mh1, sevennet-omni, chgnet, orb-v3. Default device is cuda;
accelerators default off. model_path overrides pretrained weights. This
function does not check local files, import models, or download anything.

## `export_msd`

源文件：[msd.py](msd.py)，第 48 行。

```python
export_msd(trajectory, output_csv, *, species=None, frame_interval_fs=None, skip_frames=0, number_of_segments=1, unwrap=False, drift_reference=None, overwrite=False)
```

Export true MSD (Å²) from a fixed-cell ASE .traj using ASE analysis.

species: element string/list, or None for all elements. Times are inferred
from adjacent completed MD report.json unless frame_interval_fs is given.
skip_frames removes equilibration frames. ASE divides retained frames into
non-overlapping segments, each referenced to its own first frame; this is
not an overlapping all-time-origin MSD. No diffusion coefficient is exported.

Our MD trajectories are unwrapped, so unwrap defaults False. For wrapped
input, True reconstructs nearest-image increments via ASE find_mic; saved
frames must be frequent enough to avoid ambiguous periodic crossings.
drift_reference='framework' subtracts the mass-weighted COM displacement of
atoms outside selected species. Default None makes no drift correction.

Writes only output_csv (default no overwrite), returns path and provenance.
Source trajectory and report are never modified. No model is loaded.

## `relax_structure_sevennet`

源文件：[sevennet_relax.py](sevennet_relax.py)，第 8 行。

```python
relax_structure_sevennet(structure, model='7net-omni', *, output_path=None, device='cpu', modal='mpa', fmax=0.05, steps=150, relax_cell=True)
```

Return energy (eV), forces (eV/Å), convergence and selected modal.

Inputs are a structure path, ASE Atoms or pymatgen Structure. Atoms are
copied. Only output_path is written (VASP format, overwrites if present).
No random sampling, trajectory or log. Named models may download weights;
supply a trusted local checkpoint for offline repeatable calculations.

## `BenchmarkTaskTests`

源文件：[test_benchmark_tasks.py](test_benchmark_tasks.py)，第 17 行。

```python
BenchmarkTaskTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BenchmarkTaskTests.test_all_eight_default_and_submission_configs`

源文件：[test_benchmark_tasks.py](test_benchmark_tasks.py)，第 18 行。

```python
BenchmarkTaskTests.test_all_eight_default_and_submission_configs(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BenchmarkTaskTests.test_all_eight_real_nvt_msd_pipelines_with_emt`

源文件：[test_benchmark_tasks.py](test_benchmark_tasks.py)，第 42 行。

```python
BenchmarkTaskTests.test_all_eight_real_nvt_msd_pipelines_with_emt(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MaceCompatibilityTests`

源文件：[test_mace_compatibility.py](test_mace_compatibility.py)，第 13 行。

```python
MaceCompatibilityTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MaceCompatibilityTests.test_old_and_new_entry_points`

源文件：[test_mace_compatibility.py](test_mace_compatibility.py)，第 14 行。

```python
MaceCompatibilityTests.test_old_and_new_entry_points(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `NoStress`

源文件：[test_md.py](test_md.py)，第 19 行。

```python
NoStress
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `NoStress.calculate`

源文件：[test_md.py](test_md.py)，第 22 行。

```python
NoStress.calculate(self, atoms=None, properties=None, system_changes=all_changes)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests`

源文件：[test_md.py](test_md.py)，第 27 行。

```python
MDTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.setUp`

源文件：[test_md.py](test_md.py)，第 28 行。

```python
MDTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.run_stage`

源文件：[test_md.py](test_md.py)，第 34 行。

```python
MDTests.run_stage(self, name='md', **kwargs)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_nvt_outputs_seed_and_input_copy`

源文件：[test_md.py](test_md.py)，第 40 行。

```python
MDTests.test_nvt_outputs_seed_and_input_copy(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_independent_npt_and_chained_velocity_preservation`

源文件：[test_md.py](test_md.py)，第 65 行。

```python
MDTests.test_independent_npt_and_chained_velocity_preservation(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_zero_steps_and_file_input_preserve_velocities`

源文件：[test_md.py](test_md.py)，第 80 行。

```python
MDTests.test_zero_steps_and_file_input_preserve_velocities(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_invalid_options_do_not_write`

源文件：[test_md.py](test_md.py)，第 88 行。

```python
MDTests.test_invalid_options_do_not_write(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_constraints_and_nonperiodic_npt_rejected`

源文件：[test_md.py](test_md.py)，第 100 行。

```python
MDTests.test_constraints_and_nonperiodic_npt_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_missing_stress_nvt_allowed_npt_rejected`

源文件：[test_md.py](test_md.py)，第 109 行。

```python
MDTests.test_missing_stress_nvt_allowed_npt_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_output_collision_requires_explicit_overwrite`

源文件：[test_md.py](test_md.py)，第 116 行。

```python
MDTests.test_output_collision_requires_explicit_overwrite(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_failed_dynamics_reported_and_nonfinite_preflight_rejected`

源文件：[test_md.py](test_md.py)，第 127 行。

```python
MDTests.test_failed_dynamics_reported_and_nonfinite_preflight_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDTests.test_nonfinite_model_output_stops_dynamics`

源文件：[test_md.py](test_md.py)，第 146 行。

```python
MDTests.test_nonfinite_model_output_stops_dynamics(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 17 行。

```python
ControllerTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.setUp`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 18 行。

```python
ControllerTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.run_stage`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 24 行。

```python
ControllerTests.run_stage(self, name='md', **parameters)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_defaults_and_invalid_parameters`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 29 行。

```python
ControllerTests.test_defaults_and_invalid_parameters(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_nvt_forwards_only_thermostat_parameters`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 42 行。

```python
ControllerTests.test_nvt_forwards_only_thermostat_parameters(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_isotropic_forwards_both_chains_and_preserves_shape`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 53 行。

```python
ControllerTests.test_isotropic_forwards_both_chains_and_preserves_shape(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_full_dispatch_contract`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 67 行。

```python
ControllerTests.test_full_dispatch_contract(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_missing_full_implementation_fails_before_loading_or_writing`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 77 行。

```python
ControllerTests.test_missing_full_implementation_fails_before_loading_or_writing(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_stage_overrides_and_reporting`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 93 行。

```python
ControllerTests.test_stage_overrides_and_reporting(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ControllerTests.test_real_full_mtk_changes_cell_shape`

源文件：[test_md_controllers.py](test_md_controllers.py)，第 109 行。

```python
ControllerTests.test_real_full_mtk_changes_cell_shape(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests`

源文件：[test_md_example.py](test_md_example.py)，第 16 行。

```python
MDExampleTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.setUp`

源文件：[test_md_example.py](test_md_example.py)，第 17 行。

```python
MDExampleTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.run_example`

源文件：[test_md_example.py](test_md_example.py)，第 29 行。

```python
MDExampleTests.run_example(self, config, stages=None, preview=False)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_enabled_exports_last_nvt_after_md`

源文件：[test_md_example.py](test_md_example.py)，第 40 行。

```python
MDExampleTests.test_enabled_exports_last_nvt_after_md(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_disabled_does_not_call_exporter`

源文件：[test_md_example.py](test_md_example.py)，第 49 行。

```python
MDExampleTests.test_disabled_does_not_call_exporter(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_last_nvt_selection_skips_later_npt`

源文件：[test_md_example.py](test_md_example.py)，第 54 行。

```python
MDExampleTests.test_last_nvt_selection_skips_later_npt(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_custom_path_and_explicit_nvt_stage`

源文件：[test_md_example.py](test_md_example.py)，第 62 行。

```python
MDExampleTests.test_custom_path_and_explicit_nvt_stage(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_no_nvt_or_wrong_stage_rejected_before_loading`

源文件：[test_md_example.py](test_md_example.py)，第 68 行。

```python
MDExampleTests.test_no_nvt_or_wrong_stage_rejected_before_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_existing_csv_rejected_before_loading_and_preview_is_readonly`

源文件：[test_md_example.py](test_md_example.py)，第 77 行。

```python
MDExampleTests.test_existing_csv_rejected_before_loading_and_preview_is_readonly(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDExampleTests.test_md_log_cannot_be_overwritten_and_zero_steps_rejected`

源文件：[test_md_example.py](test_md_example.py)，第 87 行。

```python
MDExampleTests.test_md_log_cannot_be_overwritten_and_zero_steps_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests`

源文件：[test_md_speed.py](test_md_speed.py)，第 16 行。

```python
MDSpeedTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.setUp`

源文件：[test_md_speed.py](test_md_speed.py)，第 17 行。

```python
MDSpeedTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.test_optional_and_validated`

源文件：[test_md_speed.py](test_md_speed.py)，第 23 行。

```python
MDSpeedTests.test_optional_and_validated(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.test_stage_rate_uses_integration_duration_and_is_saved`

源文件：[test_md_speed.py](test_md_speed.py)，第 31 行。

```python
MDSpeedTests.test_stage_rate_uses_integration_duration_and_is_saved(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.test_zero_steps_has_no_rate`

源文件：[test_md_speed.py](test_md_speed.py)，第 40 行。

```python
MDSpeedTests.test_zero_steps_has_no_rate(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.test_gpu_synchronization_brackets_timer`

源文件：[test_md_speed.py](test_md_speed.py)，第 45 行。

```python
MDSpeedTests.test_gpu_synchronization_brackets_timer(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MDSpeedTests.test_workflow_combines_rates_by_total_time`

源文件：[test_md_speed.py](test_md_speed.py)，第 62 行。

```python
MDSpeedTests.test_workflow_combines_rates_by_total_time(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 17 行。

```python
TimestepTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests.setUp`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 18 行。

```python
TimestepTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests.test_defaults_and_explicit_values`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 24 行。

```python
TimestepTests.test_defaults_and_explicit_values(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests.test_run_md_and_msd_time_grid`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 33 行。

```python
TimestepTests.test_run_md_and_msd_time_grid(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests.test_stage_defaults_and_common_stage_overrides`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 46 行。

```python
TimestepTests.test_stage_defaults_and_common_stage_overrides(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TimestepTests.test_example_transport_preflight_with_auto_timestep`

源文件：[test_md_timestep.py](test_md_timestep.py)，第 60 行。

```python
TimestepTests.test_example_transport_preflight_with_auto_timestep(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PresetTests`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 21 行。

```python
PresetTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PresetTests.test_independent_defaults_and_overrides`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 22 行。

```python
PresetTests.test_independent_defaults_and_overrides(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PresetTests.test_dispatch_all_four_backends`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 37 行。

```python
PresetTests.test_dispatch_all_four_backends(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BackendContractTests`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 53 行。

```python
BackendContractTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BackendContractTests.test_mace_and_sevennet_acceleration_flags`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 54 行。

```python
BackendContractTests.test_mace_and_sevennet_acceleration_flags(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BackendContractTests.test_chgnet_pretrained_checkpoint_and_model_instance`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 90 行。

```python
BackendContractTests.test_chgnet_pretrained_checkpoint_and_model_instance(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `BackendContractTests.test_orb_new_and_legacy_api_local_weights`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 110 行。

```python
BackendContractTests.test_orb_new_and_legacy_api_local_weights(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 132 行。

```python
WorkflowTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests.setUp`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 133 行。

```python
WorkflowTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests.test_load_once_stage_precedence_and_continuation`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 142 行。

```python
WorkflowTests.test_load_once_stage_precedence_and_continuation(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests.test_independent_single_stage_and_explicit_resampling`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 163 行。

```python
WorkflowTests.test_independent_single_stage_and_explicit_resampling(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests.test_validate_all_stages_and_collisions_before_loading`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 172 行。

```python
WorkflowTests.test_validate_all_stages_and_collisions_before_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `WorkflowTests.test_failure_summary_does_not_claim_completion`

源文件：[test_md_workflow.py](test_md_workflow.py)，第 195 行。

```python
WorkflowTests.test_failure_summary_does_not_claim_completion(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ModelAdapterTests`

源文件：[test_model_adapters.py](test_model_adapters.py)，第 16 行。

```python
ModelAdapterTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ModelAdapterTests.setUp`

源文件：[test_model_adapters.py](test_model_adapters.py)，第 17 行。

```python
ModelAdapterTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ModelAdapterTests.test_mh1_filename_variants_and_explicit_head`

源文件：[test_model_adapters.py](test_model_adapters.py)，第 23 行。

```python
ModelAdapterTests.test_mh1_filename_variants_and_explicit_head(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ModelAdapterTests.test_omni_modal_and_cell_relaxation`

源文件：[test_model_adapters.py](test_model_adapters.py)，第 37 行。

```python
ModelAdapterTests.test_omni_modal_and_cell_relaxation(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `ModelAdapterTests.test_invalid_parameters_and_missing_weights`

源文件：[test_model_adapters.py](test_model_adapters.py)，第 60 行。

```python
ModelAdapterTests.test_invalid_parameters_and_missing_weights(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests`

源文件：[test_msd.py](test_msd.py)，第 19 行。

```python
MSDTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.setUp`

源文件：[test_msd.py](test_msd.py)，第 20 行。

```python
MSDTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.trajectory`

源文件：[test_msd.py](test_msd.py)，第 25 行。

```python
MSDTests.trajectory(self, positions, name='md.traj', symbols='NaO', cell=10)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.rows`

源文件：[test_msd.py](test_msd.py)，第 32 行。

```python
MSDTests.rows(self, path)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_true_msd_normalization_and_species_selection_use_ase`

源文件：[test_msd.py](test_msd.py)，第 36 行。

```python
MSDTests.test_true_msd_normalization_and_species_selection_use_ase(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_unwrapped_large_displacements_are_preserved_by_default`

源文件：[test_msd.py](test_msd.py)，第 52 行。

```python
MSDTests.test_unwrapped_large_displacements_are_preserved_by_default(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_species_population_average`

源文件：[test_msd.py](test_msd.py)，第 57 行。

```python
MSDTests.test_species_population_average(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_real_nvt_trajectory_all_frames_and_automatic_times`

源文件：[test_msd.py](test_msd.py)，第 65 行。

```python
MSDTests.test_real_nvt_trajectory_all_frames_and_automatic_times(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_wrapped_nonorthogonal_cell`

源文件：[test_msd.py](test_msd.py)，第 76 行。

```python
MSDTests.test_wrapped_nonorthogonal_cell(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_wrapped_trajectory_uses_ase_minimum_image`

源文件：[test_msd.py](test_msd.py)，第 86 行。

```python
MSDTests.test_wrapped_trajectory_uses_ase_minimum_image(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_framework_drift_correction`

源文件：[test_msd.py](test_msd.py)，第 93 行。

```python
MSDTests.test_framework_drift_correction(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_report_time_axis_includes_irregular_last_frame`

源文件：[test_msd.py](test_msd.py)，第 99 行。

```python
MSDTests.test_report_time_axis_includes_irregular_last_frame(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_skip_segments_and_multiple_species`

源文件：[test_msd.py](test_msd.py)，第 109 行。

```python
MSDTests.test_skip_segments_and_multiple_species(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_missing_time_invalid_options_and_output_protection`

源文件：[test_msd.py](test_msd.py)，第 118 行。

```python
MSDTests.test_missing_time_invalid_options_and_output_protection(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `MSDTests.test_changing_cell_and_atom_order_rejected`

源文件：[test_msd.py](test_msd.py)，第 135 行。

```python
MSDTests.test_changing_cell_and_atom_order_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 20 行。

```python
PreRelaxTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.setUp`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 21 行。

```python
PreRelaxTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.run_workflow`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 31 行。

```python
PreRelaxTests.run_workflow(self, name='md', **kwargs)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_disabled_by_default`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 34 行。

```python
PreRelaxTests.test_disabled_by_default(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_explicit_enabled_flag_in_configuration`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 40 行。

```python
PreRelaxTests.test_explicit_enabled_flag_in_configuration(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_alternative_optimizers`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 46 行。

```python
PreRelaxTests.test_alternative_optimizers(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_atoms_only_relaxation_reuses_model_and_feeds_md`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 52 行。

```python
PreRelaxTests.test_atoms_only_relaxation_reuses_model_and_feeds_md(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_cell_relaxation_and_md_cell_inheritance`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 75 行。

```python
PreRelaxTests.test_cell_relaxation_and_md_cell_inheritance(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_explicit_overwrite_preserves_unrelated_files`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 92 行。

```python
PreRelaxTests.test_explicit_overwrite_preserves_unrelated_files(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_nonconvergence_stops_by_default_or_explicitly_continues`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 100 行。

```python
PreRelaxTests.test_nonconvergence_stops_by_default_or_explicitly_continues(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_bad_configuration_and_collisions_fail_before_loading`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 113 行。

```python
PreRelaxTests.test_bad_configuration_and_collisions_fail_before_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_cell_requires_pbc_and_stress_but_atoms_only_does_not`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 130 行。

```python
PreRelaxTests.test_cell_requires_pbc_and_stress_but_atoms_only_does_not(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_existing_momenta_preserved_and_new_velocities_initialized_after_relaxation`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 142 行。

```python
PreRelaxTests.test_existing_momenta_preserved_and_new_velocities_initialized_after_relaxation(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_optimizer_failure_stops_md_and_records_failure`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 154 行。

```python
PreRelaxTests.test_optimizer_failure_stops_md_and_records_failure(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_frechet_step_limit_and_effective_scaling_report`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 162 行。

```python
PreRelaxTests.test_frechet_step_limit_and_effective_scaling_report(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_custom_step_and_cell_scaling`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 176 行。

```python
PreRelaxTests.test_custom_step_and_cell_scaling(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_invalid_step_settings_fail_before_model_loading`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 187 行。

```python
PreRelaxTests.test_invalid_step_settings_fail_before_model_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `PreRelaxTests.test_supercell_full_relaxation_remains_finite_and_reduces_energy`

源文件：[test_pre_relax.py](test_pre_relax.py)，第 196 行。

```python
PreRelaxTests.test_supercell_full_relaxation_remains_finite_and_reduces_energy(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests`

源文件：[test_relax.py](test_relax.py)，第 9 行。

```python
RelaxTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests.test_convergence_and_constraints`

源文件：[test_relax.py](test_relax.py)，第 10 行。

```python
RelaxTests.test_convergence_and_constraints(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `RelaxTests.test_invalid_input`

源文件：[test_relax.py](test_relax.py)，第 21 行。

```python
RelaxTests.test_invalid_input(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 15 行。

```python
SymmetrixTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.setUp`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 16 行。

```python
SymmetrixTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.test_conversion_closes_json_cleans_and_restores_dtype`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 41 行。

```python
SymmetrixTests.test_conversion_closes_json_cleans_and_restores_dtype(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.test_json_no_conversion_and_kokkos_forwarding`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 55 行。

```python
SymmetrixTests.test_json_no_conversion_and_kokkos_forwarding(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.test_invalid_options`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 64 行。

```python
SymmetrixTests.test_invalid_options(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.test_conversion_failure_propagates_and_restores_dtype`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 78 行。

```python
SymmetrixTests.test_conversion_failure_propagates_and_restores_dtype(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `SymmetrixTests.test_config_dispatch_and_workflow_reuses_calculator`

源文件：[test_symmetrix.py](test_symmetrix.py)，第 85 行。

```python
SymmetrixTests.test_config_dispatch_and_workflow_reuses_calculator(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests`

源文件：[test_trajectory.py](test_trajectory.py)，第 13 行。

```python
TrajectoryExportTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.setUp`

源文件：[test_trajectory.py](test_trajectory.py)，第 14 行。

```python
TrajectoryExportTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_vasp_indices_geometry_and_atom_order`

源文件：[test_trajectory.py](test_trajectory.py)，第 28 行。

```python
TrajectoryExportTests.test_vasp_indices_geometry_and_atom_order(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_default_last_all_slice_and_traj_momenta`

源文件：[test_trajectory.py](test_trajectory.py)，第 37 行。

```python
TrajectoryExportTests.test_default_last_all_slice_and_traj_momenta(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_other_formats`

源文件：[test_trajectory.py](test_trajectory.py)，第 47 行。

```python
TrajectoryExportTests.test_other_formats(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_invalid_selection_writes_nothing`

源文件：[test_trajectory.py](test_trajectory.py)，第 53 行。

```python
TrajectoryExportTests.test_invalid_selection_writes_nothing(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_output_protection_and_overwrite`

源文件：[test_trajectory.py](test_trajectory.py)，第 62 行。

```python
TrajectoryExportTests.test_output_protection_and_overwrite(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TrajectoryExportTests.test_no_cell_and_empty_trajectory`

源文件：[test_trajectory.py](test_trajectory.py)，第 76 行。

```python
TrajectoryExportTests.test_no_cell_and_empty_trajectory(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests`

源文件：[test_transport.py](test_transport.py)，第 13 行。

```python
TransportTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.setUp`

源文件：[test_transport.py](test_transport.py)，第 14 行。

```python
TransportTests.setUp(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.write`

源文件：[test_transport.py](test_transport.py)，第 21 行。

```python
TransportTests.write(self, slope=6)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.fit`

源文件：[test_transport.py](test_transport.py)，第 31 行。

```python
TransportTests.fit(self, **kw)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.test_analytic_units_free_intercept_segments_and_charge`

源文件：[test_transport.py](test_transport.py)，第 37 行。

```python
TransportTests.test_analytic_units_free_intercept_segments_and_charge(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.test_invalid_and_protected_outputs`

源文件：[test_transport.py](test_transport.py)，第 54 行。

```python
TransportTests.test_invalid_and_protected_outputs(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.test_nonphysical_negative_and_zero_slope`

源文件：[test_transport.py](test_transport.py)，第 68 行。

```python
TransportTests.test_nonphysical_negative_and_zero_slope(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportTests.test_malformed_data_rejected`

源文件：[test_transport.py](test_transport.py)，第 77 行。

```python
TransportTests.test_malformed_data_rejected(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportExampleTests`

源文件：[test_transport.py](test_transport.py)，第 88 行。

```python
TransportExampleTests
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportExampleTests.test_transport_integration`

源文件：[test_transport.py](test_transport.py)，第 91 行。

```python
TransportExampleTests.test_transport_integration(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportExampleTests.test_requires_msd_before_model_loading`

源文件：[test_transport.py](test_transport.py)，第 103 行。

```python
TransportExampleTests.test_requires_msd_before_model_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `TransportExampleTests.test_invalid_fit_window_before_model_loading`

源文件：[test_transport.py](test_transport.py)，第 109 行。

```python
TransportExampleTests.test_invalid_fit_window_before_model_loading(self)
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `export_traj_frames`

源文件：[trajectory.py](trajectory.py)，第 8 行。

```python
export_traj_frames(trajectory, output_dir=None, frames=-1, *, format='vasp', overwrite=False)
```

按保存帧索引导出结构，返回 frame_indices、structure_files 和 frame_count。

frames: 整数/整数列表/slice；0 为首帧，-1 为末帧，None 为全部。
output_dir=None: 输出到输入轨迹所在目录。
format: vasp（默认）/ cif / xyz / extxyz / traj；文件名 frame_000000.格式。
索引对应 MSD 的 frame_index，不一定是 MD 步号。负索引转为实际索引。
原子顺序保持不变；不弛豫、不加载模型、不修改源轨迹，默认不覆盖文件。
VASP 使用分数坐标；需完整晶胞。保留 ASE 动量等信息请用 traj。

## `fit_msd`

源文件：[transport.py](transport.py)，第 10 行。

```python
fit_msd(msd_csv, *, fit_start_ps, fit_end_ps, temperature_K, volume_A3, ion_charge, species=None, output_json=None, overwrite=False)
```

Fit MSD CSV and estimate uncorrelated Nernst–Einstein conductivity.

Inclusive fit window in ps; positive temperature in K and fixed cell volume
in Å³. ion_charge is a signed nonzero charge number (e.g. +1), or a dict
mapping selected elements to charge numbers. species is a string/list or
None (all CSV elements). Fits each segment separately, with a free intercept
and at least three samples. D_total=slope_total/6; D_axis=slope_axis/2.
Returns SI and cm²/s diffusion, S/m and S/cm conductivity, and diagnostics.
Optional JSON refuses overwrite by default. No uncertainty or correlation
correction is inferred; R² alone does not establish a diffusive regime.


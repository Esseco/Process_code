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

源文件：[examples/batch_postprocess_md.py](examples/batch_postprocess_md.py)，第 21 行。

```python
main()
```

每个 NVT 阶段一行；失败也记录，避免一个任务中断整批。

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

源文件：[examples/mlip_md.py](examples/mlip_md.py)，第 193 行。

```python
main(argv=None)
```

Preview configuration or run MD after editing the parameters above.

## `main`

源文件：[examples/msd.py](examples/msd.py)，第 40 行。

```python
main()
```

Export native max-mode lag sampling; fit only an explicitly chosen range.

## `main`

源文件：[examples/postprocess_md.py](examples/postprocess_md.py)，第 21 行。

```python
main()
```

复用项目后处理函数；只写 msd.csv 和 transport.json。

## `main`

源文件：[examples/sevennet_relax.py](examples/sevennet_relax.py)，第 11 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_500K_30ps/run_md.py](examples/sym_md_scan/sym_500K_30ps/run_md.py)，第 25 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_700K_10ps/run_md.py](examples/sym_md_scan/sym_700K_10ps/run_md.py)，第 25 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_700K_30ps/run_md.py](examples/sym_md_scan/sym_700K_30ps/run_md.py)，第 25 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_700K_50ps/run_md.py](examples/sym_md_scan/sym_700K_50ps/run_md.py)，第 25 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_700K_70ps/run_md.py](examples/sym_md_scan/sym_700K_70ps/run_md.py)，第 25 行。

```python
main()
```

原源码尚未说明输入/返回含义；执行前阅读实现，勿根据函数名猜测。

## `main`

源文件：[examples/sym_md_scan/sym_900K_30ps/run_md.py](examples/sym_md_scan/sym_900K_30ps/run_md.py)，第 25 行。

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

源文件：[md.py](md.py)，第 28 行。

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

源文件：[md_workflow.py](md_workflow.py)，第 15 行。

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

源文件：[msd.py](msd.py)，第 70 行。

```python
export_msd(trajectory, output_csv, *, species=None, frame_interval_fs=None, skip_frames=0, number_of_segments=1, unwrap=False, drift_reference=None, overwrite=False, min_obs=30)
```

Export pymatgen max-mode MSD (Å²), averaged over atoms and time origins.

species: element/list/None (all). skip_frames removes equilibration;
number_of_segments splits equally, each analyzed independently. min_obs=30
controls pymatgen's maximum lag; native sampling starts near 1 ps.
CSV columns are unchanged; time_fs/time_ps are lag times, frame_index is
segment start + lag in frames (not a unique displacement endpoint).

Times come from adjacent report.json or frame_interval_fs. A short final
saved interval is excluded with a warning; other unequal spacing is rejected.
unwrap=True uses ASE MIC for wrapped input; default preserves continuous
MD positions. drift_reference='framework' subtracts the mass-weighted COM
displacement of unselected atoms; None applies no drift correction.

Requires pymatgen-analysis-diffusion only when called; no models are loaded.
Writes only output_csv, refuses overwrite by default. Internal pymatgen
diffusion/conductivity fits are discarded; use fit_msd explicitly.

## `relax_structure_sevennet`

源文件：[sevennet_relax.py](sevennet_relax.py)，第 6 行。

```python
relax_structure_sevennet(structure, model='7net-omni', *, output_path=None, device='cpu', modal='mpa', fmax=0.05, steps=150, relax_cell=True)
```

Return energy (eV), forces (eV/Å), convergence and selected modal.

Inputs are a structure path, ASE Atoms or pymatgen Structure. Atoms are
copied. Only output_path is written (VASP format, overwrites if present).
No random sampling, trajectory or log. Named models may download weights;
supply a trusted local checkpoint for offline repeatable calculations.

## `export_traj_frames`

源文件：[trajectory.py](trajectory.py)，第 8 行。

```python
export_traj_frames(trajectory, output_dir=None, frames=-1, *, format='vasp', overwrite=False)
```

按保存帧索引导出结构，返回 frame_indices、structure_files 和 frame_count。

frames: 整数/整数列表/slice；0 为首帧，-1 为末帧，None 为全部。
output_dir=None: 输出到输入轨迹所在目录。
format: vasp（默认）/ cif / xyz / extxyz / traj；文件名 frame_000000.格式。
索引不是 MD 步号；多起点 MSD 的 frame_index 仅作 lag 参考，不代表唯一终点。
负索引转为实际索引。
原子顺序保持不变；不弛豫、不加载模型、不修改源轨迹，默认不覆盖文件。
VASP 使用分数坐标；需完整晶胞。保留 ASE 动量等信息请用 traj。

## `fit_msd`

源文件：[transport.py](transport.py)，第 41 行。

```python
fit_msd(msd_csv, *, fit_start_ps=None, fit_end_ps=None, temperature_K, volume_A3, ion_charge, species=None, output_json=None, overwrite=False)
```

Fit MSD CSV and estimate uncorrelated Nernst–Einstein conductivity.

Inclusive fit window in ps; None defaults to the first/last positive lag
of each species/segment separately. Zero lag is excluded. A manual bound
may be supplied on either side; this does not detect the diffusive regime.
Positive temperature in K and fixed cell volume
in Å³. ion_charge is a signed nonzero charge number (e.g. +1), or a dict
mapping selected elements to charge numbers. species is a string/list or
None (all CSV elements). Fits each segment separately, with a free intercept
and at least three positive-lag samples. Calls pymatgen's native fitter
with its defaults (max-mode, weights 1/lag, positive slope floor), after
selecting the window. D_total=slope_total/6; D_axis=slope_axis/2.
Slopes/intercepts describe the raw weighted line before its slope floor;
r_squared remains ordinary, unweighted R² of the fitted line.
Native slope-floor flags identify zero/negative slopes replaced by its
small positive value; these results do not establish resolved diffusion.
Returns SI and cm²/s diffusion, S/m and S/cm conductivity, and diagnostics.
Optional JSON refuses overwrite by default. No uncertainty or correlation
correction is inferred; R² alone does not establish a diffusive regime.


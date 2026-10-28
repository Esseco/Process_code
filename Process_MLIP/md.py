"""单阶段 ASE MD；模型加载和多阶段编排见 calculators / md_workflow。"""
import csv
import json
from pathlib import Path
from numbers import Integral
from time import perf_counter

import numpy as np
from ase import units
from ase.io import write
from ase.io.trajectory import Trajectory

# 保留既有私有导入路径；工作流和预弛豫直接复用共享模块。
from ._md_support import (
    _DEFAULTS, _FILES, _check_outputs, _copy_structure, _get_dynamics_class,
    _snapshot, _validate_atoms, _validate_options, _versions, _write_json,
)


def _synchronize_for_timing(calculator, metadata):
    if isinstance(metadata, dict) and metadata.get("benchmark_backend") == "tensorflow":
        import tensorflow as tf
        if not tf.config.experimental.get_synchronous_execution():
            raise RuntimeError("TensorFlow synchronous execution was disabled during timing")
        return
    if isinstance(metadata, dict) and metadata.get("external_gpu", False):
        # GPUNEP waits for each GPUMD subprocess to exit before returning.
        return
    device = getattr(calculator, "device", None)
    if device is None and isinstance(metadata, dict):
        device = metadata.get("device")
    if device is not None and str(device).startswith("cuda"):
        import torch
        torch.cuda.synchronize(device)


def run_md(structure, calculator, output_dir, *, ensemble="nvt", temperature_K=300.0,
           steps=1000, timestep_fs=None, tdamp_fs=100.0, pressure_bar=1.0,
           pdamp_fs=1000.0, initialize_velocities=None, seed=42, remove_com=True,
           zero_rotation=False, trajectory_interval=10, log_interval=10,
           overwrite=False, time_offset_fs=0.0, model_metadata=None,
           measure_steps_per_second=False, npt_cell_mode="isotropic",
           tchain=3, pchain=3, tloop=1, ploop=1,
           segment_steps=None, on_segment=None):
    """Run one NHC NVT or MTK NPT stage with an ASE calculator.

    Positions/cell use Å; energies eV, temperature K, time/damping fs, pressure
    bar (positive compression). Input atoms are copied. initialize_velocities
    None initializes only when momenta are absent; False preserves velocities;
    True samples Maxwell-Boltzmann momenta using seed. COM removal/rotation
    options apply only to initialization. Constraints are not supported.
    npt_cell_mode selects isotropic volume scaling or full flexible-cell MTK.
    tchain/tloop control the thermostat; pchain/ploop apply only to NPT.
    Chain lengths and integration substeps must be positive integers.

    segment_steps optionally advances the SAME integrator in blocks. It must
    be a positive multiple of trajectory_interval and log_interval; total
    steps must align with trajectory_interval as well. After
    each block, on_segment(event) sees flushed output and completed steps,
    time_fs, paths, temperature_K and saved-frame interval. Return True to
    request a normal early stop; False/None continues. No decision rules are
    built in. This is in-process continuity, not cross-process checkpointing.
    timestep_fs=None selects 2 fs for NVT or 1 fs for NPT; explicit values override.

    Writes md.traj, md.csv, final.traj (with momenta), report.json. Existing
    owned files require overwrite=True; unrelated files are never removed.
    No exact thermostat/barostat restart is provided. Returns final_atoms,
    output paths, final thermodynamic state and actual completed step count.
    measure_steps_per_second times dyn.run (including observers/output), with
    CUDA synchronization. Loading, pre-relaxation, property probes and final
    export are excluded. steps_per_second is None when off or steps is zero.
    """
    options = _validate_options({key: value for key, value in locals().copy().items()
                                 if key in _DEFAULTS})
    timestep_fs = options["timestep_fs"]
    if segment_steps is not None:
        if isinstance(segment_steps, bool) or not isinstance(segment_steps, Integral) or segment_steps <= 0:
            raise ValueError("segment_steps must be a positive integer or None")
        segment_steps = int(segment_steps)
        if steps % trajectory_interval:
            raise ValueError("segmented steps must align with trajectory_interval")
        if segment_steps % trajectory_interval or segment_steps % log_interval:
            raise ValueError("segment_steps must be a multiple of trajectory_interval and log_interval")
    if on_segment is not None and (not callable(on_segment) or segment_steps is None):
        raise ValueError("on_segment requires a callable and explicit segment_steps")
    atoms = _copy_structure(structure)
    _validate_atoms(atoms, options)
    root = _check_outputs(output_dir, overwrite)
    metadata = {} if model_metadata is None else model_metadata
    json.dumps(metadata, allow_nan=False)  # fail before producing outputs
    dynamics_class = _get_dynamics_class(options)
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
    initialized = initialize_velocities is True or (
        initialize_velocities is None and not atoms.has("momenta"))
    if initialized:
        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature_K,
                                    rng=np.random.default_rng(seed), force_temp=True)
        if remove_com:
            Stationary(atoms)
        if zero_rotation:
            ZeroRotation(atoms)
    atoms.calc = calculator
    # Probe properties before touching outputs (including required NPT stress).
    initial_state = _snapshot(atoms, ensemble.lower() == "npt")
    arguments = dict(atoms=atoms, timestep=timestep_fs * units.fs,
                     temperature_K=temperature_K, tdamp=tdamp_fs * units.fs,
                     tchain=options["tchain"], tloop=options["tloop"], logfile=None)
    if options["ensemble"] == "npt":
        arguments.update(pressure_au=pressure_bar * units.bar, pdamp=pdamp_fs * units.fs,
                         pchain=options["pchain"], ploop=options["ploop"])
    dyn = dynamics_class(**arguments)
    root.mkdir(parents=True, exist_ok=True)
    paths = dict(trajectory_file=str(root / "md.traj"), log_file=str(root / "md.csv"),
                 final_structure=str(root / "final.traj"), report_file=str(root / "report.json"))
    # In overwrite mode clear stale completion artifacts, never a whole directory.
    for name in ("final.traj",):
        if overwrite and (root / name).exists():
            (root / name).unlink()
    report = dict(status="running", parameters=options, model=metadata,
                  calculator=f"{type(calculator).__module__}.{type(calculator).__name__}",
                  md_controller=type(dyn).__name__,
                  versions=_versions(calculator), steps_completed=0, steps_per_second=None,
                  velocity_initialization="sampled" if initialized else "preserved",
                  initial_state=initial_state, segment_steps=segment_steps, stop_reason=None, **paths)
    _write_json(paths["report_file"], report)
    fields = ["step", "time_fs", *initial_state]
    try:
        with Trajectory(paths["trajectory_file"], "w", atoms) as trajectory, \
                open(paths["log_file"], "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()

            def observe():
                state = _snapshot(atoms, options["ensemble"] == "npt")
                step = dyn.nsteps
                if step % log_interval == 0 or step == steps:
                    writer.writerow(dict(step=step, time_fs=time_offset_fs + step * timestep_fs,
                                         **state))
                    handle.flush()
                if step % trajectory_interval == 0 or step == steps:
                    trajectory.write(atoms)
                report["final_state"] = state

            dyn.attach(observe, interval=1)
            if measure_steps_per_second:
                _synchronize_for_timing(calculator, metadata)
                start = perf_counter()
            stopped = False
            if segment_steps is None:
                dyn.run(steps)
            else:
                segment_index = 0
                while dyn.nsteps < steps:
                    dyn.run(min(segment_steps, steps - dyn.nsteps))
                    segment_index += 1
                    report.update(steps_completed=int(dyn.nsteps),
                                  end_time_fs=float(time_offset_fs + dyn.nsteps * timestep_fs))
                    _write_json(paths["report_file"], report)
                    if on_segment is not None:
                        event = dict(segment_index=segment_index, steps_completed=int(dyn.nsteps),
                                     time_fs=float(time_offset_fs + dyn.nsteps * timestep_fs),
                                     temperature_K=temperature_K,
                                     frame_interval_fs=timestep_fs * trajectory_interval, **paths)
                        request_stop = on_segment(event)
                        if request_stop is not None and type(request_stop) is not bool:
                            raise TypeError("on_segment must return bool or None")
                        if request_stop and dyn.nsteps < steps:
                            stopped = True
                            break
            if measure_steps_per_second:
                _synchronize_for_timing(calculator, metadata)
                duration = perf_counter() - start
                if dyn.nsteps > 0 and np.isfinite(duration) and duration > 0:
                    report["steps_per_second"] = float(dyn.nsteps / duration)
        write(paths["final_structure"], atoms, format="traj")
        report.update(status="stopped" if stopped else "completed",
                      stop_reason="callback" if stopped else None, steps_completed=int(dyn.nsteps),
                      end_time_fs=float(time_offset_fs + dyn.nsteps * timestep_fs))
        _write_json(paths["report_file"], report)
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status="failed", steps_completed=int(dyn.nsteps),
                      error=f"{type(exc).__name__}: {exc}")
        _write_json(paths["report_file"], report)
        raise
    finally:
        dyn.close()
    return dict(report, final_atoms=atoms, output_dir=str(root))

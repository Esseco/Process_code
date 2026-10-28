"""Shared measurements and relaxation, using existing tested ASE operations."""
from pathlib import Path
from time import perf_counter

from ase.calculators.loggingcalc import LoggingCalculator
from ase.io import write
import numpy as np

from ..MLIP_Relax import MLIPRelaxer
from ..md import run_md


class Measurement:
    """Synchronized wall time and same-process torch allocator peak in MiB."""

    def __init__(self, device, external_gpu=False, backend="torch"):
        self.device = device
        self.external_gpu = external_gpu
        self.backend = backend
        self.torch = None
        self.tensorflow = None
        self.result = {}
        if backend not in ("torch", "tensorflow"):
            raise ValueError(f"Unknown measurement backend: {backend}")
        if device.startswith("cuda") and backend == "tensorflow":
            import tensorflow as tf
            if device not in ("cuda", "cuda:0") or len(tf.config.get_visible_devices("GPU")) != 1:
                raise RuntimeError("GRACE requires exactly one visible GPU and device cuda or cuda:0")
            tf.config.experimental.set_synchronous_execution(True)
            self.tensorflow = tf
        elif device.startswith("cuda") and not external_gpu:
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError(f"CUDA requested but unavailable: {device}")
            self.torch = torch

    def synchronize(self):
        if self.tensorflow is not None and not self.tensorflow.config.experimental.get_synchronous_execution():
            raise RuntimeError("TensorFlow synchronous execution was disabled during timing")
        if self.torch is not None:
            self.torch.cuda.synchronize(self.device)

    def __enter__(self):
        self.synchronize()
        if self.torch is not None:
            self.torch.cuda.reset_peak_memory_stats(self.device)
        if self.tensorflow is not None:
            self.tensorflow.config.experimental.reset_memory_stats("GPU:0")
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.synchronize()
        self.result.update(elapsed_seconds=perf_counter() - self.start,
                           peak_gpu_allocated_MiB=None, peak_gpu_reserved_MiB=None,
                           gpu_memory_scope=("unavailable_external_gpu_subprocess" if self.external_gpu
                                             else "not_applicable_cpu"))
        if self.torch is not None:
            self.result.update(
                peak_gpu_allocated_MiB=self.torch.cuda.max_memory_allocated(self.device) / 1024**2,
                peak_gpu_reserved_MiB=self.torch.cuda.max_memory_reserved(self.device) / 1024**2,
                gpu_memory_scope="torch_allocator_current_process_includes_resident_model")
        if self.tensorflow is not None:
            info = self.tensorflow.config.experimental.get_memory_info("GPU:0")
            self.result.update(peak_gpu_allocated_MiB=info["peak"] / 1024**2,
                               gpu_memory_scope="tensorflow_allocator_includes_resident_model")


def warmup(atoms, calculator, device):
    """One uncached energy/force/stress probe per structure, outside both timers."""
    calculator.reset()
    probe = atoms.copy()
    probe.calc = calculator
    with Measurement(device, getattr(calculator, "benchmark_external_gpu", False),
                     getattr(calculator, "benchmark_backend", "torch")) as meter:
        values = (probe.get_potential_energy(), probe.get_forces(), probe.get_stress())
        if any(not np.all(np.isfinite(value)) for value in values):
            raise RuntimeError("Warmup returned non-finite energy/forces/stress")
    calculator.reset()
    return meter.result


def relax(atoms, calculator, directory, parameters, device):
    """Full-cell LBFGS; count uncached ASE force requests, save final structure."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    calculator.reset()
    logged = LoggingCalculator(calculator)
    relaxed = atoms.copy()
    meter = Measurement(device, getattr(calculator, "benchmark_external_gpu", False),
                        getattr(calculator, "benchmark_backend", "torch"))
    try:
        with meter:
            result = MLIPRelaxer(relaxed, logged, optimizer="LBFGS", relax_cell=True,
                                 **parameters).relax(traj_file=str(directory / "relax.traj"),
                                                     log_file=str(directory / "relax.log"))
    except Exception as exc:
        # The runner persists this diagnostic alongside partial trajectory/logs.
        exc.benchmark_measurement = dict(meter.result,
            force_evaluations=sum(len(values) for values in logged.fmax.values()))
        raise
    final_path = directory / "final.extxyz"
    write(final_path, relaxed)
    return dict(meter.result, converged=result["optimizer_converged"],
                optimization_steps=result["relax_steps_used"],
                force_evaluations=sum(len(values) for values in logged.fmax.values()),
                force_count_definition="uncached_ASE_force_requests_not_internal_network_passes",
                max_force_eV_per_A=result["force_max_ev_per_angstrom"],
                energy_eV=float(result["energy"]), energy_eV_per_atom=float(result["energy_per_atom"]),
                natoms=len(relaxed), composition=relaxed.get_chemical_symbols(),
                final_structure=str(final_path))


def molecular_dynamics(atoms, calculator, directory, parameters, device, seed):
    """Reuse NHC NVT; return the existing integrator-only timer, not outer wall time."""
    calculator.reset()
    external_gpu = getattr(calculator, "benchmark_external_gpu", False)
    backend = getattr(calculator, "benchmark_backend", "torch")
    meter = Measurement(device, external_gpu, backend)
    try:
        with meter:
            result = run_md(atoms, calculator, directory, ensemble="nvt", seed=seed,
                            initialize_velocities=True, measure_steps_per_second=True,
                            overwrite=True, model_metadata={"device": device, "external_gpu": external_gpu,
                                                            "benchmark_backend": backend}, **parameters)
    except Exception as exc:
        details = dict(meter.result)
        details["stage_wall_seconds"] = details.pop("elapsed_seconds", None)
        details["elapsed_seconds"] = None
        exc.benchmark_measurement = details
        raise
    # Existing run_md synchronizes immediately around dyn.run; setup/probes/export excluded.
    duration = result["steps_completed"] / result["steps_per_second"]
    return dict(meter.result, elapsed_seconds=duration,
                stage_wall_seconds=meter.result["elapsed_seconds"],
                steps_completed=result["steps_completed"], steps_per_second=result["steps_per_second"],
                simulated_time_ps=result["steps_completed"] * parameters["timestep_fs"] / 1000,
                timing_scope="dyn.run_including_consistent_observers_and_trajectory_IO",
                final_structure=result["final_structure"])

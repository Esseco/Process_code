"""NVT adapter using Process_MLIP's existing ASE integration implementation."""
from pathlib import Path
from inspect import signature
from typing import Callable

from ase import Atoms
from ase.calculators.calculator import BaseCalculator

from ..models import MDConfig, MDResult
from ..io import save_json, save_results


class MDRunner:
    """Accept an ASE calculator independently of the analysis modules."""

    def __init__(self, calculator: BaseCalculator):
        self.calculator = calculator

    def run(
        self,
        structure: Atoms,
        *,
        temperature_K: float,
        duration_ps: float,
        timestep_fs: float = 2.0,
        output_dir: str | Path = "run_001",
        equilibration_ps: float = 0.0,
        trajectory_interval: int = 10,
        checkpoint_interval: int | None = None,
        seed: int = 42,
        segment_ps: float | None = None,
        on_segment: Callable[[dict], bool | None] | None = None,
    ) -> MDResult:
        """Run existing NHC NVT; production duration excludes equilibration.

        The same calculator is used for both stages. Process_MLIP copies
        input atoms and preserves momenta between stages, but reinitializes
        the thermostat. Intervals are steps. output_dir must not exist.
        Checkpoints are unsupported and must be left disabled (None).
        segment_ps subdivides production within one integrator. on_segment
        receives flushed progress and may return True for a normal stop;
        no screening or review rules are provided by the runner.
        """
        config = MDConfig(
            temperature_K=temperature_K, duration_ps=duration_ps, timestep_fs=timestep_fs,
            equilibration_ps=equilibration_ps, trajectory_interval=trajectory_interval,
            checkpoint_interval=checkpoint_interval, seed=seed, segment_ps=segment_ps,
        )
        if checkpoint_interval is not None:
            raise NotImplementedError("Process_MLIP does not yet support checkpoint saving")
        from Process_MLIP.md import run_md

        if on_segment is not None and (not callable(on_segment) or segment_ps is None):
            raise ValueError("on_segment requires a callable and explicit segment_ps")
        if segment_ps is not None and "segment_steps" not in signature(run_md).parameters:
            raise NotImplementedError("The installed Process_MLIP needs its continuous-segment extension")

        root = Path(output_dir).resolve()
        root.mkdir(parents=True, exist_ok=False)
        result = MDResult(parameters=config, status="running", output_dir=root,
                          steps_completed=None,
                          records=["Backend: Process_MLIP.md.run_md (NHC NVT)"])
        save_results({"md": result}, root)
        atoms = structure
        offset_fs = 0.0
        try:
            for stage, steps in (("equilibration", config.equilibration_steps),
                                 ("production", config.production_steps)):
                if steps == 0:
                    continue
                stage_result = run_md(
                    atoms, self.calculator, root / stage, ensemble="nvt",
                    temperature_K=temperature_K, steps=steps, timestep_fs=timestep_fs,
                    trajectory_interval=trajectory_interval, log_interval=trajectory_interval,
                    seed=seed, time_offset_fs=offset_fs,
                    initialize_velocities=False if offset_fs > 0 else None,
                    **({"segment_steps": config.segment_steps, "on_segment": on_segment}
                       if stage == "production" and segment_ps is not None else {}),
                )
                atoms = stage_result["final_atoms"]
                offset_fs = stage_result["end_time_fs"]
                result.records.append(f"{stage}: {stage_result['steps_completed']} steps completed")
                if stage == "equilibration":
                    result.equilibration_trajectory = Path(stage_result["trajectory_file"])
                    result.records.append("Production keeps momenta; thermostat state is reinitialized")
                else:
                    result.trajectory = Path(stage_result["trajectory_file"])
                    result.final_structure = Path(stage_result["final_structure"])
                    result.report = Path(stage_result["report_file"])
                    result.steps_completed = stage_result["steps_completed"]
                    result.status = stage_result["status"]
        except (Exception, KeyboardInterrupt) as exc:
            result.status = "failed"
            result.error = f"{type(exc).__name__}: {exc}"
            result.steps_completed = None
            result.records.append("See stage report.json for partial integration progress, if available")
            save_json({"schema_version": 1, "results": {"md": result}}, root / "results.json", overwrite=True)
            raise
        save_json({"schema_version": 1, "results": {"md": result}}, root / "results.json", overwrite=True)
        return result

    def resume(self, previous_run: str | Path, duration_ps: float) -> MDResult:
        """Phase-4 strict restart interface, never a coordinate-frame fallback.

        A real checkpoint must include momenta, integration/thermostat and
        RNG state, completed steps, parameters and calculator compatibility.
        Merely reading final.traj cannot satisfy this contract.
        """
        raise NotImplementedError("Strict resume needs a complete checkpoint; scheduled for phase 4")

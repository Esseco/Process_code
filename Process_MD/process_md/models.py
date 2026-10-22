"""Small public data objects. Field names carry their physical units."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isclose, isfinite
from numbers import Integral, Real
from pathlib import Path
from typing import Literal, Sequence


def _steps(duration_ps: float, timestep_fs: float) -> int:
    steps = duration_ps * 1000 / timestep_fs
    if (not isfinite(steps) or (duration_ps > 0 and round(steps) == 0)
            or not isclose(steps, round(steps), rel_tol=0, abs_tol=1e-8)):
        raise ValueError("duration must correspond to an integer number of steps")
    return round(steps)


@dataclass(frozen=True)
class MDConfig:
    """NVT parameter contract; duration_ps is production time only.

    Intervals are integration steps, not fs. No simulation is started by
    creating a config. Checkpointing is not yet supported by the MD backend;
    leave checkpoint_interval=None to run without checkpointing.
    """

    temperature_K: float
    duration_ps: float
    timestep_fs: float = 2.0
    equilibration_ps: float = 0.0
    trajectory_interval: int = 10
    checkpoint_interval: int | None = None
    seed: int = 42
    segment_ps: float | None = None

    def __post_init__(self) -> None:
        for name in ("temperature_K", "duration_ps", "timestep_fs", "equilibration_ps"):
            value = getattr(self, name)
            minimum_ok = value >= 0 if isinstance(value, Real) else False
            if (isinstance(value, bool) or not isinstance(value, Real)
                    or not isfinite(value) or not minimum_ok
                    or (name != "equilibration_ps" and value == 0)):
                raise ValueError(f"{name} must be finite and "
                                 + ("nonnegative" if name == "equilibration_ps" else "positive"))
        for name in ("trajectory_interval", "checkpoint_interval"):
            value = getattr(self, name)
            if name == "checkpoint_interval" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if isinstance(self.seed, bool) or not isinstance(self.seed, Integral) or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        _steps(self.duration_ps, self.timestep_fs)
        _steps(self.equilibration_ps, self.timestep_fs)
        if self.segment_ps is not None:
            if (isinstance(self.segment_ps, bool) or not isinstance(self.segment_ps, Real)
                    or not isfinite(self.segment_ps) or self.segment_ps <= 0):
                raise ValueError("segment_ps must be finite and positive or None")
            if self.segment_steps % self.trajectory_interval:
                raise ValueError("segment_ps must align with trajectory_interval")
            if self.production_steps % self.trajectory_interval:
                raise ValueError("Segmented production duration must align with trajectory_interval")

    @property
    def production_steps(self) -> int:
        return _steps(self.duration_ps, self.timestep_fs)

    @property
    def equilibration_steps(self) -> int:
        return _steps(self.equilibration_ps, self.timestep_fs)

    @property
    def segment_steps(self) -> int | None:
        return None if self.segment_ps is None else _steps(self.segment_ps, self.timestep_fs)


@dataclass(frozen=True)
class StructureInfo:
    n_atoms: int
    elements: tuple[str, ...]
    element_counts: dict[str, int]
    cell_lengths_A: tuple[float, float, float]
    cell_angles_deg: tuple[float, float, float]
    volume_A3: float
    pbc: tuple[bool, bool, bool]


@dataclass
class MDResult:
    parameters: MDConfig
    status: Literal["pending", "running", "completed", "stopped", "failed"] = "pending"
    output_dir: Path | None = None
    trajectory: Path | None = None
    equilibration_trajectory: Path | None = None
    report: Path | None = None
    final_structure: Path | None = None
    checkpoint: Path | None = None
    steps_completed: int | None = 0
    error: str | None = None
    records: list[str] = field(default_factory=list)


@dataclass
class MSDResult:
    """MSD output; axes are Cartesian, time_ps contains lag times."""

    species: str
    axes: str
    time_ps: Sequence[float]
    msd_A2: Sequence[float]
    n_mobile_atoms: int
    components_A2: Sequence[Sequence[float]] | None = None
    frame_interval_ps: float | None = None
    coordinate_mode: str = "unwrapped"
    drift_reference: str | None = None
    method: str = "Process_MLIP/pymatgen"
    n_frames: int | None = None
    trajectory_duration_ps: float | None = None
    volume_A3: float | None = None
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class DiffusionResult:
    """None is permitted when diffusion is unresolved; R² is not convergence."""

    diffusion_cm2_s: float | None
    fit_start_ps: float
    fit_end_ps: float
    r_squared: float | None
    slope_A2_per_ps: float | None = None
    conductivity_NE_S_cm: float | None = None
    temperature_K: float | None = None
    volume_A3: float | None = None
    ion_charge: float | None = None
    n_mobile_atoms: int | None = None
    axes: str = "xyz"
    uncertainty_status: str = "not_evaluated"
    method: str = "pymatgen WLS; Nernst-Einstein"
    species: str | None = None
    observation_duration_ps: float | None = None
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Numerical diagnostics without a single-threshold collapse verdict."""

    framework_species: tuple[str, ...]
    framework_msd_A2: float | None = None
    rdf_difference: float | None = None
    coordination_change_fraction: float | None = None
    framework_msd_curve_A2: Sequence[float] | None = None
    framework_drift_A: Sequence[Sequence[float]] | None = None
    rdf_r_A: Sequence[float] | None = None
    rdf_initial: Sequence[float] | None = None
    rdf_final: Sequence[float] | None = None
    coordination_initial_mean: float | None = None
    coordination_final_mean: float | None = None
    diagnostics: list[str] = field(default_factory=list)
    rdf_reference_frames: Sequence[int] | None = None
    rdf_final_frames: Sequence[int] | None = None
    rdf_repeat: tuple[int, int, int] = (1, 1, 1)

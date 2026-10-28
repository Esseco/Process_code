"""Small, explicit configuration. Durations are ps; output intervals are steps."""
from dataclasses import dataclass, field
from math import gcd, isfinite
from numbers import Integral, Real
from pathlib import Path

from ase.data import atomic_numbers
from process_md import MDConfig

from .stopping import StopCriteria
from .stability import FrameworkCriteria


@dataclass(frozen=True)
class ScreeningConfig:
    mobile_species: str = "Li"
    target_atoms: int | None = 200
    temperature_K: float = 800
    precheck_ps: float = 5
    check_interval_ps: float = 10
    max_production_ps: float = 200
    timestep_fs: float = 2
    trajectory_interval: int = 10
    seed: int = 42
    axes: str = "xyz"
    min_obs: int = 30
    fit_start_ps: float = 1
    fit_end_ps: float | None = None
    ion_charge: float = 1
    coordination_cutoff_A: float | None = None
    configuration_id: str | None = None
    model_label: str | None = None
    model_path: str | Path | None = None
    model_type: str = "mace"
    model_name: str | None = None
    modal: str = "mpa"
    precision: str = "float32-highest"
    compile_model: bool = True
    enable_flash: bool = False
    enable_openequivariance: bool = False
    backend: str | None = None
    gpumd_command: str | Path | None = None
    model_options: dict = field(default_factory=dict)
    pre_relax: bool = True
    relax_cell: bool = True
    relax_optimizer: str = "LBFGS"
    relax_fmax_ev_A: float = 0.05
    relax_steps: int = 1000
    relax_maxstep_A: float = 0.05
    require_relax_convergence: bool = True
    device: str = "cuda"
    default_dtype: str = "float64"
    enable_cueq: bool = False
    enable_symmetrix: bool = False
    symmetrix_use_kokkos: bool = False
    symmetrix_species: tuple[str, ...] | None = None
    hop_distance_A: float | None = None
    stop_criteria: StopCriteria | None = field(default_factory=StopCriteria)
    uncertainty_on_stop: bool = False
    uncertainty_samples: int = 1000
    jump_analysis: bool = True
    jump_min_residence_ps: float = 0.2
    jump_site_radius_A: float | None = None
    jump_site_inner_fraction: float = 0.8
    framework_criteria: FrameworkCriteria | None = field(default_factory=FrameworkCriteria)
    framework_rdf_repeat: tuple[int, int, int] = (1, 1, 1)
    compress_trajectory: bool = False

    def __post_init__(self) -> None:
        for duration in (self.precheck_ps, self.check_interval_ps, self.max_production_ps):
            MDConfig(temperature_K=self.temperature_K, duration_ps=duration,
                     timestep_fs=self.timestep_fs, trajectory_interval=self.trajectory_interval,
                     seed=self.seed)
        for name in ("target_atoms", "min_obs"):
            value = getattr(self, name)
            if name == "target_atoms" and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.mobile_species, str) or atomic_numbers.get(self.mobile_species, 0) <= 0:
            raise ValueError("mobile_species must be an element symbol")
        if (not isinstance(self.axes, str) or not self.axes or len(set(self.axes)) != len(self.axes)
                or set(self.axes) - set("xyz")):
            raise ValueError("axes must contain distinct Cartesian x/y/z letters")
        for name in ("fit_start_ps", "fit_end_ps", "coordination_cutoff_A", "hop_distance_A", "ion_charge"):
            value = getattr(self, name)
            if value is None and name in ("fit_end_ps", "coordination_cutoff_A", "hop_distance_A"):
                continue
            if (isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value)
                    or (value == 0 if name == "ion_charge" else value <= 0)):
                raise ValueError(f"{name} must be finite and " + ("nonzero" if name == "ion_charge" else "positive"))
        if self.fit_end_ps is not None and self.fit_start_ps >= self.fit_end_ps:
            raise ValueError("fit_start_ps must be smaller than fit_end_ps")
        for name in ("configuration_id", "model_label"):
            if getattr(self, name) is not None and not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be a string or None")
        if self.model_path is not None and not isinstance(self.model_path, (str, Path)):
            raise ValueError("model_path must be a path or None")
        if self.model_type not in ("mace", "sevennet", "orb", "nep", "grace", "nequip"):
            raise ValueError("model_type must be mace, sevennet, orb, nep, grace or nequip")
        if self.model_name is not None and not isinstance(self.model_name, str):
            raise ValueError("model_name must be a string or None")
        for name in ("modal", "precision"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        for name in ("compile_model", "enable_flash", "enable_openequivariance"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be bool")
        if self.backend not in (None, "cpu", "gpu"):
            raise ValueError("backend must be None, cpu or gpu")
        if self.gpumd_command is not None and not isinstance(self.gpumd_command, (str, Path)):
            raise ValueError("gpumd_command must be a path, string or None")
        if (not isinstance(self.model_options, dict)
                or any(not isinstance(key, str) for key in self.model_options)):
            raise ValueError("model_options must be a dictionary with string keys")
        if any(type(value) is not bool for value in (self.pre_relax, self.relax_cell, self.require_relax_convergence)):
            raise ValueError("pre_relax, relax_cell and require_relax_convergence must be bool")
        if self.relax_optimizer not in ("FIRE", "BFGS", "LBFGS"):
            raise ValueError("relax_optimizer must be FIRE, BFGS or LBFGS")
        for name in ("relax_fmax_ev_A", "relax_maxstep_A"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if isinstance(self.relax_steps, bool) or not isinstance(self.relax_steps, Integral) or self.relax_steps < 0:
            raise ValueError("relax_steps must be a nonnegative integer")
        if not isinstance(self.device, str) or not self.device.strip():
            raise ValueError("device must be an explicit device string")
        if self.default_dtype not in ("float32", "float64"):
            raise ValueError("default_dtype must be float32 or float64")
        for name in ("enable_cueq", "enable_symmetrix", "symmetrix_use_kokkos"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be bool")
        if self.enable_cueq and self.enable_symmetrix:
            raise ValueError("enable_cueq and enable_symmetrix are mutually exclusive")
        if self.symmetrix_use_kokkos and not self.enable_symmetrix:
            raise ValueError("symmetrix_use_kokkos requires enable_symmetrix")
        if self.enable_symmetrix and self.device == "cuda" and not self.symmetrix_use_kokkos:
            raise ValueError("CUDA Symmetrix requires symmetrix_use_kokkos=True")
        if self.symmetrix_species is not None:
            if (not isinstance(self.symmetrix_species, tuple) or not self.symmetrix_species
                    or any(not isinstance(symbol, str) or atomic_numbers.get(symbol, 0) <= 0
                           for symbol in self.symmetrix_species)):
                raise ValueError("symmetrix_species must be a nonempty tuple of element symbols")
        if self.stop_criteria is not None and not isinstance(self.stop_criteria, StopCriteria):
            raise ValueError("stop_criteria must be StopCriteria or None")
        if self.framework_criteria is not None and not isinstance(self.framework_criteria, FrameworkCriteria):
            raise ValueError("framework_criteria must be FrameworkCriteria or None")
        if (not isinstance(self.framework_rdf_repeat, tuple) or len(self.framework_rdf_repeat) != 3
                or any(isinstance(v, bool) or not isinstance(v, Integral) or v <= 0 for v in self.framework_rdf_repeat)):
            raise ValueError("framework_rdf_repeat must be a tuple of three positive integers")
        if type(self.compress_trajectory) is not bool:
            raise ValueError("compress_trajectory must be bool")
        if type(self.jump_analysis) is not bool:
            raise ValueError("jump_analysis must be bool")
        value = self.jump_site_inner_fraction
        if (isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value)
                or not 0 < value <= 1):
            raise ValueError("jump_site_inner_fraction must be finite and lie in (0, 1]")
        for name in ("jump_min_residence_ps", "jump_site_radius_A"):
            value = getattr(self, name)
            if value is None and name == "jump_site_radius_A":
                continue
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if type(self.uncertainty_on_stop) is not bool:
            raise ValueError("uncertainty_on_stop must be bool")
        if (isinstance(self.uncertainty_samples, bool) or not isinstance(self.uncertainty_samples, Integral)
                or self.uncertainty_samples < 10):
            raise ValueError("uncertainty_samples must be an integer >= 10")
        if self.frame_interval_ps > 1:
            raise ValueError("pymatgen MSD requires saved-frame spacing <= 1 ps")
        if any(self.steps(value) % self.trajectory_interval
               for value in (self.precheck_ps, self.check_interval_ps, self.max_production_ps)):
            raise ValueError("All durations must align with trajectory_interval")
        if self.steps(self.max_production_ps) % self.steps(self.check_interval_ps):
            raise ValueError("max_production_ps must be a multiple of check_interval_ps")

    def steps(self, duration_ps: float) -> int:
        # Already validated through the public Process_MD step contract.
        return round(duration_ps * 1000 / self.timestep_fs)

    @property
    def frame_interval_ps(self) -> float:
        return self.timestep_fs * self.trajectory_interval / 1000

    @property
    def backend_segment_ps(self) -> float:
        """Align a 5 ps precheck and 10 ps production checks without a reset."""
        steps = gcd(self.steps(self.precheck_ps), self.steps(self.check_interval_ps))
        return steps * self.timestep_fs / 1000

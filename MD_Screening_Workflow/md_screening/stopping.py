"""Cheap transport screening: production time, displacement scale and R²."""
from dataclasses import dataclass
from math import isfinite
from numbers import Real

import numpy as np

from .review import CheckReport, Decision


@dataclass(frozen=True)
class StopCriteria:
    min_production_ps: float = 10
    msd_hop_factor: float = 3
    min_r_squared: float = 0.95
    no_jump_stop_ps: float = 10
    max_plateau_relative_change: float = 0.2
    min_site_coverage: float = 0.95
    min_ion_site_coverage: float = 0.8

    def __post_init__(self) -> None:
        for name in ("min_production_ps", "msd_hop_factor", "min_r_squared", "no_jump_stop_ps",
                     "max_plateau_relative_change", "min_site_coverage", "min_ion_site_coverage"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if self.min_r_squared >= 1:
            raise ValueError("min_r_squared must be smaller than 1")
        if self.min_site_coverage > 1 or self.min_ion_site_coverage > 1:
            raise ValueError("Site coverage thresholds must be <= 1")


def _plateau_relative_change(report: CheckReport) -> float | None:
    """Absolute fitted change in the final half of the MSD lag grid / its mean."""
    if report.msd is None:
        return None
    times = np.asarray(report.msd.time_ps, dtype=float)
    curve = np.asarray(report.msd.msd_A2, dtype=float)
    if (times.ndim != 1 or curve.shape != times.shape or len(times) < 3
            or not np.isfinite(times).all() or not np.isfinite(curve).all()
            or np.any(np.diff(times) <= 0)):
        return None
    selected = times >= (times[0] + times[-1]) / 2
    t, y = times[selected], curve[selected]
    if len(t) < 3:
        return None
    slope = float(np.polyfit(t - t[0], y, 1)[0])
    # A small floor keeps the exactly immobile case well defined (angstrom²).
    return abs(slope) * float(t[-1] - t[0]) / max(float(np.mean(np.abs(y))), 0.05)


class TransportStopper:
    """One eligible curve can stop. Uncertainty does not gate this heuristic.

    hop_distance_A is an occupied-site geometric proxy unless overridden;
    it does not locate vacant sites or establish a migration mechanism.
    """

    def __init__(self, *, hop_distance_A: float, criteria: StopCriteria | None = None):
        if (isinstance(hop_distance_A, bool) or not isinstance(hop_distance_A, Real)
                or not isfinite(hop_distance_A) or hop_distance_A <= 0):
            raise ValueError("hop_distance_A must be finite and positive")
        self.criteria = StopCriteria() if criteria is None else criteria
        self.hop_distance_A = float(hop_distance_A)

    def is_candidate(self, report: CheckReport) -> bool:
        c = self.criteria
        metrics = report.stop_metrics
        metrics.update(hop_distance_A=self.hop_distance_A,
                       msd_threshold_A2=c.msd_hop_factor * self.hop_distance_A**2,
                       production_pass=report.production_time_ps >= c.min_production_ps)
        msd, fit = report.msd, report.transport
        if report.phase != "production" or report.transport_status != "estimated" or msd is None or fit is None:
            metrics["curve_pass"] = False
            return False
        lag, curve = np.asarray(msd.time_ps), np.asarray(msd.msd_A2)
        selected = curve[(lag >= fit.fit_start_ps) & (lag <= fit.fit_end_ps)]
        value = float(selected[-1]) if len(selected) else None
        metrics.update(
            msd_at_fit_end_A2=value,
            msd_pass=value is not None and isfinite(value) and value > metrics["msd_threshold_A2"],
            r_squared_pass=fit.r_squared is not None and isfinite(fit.r_squared) and fit.r_squared > c.min_r_squared,
            positive_transport_pass=all(v is not None and isfinite(v) and v > 0 for v in
                                        (fit.diffusion_cm2_s, fit.conductivity_NE_S_cm, fit.slope_A2_per_ps)),
        )
        for name in ("production_pass", "msd_pass", "r_squared_pass", "positive_transport_pass"):
            metrics[name] = bool(metrics[name])
        metrics["curve_pass"] = all(metrics[name] for name in
                                     ("production_pass", "msd_pass", "r_squared_pass", "positive_transport_pass"))
        return metrics["curve_pass"]

    def __call__(self, report: CheckReport) -> Decision:
        candidate = self.is_candidate(report)
        if report.phase == "production":
            change = _plateau_relative_change(report)
            report.stop_metrics["plateau_relative_change"] = change
            jumps = report.jumps
            reliable = (jumps is not None and jumps.status == "estimated"
                        and jumps.site_coverage is not None and jumps.minimum_ion_site_coverage is not None
                        and jumps.site_coverage >= self.criteria.min_site_coverage
                        and jumps.minimum_ion_site_coverage >= self.criteria.min_ion_site_coverage)
            if not reliable:
                report.mobility_status = "unknown_site_mapping" if jumps is not None else "not_evaluated"
            elif jumps.n_jumps > 0:
                report.mobility_status = "jumps_observed"
            elif change is not None and change <= self.criteria.max_plateau_relative_change:
                report.mobility_status = "no_jumps_plateau"
                if not candidate and report.production_time_ps >= self.criteria.no_jump_stop_ps:
                    return Decision("raise_temperature", "No effective jumps and an MSD plateau within the production observation window; stop to save cost and recommend a higher temperature. Slow diffusion is not excluded; temperature is unchanged.")
            else:
                report.mobility_status = "no_jumps_unresolved"
        if candidate:
            return Decision("accept", "Coarse transport screen passed: minimum production time, MSD > factor*d² and R² threshold. This is an approximate D/sigma_NE estimate; framework stability and convergence are not certified.")
        return Decision("continue", "Coarse transport screen not yet met; continue sampling within the production budget.")

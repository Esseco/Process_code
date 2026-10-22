"""A small, configurable framework warning; this does not measure melting."""
from dataclasses import dataclass
from math import isfinite
from numbers import Real

import numpy as np

from .review import CheckReport


@dataclass(frozen=True)
class FrameworkCriteria:
    """Provisional screening values, not universal phase boundaries.

    Require large displacement, growth across both late windows and RDF
    change together. A one-off relaxation followed by a plateau does not
    trigger. The same check is used during precheck and production.
    """

    min_msd_A2: float = 1.0
    min_window_growth_A2: float = 0.2
    min_rdf_difference: float = 0.5

    def __post_init__(self):
        for name in ("min_msd_A2", "min_window_growth_A2", "min_rdf_difference"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")


def assess_framework(report: CheckReport, criteria: FrameworkCriteria | None) -> bool:
    """Store cheap joint evidence and return whether clear instability is flagged."""
    if criteria is None:
        report.framework_status = "not_evaluated"
        return False
    curve = np.asarray(report.framework.framework_msd_curve_A2, dtype=float)
    rdf = report.framework.rdf_difference
    if (curve.ndim != 1 or len(curve) < 8 or not np.isfinite(curve).all()
            or rdf is None or not isfinite(rdf)):
        report.framework_status = "insufficient_data"
        return False
    windows = [float(np.mean(part)) for part in np.array_split(curve, 4)]
    growth = [windows[2] - windows[1], windows[3] - windows[2]]
    flags = dict(
        large_displacement=windows[-1] > criteria.min_msd_A2,
        persistent_growth=min(growth) > criteria.min_window_growth_A2,
        rdf_changed=rdf > criteria.min_rdf_difference,
    )
    unstable = all(flags.values())
    report.stability_metrics.update(
        late_msd_A2=windows[-1], late_window_growth_A2=growth,
        rdf_difference=float(rdf), **flags,
    )
    report.framework_status = "unstable" if unstable else "no_instability_detected"
    return unstable

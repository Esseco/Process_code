import numpy as np
import pytest
from process_md import ThermodynamicSummary, ValidationResult

from md_screening import CheckReport, FrameworkCriteria
from md_screening.stability import assess_framework


def report(curve, rdf=0.8):
    return CheckReport(0, "precheck", 5, 0,
                       ValidationResult(("O",), framework_msd_curve_A2=curve, rdf_difference=rdf),
                       ThermodynamicSummary(20, 0, 5, {}, {}, {}, {}))


def test_joint_persistent_msd_and_rdf_warning():
    check = report(np.linspace(0, 5, 100))
    assert assess_framework(check, FrameworkCriteria())
    assert check.framework_status == "unstable"
    assert all(check.stability_metrics[key] for key in ("large_displacement", "persistent_growth", "rdf_changed"))


@pytest.mark.parametrize("curve,rdf", [
    (np.linspace(0, 5, 100), 0.1),  # growth alone does not establish collapse
    (np.zeros(100), 0.8),           # RDF change alone is not melting
    (np.r_[np.linspace(0, 5, 20), np.full(80, 5)], 0.8),  # relaxation then plateau
    (np.linspace(0, 0.5, 100), 0.8),
])
def test_single_signal_or_relaxation_cannot_trigger(curve, rdf):
    check = report(curve, rdf)
    assert not assess_framework(check, FrameworkCriteria())
    assert check.framework_status == "no_instability_detected"


@pytest.mark.parametrize("curve,rdf", [(None, 0.8), ([0, 5], 0.8), (np.arange(20), None)])
def test_missing_evidence_is_not_called_stable(curve, rdf):
    check = report(curve, rdf)
    assert not assess_framework(check, FrameworkCriteria())
    assert check.framework_status == "insufficient_data"


def test_disabled_and_custom_thresholds():
    check = report(np.linspace(0, 5, 100))
    assert not assess_framework(check, None)
    assert check.framework_status == "not_evaluated"
    assert not assess_framework(check, FrameworkCriteria(min_msd_A2=10))


@pytest.mark.parametrize("options", [{"min_msd_A2": 0}, {"min_window_growth_A2": True}, {"min_rdf_difference": float("nan")}])
def test_invalid_thresholds(options):
    with pytest.raises(ValueError):
        FrameworkCriteria(**options)

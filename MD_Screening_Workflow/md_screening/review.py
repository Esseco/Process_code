"""Reviewer contracts; material-specific framework thresholds remain external."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING

from process_md import DiffusionResult, MSDResult, ThermodynamicSummary, ValidationResult

if TYPE_CHECKING:
    from process_md import JumpResult, UncertaintyResult


@dataclass(frozen=True)
class Decision:
    """continue samples longer; other actions stop and record the request.

    accept is a conclusion supplied by the caller's reviewer, not by this
    package. Cell, temperature and model requests are not executed in v0.1.
    """
    action: Literal["continue", "accept", "review_cell", "raise_temperature",
                    "lower_temperature", "review_model", "stop"] = "continue"
    reason: str = "No automatic review criteria configured; record diagnostics only."

    def __post_init__(self) -> None:
        if self.action not in ("continue", "accept", "review_cell", "raise_temperature",
                               "lower_temperature", "review_model", "stop"):
            raise ValueError(f"Unknown review action: {self.action}")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("Review decisions require a reason")


@dataclass
class CheckReport:
    index: int
    phase: Literal["precheck", "production"]
    total_time_ps: float
    production_time_ps: float
    framework: ValidationResult
    thermodynamics: ThermodynamicSummary
    msd: MSDResult | None = None
    transport: DiffusionResult | None = None
    transport_status: str = "not_evaluated"
    decision: Decision | None = None
    diagnostics: list[str] = field(default_factory=list)
    uncertainty: UncertaintyResult | None = None
    stop_metrics: dict[str, float | int | bool | None] = field(default_factory=dict)
    jumps: JumpResult | None = None
    mobility_status: str = "not_evaluated"
    framework_status: str = "not_evaluated"
    stability_metrics: dict = field(default_factory=dict)

"""Generate substitution-site compositions and screen formal redox capacity."""

from __future__ import annotations

import itertools
import re
from fractions import Fraction
from typing import Iterable, Mapping

from pymatgen.core import Composition

from Process_Struct.Chemical_Capacity_Constraints import (
    estimate_mobile_ion_window,
    estimate_redox_capacity,
)


def _parse_template(template: str) -> tuple[dict[str, float], float]:
    compact = template.replace("-", "")
    matches = list(re.finditer(r"X(?P<count>\d*(?:\.\d+)?)", compact))
    if len(matches) != 1:
        raise ValueError("template must contain exactly one X placeholder")
    match = matches[0]
    count = float(match.group("count") or 1.0)
    fixed = compact[: match.start()] + compact[match.end() :]
    amounts = Composition(fixed).get_el_amt_dict() if fixed else {}
    return {str(k): float(v) for k, v in amounts.items()}, count


def _compositions_of_sum(n: int, units: int) -> Iterable[tuple[int, ...]]:
    if n == 1:
        if units >= 0:
            yield (units,)
        return
    for first in range(units + 1):
        for rest in _compositions_of_sum(n - 1, units - first):
            yield (first,) + rest


def _ratio_vectors(n: int, granularity: float, max_integer_coefficient: int) -> set[tuple[float, ...]]:
    if n < 1:
        raise ValueError("n_elements must be positive")
    if max_integer_coefficient < 1:
        raise ValueError("max_integer_coefficient must be positive")
    step = Fraction(str(granularity))
    if step <= 0 or step > 1:
        raise ValueError("granularity must be in (0, 1]")

    ratios: set[tuple[float, ...]] = set()
    equal = Fraction(1, n)
    ratios.add(tuple(float(equal) for _ in range(n)))

    for counts in itertools.product(range(1, max_integer_coefficient + 1), repeat=n):
        total = sum(counts)
        ratios.add(tuple(float(Fraction(value, total)) for value in counts))

    if (Fraction(1, 1) / step).denominator == 1:
        units = int(Fraction(1, 1) / step)
        if units >= n:
            # ``n_elements`` means exactly n non-zero components. Shift the
            # grid compositions by one unit before distributing the remainder.
            for counts in _compositions_of_sum(n, units - n):
                ratios.add(
                    tuple(float(Fraction(value + 1, units)) for value in counts)
                )
    return ratios


def _formula_for(template: str, elements: tuple[str, ...], ratios: tuple[float, ...]) -> str:
    fixed, site_count = _parse_template(template)
    amounts = dict(fixed)
    for element, ratio in zip(elements, ratios):
        # An empty candidate denotes an unoccupied part of the X site.
        if not element:
            continue
        amounts[element] = amounts.get(element, 0.0) + site_count * ratio
    composition = Composition(amounts)
    return composition.formula.replace(" ", "")


def _adjust_mobile_ion_formula(
    formula: str,
    *,
    mobile_ion: str,
    environment: str,
) -> tuple[str, dict] | None:
    composition = Composition(formula)
    amounts = composition.get_el_amt_dict()
    initial_amount = float(amounts.get(mobile_ion, 0.0))
    if initial_amount <= 0:
        return None
    framework_amounts = dict(amounts)
    framework_amounts.pop(mobile_ion, None)
    framework_formula = Composition(framework_amounts).formula
    window = estimate_mobile_ion_window(
        framework_formula,
        mobile_ion=mobile_ion,
        environment=environment,
    )
    x_min = window.get("x_min_mobile_per_formula")
    x_max = window.get("x_max_mobile_per_formula")
    if x_min is None or x_max is None:
        return None
    target = min(initial_amount, float(x_max))
    if target < float(x_min) - 1e-8:
        return None
    amounts[mobile_ion] = target
    adjusted = Composition(amounts).formula.replace(" ", "")
    return adjusted, window


def generate_compositions(
    template: str,
    candidates: Iterable[str],
    *,
    n_elements: int = 1,
    granularity: float = 0.1,
    max_integer_coefficient: int = 10,
    allowed_ranges: Mapping[str, tuple[float, float]] | None = None,
) -> list[str]:
    """Generate unique formulas for one ``X`` substitution site.

    Equal ratios and all positive integer ratios up to ``max_integer_coefficient``
    are always considered. Additional ratios are generated on the requested
    granularity grid. ``allowed_ranges`` constrains each element fraction.
    """
    fixed, _ = _parse_template(template)
    del fixed
    # Empty strings are tolerated as a convenient input placeholder, but they
    # are not an X component. X fractions are always normalized over real
    # elements and therefore sum to one.
    elements = tuple(dict.fromkeys(str(item) for item in candidates if str(item)))
    if n_elements < 1 or n_elements > len(elements):
        raise ValueError("n_elements must be between 1 and the candidate count")
    ranges = allowed_ranges or {}
    for element, bounds in ranges.items():
        if element not in elements or len(bounds) != 2 or bounds[0] > bounds[1]:
            raise ValueError(f"invalid allowed range for {element!r}")

    formulas: set[str] = set()
    for selected in itertools.combinations(elements, n_elements):
        for ratios in _ratio_vectors(n_elements, granularity, max_integer_coefficient):
            if any(
                element in ranges
                and not (ranges[element][0] - 1e-9 <= ratio <= ranges[element][1] + 1e-9)
                for element, ratio in zip(selected, ratios)
            ):
                continue
            formulas.add(_formula_for(template, selected, ratios))
    return sorted(formulas)


def screen_compositions(
    template: str,
    candidates: Iterable[str],
    *,
    n_elements: int = 1,
    granularity: float = 0.1,
    max_integer_coefficient: int = 10,
    allowed_ranges: Mapping[str, tuple[float, float]] | None = None,
    capacity_cutoff_mAh_g: float = 100.0,
    environment: str = "auto",
    mobile_ion: str = "Li",
    adjust_mobile_ion: bool = True,
    active_elements: Iterable[str] | None = None,
    return_details: bool = False,
) -> dict:
    """Generate formulas and count candidates passing the capacity cutoff."""
    formulas = generate_compositions(
        template,
        candidates,
        n_elements=n_elements,
        granularity=granularity,
        max_integer_coefficient=max_integer_coefficient,
        allowed_ranges=allowed_ranges,
    )
    details = []
    for formula in formulas:
        original_formula = formula
        mobile_ion_adjusted = False
        mobile_ion_window = None
        try:
            estimate = estimate_redox_capacity(
                formula,
                environment=environment,
                active_elements=active_elements,
            )
            if (
                adjust_mobile_ion
                and estimate.get("status") == "no_neutral_valence_assignment"
            ):
                adjusted = _adjust_mobile_ion_formula(
                    formula,
                    mobile_ion=mobile_ion,
                    environment=estimate["environment"],
                )
                if adjusted is not None:
                    formula, mobile_ion_window = adjusted
                    mobile_ion_adjusted = formula != original_formula
                    estimate = estimate_redox_capacity(
                        formula,
                        environment=estimate["environment"],
                        active_elements=active_elements,
                    )
            capacity = estimate.get("capacity_mAh_g")
            passed = capacity is not None and capacity >= capacity_cutoff_mAh_g
            details.append(
                {
                    "formula": formula,
                    "original_formula": original_formula,
                    "status": estimate.get("status"),
                    "capacity_mAh_g": capacity,
                    "passes_cutoff": passed,
                    "filter_reason": "passed" if passed else "capacity_below_cutoff_or_unresolved",
                    "mobile_ion_adjusted": mobile_ion_adjusted,
                    "mobile_ion_window": mobile_ion_window,
                    "estimate": estimate,
                }
            )
        except Exception as error:
            details.append(
                {
                    "formula": formula,
                    "original_formula": original_formula,
                    "status": "error",
                    "capacity_mAh_g": None,
                    "passes_cutoff": False,
                    "filter_reason": f"{type(error).__name__}: {error}",
                    "mobile_ion_adjusted": mobile_ion_adjusted,
                    "mobile_ion_window": mobile_ion_window,
                }
            )
    passed_count = sum(row["passes_cutoff"] for row in details)
    result = {
        "generated_count": len(details),
        "passed_count": passed_count,
        "failed_count": len(details) - passed_count,
        "capacity_cutoff_mAh_g": capacity_cutoff_mAh_g,
    }
    if return_details:
        result["details"] = details
    return result

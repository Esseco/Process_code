"""Estimate Li/Na content windows from formal oxidation-state bounds.

This is a deliberately permissive charge-balance envelope for early screening.
It does not predict crystallographic site capacity, phase stability, voltage, or
cycling reversibility.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from pymatgen.core import Composition, Element

if __package__:
    from .anion_context import prepare_anion_groups
    from .redox_capacity import (
        FARADAY_OVER_3P6,
        RULES_PATH,
        _amounts,
        _resolve_environment,
        _scenario_electrons,
        infer_environment,
        load_rules,
    )
else:
    from anion_context import prepare_anion_groups
    from redox_capacity import (
        FARADAY_OVER_3P6,
        RULES_PATH,
        _amounts,
        _resolve_environment,
        _scenario_electrons,
        infer_environment,
        load_rules,
    )


def estimate_mobile_ion_window(
    formula: str,
    *,
    mobile_ion: str = "Na",
    environment: str = "auto",
    anion_redox_scenario: str = "none",
    anion_groups: Mapping[str, float] | None = None,
    rules_path: str = RULES_PATH,
) -> dict:
    """Estimate the min/max Li or Na content charge-balanced by a framework.

    ``formula`` may be either a bare framework (for example ``FePO4``) or a
    full composition containing the selected mobile ion (for example
    ``NaFePO4``). The selected Li/Na is removed before framework charges are
    evaluated. If present, its input amount is returned as ``initial_x``.

    For each framework element, the configured oxidation-state endpoints are
    combined independently. The guest-ion range is therefore a permissive
    envelope that allows mixed valence / partial occupancy between endpoints.
    """
    if mobile_ion not in {"Li", "Na"}:
        raise ValueError("mobile_ion must be 'Li' or 'Na'.")

    input_composition = Composition(formula)
    amounts = _amounts(input_composition)
    initial_x = amounts.pop(mobile_ion, 0.0)
    if not amounts:
        raise ValueError("Formula must include at least one framework element.")

    framework = Composition(amounts)
    rules = load_rules(rules_path)
    anion_model = prepare_anion_groups(formula, amounts, rules, anion_groups)
    ionic_amounts = anion_model["remaining_amounts"]
    if environment == "auto":
        if anion_model["recognized_groups"]:
            free_anions = {"O", "F", "Cl", "Br", "I", "S", "Se", "Te"}
            has_free_anion = any(
                ionic_amounts.get(element, 0.0) > 1e-8
                for element in free_anions
            )
            environment = "mixed_anion" if has_free_anion else "polyanion"
        else:
            environment = infer_environment(framework)
    environment = _resolve_environment(framework, environment, rules)

    fixed_common = rules["fixed_oxidation_states"]["common"]
    fixed_environment = rules["fixed_oxidation_states"]["by_environment"].get(
        environment, {}
    )
    redox_states = rules["environments"][environment]["redox_cation_states"]

    q_min = float(anion_model["fixed_charge"])
    q_max = float(anion_model["fixed_charge"])
    min_content_states: dict[str, float] = {}
    max_content_states: dict[str, float] = {}
    unresolved: list[str] = []
    used_state_ranges: dict[str, list[float]] = {}

    for element, amount in sorted(ionic_amounts.items()):
        if element in redox_states:
            states = sorted({float(state) for state in redox_states[element]})
            if not states:
                unresolved.append(element)
                continue
            low_state, high_state = states[0], states[-1]
            q_min += amount * low_state
            q_max += amount * high_state
            max_content_states[element] = low_state
            min_content_states[element] = high_state
            used_state_ranges[element] = states
        elif element in fixed_environment:
            state = float(fixed_environment[element])
            q_min += amount * state
            q_max += amount * state
            min_content_states[element] = state
            max_content_states[element] = state
        elif element in fixed_common:
            state = float(fixed_common[element])
            q_min += amount * state
            q_max += amount * state
            min_content_states[element] = state
            max_content_states[element] = state
        else:
            unresolved.append(element)

    result = {
        "input_formula": formula,
        "framework_formula": framework.formula,
        "mobile_ion": mobile_ion,
        "initial_x": round(initial_x, 6) if initial_x > 0 else None,
        "environment": environment,
        "status": "ok",
        "unresolved_elements": unresolved,
        "recognized_anion_groups": anion_model["recognized_groups"],
        "anion_group_assignment_ambiguous": anion_model["ambiguous"],
        "grouped_atom_amounts": anion_model["grouped_atom_amounts"],
        "framework_charge_min_e_per_formula": None,
        "framework_charge_max_e_per_formula": None,
        "x_min_mobile_per_formula": None,
        "x_max_mobile_per_formula": None,
        "delta_x_e_per_formula": None,
        "max_packed_formula_mass_g_mol": None,
        "capacity_mAh_g": None,
        "capacity_mAh_g_framework_mass_basis": None,
        "reference_x_within_window": None,
        "extractable_ions_from_reference": None,
        "insertable_ions_from_reference": None,
        "anion_redox_scenario": anion_redox_scenario,
        "anion_redox_charge_span_e_per_formula": 0.0,
        "min_content_endpoint_states": {},
        "max_content_endpoint_states": {},
        "assumption": (
            "Permissive formal-charge envelope: each element independently uses "
            "the configured stable-valence endpoints; mixed valence and partial "
            "Li/Na occupancy may interpolate between them. No geometric site "
            "limit or structural/electrochemical stability is imposed."
        ),
    }
    if unresolved:
        result["status"] = "unresolved_elements"
        return result

    anion_span = _scenario_electrons(
        ionic_amounts, environment, anion_redox_scenario, rules
    )
    q_max += anion_span
    result.update(
        {
            "framework_charge_min_e_per_formula": round(q_min, 6),
            "framework_charge_max_e_per_formula": round(q_max, 6),
            "anion_redox_charge_span_e_per_formula": round(anion_span, 6),
            "min_content_endpoint_states": {
                key: round(value, 6) for key, value in min_content_states.items()
            },
            "max_content_endpoint_states": {
                key: round(value, 6) for key, value in max_content_states.items()
            },
            "configured_redox_state_ranges": used_state_ranges,
        }
    )

    tolerance = 1e-8
    has_redox_element = bool(used_state_ranges) or anion_span > tolerance
    if not has_redox_element:
        result.update(
            {
                "delta_x_e_per_formula": 0.0,
                "capacity_mAh_g": 0.0,
                "capacity_mAh_g_framework_mass_basis": 0.0,
            }
        )
        if q_min <= tolerance:
            fixed_x = max(0.0, -q_min)
            framework_mass = float(framework.weight)
            packed_mass = framework_mass + fixed_x * float(
                Element(mobile_ion).atomic_mass
            )
            result.update(
                {
                    "x_min_mobile_per_formula": round(fixed_x, 6),
                    "x_max_mobile_per_formula": round(fixed_x, 6),
                    "max_packed_formula_mass_g_mol": round(packed_mass, 6),
                }
            )
            if initial_x > 0:
                result.update(
                    {
                        "reference_x_within_window": abs(initial_x - fixed_x)
                        <= tolerance,
                        "extractable_ions_from_reference": 0.0,
                        "insertable_ions_from_reference": 0.0,
                    }
                )
        else:
            result["mobile_ion_window_status"] = (
                "no_nonnegative_neutral_composition"
            )
        result["status"] = "no_redox_active_elements"
        return result

    if q_min > tolerance:
        result["status"] = "no_nonnegative_mobile_ion_window"
        return result

    # A+ compensates negative framework charge: x = -Q_framework.
    x_max = max(0.0, -q_min)
    x_min = max(0.0, -q_max)
    delta_x = max(0.0, x_max - x_min)
    framework_mass = float(framework.weight)
    max_packed_mass = framework_mass + x_max * float(Element(mobile_ion).atomic_mass)
    capacity = (
        FARADAY_OVER_3P6 * delta_x / max_packed_mass
        if max_packed_mass > 0
        else 0.0
    )
    framework_basis_capacity = (
        FARADAY_OVER_3P6 * delta_x / framework_mass
        if framework_mass > 0
        else 0.0
    )

    result.update(
        {
            "x_min_mobile_per_formula": round(x_min, 6),
            "x_max_mobile_per_formula": round(x_max, 6),
            "delta_x_e_per_formula": round(delta_x, 6),
            "max_packed_formula_mass_g_mol": round(max_packed_mass, 6),
            "capacity_mAh_g": round(capacity, 6),
            "capacity_mAh_g_framework_mass_basis": round(
                framework_basis_capacity, 6
            ),
        }
    )

    if initial_x > 0:
        within = x_min - tolerance <= initial_x <= x_max + tolerance
        result.update(
            {
                "reference_x_within_window": within,
                "extractable_ions_from_reference": round(
                    max(0.0, initial_x - x_min), 6
                ),
                "insertable_ions_from_reference": round(
                    max(0.0, x_max - initial_x), 6
                ),
            }
        )
    return result


def batch_estimate_mobile_ion_windows(
    formulas: Iterable[str],
    *,
    mobile_ion: str = "Na",
    environment: str = "auto",
    anion_redox_scenario: str = "none",
    anion_groups: Mapping[str, float] | None = None,
    rules_path: str = RULES_PATH,
) -> list[dict]:
    """Estimate guest-ion windows for many formulas, retaining row-level errors."""
    rows = []
    for index, formula in enumerate(formulas):
        try:
            row = estimate_mobile_ion_window(
                str(formula),
                mobile_ion=mobile_ion,
                environment=environment,
                anion_redox_scenario=anion_redox_scenario,
                anion_groups=anion_groups,
                rules_path=rules_path,
            )
        except Exception as error:
            row = {
                "input_formula": str(formula),
                "mobile_ion": mobile_ion,
                "environment": environment,
                "status": "error",
                "error": f"{type(error).__name__}: {error}",
            }
        row["row_index"] = index
        rows.append(row)
    return rows


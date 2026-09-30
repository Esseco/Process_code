"""Heuristic charge-balance and redox-capacity estimates for cathode screening.

This module is an early-stage upper-bound estimator, not a voltage, stability,
or cycling-life predictor. It requires pymatgen, available in the project's py1
environment.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from pymatgen.core import Composition
if __package__:
    from .anion_context import prepare_anion_groups
else:
    from anion_context import prepare_anion_groups

RULES_PATH = Path(__file__).with_name("redox_rules.json")
FARADAY_OVER_3P6 = 26801.4  # mAh mol(e-)^-1
DEFAULT_MOBILE_IONS = {"Li": 1.0, "Na": 1.0, "K": 1.0}


def load_rules(path: str | Path = RULES_PATH) -> dict:
    """Load the editable oxidation-state rules."""
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _amounts(composition: Composition) -> dict[str, float]:
    return {element.symbol: float(amount) for element, amount in composition.items()}


def infer_environment(formula: str | Composition) -> str:
    """Infer a broad anion family; pass environment explicitly when ambiguous."""
    composition = formula if isinstance(formula, Composition) else Composition(formula)
    symbols = {element.symbol for element in composition.elements}
    amounts = _amounts(composition)

    halogens = symbols.intersection({"F", "Cl", "Br", "I"})
    polyanion_centers = symbols.intersection({"P", "Si", "B", "C", "N"})
    has_sulfur_family = bool(symbols.intersection({"S", "Se", "Te"}))

    if "O" in symbols and "S" in symbols:
        oxygen_per_sulfur = amounts.get("O", 0.0) / max(
            amounts.get("S", 1.0), 1e-12
        )
        if oxygen_per_sulfur >= 3.0 and not halogens and not polyanion_centers:
            return "polyanion"
        return "mixed_anion"
    if "O" in symbols and polyanion_centers:
        return "mixed_anion" if halogens or has_sulfur_family else "polyanion"
    if "O" in symbols and halogens:
        return "oxyhalide"
    if "O" in symbols:
        return "oxide"
    if halogens and has_sulfur_family:
        return "mixed_anion"
    if halogens:
        return "halide"
    if has_sulfur_family:
        return "sulfide"
    raise ValueError(
        "Could not infer an anion environment. Pass oxide, oxyhalide, "
        "halide, sulfide, polyanion, or mixed_anion explicitly."
    )


def _resolve_environment(
    composition: Composition, environment: str, rules: Mapping
) -> str:
    if environment == "auto":
        environment = infer_environment(composition)
    if environment not in rules["environments"]:
        valid = ", ".join(sorted(rules["environments"]))
        raise ValueError(f"Unknown environment {environment!r}. Choose: {valid}")
    return environment


def _enumerate_neutral_assignments(
    amounts: Mapping[str, float],
    environment: str,
    rules: Mapping,
    max_solutions: int,
    tolerance: float = 1e-6,
    fixed_charge_offset: float = 0.0,
) -> tuple[list[dict[str, float]], list[str], bool]:
    """Enumerate charge-neutral formal valence assignments with branch pruning."""
    common_fixed = rules["fixed_oxidation_states"]["common"]
    env_fixed = rules["fixed_oxidation_states"]["by_environment"].get(
        environment, {}
    )
    redox_states = rules["environments"][environment]["redox_cation_states"]

    fixed_charge = float(fixed_charge_offset)
    fixed_assignment: dict[str, float] = {}
    variables: list[tuple[str, float, list[float]]] = []
    unresolved: list[str] = []

    for element, amount in sorted(amounts.items()):
        if amount <= 0:
            continue
        if element in redox_states:
            states = [float(x) for x in redox_states[element]]
            variables.append((element, amount, states))
        elif element in env_fixed:
            fixed_state = float(env_fixed[element])
            fixed_charge += amount * fixed_state
            fixed_assignment[element] = fixed_state
        elif element in common_fixed:
            fixed_state = float(common_fixed[element])
            fixed_charge += amount * fixed_state
            fixed_assignment[element] = fixed_state
        else:
            unresolved.append(element)

    if unresolved:
        return [], unresolved, False

    # Precompute the smallest/largest possible remaining charge to prune branches.
    min_remaining = [0.0] * (len(variables) + 1)
    max_remaining = [0.0] * (len(variables) + 1)
    for index in range(len(variables) - 1, -1, -1):
        _, amount, states = variables[index]
        min_remaining[index] = min_remaining[index + 1] + amount * min(states)
        max_remaining[index] = max_remaining[index + 1] + amount * max(states)

    solutions: list[dict[str, float]] = []
    assignment: dict[str, float] = dict(fixed_assignment)
    truncated = False

    def visit(index: int, partial_charge: float) -> None:
        nonlocal truncated
        if len(solutions) >= max_solutions:
            truncated = True
            return
        if partial_charge + min_remaining[index] > tolerance:
            return
        if partial_charge + max_remaining[index] < -tolerance:
            return
        if index == len(variables):
            if abs(partial_charge) <= tolerance:
                solutions.append(dict(assignment))
            return

        element, amount, states = variables[index]
        for state in states:
            assignment[element] = state
            visit(index + 1, partial_charge + amount * state)
            if truncated:
                break
        assignment.pop(element, None)

    visit(0, fixed_charge)
    return solutions, [], truncated


def _range(values: Sequence[float]) -> dict[str, float] | None:
    if not values:
        return None
    return {"min": round(min(values), 6), "max": round(max(values), 6)}


def _scenario_electrons(
    amounts: Mapping[str, float], environment: str, scenario: str, rules: Mapping
) -> float:
    scenarios = rules["anion_redox_scenarios"]
    if scenario not in scenarios:
        raise ValueError(
            f"Unknown anion redox scenario {scenario!r}; choose "
            + ", ".join(sorted(scenarios))
        )
    if scenario == "none":
        return 0.0

    config = scenarios[scenario]
    element = config["element"]
    allowed = {
        "oxygen_peroxo": {"oxide", "oxyhalide", "polyanion", "mixed_anion"},
        "sulfide_disulfide": {"sulfide", "mixed_anion"},
        "sulfur_conversion": {"sulfide", "mixed_anion"},
        "chloride_conversion": {"halide", "oxyhalide", "mixed_anion"},
    }
    if environment not in allowed[scenario]:
        raise ValueError(
            f"Scenario {scenario!r} is not configured for environment "
            f"{environment!r}."
        )
    return float(amounts.get(element, 0.0)) * float(config["electrons_per_atom"])


def _capacity(electrons: float, formula_mass: float) -> float:
    if formula_mass <= 0:
        return 0.0
    return FARADAY_OVER_3P6 * electrons / formula_mass


def estimate_redox_capacity(
    formula: str,
    *,
    environment: str = "auto",
    mobile_ions: Mapping[str, float] | None = None,
    active_elements: Iterable[str] | None = None,
    anion_redox_scenario: str = "none",
    anion_groups: Mapping[str, float] | None = None,
    rules_path: str | Path = RULES_PATH,
    max_solutions: int = 10000,
) -> dict:
    """Estimate charge-neutral valences and a heuristic electron/capacity budget.

    Pass the full composition at the intended initial SOC (normally the
    alkali-containing, discharged composition). Alkali ions are assigned their
    fixed formal charges for neutrality and their extractable charge inventory
    caps the reported capacity. If no mobile ion from mobile_ions is present,
    no mobile-ion cap is applied.

    The default Q_redox includes transition-metal/cation oxidation only.
    Optional anion scenarios are reported separately and added only when
    explicitly selected.
    """
    rules = load_rules(rules_path)
    composition = Composition(formula)
    amounts = _amounts(composition)
    anion_model = prepare_anion_groups(formula, amounts, rules, anion_groups)
    ionic_amounts = anion_model["remaining_amounts"]
    if environment == "auto":
        if anion_model["recognized_groups"]:
            free_anions = {"O", "F", "Cl", "Br", "I", "S", "Se", "Te"}
            has_free_anion = any(ionic_amounts.get(element, 0.0) > 1e-8 for element in free_anions)
            environment = "mixed_anion" if has_free_anion else "polyanion"
        else:
            environment = infer_environment(composition)
    environment = _resolve_environment(composition, environment, rules)
    formula_mass = float(composition.weight)
    solutions, unresolved, truncated = _enumerate_neutral_assignments(
        ionic_amounts,
        environment,
        rules,
        max_solutions,
        fixed_charge_offset=anion_model["fixed_charge"],
    )

    output = {
        "input_formula": formula,
        "normalized_formula": composition.formula,
        "environment": environment,
        "formula_mass_g_mol": round(formula_mass, 6),
        "status": "ok" if solutions else (
            "unresolved_elements" if unresolved else "no_neutral_valence_assignment"
        ),
        "unresolved_elements": unresolved,
        "neutral_assignment_count": len(solutions),
        "assignments_truncated": truncated,
        "q_redox_e_per_formula": None,
        "q_reduction_e_per_formula": None,
        "full_cation_swing_e_per_formula": None,
        "mobile_ion_inventory_e_per_formula": None,
        "anion_redox_scenario": anion_redox_scenario,
        "anion_redox_e_per_formula": 0.0,
        "capacity_mAh_g": None,
        "capacity_range_mAh_g": None,
        "sample_neutral_valence_assignments": [],
        "recognized_anion_groups": anion_model["recognized_groups"],
        "anion_group_assignment_ambiguous": anion_model["ambiguous"],
        "grouped_atom_amounts": anion_model["grouped_atom_amounts"],
        "interpretation": (
            "Heuristic formal-valence upper bound. It does not establish "
            "electrochemical reversibility, voltage, phase stability, or "
            "kinetic accessibility."
        ),
    }
    if not solutions:
        if not unresolved and anion_redox_scenario == "none":
            configured_states = rules["environments"][environment][
                "redox_cation_states"
            ]
            selected_elements = (
                set(configured_states)
                if active_elements is None
                else set(active_elements)
            )
            has_redox_element = any(
                element in selected_elements
                and element in configured_states
                and ionic_amounts.get(element, 0.0) > 0
                for element in amounts
            )
            if not has_redox_element:
                output.update(
                    {
                        "status": "no_redox_active_elements",
                        "q_redox_e_per_formula": {"min": 0.0, "max": 0.0},
                        "q_cation_oxidation_e_per_formula_uncapped": {
                            "min": 0.0,
                            "max": 0.0,
                        },
                        "q_reduction_e_per_formula": {"min": 0.0, "max": 0.0},
                        "full_cation_swing_e_per_formula": {
                            "min": 0.0,
                            "max": 0.0,
                        },
                        "capacity_mAh_g": 0.0,
                        "capacity_range_mAh_g": {"min": 0.0, "max": 0.0},
                        "interpretation": (
                            "No configured redox-active element is present; "
                            "redox capacity is set to zero."
                        ),
                    }
                )
        return output

    if active_elements is None:
        counted_elements = set(
            rules["environments"][environment]["redox_cation_states"]
        )
    else:
        counted_elements = set(active_elements)

    redox_states = rules["environments"][environment]["redox_cation_states"]
    oxidation_values: list[float] = []
    reduction_values: list[float] = []
    swing_values: list[float] = []
    for assignment in solutions:
        oxidation = 0.0
        reduction = 0.0
        swing = 0.0
        for element, current_state in assignment.items():
            if element not in counted_elements:
                continue
            states = [float(x) for x in redox_states[element]]
            amount = ionic_amounts[element]
            oxidation += amount * max(0.0, max(states) - current_state)
            reduction += amount * max(0.0, current_state - min(states))
            swing += amount * (max(states) - min(states))
        oxidation_values.append(oxidation)
        reduction_values.append(reduction)
        swing_values.append(swing)

    if mobile_ions is None:
        mobile_ions = DEFAULT_MOBILE_IONS
    mobile_inventory = sum(
        amounts.get(element, 0.0) * float(charge)
        for element, charge in mobile_ions.items()
    )
    mobile_cap = mobile_inventory if mobile_inventory > 0 else None
    anion_e = _scenario_electrons(
        ionic_amounts, environment, anion_redox_scenario, rules
    )

    # Apply the ion-inventory cap to each neutral valence solution.
    capped_total = []
    for oxidation in oxidation_values:
        total = oxidation + anion_e
        if mobile_cap is not None:
            total = min(total, mobile_cap)
        capped_total.append(max(0.0, total))

    q_range = _range(capped_total)
    capacity_range = (
        {
            "min": round(_capacity(q_range["min"], formula_mass), 6),
            "max": round(_capacity(q_range["max"], formula_mass), 6),
        }
        if q_range
        else None
    )

    output.update(
        {
            "q_redox_e_per_formula": q_range,
            "q_cation_oxidation_e_per_formula_uncapped": _range(oxidation_values),
            "q_reduction_e_per_formula": _range(reduction_values),
            "full_cation_swing_e_per_formula": _range(swing_values),
            "mobile_ion_inventory_e_per_formula": (
                round(mobile_inventory, 6) if mobile_cap is not None else None
            ),
            "anion_redox_e_per_formula": round(anion_e, 6),
            "capacity_mAh_g": capacity_range["max"] if capacity_range else None,
            "capacity_range_mAh_g": capacity_range,
            "sample_neutral_valence_assignments": [
                {key: round(value, 4) for key, value in assignment.items()}
                for assignment in solutions[:20]
            ],
            "cation_redox_window_states": {
                element: states
                for element, states in redox_states.items()
                if element in ionic_amounts and element in counted_elements
            },
        }
    )
    has_cation_redox = any(
        element in counted_elements
        and element in redox_states
        and ionic_amounts.get(element, 0.0) > 0
        for element in amounts
    )
    if not has_cation_redox and anion_e <= 0:
        output["status"] = "no_redox_active_elements"
        output["interpretation"] = (
            "No configured redox-active element is present; redox capacity is zero."
        )
    return output


def batch_estimate_redox_capacity(
    formulas: Iterable[str],
    *,
    environment: str = "auto",
    capacity_cutoff_mAh_g: float = 100.0,
    mobile_ions: Mapping[str, float] | None = None,
    anion_redox_scenario: str = "none",
    anion_groups: Mapping[str, float] | None = None,
    rules_path: str | Path = RULES_PATH,
) -> list[dict]:
    """Apply the estimator to many formulas and return flat, CSV-friendly rows."""
    rows = []
    for index, formula in enumerate(formulas):
        try:
            result = estimate_redox_capacity(
                str(formula),
                environment=environment,
                mobile_ions=mobile_ions,
                anion_redox_scenario=anion_redox_scenario,
                anion_groups=anion_groups,
                rules_path=rules_path,
            )
            q_range = result.get("q_redox_e_per_formula")
            capacity = result.get("capacity_mAh_g")
            rows.append(
                {
                    "row_index": index,
                    "formula": str(formula),
                    "environment": result.get("environment"),
                    "status": result.get("status"),
                    "q_redox_min_e_per_formula": (
                        q_range["min"] if q_range else None
                    ),
                    "q_redox_max_e_per_formula": (
                        q_range["max"] if q_range else None
                    ),
                    "capacity_min_mAh_g": (
                        result["capacity_range_mAh_g"]["min"]
                        if result.get("capacity_range_mAh_g")
                        else None
                    ),
                    "capacity_max_mAh_g": capacity,
                    "passes_capacity_cutoff": (
                        capacity is not None
                        and capacity >= capacity_cutoff_mAh_g
                    ),
                    "unresolved_elements": ",".join(
                        result.get("unresolved_elements", [])
                    ),
                    "details": result,
                }
            )
        except Exception as error:
            rows.append(
                {
                    "row_index": index,
                    "formula": str(formula),
                    "environment": environment,
                    "status": "error",
                    "q_redox_min_e_per_formula": None,
                    "q_redox_max_e_per_formula": None,
                    "capacity_min_mAh_g": None,
                    "capacity_max_mAh_g": None,
                    "passes_capacity_cutoff": False,
                    "unresolved_elements": "",
                    "error": f"{type(error).__name__}: {error}",
                }
            )
    return rows

def screen_substitutions(
    formula: str,
    replaced_element: str,
    candidate_elements: Sequence[str] | None = None,
    *,
    environment: str = "auto",
    capacity_cutoff_mAh_g: float = 100.0,
    q_cutoff_e_per_formula: float | None = None,
    mobile_ions: Mapping[str, float] | None = None,
    anion_redox_scenario: str = "none",
    anion_groups: Mapping[str, float] | None = None,
    rules_path: str | Path = RULES_PATH,
) -> dict:
    """Screen same-stoichiometry elemental substitutions by charge/capacity only.

    This does not create or relax structures and does not predict synthesis,
    phase stability, percolation, ion transport, or electronic conductivity.
    """
    rules = load_rules(rules_path)
    original = Composition(formula)
    amounts = _amounts(original)
    if replaced_element not in amounts:
        raise ValueError(f"{replaced_element} is not present in {formula!r}.")

    group_model = prepare_anion_groups(formula, amounts, rules, anion_groups)
    if anion_groups is None:
        explicit_groups: dict[str, float] = {}
        for group in group_model["recognized_groups"]:
            if group["recognition"] == "explicit_parentheses":
                name = group["group"]
                explicit_groups[name] = explicit_groups.get(name, 0.0) + float(
                    group["count"]
                )
        candidate_anion_groups = explicit_groups or None
    else:
        candidate_anion_groups = anion_groups

    if environment == "auto":
        if group_model["recognized_groups"]:
            remaining = group_model["remaining_amounts"]
            free_anions = {"O", "F", "Cl", "Br", "I", "S", "Se", "Te"}
            has_free_anion = any(
                remaining.get(element, 0.0) > 1e-8
                for element in free_anions
            )
            environment = "mixed_anion" if has_free_anion else "polyanion"
        else:
            environment = infer_environment(original)
    if environment not in rules["environments"]:
        raise ValueError(f"Unknown environment: {environment}")

    if candidate_elements is None:
        candidate_elements = (
            rules["substitution_candidates"]["lower_cost_first_pass"]
            + rules["substitution_candidates"]["secondary_screen"]
        )

    results = []
    for candidate in candidate_elements:
        if candidate == replaced_element:
            continue
        new_amounts = dict(amounts)
        replaced_amount = new_amounts.pop(replaced_element)
        new_amounts[candidate] = new_amounts.get(candidate, 0.0) + replaced_amount
        candidate_formula = Composition(new_amounts).formula
        estimate = estimate_redox_capacity(
            candidate_formula,
            environment=environment,
            mobile_ions=mobile_ions,
            anion_redox_scenario=anion_redox_scenario,
            anion_groups=candidate_anion_groups,
            rules_path=rules_path,
        )
        qmax = (
            estimate["q_redox_e_per_formula"]["max"]
            if estimate["q_redox_e_per_formula"]
            else None
        )
        cmax = estimate["capacity_mAh_g"]
        passes_q = (
            q_cutoff_e_per_formula is None
            or (qmax is not None and qmax >= q_cutoff_e_per_formula)
        )
        passes_capacity = (
            cmax is not None and cmax >= capacity_cutoff_mAh_g
        )
        results.append(
            {
                "replaced_element": replaced_element,
                "candidate_element": candidate,
                "candidate_formula": candidate_formula,
                "status": estimate["status"],
                "q_redox_e_per_formula": estimate["q_redox_e_per_formula"],
                "capacity_mAh_g": cmax,
                "passes_q_cutoff": passes_q,
                "passes_capacity_cutoff": passes_capacity,
                "estimate": estimate,
            }
        )

    results.sort(
        key=lambda item: (
            item["status"] != "ok",
            not item["passes_capacity_cutoff"],
            -(item["capacity_mAh_g"] or 0.0),
        )
    )
    return {
        "input_formula": formula,
        "replaced_element": replaced_element,
        "environment": environment,
        "capacity_cutoff_mAh_g": capacity_cutoff_mAh_g,
        "q_cutoff_e_per_formula": q_cutoff_e_per_formula,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate formal-valence charge capacity for a cathode formula."
    )
    parser.add_argument("formula", help="Full initial-SOC formula, e.g. NaFePO4")
    parser.add_argument(
        "--environment",
        default="auto",
        choices=[
            "auto", "oxide", "oxyhalide", "halide", "sulfide",
            "polyanion", "mixed_anion",
        ],
    )
    parser.add_argument(
        "--anion-redox",
        default="none",
        choices=[
            "none",
            "oxygen_peroxo",
            "sulfide_disulfide",
            "sulfur_conversion",
            "chloride_conversion",
        ],
    )
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = estimate_redox_capacity(
        args.formula,
        environment=args.environment,
        anion_redox_scenario=args.anion_redox,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()



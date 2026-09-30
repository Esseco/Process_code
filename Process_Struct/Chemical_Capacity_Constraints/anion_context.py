"""Context-aware bookkeeping for fixed polyatomic anion groups."""
from __future__ import annotations

import re
from typing import Mapping

from pymatgen.core import Composition


ANION_ELEMENTS = {"O", "F", "Cl", "Br", "I", "S", "Se", "Te"}


def prepare_anion_groups(
    formula: str,
    amounts: Mapping[str, float],
    rules: Mapping,
    anion_groups: Mapping[str, float] | None = None,
) -> dict:
    """Remove recognized fixed-charge groups and return their net charge.

    Groups in parentheses are treated as explicit. Without explicit grouping,
    common groups are inferred from the composition and the result is marked as
    heuristic. Pass ``anion_groups={"PO4": 2, "SO4": 1}`` to resolve ambiguous
    or unparenthesized formulas. Context-dependent groups are never inferred.
    """
    remaining = {str(key): float(value) for key, value in amounts.items()}
    configs = list(rules.get("polyanion_groups", []))
    by_name = {str(item["group"]): item for item in configs}
    records: list[tuple[dict, float, str]] = []
    ambiguous = False

    if anion_groups is not None:
        for name, count in anion_groups.items():
            if name not in by_name:
                raise ValueError(
                    f"Unknown anion group {name!r}; available groups: "
                    + ", ".join(sorted(by_name))
                )
            records.append((by_name[name], float(count), "user_override"))
    else:
        labels = sorted(by_name, key=len, reverse=True)
        if labels:
            pattern = re.compile(
                r"\((" + "|".join(re.escape(label) for label in labels) +
                r")\)(\d+(?:\.\d+)?)?"
            )
            for match in pattern.finditer(formula):
                count = float(match.group(2)) if match.group(2) else 1.0
                records.append((by_name[match.group(1)], count, "explicit_parentheses"))

    recognized: list[dict] = []
    fixed_charge = 0.0

    def apply_group(config: Mapping, count: float, source: str) -> None:
        nonlocal fixed_charge
        if count < 0:
            raise ValueError("Anion group counts must be nonnegative.")
        group_formula = str(config.get("formula", config["group"]))
        group_comp = Composition(group_formula)
        group_amounts = {
            element.symbol: float(value) for element, value in group_comp.items()
        }
        for element, coefficient in group_amounts.items():
            if remaining.get(element, 0.0) + 1e-8 < coefficient * count:
                raise ValueError(
                    f"Formula does not contain enough {element} for "
                    f"{count:g} {config['group']} group(s)."
                )
        for element, coefficient in group_amounts.items():
            remaining[element] = max(
                0.0, remaining.get(element, 0.0) - coefficient * count
            )
        charge = float(config["formal_charge"])
        fixed_charge += charge * count
        recognized.append(
            {
                "group": config["group"],
                "count": round(count, 6),
                "formal_charge_each": charge,
                "net_charge": round(charge * count, 6),
                "recognition": source,
            }
        )

    for config, count, source in records:
        apply_group(config, count, source)

    if anion_groups is None:
        auto_configs = [
            item for item in configs
            if item.get("auto_detect", item.get("default_redox_active") is False)
            and item.get("default_redox_active") is False
        ]
        centers = []
        for item in auto_configs:
            center = str(item["center_element"])
            if center not in centers:
                centers.append(center)

        for center in centers:
            if remaining.get(center, 0.0) <= 1e-8:
                continue
            candidates = []
            for config in auto_configs:
                if str(config["center_element"]) != center:
                    continue
                group_comp = Composition(str(config.get("formula", config["group"])))
                group_amounts = {
                    element.symbol: float(value)
                    for element, value in group_comp.items()
                }
                possible_count = min(
                    remaining.get(element, 0.0) / coefficient
                    for element, coefficient in group_amounts.items()
                )
                if possible_count <= 1e-8:
                    continue
                relevant = set(group_amounts) | {center}
                relevant.update(element for element in remaining if element in ANION_ELEMENTS)
                leftover_score = sum(
                    max(
                        0.0,
                        remaining.get(element, 0.0)
                        - possible_count * group_amounts.get(element, 0.0),
                    )
                    for element in relevant
                )
                candidates.append((leftover_score, config, possible_count))

            if not candidates:
                continue
            candidates.sort(key=lambda item: (item[0], str(item[1]["group"])))
            best_score, best_config, best_count = candidates[0]
            if len(candidates) > 1 and abs(candidates[1][0] - best_score) <= 1e-8:
                ambiguous = True
            apply_group(best_config, best_count, "stoichiometric_heuristic")

    for element in list(remaining):
        if remaining[element] <= 1e-8:
            remaining.pop(element)

    return {
        "remaining_amounts": remaining,
        "fixed_charge": round(fixed_charge, 8),
        "recognized_groups": recognized,
        "ambiguous": ambiguous,
        "grouped_atom_amounts": {
            element: round(
                float(amounts.get(element, 0.0)) - remaining.get(element, 0.0), 6
            )
            for element in amounts
            if float(amounts.get(element, 0.0)) - remaining.get(element, 0.0) > 1e-8
        },
    }
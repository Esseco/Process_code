from Process_Struct.Chemical_Capacity_Constraints import estimate_redox_capacity
from Process_Struct.Chemical_Capacity_Constraints.redox_capacity import load_rules


ELEMENTS = [
    "Ni", "Co", "Mn", "Fe", "Cr", "V", "Cu", "Ru",
    "Ti", "Mo", "Nb", "Sn", "Sb", "Mg", "Al", "Zn", "Zr",
    "Ta", "W", "Hf", "Ga", "Ge", "Sc", "Y", "La", "Ce", "Pr",
    "Nd", "Sm", "Gd", "Cd", "Pb",
]


def test_layered_oxide_group_elements_are_configured():
    rules = load_rules()
    env = rules["environments"]["layered_oxide"]
    fixed = rules["fixed_oxidation_states"]["by_environment"]["layered_oxide"]
    common = rules["fixed_oxidation_states"]["common"]

    assert all(
        element in env["redox_cation_states"] or element in fixed or element in common
        for element in ELEMENTS
    )
    assert env["redox_cation_states"]["Ru"] == [3, 4]
    assert env["redox_cation_states"]["Mo"] == [4, 5, 6]
    assert env["redox_cation_states"]["Nb"] == [4, 5]
    assert fixed["Ga"] == 3
    assert fixed["Ge"] == 4
    assert fixed["Nd"] == 3
    assert fixed["Cd"] == 2
    assert fixed["Pb"] == 2


def test_fixed_layered_oxide_dopant_is_charge_balanced_when_formula_allows_it():
    result = estimate_redox_capacity("LiGaO2")

    assert result["environment"] == "layered_oxide"
    assert result["status"] == "no_redox_active_elements"

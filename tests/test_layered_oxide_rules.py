from Process_Struct.Chemical_Capacity_Constraints import estimate_redox_capacity
from Process_Struct.Chemical_Capacity_Constraints.redox_capacity import load_rules


def test_layered_oxide_is_auto_detected_for_alkali_transition_metal_oxide():
    result = estimate_redox_capacity("LiCoO2")

    assert result["environment"] == "layered_oxide"
    assert result["cation_redox_window_states"]["Co"] == [3, 4]


def test_explicit_layered_oxide_uses_configured_ranges():
    result = estimate_redox_capacity("LiNi0.5Mn0.5O2", environment="layered_oxide")

    assert result["environment"] == "layered_oxide"
    assert load_rules()["environments"]["layered_oxide"]["redox_cation_states"]["Ti"] == [4]
    assert load_rules()["environments"]["layered_oxide"]["redox_cation_states"]["V"] == [3, 4, 5]
    assert result["cation_redox_window_states"]["Mn"] == [3, 4]

"""Minimal examples for the chemical capacity screening package."""

from Process_Struct.Chemical_Capacity_Constraints import (
    estimate_mobile_ion_window,
    estimate_redox_capacity,
)

window = estimate_mobile_ion_window(
    "Na3V2(PO4)2F3", mobile_ion="Na"
)
print("Na window:", window["x_min_mobile_per_formula"],
      window["x_max_mobile_per_formula"])

capacity = estimate_redox_capacity("Na3V2(PO4)2F3")
print("Redox capacity (mAh/g):", capacity["capacity_mAh_g"])

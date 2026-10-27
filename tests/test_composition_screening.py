from pymatgen.core import Composition

from CompositionScreening import generate_compositions, screen_compositions


def test_equal_and_integer_ratios_include_nfm111_and_integer_variants():
    formulas = generate_compositions(
        "Li-X-O2",
        ["Ni", "Mn", "Fe"],
        n_elements=3,
        granularity=0.1,
        max_integer_coefficient=2,
    )

    assert any(
        all(abs(Composition(formula)[element] - expected) < 1e-8 for element, expected in {
            "Li": 1.0,
            "Ni": 1 / 3,
            "Mn": 1 / 3,
            "Fe": 1 / 3,
            "O": 2.0,
        }.items())
        for formula in formulas
    )
    assert any(
        all(abs(Composition(formula)[element] - expected) < 1e-8 for element, expected in {
            "Li": 1.0,
            "Ni": 0.25,
            "Mn": 0.25,
            "Fe": 0.5,
            "O": 2.0,
        }.items())
        for formula in formulas
    )
    assert len(formulas) == len(set(formulas))


def test_screening_returns_count_and_rejection_reason():
    result = screen_compositions(
        "Li-X-O2",
        ["Ni", "Mn"],
        n_elements=2,
        granularity=0.1,
        capacity_cutoff_mAh_g=1000.0,
        return_details=True,
    )

    assert result["generated_count"] > 0
    assert result["passed_count"] == 0
    assert result["failed_count"] == result["generated_count"]
    assert all(row["filter_reason"] for row in result["details"])


def test_empty_candidate_is_ignored_and_x_fractions_still_sum_to_one():
    formulas = generate_compositions(
        "Li-X-O2",
        ["", "Mn", "Co"],
        n_elements=2,
        granularity=0.1,
        max_integer_coefficient=2,
    )

    assert "Li1Mn0.5Co0.5O2" in formulas
    assert "Li1Co1O2" not in formulas
    assert not any("Co0.9" in formula and "Mn" not in formula for formula in formulas)
    assert not any(formula.startswith("0.") for formula in formulas)


def test_screening_adjusts_full_mobile_ion_to_neutral_layered_oxide_amount():
    result = screen_compositions(
        "Li-X-O2",
        ["Ti", "Mn"],
        n_elements=2,
        granularity=0.1,
        max_integer_coefficient=2,
        capacity_cutoff_mAh_g=200.0,
        return_details=True,
    )

    row = next(
        item
        for item in result["details"]
        if "Ti0.1" in item["original_formula"] and "Mn0.9" in item["original_formula"]
    )
    assert row["formula"].startswith("Li0.9")
    assert row["mobile_ion_adjusted"] is True
    assert row["capacity_mAh_g"] > 200.0

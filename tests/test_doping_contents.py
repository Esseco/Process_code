import warnings

import pytest
from pymatgen.core import Lattice, Structure
from pymatgen.analysis.structure_matcher import StructureMatcher

from Process_Vasp import gen_ESGS_by_content

OXI = {"Li": 1, "Co": 3, "O": -2}


def reference():
    lat = Lattice.hexagonal(2.82, 14.05)
    struct = Structure.from_spacegroup(
        "R-3m", lat, ["Li", "Co", "O"], [[0, 0, 0], [0, 0, 0.5], [0, 0, 0.24]]
    )
    struct.make_supercell([2, 2, 1])
    return struct


def test_series_keeps_requested_counts_and_labels():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        series = gen_ESGS_by_content(reference(), [12, 6, 0], 2, species="Li", oxidation_states=OXI)

    assert list(series) == ["12_12", "6_12", "0_12"]
    assert len(series["12_12"]) == 1  # no disorder, reference only
    assert len(series["6_12"]) == 2
    assert len(series["0_12"]) == 1
    assert int(round(series["6_12"][0].composition["Li"])) == 6
    assert "Li" not in series["0_12"][0].composition


def test_returned_structures_are_distinct():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        series = gen_ESGS_by_content(reference(), [6], 2, species="Li", oxidation_states=OXI)

    first, second = series["6_12"]
    assert not StructureMatcher().fit(first, second)


@pytest.mark.parametrize(
    "contents,error",
    [([13], ValueError), ([-1], ValueError), ([6.5], TypeError), (["6"], TypeError)],
)
def test_invalid_contents_are_rejected(contents, error):
    with pytest.raises(error):
        gen_ESGS_by_content(reference(), contents, 1, species="Li", oxidation_states=OXI)


def test_missing_species_is_rejected():
    with pytest.raises(ValueError):
        gen_ESGS_by_content(reference(), [6], 1, species="Na", oxidation_states=OXI)


def test_explicit_oxidation_states_are_used():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        series = gen_ESGS_by_content(reference(), [6], 1, species="Li", oxidation_states=OXI)

    states = {specie.symbol: specie.oxi_state for site in series["6_12"][0] for specie in site.species}
    assert states["Co"] == 3

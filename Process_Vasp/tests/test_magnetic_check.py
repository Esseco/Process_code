"""Offline scalar Fe/Mn diagnostics; no VASP execution."""
import gzip
from types import SimpleNamespace
from unittest.mock import patch

from pymatgen.core import Lattice, Structure
import pytest
from Process_Vasp import check_dft_magnetic_moments, check_layered_oxide_moments, read_dft_magnetic_data


@pytest.mark.parametrize("moments,status,count", [
    ([4.3, -3.9, 0], "passed", 0), ([3.5, -4, 0], "passed", 0),
    ([4.5, 3, 0], "passed", 0), ([3.49, 4.01, 0], "warning", 2)])
def test_ranges(moments, status, count):
    report = check_layered_oxide_moments(["Fe", "Mn", "O"], moments, is_layered_oxide=True)
    assert report["status"] == status
    assert len(report["anomalous_atoms"]) == count
    assert report["checked_atoms"] == 2


@pytest.mark.parametrize("elements,layered,expected", [
    (["Ni", "O"], True, "skipped"), (["Fe", "O"], False, "skipped"),
    (["Fe"], True, "skipped"), (["Fe", "O"], None, "unknown")])
def test_applicability(elements, layered, expected):
    assert check_layered_oxide_moments(elements, [4] * len(elements), is_layered_oxide=layered)["status"] == expected


@pytest.mark.parametrize("moments", [None, [], [4], [float("nan"), 0], [float("inf"), 0]])
def test_missing_not_pass(moments):
    assert check_layered_oxide_moments(["Fe", "O"], moments, is_layered_oxide=True)["status"] == "unknown"


def test_reader_compressed_and_last_table(tmp_path):
    structure = Structure(Lattice.cubic(4), ["Fe", "Mn", "O"], [[0,0,0],[.5,.5,0],[.5,0,.5]])
    path = tmp_path / "OUTCAR.gz"
    with gzip.open(path, "wt") as stream:
        stream.write("fixture")
    with patch("pymatgen.io.vasp.outputs.Outcar", return_value=SimpleNamespace(magnetization=[
            {"tot": 4.3}, {"tot": -3.9}, {"tot": .01}])) as read:
        report = check_dft_magnetic_moments(tmp_path, structure=structure, is_layered_oxide=True, parameters={})
        assert str(read.call_args.args[0]).endswith("OUTCAR.gz")
    assert report["status"] == "passed"
    assert report["moments"] == [4.3, -3.9, .01]


def test_soc_and_skip_dont_read(tmp_path):
    structure = Structure(Lattice.cubic(4), ["Fe", "O"], [[0,0,0],[.5,.5,.5]])
    with patch("pymatgen.io.vasp.outputs.Outcar") as read:
        report = check_dft_magnetic_moments(tmp_path, structure=structure, is_layered_oxide=True,
            parameters={"LSORBIT": ".TRUE."})
        assert report["reason"] == "noncollinear_or_SOC_not_supported"
        assert check_dft_magnetic_moments(tmp_path, structure=structure, is_layered_oxide=False)["status"] == "skipped"
        read.assert_not_called()


def test_actual_outcar_final_table(tmp_path):
    structure = Structure(Lattice.cubic(4), ["Fe", "O"], [[0,0,0],[.5,.5,.5]])
    header = "number of bands NBANDS= 12\ntotal plane-waves  NPLWV = 24\nIBRION = -1\n"
    table = "\nmagnetization (x)\n# of ion       s       p       d       tot\n--------------------------------------------------\n1  0.0  0.0  {m}  {m}\n2  0.0  0.0  0.0  0.0\ntot  0.0  0.0  {m}  {m}\n"
    with gzip.open(tmp_path / "OUTCAR.gz", "wt") as stream:
        stream.write(header + table.format(m=1.2) + table.format(m=-4.3))
    report = check_dft_magnetic_moments(tmp_path, structure=structure, is_layered_oxide=True, parameters={})
    assert report["status"] == "passed", report
    assert report["moments"] == [-4.3, 0]


def test_raw_reader_retains_unsupported_elements(tmp_path):
    structure = Structure(Lattice.cubic(4), ["Ni", "O"], [[0,0,0],[.5,.5,.5]])
    with patch("pymatgen.io.vasp.outputs.Outcar", return_value=SimpleNamespace(
            noncollinear=False, magnetization=[{"tot": 1.7}, {"tot": .02}])):
        raw = read_dft_magnetic_data(tmp_path, structure=structure, parameters={})
    assert raw["status"] == "available"
    assert raw["sites"][0] == {"atom_index": 0, "element": "Ni", "moment": 1.7}
    assert "anomalous_atoms" not in raw


def test_raw_reader_retains_vector(tmp_path):
    from pymatgen.electronic_structure.core import Magmom
    structure = Structure(Lattice.cubic(4), ["Fe", "O"], [[0,0,0],[.5,.5,.5]])
    with patch("pymatgen.io.vasp.outputs.Outcar", return_value=SimpleNamespace(
            noncollinear=True, magnetization=[{"tot": Magmom([1,2,3])}, {"tot": Magmom([0,0,0])}])):
        raw = read_dft_magnetic_data(tmp_path, structure=structure, parameters={})
    assert raw["status"] == "available" and raw["noncollinear"] is True
    assert raw["moments"] == [[1,2,3], [0,0,0]]

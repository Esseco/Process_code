import csv
import json

import numpy as np
import pytest

from process_md import MDConfig, get_structure_info, save_csv, save_json, save_results
from process_md.models import MDResult


def test_results_preserve_metadata_units_and_errors(crystal, tmp_path):
    config = MDConfig(temperature_K=800, duration_ps=50)
    run = MDResult(parameters=config, status="failed", trajectory=tmp_path / "md.traj",
                   error="synthetic calculator error")
    path = save_results({"structure": get_structure_info(crystal), "md": run,
                         "array": np.array([1, 2]), "scalar": np.float64(3)}, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["results"]["md"]["parameters"]["duration_ps"] == 50
    assert data["results"]["md"]["error"] == "synthetic calculator error"
    assert data["results"]["structure"]["volume_A3"] == pytest.approx(60)
    assert data["results"]["array"] == [1, 2]
    assert data["results"]["scalar"] == 3


def test_json_refuses_overwrite_and_preserves_existing_data(tmp_path):
    path = save_json({"old": 1}, tmp_path / "result.json")
    with pytest.raises(FileExistsError):
        save_json({"new": 2}, path)
    assert json.loads(path.read_text()) == {"old": 1}
    save_json({"new": 2}, path, overwrite=True)
    assert json.loads(path.read_text()) == {"new": 2}


@pytest.mark.parametrize("value", [float("nan"), float("inf"), object()])
def test_invalid_json_does_not_damage_existing_results(tmp_path, value):
    path = tmp_path / "result.json"
    path.write_text("keep me", encoding="utf-8")
    with pytest.raises((ValueError, TypeError)):
        save_json({"bad": value}, path, overwrite=True)
    assert path.read_text() == "keep me"


def test_csv_round_trip_with_units_and_missing_values(tmp_path):
    path = save_csv([{"time_ps": 0, "msd_A2": np.float64(0)},
                     {"time_ps": 1, "msd_A2": 6, "diffusion_cm2_s": None}],
                    tmp_path / "curve.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[1] == {"time_ps": "1", "msd_A2": "6", "diffusion_cm2_s": ""}
    with pytest.raises(FileExistsError):
        save_csv([{"time_ps": 5}], path)


@pytest.mark.parametrize("rows", [[], [{"x": [1, 2]}], [{"x": float("nan")}], [{}]])
def test_csv_rejects_ambiguous_or_nonfinite_tables(tmp_path, rows):
    path = tmp_path / "bad.csv"
    with pytest.raises((ValueError, TypeError)):
        save_csv(rows, path)
    assert not path.exists()


@pytest.mark.parametrize("kind", ["json", "csv"])
def test_encoding_failure_preserves_existing_file(tmp_path, kind):
    path = tmp_path / f"existing.{kind}"
    path.write_bytes(b"keep me")
    with pytest.raises(UnicodeEncodeError):
        if kind == "json":
            save_json({"text": "\ud800"}, path, overwrite=True)
        else:
            save_csv([{"text": "\ud800"}], path, overwrite=True)
    assert path.read_bytes() == b"keep me"

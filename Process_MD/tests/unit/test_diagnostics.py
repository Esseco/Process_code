import pytest

from process_md.analysis.diagnostics import compare_transport, describe_cell, summarize_md_log
from process_md.models import DiffusionResult
from process_md import save_csv


def test_cell_heights_are_basis_aware(crystal):
    result = describe_cell(crystal)
    assert result["n_atoms"] == 2
    assert result["perpendicular_heights_A"][2] == pytest.approx(5)
    assert result["size_convergence"] == "not_assessed"


def test_md_log_statistics_preserve_units_and_time_window(tmp_path):
    path = save_csv([dict(step=i, time_fs=i * 1000, temperature_K=t, pressure_bar=None)
                     for i, t in enumerate([700, 790, 810])], tmp_path / "md.csv")
    result = summarize_md_log(path, start_ps=1)
    assert result.n_samples == 2
    assert result.start_ps == 1
    assert result.means["temperature_K"] == 800
    assert result.standard_deviations["temperature_K"] == 10
    assert "pressure_bar" not in result.means


@pytest.mark.parametrize("times", [[0, 0], [1, 0], [0, float("nan")]])
def test_invalid_log_times_fail(tmp_path, times):
    path = tmp_path / "md.csv"
    path.write_text("time_fs,temperature_K\n" + "\n".join(f"{t},800" for t in times))
    with pytest.raises(ValueError, match="times"):
        summarize_md_log(path)


def test_comparisons_return_evidence_without_convergence_verdict():
    left = DiffusionResult(1e-5, 1, 10, 0.99, temperature_K=800, conductivity_NE_S_cm=0.1)
    right = DiffusionResult(1.2e-5, 1, 20, 0.99, temperature_K=800, conductivity_NE_S_cm=0.12)
    result = compare_transport(left, right, varied="duration")
    assert result["relative_diffusion_change"] == pytest.approx(0.2)
    assert result["convergence"] == "not_assessed"
    right.temperature_K = 900
    with pytest.raises(ValueError, match="temperatures"):
        compare_transport(left, right, varied="cell")


def test_missing_temperatures_are_not_silently_dropped(tmp_path):
    path = save_csv([dict(time_fs=0, temperature_K=800), dict(time_fs=1, temperature_K=None)],
                    tmp_path / "md.csv")
    with pytest.raises(ValueError, match="missing"):
        summarize_md_log(path)


def test_invalid_transport_values_are_rejected_even_with_missing_partner():
    left = DiffusionResult(None, 1, 10, None, temperature_K=800)
    right = DiffusionResult(-1, 1, 10, None, temperature_K=800)
    with pytest.raises(ValueError, match="nonnegative"):
        compare_transport(left, right, varied="duration")

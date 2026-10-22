import pytest
from ase import Atoms
from ase.io.trajectory import Trajectory

from process_md import export_msd, fit_msd


def test_existing_msd_and_fit_apis_are_reused(tmp_path):
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    trajectory = tmp_path / "md.traj"
    with Trajectory(trajectory, "w") as frames:
        for index in range(151):
            frames.write(Atoms("LiO", positions=[[index * 0.1, 0, 0], [5, 5, 5]],
                               cell=[10, 10, 10], pbc=True))
    table = tmp_path / "msd.csv"
    metadata = export_msd(trajectory, table, species="Li", frame_interval_fs=1000,
                          unwrap=False)
    assert metadata["method"] == "pymatgen.analysis.diffusion.analyzer.DiffusionAnalyzer"
    assert metadata["frame_count"] == 151
    result = fit_msd(table, fit_start_ps=1, fit_end_ps=3, temperature_K=800,
                     volume_A3=1000, ion_charge=1, species="Li", diffusion_mode="3d")
    assert result["fit_method"] == "pymatgen"
    assert result["results"][0]["actual_fit_range_ps"] == [1, 3]
    assert result["results"][0]["species"] == "Li"
    assert "pymatgen_slope_floor_applied" in result["results"][0]
    assert "limitations" in result

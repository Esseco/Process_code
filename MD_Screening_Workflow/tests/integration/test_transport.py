import csv

import pytest
from ase import Atoms
from ase.io.trajectory import Trajectory

from md_screening import ScreeningConfig
from md_screening.analysis import analyze_check


def test_synthetic_continuous_transport_reuses_native_msd_and_fit(tmp_path):
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    trajectory = tmp_path / "trajectory.traj"
    # Synthetic trajectory, not a physical model: deterministic native-MSD exercise.
    with Trajectory(str(trajectory), "w") as frames:
        for index in range(156):
            frames.write(Atoms("LiO", positions=[[index*0.2, 0, 0], [5, 5, 5]], cell=[10]*3, pbc=True))
    log = tmp_path / "md.csv"
    with log.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_fs", "temperature_K"])
        writer.writerows((index * 1000, 800) for index in range(156))
    config = ScreeningConfig(precheck_ps=5, check_interval_ps=10, max_production_ps=150,
                             timestep_fs=1, trajectory_interval=1000, axes="x", jump_analysis=False)
    report = analyze_check(dict(steps_completed=155000, trajectory_file=trajectory, log_file=log), config, 15)
    assert report.production_time_ps == 150
    assert report.msd.n_frames == 151
    assert report.msd.msd_A2 == pytest.approx([0.04, 0.16, 0.36, 0.64])
    assert report.transport_status == "estimated"
    assert report.transport.diffusion_cm2_s > 0
    assert report.transport.conductivity_NE_S_cm > 0
    assert report.transport.uncertainty_status == "not_evaluated"
    assert report.decision is None

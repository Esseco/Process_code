"""Real GEMDAT -> existing pymatgen MSD -> no-jump decision, without MD."""
import csv

import pytest
from ase import Atoms
from ase.io.trajectory import Trajectory

from md_screening import ScreeningConfig, TransportStopper
from md_screening.analysis import analyze_check


def test_native_zero_jumps_plateau_connects_to_ten_ps_stop(tmp_path):
    pytest.importorskip("gemdat")
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    atoms = Atoms("Li2O4", positions=[[1, 1, 1], [4, 1, 1], [2, 4, 4], [4, 4, 4],
                                     [6, 4, 4], [8, 4, 4]], cell=[10]*3, pbc=True)
    trajectory = tmp_path / "static.traj"
    with Trajectory(str(trajectory), "w") as frames:
        for _ in range(301):
            frames.write(atoms)
    log = tmp_path / "md.csv"
    with log.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_fs", "temperature_K"])
        writer.writerows((50*index, 800) for index in range(301))
    config = ScreeningConfig(target_atoms=6, max_production_ps=10, timestep_fs=1,
                             trajectory_interval=50, min_obs=1)
    report = analyze_check(dict(steps_completed=15000, trajectory_file=trajectory, log_file=log), config, 1,
                           reference_sites=atoms)
    assert report.jumps.status == "estimated"
    assert report.jumps.reference_source == "explicit_reference"
    assert report.jumps.n_jumps == 0
    assert report.jumps.n_frames == 201
    assert report.framework_status == "no_instability_detected"
    assert report.msd is not None
    assert report.transport_status == "unresolved"
    assert TransportStopper(hop_distance_A=3)(report).action == "raise_temperature"
    assert report.production_time_ps == 10 and report.total_time_ps == 15

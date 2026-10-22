"""Analyze flushed snapshots using Process_MD, without duplicating algorithms."""
from itertools import islice

import numpy as np
from ase.io.trajectory import Trajectory
from process_md import calculate_msd, fit_diffusion, summarize_md_log, validate_framework

from .config import ScreeningConfig
from .review import CheckReport
from .stability import assess_framework


def analyze_check(event: dict, config: ScreeningConfig, index: int, *, reference_sites=None,
                  stop_on_instability: bool = False) -> CheckReport:
    """Framework uses the latest check window; transport excludes the precheck.

    Only the backend's explicit insufficient-MSD-data error is recoverable.
    Corrupt trajectories, failed analysis and missing dependencies propagate.
    """
    production_steps = event["steps_completed"] - config.steps(config.precheck_ps)
    phase = "production" if production_steps > 0 else "precheck"
    end_frame = event["steps_completed"] // config.trajectory_interval + 1
    window_steps = config.steps(config.precheck_ps if phase == "precheck" else config.check_interval_ps)
    start_frame = max(0, event["steps_completed"] - window_steps) // config.trajectory_interval
    with Trajectory(str(event["trajectory_file"]), "r") as frames:
        framework = validate_framework(
            islice(frames, start_frame, end_frame), mobile_species=(config.mobile_species,), coordinate_mode="unwrapped",
            coordination_cutoff_A=config.coordination_cutoff_A,
            rdf_window_fraction=0.2, rdf_frames_per_window=5,
            rdf_repeat=config.framework_rdf_repeat,
        )
    report = CheckReport(
        index=index, phase=phase, total_time_ps=event["steps_completed"] * config.timestep_fs / 1000,
        production_time_ps=max(0, production_steps * config.timestep_fs / 1000),
        framework=framework,
        thermodynamics=summarize_md_log(event["log_file"], start_ps=config.precheck_ps if phase == "production" else 0),
        diagnostics=["Framework diagnostics use the latest check window; RDF averages at most five snapshots per early/late window.",
                     "Size convergence and statistical sufficiency are not assessed.",
                     "All atoms other than mobile_species define the framework and its drift reference."],
    )
    unstable = assess_framework(report, config.framework_criteria)
    if unstable:
        report.diagnostics.append("Joint framework warning: transport in this state needs caller review.")
    if unstable and stop_on_instability:
        report.transport_status = "framework_unstable"
        report.diagnostics.append("Joint framework warning: skip transport fitting and jump analysis for this check.")
        return report
    if phase == "precheck":
        report.diagnostics.append("Precheck: no diffusion fit; subsequent MSD starts at this boundary frame.")
        return report

    first_production_frame = config.steps(config.precheck_ps) // config.trajectory_interval
    # Short integration examples need no expensive/backend-dependent jump analysis.
    jump_minimum = config.stop_criteria.no_jump_stop_ps if config.stop_criteria is not None else config.check_interval_ps
    if config.jump_analysis and report.production_time_ps >= jump_minimum:
        if reference_sites is None:
            raise ValueError("reference_sites is required for workflow GEMDAT jump analysis")
        from process_md import analyze_jumps
        with Trajectory(str(event["trajectory_file"]), "r") as frames:
            report.jumps = analyze_jumps(
                islice(frames, first_production_frame, end_frame), species=config.mobile_species,
                frame_interval_ps=config.frame_interval_ps, reference_sites=reference_sites,
                site_radius_A=config.jump_site_radius_A, min_residence_ps=config.jump_min_residence_ps,
            )

    with Trajectory(str(event["trajectory_file"]), "r") as frames:
        try:
            report.msd = calculate_msd(
                islice(frames, first_production_frame, end_frame), species=config.mobile_species,
                frame_interval_ps=config.frame_interval_ps, axes=config.axes,
                coordinate_mode="unwrapped", drift_reference="framework", min_obs=config.min_obs,
            )
        except ValueError as exc:
            if not str(exc).startswith("Not enough data for pymatgen multi-origin MSD:"):
                raise
            report.transport_status = "insufficient_data"
            report.diagnostics.append(str(exc))
            return report
    times = np.asarray(report.msd.time_ps)
    end = float(times[-1]) if config.fit_end_ps is None else config.fit_end_ps
    selected = times[(times >= config.fit_start_ps) & (times <= end)]
    if config.fit_start_ps < times[0]:
        raise ValueError("fit_start_ps precedes the actual MSD lag grid; choose a valid fit window")
    if end > times[-1] or len(selected) < 3:
        report.transport_status = "insufficient_fit_window"
        report.diagnostics.append("Requested lag-time fit window is not yet covered by at least three samples.")
        return report
    report.transport = fit_diffusion(
        report.msd, fit_start_ps=config.fit_start_ps, fit_end_ps=end,
        temperature_K=config.temperature_K, volume_A3=report.msd.volume_A3, ion_charge=config.ion_charge,
    )
    report.transport_status = "estimated" if report.transport.diffusion_cm2_s is not None else "unresolved"
    report.diagnostics.append("The requested lag window is fitted; no automatic linear-region selection or convergence test.")
    return report

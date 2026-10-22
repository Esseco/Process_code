"""One structure, one calculator, one continuous NVT run and replaceable review."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Callable

import numpy as np
from ase import Atoms
from ase.io import write
from ase.io.trajectory import Trajectory
from process_md import (MDResult, MDRunner, describe_alkali_state, describe_cell,
                        get_structure_info, prepare_structure, save_csv, save_json)
from process_md.structure import estimate_hop_distance

from .analysis import analyze_check
from .config import ScreeningConfig
from .calculators import create_default_calculator, mace_model_path
from .review import CheckReport, Decision
from .stopping import TransportStopper
from .stability import assess_framework


@dataclass
class WorkflowResult:
    output_dir: Path
    status: str = "running"
    md: MDResult | None = None
    check_reports: list[Path] = field(default_factory=list)
    last_check: CheckReport | None = None
    error: str | None = None


def _summary(report: CheckReport) -> dict:
    transport = report.transport
    interval = report.uncertainty
    return dict(
        check_index=report.index, phase=report.phase, total_time_ps=report.total_time_ps,
        production_time_ps=report.production_time_ps,
        framework_msd_A2=report.framework.framework_msd_A2,
        rdf_difference=report.framework.rdf_difference,
        coordination_change_fraction=report.framework.coordination_change_fraction,
        framework_status=report.framework_status,
        mobility_status=report.mobility_status,
        n_jumps=None if report.jumps is None else report.jumps.n_jumps,
        n_jumping_ions=None if report.jumps is None else report.jumps.n_jumping_ions,
        site_coverage=None if report.jumps is None else report.jumps.site_coverage,
        plateau_relative_change=report.stop_metrics.get("plateau_relative_change"),
        transport_status=report.transport_status,
        diffusion_cm2_s=None if transport is None else transport.diffusion_cm2_s,
        conductivity_NE_S_cm=None if transport is None else transport.conductivity_NE_S_cm,
        r_squared=None if transport is None else transport.r_squared,
        msd_at_fit_end_A2=report.stop_metrics.get("msd_at_fit_end_A2"),
        msd_threshold_A2=report.stop_metrics.get("msd_threshold_A2"),
        hop_distance_A=report.stop_metrics.get("hop_distance_A"),
        uncertainty_status=None if interval is None else interval.status,
        kinisi_diffusion_median_cm2_s=None if interval is None else interval.diffusion_median_cm2_s,
        kinisi_diffusion_lower_cm2_s=None if interval is None else interval.diffusion_lower_cm2_s,
        kinisi_diffusion_upper_cm2_s=None if interval is None else interval.diffusion_upper_cm2_s,
        kinisi_conductivity_NE_median_S_cm=None if interval is None else interval.conductivity_NE_median_S_cm,
        kinisi_conductivity_NE_lower_S_cm=None if interval is None else interval.conductivity_NE_lower_S_cm,
        kinisi_conductivity_NE_upper_S_cm=None if interval is None else interval.conductivity_NE_upper_S_cm,
        action=None if report.decision is None else report.decision.action,
        reason=None if report.decision is None else report.decision.reason,
    )


def _estimate_uncertainty(event: dict, config: ScreeningConfig, report: CheckReport):
    from process_md import analyze_diffusion_uncertainty

    fit = report.transport
    with Trajectory(str(event["trajectory_file"]), "r") as frames:
        start = config.steps(config.precheck_ps) // config.trajectory_interval
        return analyze_diffusion_uncertainty(
            islice(frames, start, None), species=config.mobile_species,
            frame_interval_ps=config.frame_interval_ps, axes=config.axes,
            fit_start_ps=fit.fit_start_ps, fit_end_ps=fit.fit_end_ps,
            temperature_K=config.temperature_K, volume_A3=fit.volume_A3,
            ion_charge=config.ion_charge, n_samples=config.uncertainty_samples, seed=config.seed,
        )


def run_screening(
    structure: Atoms | str | Path, *, calculator=None, output_dir: str | Path,
    config: ScreeningConfig | None = None,
    reviewer: Callable[[CheckReport], Decision] | None = None,
    reference_sites: Atoms | str | Path | None = None,
) -> WorkflowResult:
    """Run a supplied SOC structure; output_dir must be new.

    Defaults to local MACE-OMat and a coarse transport stopping rule. An
    injected calculator or reviewer overrides the corresponding default.
    stop_criteria=None with no reviewer restores record-only budget runs.
    reference_sites must supply all mobile sites (including vacancies) in
    the INPUT cell; the same supercell matrix is applied to both inputs.
    Optional kinisi runs once after an accept decision; it does not gate it.
    Exceptions are recorded and re-raised. This API does not resume a run.
    """
    if reviewer is not None and not callable(reviewer):
        raise TypeError("reviewer must be callable or None")
    config = ScreeningConfig() if config is None else config
    if not isinstance(config, ScreeningConfig):
        raise TypeError("config must be ScreeningConfig")
    if reference_sites is None:
        raise ValueError("reference_sites is required: supply the full-site reference structure")
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=False)
    result = WorkflowResult(root)
    automatic_review = reviewer is None and config.stop_criteria is not None
    metadata = dict(
        schema_version=1, workflow_version="0.1.0", config=config,
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        input_source=str(Path(structure).resolve()) if isinstance(structure, (str, Path)) else "ASE Atoms",
        calculator_class=None if calculator is None else f"{type(calculator).__module__}.{type(calculator).__name__}",
        default_model="mace-omat" if calculator is None else None,
        review_mode="coarse_transport" if automatic_review else ("record_only" if reviewer is None else "caller_supplied"),
        stage="preparing", structure=None,
    )
    summaries = []

    def persist() -> None:
        save_json({**metadata, "result": result}, root / "run.json", overwrite=True)

    persist()
    try:
        atoms = prepare_structure(structure, target_atoms=config.target_atoms)
        state = describe_alkali_state(atoms, mobile_species=config.mobile_species,
                                      configuration_id=config.configuration_id)
        if not atoms.pbc.all():
            raise ValueError("Screening requires full 3D PBC")
        if state.n_mobile_atoms == 0 or state.n_mobile_atoms == len(atoms):
            raise ValueError("Screening requires mobile ions and framework atoms")
        prepared = root / "prepared"
        prepared.mkdir()
        write(str(prepared / "structure.extxyz"), atoms, format="extxyz")
        metadata["structure"] = dict(info=get_structure_info(atoms), alkali_state=state,
                                     cell=describe_cell(atoms), supercell_matrix=atoms.info["process_md_supercell_matrix"])
        original_sites = prepare_structure(reference_sites)
        if not original_sites.pbc.all():
            raise ValueError("reference_sites requires full 3D PBC")
        matrix = np.asarray(atoms.info["process_md_supercell_matrix"])
        if not np.allclose(matrix @ original_sites.cell.array, atoms.cell.array, rtol=1e-9, atol=1e-8):
            raise ValueError("reference_sites must use the input structure cell before supercell expansion")
        sites = prepare_structure(original_sites, supercell_matrix=matrix)
        if sites.get_chemical_symbols().count(config.mobile_species) < state.n_mobile_atoms:
            raise ValueError("reference_sites must contain at least as many mobile species sites as the current structure")
        write(str(prepared / "reference_sites.extxyz"), sites, format="extxyz")
        metadata["jump_reference"] = "supplied_complete_sites"
        metadata["reference_source"] = str(Path(reference_sites).resolve()) if isinstance(reference_sites, (str, Path)) else "ASE Atoms"
        nearest = estimate_hop_distance(sites, species=config.mobile_species)
        metadata["reference_nearest_neighbor_A"] = nearest
        active_reviewer = reviewer
        if automatic_review:
            distance = config.hop_distance_A
            if distance is None:
                distance = nearest
            metadata["hop_distance"] = dict(distance_A=distance,
                source="user_override" if config.hop_distance_A is not None else "reference_mobile_sites",
                limitation="Geometric proxy only; vacancies and allowed migration paths are not inferred.")
            active_reviewer = TransportStopper(hop_distance_A=distance, criteria=config.stop_criteria)
        jump_minimum = config.stop_criteria.no_jump_stop_ps if config.stop_criteria is not None else config.check_interval_ps
        if config.jump_analysis and config.max_production_ps >= jump_minimum:
            metadata["stage"] = "checking_jump_backend"
            persist()
            from process_md import check_jump_backend
            check_jump_backend()
        if config.uncertainty_on_stop:
            # Fail before spending MD time if the explicitly requested backend is unavailable.
            metadata["stage"] = "checking_uncertainty_backend"
            persist()
            from process_md import check_uncertainty_backend
            check_uncertainty_backend()
        if calculator is None:
            metadata["model_path"] = str(mace_model_path(config))
            metadata["stage"] = "loading_model"
            persist()
            calculator = create_default_calculator(config)
            metadata["calculator_class"] = f"{type(calculator).__module__}.{type(calculator).__name__}"
        metadata["stage"] = "md"
        persist()

        def on_segment(event: dict) -> bool:
            elapsed = event["steps_completed"]
            initial = config.steps(config.precheck_ps)
            if elapsed < initial or (elapsed - initial) % config.steps(config.check_interval_ps):
                return False
            metadata["stage"] = "analyzing"
            report = analyze_check(event, config, len(result.check_reports), reference_sites=sites,
                                   stop_on_instability=automatic_review)
            unstable = assess_framework(report, config.framework_criteria)
            directory = root / "checks" / f"{report.index:03d}_{report.phase}"
            path = save_json(report, directory / "report.json")
            result.check_reports.append(path)
            result.last_check = report
            summaries.append(_summary(report))
            if report.msd is not None:
                save_csv([dict(lag_time_ps=t, msd_A2=m, **{f"msd_{axis}_A2": xyz[i] for i, axis in enumerate("xyz")})
                          for t, m, xyz in zip(report.msd.time_ps, report.msd.msd_A2, report.msd.components_A2)],
                         directory / "msd.csv")
            metadata["stage"] = "reviewing"
            persist()
            if automatic_review and unstable:
                decision = Decision("stop", "Framework instability: large, persistently growing framework MSD and changed window-averaged RDF. Melting, amorphization or model error require review; temperature is unchanged.")
            else:
                decision = Decision() if active_reviewer is None else active_reviewer(report)
            if not isinstance(decision, Decision):
                raise TypeError("reviewer must return Decision")
            if decision.action == "accept" and (report.phase != "production" or report.transport_status != "estimated"):
                raise ValueError("accept requires a production transport estimate; precheck/unresolved data cannot be accepted")
            report.decision = decision
            save_json(report, path, overwrite=True)
            if decision.action == "accept" and config.uncertainty_on_stop:
                metadata["stage"] = "uncertainty"
                persist()
                report.uncertainty = _estimate_uncertainty(event, config, report)
                save_json(report, path, overwrite=True)
            summaries[-1] = _summary(report)
            save_csv(summaries, root / "summary.csv", overwrite=True)
            if decision.action != "continue":
                result.status = ("heuristic_ready" if automatic_review else "accepted") if decision.action == "accept" else "needs_review"
                if automatic_review and unstable:
                    result.status = "framework_unstable"
            metadata["stage"] = "md"
            persist()
            return decision.action != "continue"

        result.md = MDRunner(calculator).run(
            atoms, temperature_K=config.temperature_K,
            duration_ps=(config.steps(config.precheck_ps) + config.steps(config.max_production_ps)) * config.timestep_fs / 1000,
            timestep_fs=config.timestep_fs, output_dir=root / "md",
            trajectory_interval=config.trajectory_interval, seed=config.seed,
            segment_ps=config.backend_segment_ps, on_segment=on_segment,
        )
        if result.status == "running":
            result.status = "budget_exhausted"
        metadata["stage"] = "finished"
        persist()
        return result
    except (Exception, KeyboardInterrupt) as exc:
        result.status = "failed"
        result.error = f"{type(exc).__name__}: {exc}"
        if summaries:
            save_csv(summaries, root / "summary.csv", overwrite=True)
        persist()
        raise

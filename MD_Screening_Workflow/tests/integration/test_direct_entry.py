"""A few real ASE NVT steps prove the preset/output wiring without MLIP cost."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from ase.calculators.lj import LennardJones
from ase.io import read

from md_screening import run_md
import md_screening.workflow as workflow


def options():
    return dict(temperature_K=100, precheck_ps=0.002, check_interval_ps=0.004,
                max_production_ps=0.008, trajectory_interval=1,
                pre_relax=True, relax_steps=0, require_relax_convergence=False,
                jump_analysis=False, stop_criteria=None)


def calculator():
    return LennardJones(epsilon=0.0103, sigma=1.8, rc=3)


def test_supplied_supercell_relaxation_nvt_and_readable_outputs(crystal, tmp_path, monkeypatch):
    pytest.importorskip("Process_MLIP")
    pytest.importorskip("pymatgen.analysis.diffusion.analyzer")
    source = crystal.copy()
    fingerprints = []
    original_archive = workflow.archive_md_output
    def inspect_before_archive(md):
        raw = md.trajectory.read_bytes()
        fingerprints.append(hashlib.sha256(raw).hexdigest())
        return original_archive(md)
    monkeypatch.setattr(workflow, "archive_md_output", inspect_before_archive)
    result = run_md(crystal, reference_sites=crystal, calculator=calculator(),
                    output_dir=tmp_path / "run", **options())
    root = result.output_dir
    assert result.status == "budget_exhausted" and result.md.steps_completed == 5
    assert len(result.check_reports) == 3
    prepared = read(root / "prepared/structure.extxyz")
    reference = read(root / "prepared/reference_sites.extxyz")
    assert len(prepared) == len(reference) == len(source)
    np.testing.assert_allclose(prepared.cell.array, source.cell.array)
    np.testing.assert_allclose(reference.cell.array, source.cell.array)
    for name in ["README.md", "parameters.json", "run.log", "run.json", "summary.csv",
                 "relaxation/report.json", "results/summary.json", "results/summary.csv",
                 "results/final_structure.extxyz"]:
        assert (root / name).is_file(), name
    summary = json.loads((root / "results/summary.json").read_text())
    assert summary["status"] == "budget_exhausted"
    assert summary["transport_status"] == "insufficient_data"
    assert summary["diffusion_cm2_s"] is None and summary["conductivity_NE_S_cm"] is None
    assert summary["ready_for_screening"] is False
    assert summary["files"]["trajectory"] == "md/production/md.traj.gz"
    assert not (root / "md/production/md.traj").exists()
    assert hashlib.sha256(gzip.decompress(result.md.trajectory.read_bytes())).hexdigest() == fingerprints[0]
    archive = summary["trajectory_archive"]
    assert archive["status"] == "archived" and archive["sha256"] == fingerprints[0]
    for filename, key in [("md/results.json", "trajectory"), ("run.json", "trajectory")]:
        stored = json.loads((root / filename).read_text())
        stored_md = stored["results"]["md"] if filename.startswith("md/") else stored["result"]["md"]
        assert stored_md[key] == str(result.md.trajectory)
    backend = json.loads((root / "md/production/report.json").read_text())
    assert backend["trajectory_file"] == str(result.md.trajectory)
    assert "pre_relaxation" in (root / "run.log").read_text()
    assert "finished" in (root / "run.log").read_text()
    with (root / "results/summary.csv").open(newline="") as handle:
        row = list(csv.DictReader(handle))[0]
    assert row["diffusion_cm2_s"] == ""  # unresolved is not zero
    assert not list(root.rglob("*.ckpt"))
    with pytest.raises(FileExistsError):
        run_md(crystal, reference_sites=crystal, calculator=calculator(),
               output_dir=root, **options())


def test_analysis_failure_keeps_diagnosis_and_clear_failed_summary(crystal, tmp_path, monkeypatch):
    pytest.importorskip("Process_MLIP")
    def fail(*args, **kwargs):
        raise RuntimeError("analysis failed for test")
    monkeypatch.setattr(workflow, "analyze_check", fail)
    root = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="analysis failed"):
        run_md(crystal, reference_sites=crystal, calculator=calculator(),
               output_dir=root, **options())
    summary = json.loads((root / "results/summary.json").read_text())
    assert summary["status"] == "failed"
    assert "analysis failed" in summary["error"]
    assert "failed" in (root / "run.log").read_text()
    assert summary["diffusion_cm2_s"] is None


def test_final_export_failure_still_persists_failed_summary(crystal, tmp_path, monkeypatch):
    pytest.importorskip("Process_MLIP")
    import md_screening.reporting as reporting
    def bad_export(*args, **kwargs):
        raise RuntimeError("cannot export final structure")
    monkeypatch.setattr(reporting, "read", bad_export)
    root = tmp_path / "export_failed"
    with pytest.raises(RuntimeError, match="cannot export"):
        run_md(crystal, reference_sites=crystal, calculator=calculator(),
               output_dir=root, **options())
    summary = json.loads((root / "results/summary.json").read_text())
    assert summary["status"] == "failed" and "cannot export" in summary["error"]
    assert (root / "md/production/md.traj").is_file()
    assert "failed" in (root / "run.log").read_text()


def test_compression_can_be_disabled_without_changing_integration(crystal, tmp_path):
    pytest.importorskip("Process_MLIP")
    result = run_md(crystal, reference_sites=crystal, calculator=calculator(),
                    output_dir=tmp_path / "raw", compress_trajectory=False, **options())
    assert result.status == "budget_exhausted"
    assert result.md.trajectory.name == "md.traj" and result.md.trajectory.is_file()
    assert not result.md.trajectory.with_suffix(".traj.gz").exists()


def test_compression_failure_preserves_md_result_and_original(crystal, tmp_path, monkeypatch):
    pytest.importorskip("Process_MLIP")
    def fail(md):
        raise OSError("archive disk error")
    monkeypatch.setattr(workflow, "archive_md_output", fail)
    result = run_md(crystal, reference_sites=crystal, calculator=calculator(),
                    output_dir=tmp_path / "archive_failed", **options())
    assert result.status == "budget_exhausted" and result.error is None
    assert result.md.trajectory.name == "md.traj" and result.md.trajectory.is_file()
    summary = json.loads((result.output_dir / "results/summary.json").read_text())
    assert summary["trajectory_archive"]["status"] == "failed"
    assert summary["trajectory_archive"]["source_retained"] is True
    assert "archive disk error" in (result.output_dir / "run.log").read_text()


def test_persist_failure_after_compression_still_keeps_original(crystal, tmp_path, monkeypatch):
    pytest.importorskip("Process_MLIP")
    original_summary = workflow.write_summary
    def fail_once(root, metadata, result):
        if metadata.get("trajectory_archive", {}).get("status") == "archived":
            raise OSError("cannot publish archived summary")
        return original_summary(root, metadata, result)
    monkeypatch.setattr(workflow, "write_summary", fail_once)
    result = run_md(crystal, reference_sites=crystal, calculator=calculator(),
                    output_dir=tmp_path / "persist_failed", **options())
    assert result.status == "budget_exhausted" and result.error is None
    assert (result.output_dir / "md/production/md.traj").is_file()
    assert result.md.trajectory.is_file()
    summary = json.loads((result.output_dir / "results/summary.json").read_text())
    assert summary["trajectory_archive"]["status"] == "failed"
    assert summary["trajectory_archive"]["source_retained"] is True

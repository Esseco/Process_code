"""Lossless streaming archives never replace an unchecked trajectory."""
import gzip
import hashlib
import json

import pytest

from process_md import MDConfig, MDResult
from md_screening.archiving import archive_md_output, gzip_trajectory
import md_screening.archiving as archiving


def test_gzip_round_trip_keeps_source_until_workflow_persists(tmp_path):
    source = tmp_path / "md.traj"
    payload = bytes(range(256)) * 9000  # exceeds the streaming chunk size
    source.write_bytes(payload)
    info = gzip_trajectory(source)
    archive = source.with_suffix(".traj.gz")
    assert gzip.decompress(archive.read_bytes()) == payload
    assert source.read_bytes() == payload
    assert info["sha256"] == hashlib.sha256(payload).hexdigest()
    assert info["original_bytes"] == len(payload)
    assert info["compressed_bytes"] == archive.stat().st_size


def test_existing_archive_is_never_overwritten(tmp_path):
    source = tmp_path / "md.traj"
    source.write_bytes(b"original")
    archive = source.with_suffix(".traj.gz")
    archive.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        gzip_trajectory(source)
    assert source.read_bytes() == b"original"
    assert archive.read_bytes() == b"existing"


def test_failed_verification_keeps_source_and_cleans_partial_archive(tmp_path, monkeypatch):
    source = tmp_path / "md.traj"
    source.write_bytes(b"important trajectory")
    def fail(*args):
        raise ValueError("archive verification failed")
    monkeypatch.setattr(archiving, "_fingerprint", fail)
    with pytest.raises(ValueError, match="verification"):
        gzip_trajectory(source)
    assert source.read_bytes() == b"important trajectory"
    assert not source.with_suffix(".traj.gz").exists()


def test_archive_updates_backend_paths_before_source_removal(tmp_path):
    directory = tmp_path / "production"
    directory.mkdir()
    source = directory / "md.traj"
    source.write_bytes(b"trajectory data" * 100)
    report = directory / "report.json"
    report.write_text(json.dumps(dict(trajectory_file=str(source), status="completed")))
    result = MDResult(MDConfig(800, 1), status="completed", output_dir=tmp_path,
                      trajectory=source, report=report)
    info = archive_md_output(result)
    assert source.is_file()  # the workflow removes it only after its final persist
    assert result.trajectory == source.with_suffix(".traj.gz")
    assert json.loads(report.read_text())["trajectory_file"] == str(result.trajectory)
    stored = json.loads((tmp_path / "results.json").read_text())["results"]["md"]
    assert stored["trajectory"] == str(result.trajectory)
    assert info["path"] == str(result.trajectory)


def test_manifest_update_failure_restores_paths_and_reports(tmp_path, monkeypatch):
    directory = tmp_path / "production"
    directory.mkdir()
    source = directory / "md.traj"
    source.write_bytes(b"important trajectory" * 100)
    report = directory / "report.json"
    report.write_text(json.dumps(dict(trajectory_file=str(source), status="completed")))
    results = tmp_path / "results.json"
    results.write_text(json.dumps(dict(original="unchanged")))
    originals = report.read_bytes(), results.read_bytes()
    md = MDResult(MDConfig(800, 1), status="completed", output_dir=tmp_path,
                  trajectory=source, report=report, records=["original record"])
    save = archiving.save_json
    def fail_on_results(data, path, **kwargs):
        if path == results:
            results.write_bytes(b"partial write")
            raise OSError("cannot update backend results")
        return save(data, path, **kwargs)
    monkeypatch.setattr(archiving, "save_json", fail_on_results)
    with pytest.raises(OSError, match="backend results"):
        archive_md_output(md)
    assert md.trajectory == source and md.records == ["original record"]
    assert source.read_bytes() == b"important trajectory" * 100
    assert (report.read_bytes(), results.read_bytes()) == originals
    assert not source.with_suffix(".traj.gz").exists()

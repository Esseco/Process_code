"""Stream and verify gzip archives after integration and analysis have ended."""
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path

from process_md import save_json


_CHUNK_BYTES = 1024 * 1024


def _fingerprint(stream):
    digest = hashlib.sha256()
    size = 0
    for chunk in iter(lambda: stream.read(_CHUNK_BYTES), b""):
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def gzip_trajectory(source):
    """Keep source; remove a newly created archive if writing/verification fails."""
    source = Path(source)
    archive = source.with_suffix(source.suffix + ".gz")
    created = False
    try:
        digest = hashlib.sha256()
        size = 0
        with source.open("rb") as raw, archive.open("xb") as packed:
            created = True
            with gzip.GzipFile(filename="", fileobj=packed, mode="wb",
                               compresslevel=6, mtime=0) as compressed:
                for chunk in iter(lambda: raw.read(_CHUNK_BYTES), b""):
                    digest.update(chunk)
                    size += len(chunk)
                    compressed.write(chunk)
        expected = digest.hexdigest(), size
        with gzip.open(archive, "rb") as restored:
            if _fingerprint(restored) != expected:
                raise ValueError("Trajectory archive verification failed")
        return dict(status="archived", path=str(archive), sha256=expected[0],
                    original_bytes=size, compressed_bytes=archive.stat().st_size)
    except BaseException:
        if created:
            archive.unlink()
        raise


def archive_md_output(md):
    """Update backend manifests; caller persists workflow paths before unlinking."""
    results_path = Path(md.output_dir) / "results.json"
    paths = [results_path] + ([] if md.report is None else [Path(md.report)])
    originals = {path: path.read_bytes() if path.exists() else None for path in paths}
    report = None if md.report is None else json.loads(originals[Path(md.report)])
    info = gzip_trajectory(md.trajectory)
    updated = replace(
        md, trajectory=Path(info["path"]),
        records=[*md.records, "Trajectory losslessly gzip archived; decompress before ASE analysis"],
    )
    try:
        if report is not None:
            report.update(trajectory_file=str(updated.trajectory), trajectory_archive=info)
            save_json(report, md.report, overwrite=True)
        save_json({"schema_version": 1, "results": {"md": updated}},
                  results_path, overwrite=True)
    except BaseException:
        # Keep the original trajectory/path if a backend manifest update fails.
        for path, content in originals.items():
            if content is not None:
                path.write_bytes(content)
            elif path.exists():
                path.unlink()
        Path(info["path"]).unlink()
        raise
    md.trajectory, md.records = updated.trajectory, updated.records
    return info

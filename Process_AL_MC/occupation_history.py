"""Exact Na/Vac occupancy history; no geometry matching or model dependencies."""

import base64
import hashlib
import json
from pathlib import Path
import struct
import zlib

MAGIC = b"MC_OCC1\0"
MAX_BYTES = 64 * 1024 * 1024


def pack_occupation(occupation):
    packed = bytearray((len(occupation) + 7) // 8)
    for index, species in enumerate(occupation):
        if species not in ("Na", "Vac"):
            raise ValueError("Exact Na occupancy accepts only Na and Vac")
        if species == "Na":
            packed[index // 8] |= 1 << (index % 8)
    return bytes(packed)


def site_layout(structure):
    """Hash ordered reference sites once, never relaxed coordinates or symmetry."""
    rows = [
        [site.specie.symbol, *[round(float(x % 1), 10) for x in site.frac_coords]]
        for site in structure
    ]
    count = sum(row[0] == "Na" for row in rows)
    return count, hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()


def encode_snapshot(scope, site_count, basis, records):
    header = json.dumps(
        {"scope": scope, "site_count": site_count, "basis": basis}, separators=(",", ":")
    ).encode()
    raw = MAGIC + struct.pack(">I", len(header)) + header + b"".join(sorted(records))
    if len(raw) > MAX_BYTES:
        raise ValueError("MC occupancy snapshot exceeds supported size")
    return zlib.compress(raw)


def decode_snapshot(data):
    decoder = zlib.decompressobj()
    raw = decoder.decompress(data, MAX_BYTES + 1)
    if len(raw) > MAX_BYTES or not decoder.eof or decoder.unused_data:
        raise ValueError("Invalid or oversized MC occupancy snapshot")
    if raw[:8] != MAGIC or len(raw) < 12:
        raise ValueError("Invalid MC occupancy snapshot format")
    length = struct.unpack(">I", raw[8:12])[0]
    if not 0 < length <= 4096 or 12 + length > len(raw):
        raise ValueError("Invalid MC occupancy header")
    header = json.loads(raw[12 : 12 + length])
    count = header.get("site_count")
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("Invalid Na site count")
    width = (count + 7) // 8
    body = raw[12 + length :]
    if len(body) % width:
        raise ValueError("Truncated MC occupancy records")
    return header, [body[i : i + width] for i in range(0, len(body), width)]


class ReferenceOccupations:
    """Optional per-run reference; the caller owns cross-run persistence."""

    def __init__(self, scope, site_count, basis, *, seed=None, reference_file=None):
        self.scope, self.site_count, self.basis = scope, site_count, basis
        self.records = set()
        self.new_records = set()
        data = Path(reference_file).read_bytes() if reference_file else None
        for payload in (data, base64.b64decode(seed, validate=True) if seed else None):
            if payload is None:
                continue
            header, records = decode_snapshot(payload)
            if header != {"scope": scope, "site_count": site_count, "basis": basis}:
                raise ValueError("MC reference branch or site ordering mismatch")
            for bits in records:
                self._validate(bits)
            self.records.update(records)

    def _validate(self, bits):
        if len(bits) != (self.site_count + 7) // 8:
            raise ValueError("MC reference bitmap width mismatch")
        if self.site_count % 8 and bits[-1] >> (self.site_count % 8):
            raise ValueError("MC reference bitmap has nonzero padding")

    def __contains__(self, bits):
        return bits in self.records

    def __len__(self):
        return len(self.records)

    def add(self, bits):
        self._validate(bits)
        if bits in self.records:
            return False
        self.records.add(bits)
        self.new_records.add(bits)
        return True

    def write_delta(self, path):
        path = Path(path)
        temporary = path.with_name(path.name + ".part")
        temporary.write_bytes(
            encode_snapshot(self.scope, self.site_count, self.basis, self.new_records)
        )
        temporary.replace(path)

    def close(self):
        pass

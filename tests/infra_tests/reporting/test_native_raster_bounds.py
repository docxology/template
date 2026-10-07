"""Actual sparse/header images prove native raster bounds precede materialization."""

from __future__ import annotations

import hashlib
import struct
import time
import zlib
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_acceptance_checks import _read_pdf_rasters, audit_pdf_raster
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def test_sparse_file_refused_before_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "output/readiness/page-1.png"
    path.parent.mkdir(parents=True)
    with path.open("wb") as stream:
        stream.truncate(64 * 1024 * 1024 + 1)
    reader = SnapshotReader(tmp_path)
    with pytest.raises(ValueError, match="file exceeds finite encoded byte budget"):
        _read_pdf_rasters(reader, [path], deadline=time.monotonic() + 5)
    assert not reader.snapshots


def test_sparse_aggregate_refused_before_snapshot(tmp_path: Path) -> None:
    directory = tmp_path / "output/readiness"
    directory.mkdir(parents=True)
    paths = [directory / f"page-{index}.png" for index in range(5)]
    for path in paths:
        with path.open("wb") as stream:
            stream.truncate(51 * 1024 * 1024)
    reader = SnapshotReader(tmp_path)
    with pytest.raises(ValueError, match="closure exceeds finite encoded byte budget"):
        _read_pdf_rasters(reader, paths, deadline=time.monotonic() + 5)
    assert not reader.snapshots


def test_compressed_large_header_refused_before_pixel_decoder(tmp_path: Path) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

    path = tmp_path / "output/readiness/page-1.png"
    path.parent.mkdir(parents=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!IIBBBBB", 8001, 8000, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + chunk(b"IEND", b"")
    )
    with pytest.raises(ValueError, match="page exceeds finite pixel budget"):
        _read_pdf_rasters(SnapshotReader(tmp_path), [path], deadline=time.monotonic() + 5)


def test_actual_raster_preserves_pixels_hash_and_variance(tmp_path: Path) -> None:
    from PIL import Image

    path = tmp_path / "output/readiness/page-1.png"
    path.parent.mkdir(parents=True)
    image = Image.new("RGB", (8, 4), "white")
    image.putpixel((1, 2), (0, 0, 0))
    image.save(path)
    reader = SnapshotReader(tmp_path)
    rows = _read_pdf_rasters(reader, [path], deadline=time.monotonic() + 5)
    assert len(rows) == 1
    assert rows[0]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (rows[0]["width_px"], rows[0]["height_px"]) == (8, 4)
    assert rows[0]["variance"] > 0 and reader.unchanged()


def test_impossible_page_geometry_refused_before_tools(tmp_path: Path) -> None:
    from infrastructure.reporting.native_format_pdf_oracles import pdf_control_bytes

    path = tmp_path / "output/readiness/input.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(pdf_control_bytes("baseline"))
    artifact = SnapshotReader(tmp_path).read(path.relative_to(tmp_path).as_posix())
    with pytest.raises(ValueError, match="geometry/pixel budget"):
        audit_pdf_raster(
            tmp_path,
            path.parent,
            artifact,
            {"pages": 1, "page_boxes_pt": [[0, 0, 100000, 100000]]},
            env={"PATH": ""},
            deadline=time.monotonic() + 5,
            run_id="bounded",
            ordinal=1,
        )
    assert not (path.parent / "input-0001.pdf").exists()

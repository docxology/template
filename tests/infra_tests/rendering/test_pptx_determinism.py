"""Deterministic OOXML packaging tests using real ZIP archives."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from infrastructure.rendering.pptx_deck import _normalize_pptx_archive


def _write_archive(path: Path, timestamp: tuple[int, int, int, int, int, int]) -> None:
    with ZipFile(path, "w") as archive:
        info = ZipInfo("ppt/presentation.xml", timestamp)
        info.compress_type = ZIP_DEFLATED
        archive.writestr(info, b"<presentation/>")


def test_normalize_pptx_archive_removes_wall_clock_metadata(tmp_path: Path) -> None:
    first = tmp_path / "first.pptx"
    second = tmp_path / "second.pptx"
    _write_archive(first, (2025, 1, 2, 3, 4, 6))
    _write_archive(second, (2026, 7, 8, 9, 10, 12))

    _normalize_pptx_archive(first)
    _normalize_pptx_archive(second)

    assert first.read_bytes() == second.read_bytes()
    with ZipFile(first) as archive:
        assert archive.read("ppt/presentation.xml") == b"<presentation/>"
        assert {info.date_time for info in archive.infolist()} == {(1980, 1, 1, 0, 0, 0)}

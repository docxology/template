"""Real ZIP archives against the shared bounded member admission."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from infrastructure.core.files.archive_members import bounded_members


def _archive(path: Path, members: list[tuple[zipfile.ZipInfo | str, bytes]]) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for info, data in members:
            archive.writestr(info, data)
    return path


def test_safe_archive_returns_file_members_without_directories(tmp_path: Path) -> None:
    path = _archive(
        tmp_path / "safe.zip",
        [("word/document.xml", b"<w/>"), (zipfile.ZipInfo("word/media/"), b""), ("[Content_Types].xml", b"<t/>")],
    )

    with zipfile.ZipFile(path) as archive:
        assert bounded_members(archive) == {"word/document.xml", "[Content_Types].xml"}


@pytest.mark.parametrize("name", ["../escape.xml", "/absolute.xml", "word\\document.xml"])
def test_unsafe_member_names_are_refused(tmp_path: Path, name: str) -> None:
    info = zipfile.ZipInfo("placeholder.xml")
    info.filename = name
    path = _archive(tmp_path / "unsafe.zip", [(info, b"<x/>")])

    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="unsafe, duplicate or unbounded"):
        bounded_members(archive)


def test_duplicate_member_names_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.zip"
    with pytest.warns(UserWarning, match="Duplicate name"):
        _archive(path, [("word/document.xml", b"<a/>"), ("word/document.xml", b"<b/>")])

    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="unsafe, duplicate or unbounded"):
        bounded_members(archive)


def test_symlink_member_is_refused(tmp_path: Path) -> None:
    link = zipfile.ZipInfo("word/link.xml")
    link.external_attr = 0o120777 << 16
    path = _archive(tmp_path / "symlink.zip", [(link, b"/etc/passwd")])

    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="unsafe, duplicate or unbounded"):
        bounded_members(archive)


def test_corrupted_member_crc_is_refused(tmp_path: Path) -> None:
    path = _archive(tmp_path / "crc.zip", [("word/document.xml", b"original member bytes")])
    raw = bytearray(path.read_bytes())
    offset = raw.index(b"original member bytes")
    raw[offset] ^= 0xFF
    path.write_bytes(bytes(raw))

    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="CRC is invalid"):
        bounded_members(archive)

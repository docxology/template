"""Genuine bounded ZIP controls for the official native prerequisite preparer."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import zipfile

import pytest

SOURCE = Path(__file__).resolve().parents[3] / "scripts/shell/prepare_native_epubcheck.py"
spec = importlib.util.spec_from_file_location("prepare_native_epubcheck", SOURCE)
assert spec is not None and spec.loader is not None
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


def test_original_bundle_dependency_paths_are_preserved(tmp_path: Path) -> None:
    archive = tmp_path / "original.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("epubcheck-5.4.0/epubcheck.jar", b"original main bytes")
        bundle.writestr("epubcheck-5.4.0/lib/dependency.jar", b"original dependency bytes")
    destination = tmp_path / "fresh"
    jar = preparer.extract_bundle(archive, destination)
    assert jar.read_bytes() == b"original main bytes"
    assert (jar.parent / "lib/dependency.jar").read_bytes() == b"original dependency bytes"
    with pytest.raises(FileExistsError):
        preparer.extract_bundle(archive, destination)


@pytest.mark.parametrize(
    "name",
    [
        "../escaped.jar",
        "/absolute.jar",
        "epubcheck-5.4.0/../escaped.jar",
        "other/epubcheck.jar",
        "epubcheck-5.4.0//ambiguous.jar",
    ],
)
def test_unsafe_archive_refused_before_any_extraction(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("epubcheck-5.4.0/epubcheck.jar", b"original")
        bundle.writestr(name, b"unsafe")
    destination = tmp_path / "fresh"
    with pytest.raises(ValueError):
        preparer.extract_bundle(archive, destination)
    assert not destination.exists()


def test_actual_symlink_archive_member_refused(tmp_path: Path) -> None:
    archive = tmp_path / "linked.zip"
    row = zipfile.ZipInfo("epubcheck-5.4.0/epubcheck.jar")
    row.create_system = 3
    row.external_attr = 0o120777 << 16
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(row, "../../outside")
    with pytest.raises(ValueError):
        preparer.extract_bundle(archive, tmp_path / "fresh")

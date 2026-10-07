"""Real filesystem/archive controls; no remote download success is simulated."""

from __future__ import annotations

import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
import tarfile

import pytest

from infrastructure.reporting.native_dependency_preparation import PACKAGES, declaration, verify_archive
from infrastructure.reporting.native_format_browser_cdn import compile_cdn_assets
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def original_assets(root: Path) -> None:
    directory = root / "output/readiness/native-dependencies"
    directory.mkdir(parents=True)
    lock = {"packages": {}}
    for name, filename in PACKAGES.items():
        archive = directory / filename
        with tarfile.open(archive, "w:gz") as bundle:
            data = json.dumps({"name": name, "version": "4.0.0"}).encode()
            member = tarfile.TarInfo("package/package.json")
            member.size = len(data)
            bundle.addfile(member, BytesIO(data))
        lock["packages"][f"node_modules/{name}"] = {
            "version": "4.0.0",
            "resolved": f"https://registry.npmjs.org/{name}/-/" + name.rsplit("/", 1)[-1] + "-4.0.0.tgz",
            "integrity": "sha512-" + base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode(),
        }
    (root / "package.json").write_text(json.dumps({"devDependencies": {name: "4.0.0" for name in PACKAGES}}))
    (root / "package-lock.json").write_text(json.dumps(lock))


def test_actual_original_archive_bytes_are_independently_inspected(tmp_path: Path) -> None:
    original_assets(tmp_path)
    for name, filename in PACKAGES.items():
        row = declaration(tmp_path, name)
        verify_archive(tmp_path / "output/readiness/native-dependencies" / filename, row["integrity"])
    reader = SnapshotReader(tmp_path)
    assert len(compile_cdn_assets(reader)) == 2
    assert reader.unchanged()


@pytest.mark.parametrize("change", ["version", "registry", "integrity", "bytes"])
def test_changed_source_or_actual_archive_refused(tmp_path: Path, change: str) -> None:
    original_assets(tmp_path)
    path = tmp_path / "package-lock.json"
    lock = json.loads(path.read_text())
    row = lock["packages"]["node_modules/mathjax"]
    if change == "version":
        row["version"] = "4.0.1"
    elif change == "registry":
        row["resolved"] = row["resolved"].replace("registry.npmjs.org", "unreviewed.example")
    elif change == "integrity":
        row["integrity"] = "sha512-invalid"
    else:
        archive = tmp_path / "output/readiness/native-dependencies/mathjax-4.0.0.tgz"
        archive.write_bytes(archive.read_bytes() + b"changed")
    path.write_text(json.dumps(lock))
    with pytest.raises(ValueError):
        admitted = declaration(tmp_path, "mathjax")
        verify_archive(tmp_path / "output/readiness/native-dependencies/mathjax-4.0.0.tgz", admitted["integrity"])

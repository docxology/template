"""Actual cold capture CLI rejects bad Source metadata before SDK admission."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import pytest


def _capture(tmp_path: Path, metadata: str, *, wrong_hash: bool = False) -> subprocess.CompletedProcess[str]:
    root = tmp_path / "source"
    root.mkdir()
    (root / "pyproject.toml").write_text(metadata)
    wheel = tmp_path / "candidate.whl"
    wheel.write_bytes(b"invented non-wheel; cannot grant installed custody\n")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "infrastructure.reporting.native_installed_custody_capture",
            "--root",
            str(root),
            "--core-wheel",
            str(wheel),
            "--core-wheel-sha256",
            "a" * 64 if wrong_hash else hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "--destination",
            str(root / "output/readiness/custody.json"),
            "--deadline",
            str(time.monotonic() + 20),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.mark.parametrize(
    "metadata",
    (
        '[project]\nname="other"\nversion="4.0.2"\n',
        '[project]\nname="research-project-template"\nversion="3.8.0"\n',
        '[project]\nname="research-project-template"\nversion=402\n',
        '[project]\nname="research-project-template"\nversion="4.0.2rc1"\n',
    ),
)
def test_capture_rejects_wrong_source_package_or_release(metadata: str, tmp_path: Path) -> None:
    result = _capture(tmp_path, metadata)
    assert result.returncode != 0
    assert "requires genuine platform 4 Source metadata" in result.stderr
    assert not (tmp_path / "source/output/readiness/custody.json").exists()


def test_capture_requires_the_externally_admitted_wheel_hash(tmp_path: Path) -> None:
    result = _capture(tmp_path, '[project]\nname="research-project-template"\nversion="4.0.2"\n', wrong_hash=True)
    assert result.returncode != 0
    assert "differs from the parent's actual Source-admitted wheel" in result.stderr
    assert not (tmp_path / "source/output/readiness/custody.json").exists()


@pytest.mark.parametrize("version", ("4.0.1", "4.0.2"))
def test_capture_never_treats_metadata_as_a_valid_wheel_or_runtime(version: str, tmp_path: Path) -> None:
    result = _capture(tmp_path, '[project]\nname="research-project-template"\nversion="' + version + '"\n')
    assert result.returncode != 0
    assert "requires genuine platform 4 Source metadata" not in result.stderr
    assert "wheel" in result.stderr.lower()
    assert not (tmp_path / "source/output/readiness/custody.json").exists()

"""Tests for the deterministic build-timestamp helper and end-to-end
byte-identity property.

These tests follow the no-mocks policy: every assertion uses real
``git`` invocations against a tmp-path repository, real
``subprocess.run`` calls, and real PDF rendering when ``reportlab``/
``pypdf`` are available.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from infrastructure.steganography.config import resolve_build_timestamp
from tests.infra_tests.steganography.conftest import has_pypdf, has_reportlab


# ── Helpers ───────────────────────────────────────────────────────────────


def _git_available() -> bool:
    return shutil.which("git") is not None


def _init_repo(repo: Path, *, commit_date: str) -> str:
    """Create a real git repo at *repo* with one commit pinned to
    *commit_date*. Returns the recorded ``%cI`` of that commit.
    """
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True)
    (repo / "README.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.txt"], cwd=repo, check=True)
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": commit_date,
        "GIT_COMMITTER_DATE": commit_date,
    }
    subprocess.run(
        ["git", "commit", "-q", "-m", "seed commit"],
        cwd=repo,
        env=env,
        check=True,
    )
    res = subprocess.run(
        ["git", "log", "-1", "--format=%cI"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


# ── Unit tests for resolve_build_timestamp ────────────────────────────────


@pytest.mark.skipif(not _git_available(), reason="git binary not on PATH")
def test_deterministic_returns_commit_iso8601(tmp_path: Path, monkeypatch):
    """With STEGANOGRAPHY_DETERMINISTIC=1 + a real repo, returns %cI."""
    expected = _init_repo(tmp_path, commit_date="2024-06-15T12:34:56+00:00")
    monkeypatch.setenv("STEGANOGRAPHY_DETERMINISTIC", "1")

    actual = resolve_build_timestamp(repo_root=tmp_path)

    assert actual == expected
    # Strict ISO-8601, with either Z or numeric offset
    # (e.g. "2024-06-15T12:34:56+00:00" or "...Z").
    assert re.match(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)$",
        actual,
    )


@pytest.mark.skipif(not _git_available(), reason="git binary not on PATH")
def test_explicit_deterministic_overrides_unset_env(tmp_path: Path, monkeypatch):
    """deterministic=True wins even when env var is absent."""
    expected = _init_repo(tmp_path, commit_date="2023-01-02T03:04:05+00:00")
    monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)

    actual = resolve_build_timestamp(deterministic=True, repo_root=tmp_path)

    assert actual == expected


def test_wallclock_when_env_unset(monkeypatch):
    """Default mode returns a strict ISO-8601 Z string within ≤1 s of now."""
    monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)

    before = datetime.now(timezone.utc)
    actual = resolve_build_timestamp()
    after = datetime.now(timezone.utc)

    # Strict format YYYY-MM-DDTHH:MM:SSZ
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", actual), actual
    parsed = datetime.fromisoformat(actual.replace("Z", "+00:00"))
    drift_before = (parsed - before).total_seconds()
    drift_after = (after - parsed).total_seconds()
    # Allow ≤2 s margin to absorb the second-truncation in the format.
    assert -2.0 <= drift_before <= 2.0
    assert -2.0 <= drift_after <= 2.0


def test_explicit_false_forces_wallclock(monkeypatch):
    """deterministic=False ignores the env var and returns wall-clock."""
    monkeypatch.setenv("STEGANOGRAPHY_DETERMINISTIC", "1")

    actual = resolve_build_timestamp(deterministic=False)

    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", actual)


@pytest.mark.skipif(not _git_available(), reason="git binary not on PATH")
def test_non_repo_path_falls_back_to_wallclock(tmp_path: Path, monkeypatch, caplog):
    """Deterministic mode in a non-repo directory falls back + warns."""
    monkeypatch.setenv("STEGANOGRAPHY_DETERMINISTIC", "1")

    with caplog.at_level("WARNING"):
        actual = resolve_build_timestamp(repo_root=tmp_path)

    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", actual)
    assert any("falling back to wall-clock" in r.getMessage() for r in caplog.records)


def test_missing_git_binary_falls_back(tmp_path: Path, monkeypatch, caplog):
    """If ``git`` is not on PATH, resolve_build_timestamp logs and falls back.

    We override PATH to an empty directory so any ``git`` lookup raises
    FileNotFoundError. No mocks — the override is real environment state.
    """
    empty_path = tmp_path / "empty_path"
    empty_path.mkdir()
    monkeypatch.setenv("PATH", str(empty_path))
    monkeypatch.setenv("STEGANOGRAPHY_DETERMINISTIC", "1")

    if shutil.which("git") is not None:  # pragma: no cover — sanity guard
        pytest.skip("PATH override did not hide git; runner exposes it elsewhere")

    with caplog.at_level("WARNING"):
        actual = resolve_build_timestamp(repo_root=tmp_path)

    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", actual)
    assert any("falling back to wall-clock" in r.getMessage() for r in caplog.records)


# ── End-to-end byte-identical PDF property ────────────────────────────────


@pytest.mark.skipif(not _git_available(), reason="git binary not on PATH")
@pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
@pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
def test_pipeline_byte_identical_in_deterministic_mode(tmp_path: Path, monkeypatch):
    """Two consecutive secure-pipeline runs against the same HEAD produce
    byte-identical ``*_steganography.pdf`` outputs.
    """
    from reportlab.pdfgen import canvas as rl_canvas  # type: ignore[import-untyped]

    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo, commit_date="2024-06-15T12:34:56+00:00")

    # Synthetic single-page PDF (deterministic content).
    src_pdf = repo / "input.pdf"
    c = rl_canvas.Canvas(str(src_pdf))
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, "Reproducible build fixture.")
    c.showPage()
    c.save()

    monkeypatch.setenv("STEGANOGRAPHY_DETERMINISTIC", "1")
    monkeypatch.chdir(repo)

    cfg = SteganographyConfig(
        enabled=True,
        overlays_enabled=True,
        barcodes_enabled=True,
        metadata_enabled=True,
        hashing_enabled=True,
        encryption_enabled=False,
    )

    out1 = repo / "out1.pdf"
    out2 = repo / "out2.pdf"

    SteganographyProcessor(cfg).process(src_pdf, out1, title="DetTest")
    SteganographyProcessor(cfg).process(src_pdf, out2, title="DetTest")

    bytes1 = out1.read_bytes()
    bytes2 = out2.read_bytes()

    assert bytes1 == bytes2, f"Deterministic mode failed: PDFs differ ({len(bytes1)} vs {len(bytes2)} bytes)."


@pytest.mark.skipif(not _git_available(), reason="git binary not on PATH")
@pytest.mark.skipif(not has_reportlab(), reason="reportlab not installed")
@pytest.mark.skipif(not has_pypdf(), reason="pypdf not installed")
def test_pipeline_differs_when_nondeterministic(tmp_path: Path, monkeypatch):
    """Without the env var, two runs should differ (different doc-IDs and
    timestamps) — control case for the byte-identity test above.
    """
    from reportlab.pdfgen import canvas as rl_canvas  # type: ignore[import-untyped]

    from infrastructure.steganography.config import SteganographyConfig
    from infrastructure.steganography.core import SteganographyProcessor

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo, commit_date="2024-06-15T12:34:56+00:00")

    src_pdf = repo / "input.pdf"
    c = rl_canvas.Canvas(str(src_pdf))
    c.drawString(72, 700, "control case")
    c.showPage()
    c.save()

    monkeypatch.delenv("STEGANOGRAPHY_DETERMINISTIC", raising=False)
    monkeypatch.chdir(repo)

    cfg = SteganographyConfig(
        enabled=True,
        overlays_enabled=True,
        barcodes_enabled=True,
        metadata_enabled=True,
        hashing_enabled=True,
        encryption_enabled=False,
    )

    out1 = repo / "out1.pdf"
    out2 = repo / "out2.pdf"

    SteganographyProcessor(cfg).process(src_pdf, out1, title="NDetTest")
    SteganographyProcessor(cfg).process(src_pdf, out2, title="NDetTest")

    # Random doc-IDs make the outputs differ; this is the documented
    # default behaviour and should never regress to byte-identity.
    assert out1.read_bytes() != out2.read_bytes()

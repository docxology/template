#!/usr/bin/env python3
"""Tests that output-directory cleanup never deletes git-tracked files.

Stage-01 clean wipes project ``output/`` trees; committed release artifacts
inside them (PDFs, SHA256SUMS, manifests) must survive. Every test here runs
against a real git repository with real files — no mocks.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import FileOperationError
from infrastructure.core.files.cleanup import clean_output_directories
from infrastructure.core.files.cleanup_helpers import clean_output_dir_contents
from infrastructure.core.pipeline.snapshot import create_snapshot


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def project_repo(tmp_path: Path) -> Path:
    """A real git repository laid out like a template checkout with one project."""
    repo = tmp_path / "repo"
    (repo / "projects" / "demo").mkdir(parents=True)
    (repo / "output").mkdir()
    _init_git_repo(repo)
    _git("config", "commit.gpgsign", "false", cwd=repo)
    return repo


def test_clean_preserves_tracked_files_but_removes_untracked_and_ignored(project_repo: Path) -> None:
    """A tracked release artifact survives stage-01 clean; untracked/ignored do not."""
    repo = project_repo
    output_dir = repo / "projects" / "demo" / "output"
    release = output_dir / "release"
    release.mkdir(parents=True)
    (release / "report.pdf").write_bytes(b"%PDF-1.4 tracked release artifact")
    (release / "SHA256SUMS").write_text("abc123  report.pdf\n")
    (release / "scratch.txt").write_text("untracked intermediate")
    (release / "cache.log").write_text("gitignored junk")
    _git("add", "projects/demo/output/release/report.pdf", "projects/demo/output/release/SHA256SUMS", cwd=repo)
    _git("commit", "-m", "track release artifacts", cwd=repo)
    (repo / ".gitignore").write_text("projects/*/output/**/cache.log\n")

    skipped = clean_output_directories(repo, "demo")

    assert (release / "report.pdf").read_bytes() == b"%PDF-1.4 tracked release artifact"
    assert (release / "SHA256SUMS").exists()
    assert not (release / "scratch.txt").exists()
    assert not (release / "cache.log").exists()
    assert {p.relative_to(repo) for p in skipped} == {
        Path("projects/demo/output/release/report.pdf"),
        Path("projects/demo/output/release/SHA256SUMS"),
    }


def test_clean_records_skipped_tracked_files_in_report_and_snapshot(project_repo: Path) -> None:
    """The cleanup report and the stage-01 snapshot carry the skipped-tracked count and paths."""
    repo = project_repo
    output_dir = repo / "projects" / "demo" / "output"
    release = output_dir / "release"
    release.mkdir(parents=True)
    (release / "report.pdf").write_bytes(b"%PDF-1.4 tracked")
    _git("add", "projects/demo/output/release/report.pdf", cwd=repo)
    _git("commit", "-m", "track release artifact", cwd=repo)

    clean_output_directories(repo, "demo")

    report = json.loads((output_dir / "reports" / "cleanup_report.json").read_text(encoding="utf-8"))
    assert report["skipped_tracked_count"] == 1
    assert report["skipped_tracked"] == ["projects/demo/output/release/report.pdf"]

    snapshot = create_snapshot(output_dir, stage_num=1, stage_name="Clean Output Directories")
    payload = json.loads(snapshot.path.read_text(encoding="utf-8"))
    assert payload["cleanup"]["skipped_tracked_count"] == 1
    assert payload["cleanup"]["skipped_tracked"] == ["projects/demo/output/release/report.pdf"]


def test_clean_is_selective_around_tracked_files_deep_in_a_directory(tmp_path: Path) -> None:
    """Untracked siblings of a tracked file are still removed; tracked ancestors stay."""
    output_dir = tmp_path / "output"
    nested = output_dir / "release" / "v1"
    nested.mkdir(parents=True)
    (nested / "keep.pdf").write_text("tracked")
    (nested / "drop.txt").write_text("untracked")
    (output_dir / "release" / "loose.txt").write_text("untracked")
    _init_git_repo(tmp_path)
    _git("add", "output/release/v1/keep.pdf", cwd=tmp_path)
    _git("commit", "-m", "track deep artifact", cwd=tmp_path)

    skipped = clean_output_dir_contents(output_dir, set())

    assert (nested / "keep.pdf").read_text(encoding="utf-8") == "tracked"
    assert not (nested / "drop.txt").exists()
    assert not (output_dir / "release" / "loose.txt").exists()
    assert [p.name for p in skipped] == ["keep.pdf"]
    assert (output_dir / "release" / "v1").is_dir()


def test_clean_refuses_to_delete_when_git_cannot_be_consulted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail-closed: without a usable git, nothing inside output/ is deleted."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "file.txt").write_text("data")
    _init_git_repo(tmp_path)
    _git("add", "output/file.txt", cwd=tmp_path)
    _git("commit", "-m", "track file", cwd=tmp_path)

    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()
    monkeypatch.setenv("PATH", str(empty_path))

    with pytest.raises(FileOperationError):
        clean_output_dir_contents(output_dir, set())

    assert (output_dir / "file.txt").read_text(encoding="utf-8") == "data"

"""Dry-run and explicit-boundary tests for the release rehearsal."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from infrastructure.publishing.rehearsal import (
    _clean_generated_render_output,
    _rehearsal_exit_code,
    build_clean_checkout_plan,
    run_clean_checkout_rehearsal,
)


def test_rehearsal_plan_is_offline_and_skipped_by_default() -> None:
    root = Path(__file__).resolve().parents[3]
    plan = build_clean_checkout_plan(root)
    assert plan.network_allowed is False
    assert plan.runs == 2
    assert plan.status == "skipped"
    assert "--execute" in plan.skip_reason


def test_rehearsal_plan_rejects_empty_commands(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_clean_checkout_plan(tmp_path, commands=())


def _git(cwd: Path, *args: str) -> str:
    """Run a real git command for disposable-rehearsal fixtures."""
    result = subprocess.run(("git", *args), cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


def test_rehearsal_restores_only_generated_render_output(tmp_path: Path) -> None:
    """Platform-specific canonical render bytes cannot leak into a fresh clone."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "rehearsal-test")
    output = repo / "projects/templates/template_code_project/output"
    output.mkdir(parents=True)
    (output / "tracked.txt").write_text("original\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    (output / "tracked.txt").write_text("rerendered\n", encoding="utf-8")
    (output / "new.txt").write_text("generated\n", encoding="utf-8")
    status = _git(repo, "status", "--porcelain", "--untracked-files=all")

    clean, reason = _clean_generated_render_output(repo, status)

    assert clean is True
    assert "restored 2" in reason
    assert (output / "tracked.txt").read_text(encoding="utf-8") == "original\n"
    assert not (output / "new.txt").exists()
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_rehearsal_rejects_render_changes_outside_generated_output(tmp_path: Path) -> None:
    """A render that touches source or private state remains a hard blocker."""
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = repo / "README.md"
    outside.write_text("changed\n", encoding="utf-8")

    clean, reason = _clean_generated_render_output(repo, " M README.md\n")

    assert clean is False
    assert "non-generated paths" in reason


def _git_supports_clone_revision() -> bool:
    """``git clone --revision`` needs Git 2.51+; older tooling must skip."""
    with tempfile.TemporaryDirectory() as td:
        origin = Path(td) / "origin"
        origin.mkdir()
        _git(origin, "init", "-q")
        _git(origin, "config", "user.email", "probe@example.invalid")
        _git(origin, "config", "user.name", "probe")
        (origin / "file.txt").write_text("probe\n", encoding="utf-8")
        _git(origin, "add", ".")
        _git(origin, "commit", "-qm", "probe")
        clone = subprocess.run(
            ("git", "clone", "-q", "--no-local", "--revision", "HEAD", str(origin), str(Path(td) / "clone")),
            capture_output=True,
            text=True,
        )
        return clone.returncode == 0


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "rehearsal-test")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture")
    return repo


@pytest.mark.skipif(not _git_supports_clone_revision(), reason="git clone --revision requires Git 2.51+")
def test_rehearsal_passes_when_two_runs_produce_identical_digests(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    plan = build_clean_checkout_plan(repo, commands=(("git", "rev-parse", "HEAD"),))

    receipt = run_clean_checkout_rehearsal(repo, plan, platform_name="darwin", timeout_seconds=120)

    assert receipt.status == "pass"
    assert receipt.validate() == []
    assert _rehearsal_exit_code(receipt) == 0


@pytest.mark.skipif(not _git_supports_clone_revision(), reason="git clone --revision requires Git 2.51+")
def test_rehearsal_blocks_when_runs_produce_unequal_digests(tmp_path: Path) -> None:
    repo = _fixture_repo(tmp_path)
    plan = build_clean_checkout_plan(repo, commands=(("sh", "-c", "echo $$"),))

    receipt = run_clean_checkout_rehearsal(repo, plan, platform_name="darwin", timeout_seconds=120)
    assert receipt.status == "blocked"
    assert "different deterministic output digests" in receipt.skip_reason
    passing_digests = {run.output_sha256 for run in receipt.runs if run.status == "pass"}
    assert len(passing_digests) == plan.runs
    assert receipt.validate() == []
    assert _rehearsal_exit_code(receipt) == 1

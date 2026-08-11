"""Dry-run and explicit-boundary tests for the release rehearsal."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from infrastructure.publishing.rehearsal import _clean_generated_render_output, build_clean_checkout_plan


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

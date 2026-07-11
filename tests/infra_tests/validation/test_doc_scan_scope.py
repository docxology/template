"""Regression tests for shared documentation scan exclusions."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.content.discovery import discover_markdown_files
from infrastructure.validation.docs.scan_scope import iter_markdown_files, should_exclude_path
from infrastructure.validation.integrity.link_validator import LinkValidator


def test_shared_scope_skips_local_and_generated_trees(tmp_path: Path) -> None:
    """Generated/local trees do not enter doc scans."""
    included = tmp_path / "docs" / "guide.md"
    included.parent.mkdir()
    included.write_text("# Guide\n", encoding="utf-8")

    excluded_paths = [
        tmp_path / ".claude" / "worktrees" / "scratch.md",
        tmp_path / ".codex" / "sessions" / "thread.md",
        tmp_path / "projects" / "working" / "draft" / "README.md",
        tmp_path / "projects" / "archive" / "old" / "README.md",
        tmp_path / "projects" / "demo" / "output" / "report.md",
        tmp_path / ".venv" / "lib" / "site-packages" / "pkg" / "README.md",
    ]
    for path in excluded_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Generated\n[Broken](missing.md)\n", encoding="utf-8")

    discovered = {path.relative_to(tmp_path) for path in iter_markdown_files([tmp_path])}

    assert discovered == {Path("docs/guide.md")}
    assert should_exclude_path(excluded_paths[0]) is True


def test_scan_root_inside_excluded_component_is_not_self_excluded(tmp_path: Path) -> None:
    """A checkout living under an excluded component name must still be scanned.

    Agent worktrees live at ``<repo>/.claude/worktrees/<name>/``; evaluating
    exclusions against the ABSOLUTE path silently excluded the entire checkout
    and every doc gate returned a vacuous pass. Exclusions must bind to the
    path relative to the scan root.
    """
    checkout = tmp_path / ".claude" / "worktrees" / "some-agent-worktree"
    good = checkout / "docs" / "guide.md"
    good.parent.mkdir(parents=True)
    good.write_text("# Guide\n", encoding="utf-8")
    # A NESTED excluded component inside the checkout must still be excluded.
    nested = checkout / ".claude" / "worktrees" / "inner" / "scratch.md"
    nested.parent.mkdir(parents=True)
    nested.write_text("# Scratch\n", encoding="utf-8")

    discovered = {path.relative_to(checkout) for path in iter_markdown_files([checkout])}

    assert discovered == {Path("docs/guide.md")}


def test_run_docs_lint_fails_loud_on_empty_scan(tmp_path: Path) -> None:
    """A zero-file documentation scan must raise, never report a vacuous pass."""
    import pytest

    from infrastructure.validation.docs.lint_runner import run_docs_lint

    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()

    with pytest.raises(ValueError, match="0 markdown files"):
        run_docs_lint(empty_repo, quiet=True)


def test_comprehensive_audit_fails_loud_on_empty_scan(tmp_path: Path) -> None:
    """The filepath auditor must refuse to write an all-passed report over 0 files."""
    import pytest

    from infrastructure.validation.repo.audit_orchestrator import run_comprehensive_audit

    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()

    with pytest.raises(RuntimeError, match="0 markdown files"):
        run_comprehensive_audit(empty_repo)


def test_discovery_and_link_validator_share_scope(tmp_path: Path) -> None:
    """The broad link validator uses the same exclusions as docs discovery."""
    readme = tmp_path / "README.md"
    readme.write_text("# Root\n[Docs](docs/guide.md)\n", encoding="utf-8")
    guide = tmp_path / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("# Guide\n", encoding="utf-8")

    hidden = tmp_path / ".claude" / "worktrees" / "bad.md"
    hidden.parent.mkdir(parents=True)
    hidden.write_text("# Hidden\n[Broken](missing.md)\n", encoding="utf-8")

    validator = LinkValidator(tmp_path)
    results = validator.validate_all_markdown_files()

    assert sorted(results) == ["README.md", "docs/guide.md"]
    assert [path.relative_to(tmp_path) for path in discover_markdown_files(tmp_path, scope="repo")] == [
        Path("README.md"),
        Path("docs/guide.md"),
    ]

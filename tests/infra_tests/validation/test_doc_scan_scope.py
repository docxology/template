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

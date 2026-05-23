"""Tests for infrastructure.validation.paths."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.paths import resolve_markdown_target


def test_resolve_relative_markdown_with_md_suffix_inference(tmp_path: Path) -> None:
    repo = tmp_path
    docs = repo / "docs"
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8")
    source = docs / "index.md"
    source.write_text("# Index\n", encoding="utf-8")

    resolved = resolve_markdown_target("guide", source, repo)
    assert resolved.exists
    assert resolved.path_type == "file"
    assert resolved.resolved == target.resolve()


def test_resolve_parent_relative_path(tmp_path: Path) -> None:
    repo = tmp_path
    nested = repo / "a" / "b"
    nested.mkdir(parents=True)
    sibling = repo / "a" / "sibling.md"
    sibling.write_text("# S\n", encoding="utf-8")
    source = nested / "index.md"
    source.write_text("# I\n", encoding="utf-8")

    resolved = resolve_markdown_target("../sibling.md", source, repo)
    assert resolved.exists
    assert resolved.resolved == sibling.resolve()


def test_resolve_directory_trailing_slash(tmp_path: Path) -> None:
    repo = tmp_path
    docs = repo / "docs"
    docs.mkdir()
    source = repo / "README.md"
    source.write_text("# R\n", encoding="utf-8")

    resolved = resolve_markdown_target("docs/", source, repo)
    assert resolved.exists
    assert resolved.path_type == "directory"


def test_resolve_external_url_is_allowed(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("# R\n", encoding="utf-8")
    resolved = resolve_markdown_target("https://example.com/doc", source, tmp_path)
    assert resolved.exists
    assert resolved.resolved is None


def test_resolve_outside_repo_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("# O\n", encoding="utf-8")
    source = repo / "README.md"
    source.write_text("# R\n", encoding="utf-8")

    resolved = resolve_markdown_target("../../outside.md", source, repo)
    assert not resolved.exists
    assert "outside repository" in resolved.message

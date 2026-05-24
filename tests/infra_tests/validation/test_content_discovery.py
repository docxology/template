"""Tests for infrastructure.validation.content.discovery."""

from __future__ import annotations

import pytest

from infrastructure.core.exceptions import FileNotFoundError, NotADirectoryError
from infrastructure.validation.content.discovery import discover_markdown_files


def test_tree_scope_non_recursive(tmp_path) -> None:
    root = tmp_path / "manuscript"
    root.mkdir()
    (root / "01_a.md").write_text("# A")
    (root / "sub").mkdir()
    (root / "sub" / "02_b.md").write_text("# B")

    files = discover_markdown_files(root, scope="tree")
    assert [path.name for path in files] == ["01_a.md"]


def test_tree_scope_missing_dir_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        discover_markdown_files(tmp_path / "missing", scope="tree")


def test_tree_scope_file_raises(tmp_path) -> None:
    file_path = tmp_path / "note.md"
    file_path.write_text("# Note")
    with pytest.raises(NotADirectoryError):
        discover_markdown_files(file_path, scope="tree")


def test_repo_scope_excludes_output(tmp_path) -> None:
    (tmp_path / "keep.md").write_text("# Keep")
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "skip.md").write_text("# Skip")

    files = discover_markdown_files(tmp_path, scope="repo")
    assert [path.name for path in files] == ["keep.md"]


def test_link_audit_scope_matches_link_checker_excludes(tmp_path) -> None:
    (tmp_path / "keep.md").write_text("# Keep")
    (tmp_path / "htmlcov").mkdir()
    (tmp_path / "htmlcov" / "skip.md").write_text("# Skip")

    files = discover_markdown_files(tmp_path, scope="link_audit")
    assert [path.name for path in files] == ["keep.md"]

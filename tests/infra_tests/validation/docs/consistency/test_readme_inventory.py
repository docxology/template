"""Tests for README file inventory consistency checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs.consistency_lint import check_readme_files_list

from .conftest import scaffold_repo, write_doc


def test_readme_files_list_missing_is_flagged(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=1)
    pkg = repo / "infrastructure" / "pkg0"
    write_doc(pkg / "real_mod.py", "x = 1\n")
    write_doc(pkg / "README.md", "## Files\n\n- `real_mod.py` — present\n- `ghost_mod.py` — vanished\n")
    issues = check_readme_files_list(repo)
    assert len(issues) == 1
    assert issues[0].category == "doc-files-list"
    assert "ghost_mod.py" in issues[0].detail


def test_readme_files_list_all_present_ok(tmp_path: Path) -> None:
    repo = scaffold_repo(tmp_path, n_packages=1)
    pkg = repo / "infrastructure" / "pkg0"
    write_doc(pkg / "a.py", "")
    write_doc(pkg / "README.md", "## Files\n\n- `a.py`\n")
    assert check_readme_files_list(repo) == []

"""Shared fixtures for consistency lint check-family tests."""

from __future__ import annotations

from pathlib import Path

from tests._support.projects import make_project, write_doc


def scaffold_repo(tmp_path: Path, *, n_packages: int) -> Path:
    """Build a minimal repo: infrastructure/<pkgN>/__init__.py and an active project."""
    for i in range(n_packages):
        write_doc(tmp_path / "infrastructure" / f"pkg{i}" / "__init__.py", "")
    write_doc(tmp_path / "infrastructure" / "__init__.py", "")
    make_project(tmp_path, "template_code_project")
    write_doc(tmp_path / "docs" / "_generated" / "active_projects.md", "- template_code_project\n")
    return tmp_path

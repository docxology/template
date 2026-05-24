"""Shared fixtures for consistency lint check-family tests."""

from __future__ import annotations

from pathlib import Path


def write_doc(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


def scaffold_repo(tmp_path: Path, *, n_packages: int) -> Path:
    """Build a minimal repo: infrastructure/<pkgN>/__init__.py and an active project."""
    for i in range(n_packages):
        write_doc(tmp_path / "infrastructure" / f"pkg{i}" / "__init__.py", "")
    write_doc(tmp_path / "infrastructure" / "__init__.py", "")
    write_doc(tmp_path / "projects" / "template_code_project" / "src" / "__init__.py", "")
    write_doc(tmp_path / "projects" / "template_code_project" / "tests" / "__init__.py", "")
    write_doc(tmp_path / "docs" / "_generated" / "active_projects.md", "- template_code_project\n")
    return tmp_path

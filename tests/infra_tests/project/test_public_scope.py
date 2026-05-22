"""Tests for public template project scoping."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects
from infrastructure.project.public_scope import public_ci_source_paths, public_project_names


def _scaffold_project(root: Path, name: str) -> Path:
    project = root / "projects" / name
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "__init__.py").write_text("", encoding="utf-8")
    return project


def test_public_scope_filters_to_template_projects(tmp_path: Path) -> None:
    """Public CI scope excludes non-template projects that discovery can see."""
    _scaffold_project(tmp_path, "template_code_project")
    _scaffold_project(tmp_path, "template_prose_project")
    _scaffold_project(tmp_path, "private_research_project")

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert discovered == {"private_research_project", "template_code_project", "template_prose_project"}
    assert public_project_names(tmp_path) == ["template_code_project", "template_prose_project"]
    assert public_ci_source_paths(tmp_path) == [
        Path("infrastructure"),
        Path("projects/template_code_project/src"),
        Path("projects/template_prose_project/src"),
    ]


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_public_scope_excludes_local_private_symlink(tmp_path: Path) -> None:
    """Local symlinked projects remain discoverable but absent from public scope."""
    _scaffold_project(tmp_path, "template_code_project")
    _scaffold_project(tmp_path, "template_prose_project")

    external = tmp_path / "private" / "active" / "biology_textbook"
    (external / "src").mkdir(parents=True)
    (external / "tests").mkdir()
    (external / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "projects" / "biology_textbook").symlink_to(external, target_is_directory=True)

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert "biology_textbook" in discovered
    assert public_project_names(tmp_path) == ["template_code_project", "template_prose_project"]

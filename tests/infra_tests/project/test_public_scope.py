"""Tests for public template project scoping."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from infrastructure.project.discovery import discover_projects
from infrastructure.project.public_scope import public_ci_source_paths, public_project_names


def _scaffold_project(root: Path, qualified: str) -> Path:
    project = root / "projects" / qualified
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "__init__.py").write_text("", encoding="utf-8")
    return project


def _scaffold_exemplars(root: Path) -> None:
    _scaffold_project(root, "templates/template_active_inference")
    _scaffold_project(root, "templates/template_autoresearch_project")
    _scaffold_project(root, "templates/template_code_project")
    _scaffold_project(root, "templates/template_prose_project")
    _scaffold_project(root, "templates/template_sia")
    _scaffold_project(root, "templates/template_template")


def test_public_scope_filters_to_template_projects(tmp_path: Path) -> None:
    """Public CI scope excludes non-template projects that discovery can see."""
    _scaffold_exemplars(tmp_path)
    _scaffold_project(tmp_path, "active/private_research_project")

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert discovered == {
        "active/private_research_project",
        "templates/template_active_inference",
        "templates/template_autoresearch_project",
        "templates/template_code_project",
        "templates/template_prose_project",
        "templates/template_sia",
        "templates/template_template",
    }
    assert public_project_names(tmp_path) == [
        "templates/template_active_inference",
        "templates/template_autoresearch_project",
        "templates/template_code_project",
        "templates/template_prose_project",
        "templates/template_sia",
        "templates/template_template",
    ]
    assert public_ci_source_paths(tmp_path) == [
        Path("infrastructure"),
        Path("projects/templates/template_active_inference/src"),
        Path("projects/templates/template_autoresearch_project/src"),
        Path("projects/templates/template_code_project/src"),
        Path("projects/templates/template_prose_project/src"),
        Path("projects/templates/template_sia/src"),
        Path("projects/templates/template_template/src"),
    ]


@pytest.mark.skipif(os.name == "nt", reason="POSIX symlink semantics")
def test_public_scope_excludes_local_private_symlink(tmp_path: Path) -> None:
    """Local symlinked projects remain discoverable but absent from public scope."""
    _scaffold_exemplars(tmp_path)

    external = tmp_path / "private" / "active" / "example_private_project"
    (external / "src").mkdir(parents=True)
    (external / "tests").mkdir()
    (external / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "projects" / "active").mkdir(parents=True, exist_ok=True)
    (tmp_path / "projects" / "active" / "example_private_project").symlink_to(
        external, target_is_directory=True
    )

    discovered = {project.qualified_name for project in discover_projects(tmp_path)}

    assert "active/example_private_project" in discovered
    assert public_project_names(tmp_path) == [
        "templates/template_active_inference",
        "templates/template_autoresearch_project",
        "templates/template_code_project",
        "templates/template_prose_project",
        "templates/template_sia",
        "templates/template_template",
    ]

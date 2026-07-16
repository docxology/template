"""Tests for the generated public active-projects document."""

from __future__ import annotations

from pathlib import Path

from infrastructure.documentation.active_projects_doc import (
    render_active_projects_doc,
    write_active_projects_doc,
)
from tests._support.projects import make_project

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_render_active_projects_doc_contains_header() -> None:
    """render_active_projects_doc returns a string with the expected header."""
    content = render_active_projects_doc(REPO_ROOT)
    assert "# Public active projects" in content


def test_render_active_projects_doc_contains_project_names() -> None:
    """render_active_projects_doc includes public project names in the real repo."""
    content = render_active_projects_doc(REPO_ROOT)
    # The real repo has template_code_project as a public exemplar.
    assert "template_code_project" in content


def test_render_active_projects_doc_contains_generated_marker() -> None:
    """render_active_projects_doc includes the 'generated' marker."""
    content = render_active_projects_doc(REPO_ROOT)
    assert "generated" in content.lower()


def test_render_active_projects_doc_contains_regen_command() -> None:
    """render_active_projects_doc includes the regenerate command."""
    content = render_active_projects_doc(REPO_ROOT)
    assert "active_projects.py" in content


def test_render_active_projects_doc_with_empty_repo(tmp_path: Path) -> None:
    """render_active_projects_doc on an empty repo returns the header with no entries."""
    content = render_active_projects_doc(tmp_path)
    assert "# Public active projects" in content
    assert "Current entries:" in content


def test_render_active_projects_doc_with_scaffolded_project(tmp_path: Path) -> None:
    """render_active_projects_doc includes a scaffolded public project name."""
    # Scaffold a project that matches PUBLIC_PROJECT_NAMES entry 'templates/template_code_project'
    make_project(tmp_path, "template_code_project", program="templates")
    content = render_active_projects_doc(tmp_path)
    assert "template_code_project" in content


def test_write_active_projects_doc_creates_file(tmp_path: Path) -> None:
    """write_active_projects_doc writes to docs/_generated/active_projects.md and returns the path."""
    result_path = write_active_projects_doc(tmp_path)
    assert result_path == tmp_path / "docs" / "_generated" / "active_projects.md"
    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "# Public active projects" in content


def test_write_active_projects_doc_with_scaffolded_project(tmp_path: Path) -> None:
    """write_active_projects_doc writes a file that includes the scaffolded project name."""
    make_project(tmp_path, "template_code_project", program="templates")
    result_path = write_active_projects_doc(tmp_path)
    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "template_code_project" in content


def test_write_active_projects_doc_is_idempotent(tmp_path: Path) -> None:
    """Calling write_active_projects_doc twice produces the same file."""
    first_path = write_active_projects_doc(tmp_path)
    first_content = first_path.read_text(encoding="utf-8")
    second_path = write_active_projects_doc(tmp_path)
    second_content = second_path.read_text(encoding="utf-8")
    assert first_content == second_content
    assert first_path == second_path

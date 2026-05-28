"""Unit tests for the canonical ephemeral project scaffold factory."""

from __future__ import annotations

from infrastructure.project.discovery import discover_projects
from infrastructure.project.validation import validate_project_structure
from tests._support.projects import make_project, make_repo, project_path


def test_make_project_flat_layout_passes_validation(tmp_path) -> None:
    proj = make_project(tmp_path, "template_test")
    is_valid, message = validate_project_structure(proj)
    assert is_valid, message
    assert proj == project_path(tmp_path, "template_test")


def test_make_project_nested_layout_passes_validation(tmp_path) -> None:
    proj = make_project(tmp_path, "template_test", program="templates")
    is_valid, message = validate_project_structure(proj)
    assert is_valid, message
    assert proj == project_path(tmp_path, "template_test", program="templates")


def test_discover_projects_finds_flat_project(tmp_path) -> None:
    make_project(tmp_path, "alpha")
    make_project(tmp_path, "beta")
    names = {p.name for p in discover_projects(tmp_path)}
    assert names == {"alpha", "beta"}


def test_discover_projects_finds_nested_qualified_names(tmp_path) -> None:
    make_project(tmp_path, "template_test", program="templates")
    projects = discover_projects(tmp_path)
    assert len(projects) == 1
    assert projects[0].qualified_name == "templates/template_test"
    assert projects[0].program == "templates"
    assert projects[0].name == "template_test"


def test_make_repo_scaffolds_multiple_projects(tmp_path) -> None:
    make_repo(
        tmp_path,
        (
            "template_code_project",
            "template_prose_project",
            "some_rotating_project",
        ),
    )
    names = {p.name for p in discover_projects(tmp_path)}
    assert names == {
        "template_code_project",
        "template_prose_project",
        "some_rotating_project",
    }


def test_make_project_with_pdf_creates_combined_pdf(tmp_path) -> None:
    proj = make_project(tmp_path, "template_test", with_pdf=True)
    pdf_path = proj / "output" / "pdf" / "template_test_combined.pdf"
    assert pdf_path.is_file()
    assert pdf_path.stat().st_size > 0


def test_make_project_standalone_layout_without_projects_prefix(tmp_path) -> None:
    proj = make_project(tmp_path, "project", repo_layout=False, with_manuscript=True)
    is_valid, message = validate_project_structure(proj)
    assert is_valid, message
    assert proj == tmp_path / "project"
    assert (proj / "manuscript" / "config.yaml").is_file()

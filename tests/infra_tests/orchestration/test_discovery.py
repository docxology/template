"""Tests for infrastructure.orchestration.discovery."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from infrastructure.orchestration.discovery import (
    discover_qualified_names,
    select_project_interactive,
    validate_project_slug,
)
from infrastructure.project.discovery import discover_projects


def test_discover_qualified_names_includes_canonical_templates(fake_repo: Path) -> None:
    names = discover_qualified_names(fake_repo)
    assert "template_code_project" in names
    assert "template_prose_project" in names
    assert "template_search_project" in names


def test_validate_project_slug_accepts_canonical(fake_repo: Path) -> None:
    assert validate_project_slug("template_code_project", fake_repo) == "template_code_project"
    assert validate_project_slug("template_prose_project", fake_repo) == "template_prose_project"
    assert validate_project_slug("template_search_project", fake_repo) == "template_search_project"


def test_validate_project_slug_accepts_rotating_project(fake_repo: Path) -> None:
    """Validates that rotating (non-canonical) projects are accepted when present."""
    assert validate_project_slug("some_rotating_project", fake_repo) == "some_rotating_project"


def test_validate_project_slug_accepts_unique_bare_nested_template(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "templates" / "template_demo"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "__init__.py").write_text("", encoding="utf-8")

    assert validate_project_slug("template_demo", tmp_path) == "templates/template_demo"
    assert validate_project_slug("templates/template_demo", tmp_path) == "templates/template_demo"


def test_validate_project_slug_accepts_explicit_ongoing_project(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "ongoing" / "platform"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()

    assert validate_project_slug("ongoing/platform", tmp_path) == "ongoing/platform"


def test_validate_project_slug_rejects_markerless_ongoing_directory(tmp_path: Path) -> None:
    (tmp_path / "projects" / "ongoing" / "notes").mkdir(parents=True)

    with pytest.raises(ValueError, match="not found"):
        validate_project_slug("ongoing/notes", tmp_path)


def test_validate_project_slug_rejects_empty(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_project_slug("", fake_repo)


def test_validate_project_slug_rejects_path_traversal(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match=r"\.\."):
        validate_project_slug("..", fake_repo)
    with pytest.raises(ValueError, match=r"\.\."):
        validate_project_slug("../etc/passwd", fake_repo)
    with pytest.raises(ValueError, match=r"\.\."):
        validate_project_slug("template_code_project/..", fake_repo)


def test_validate_project_slug_rejects_absolute_path(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match="must not start with '/'"):
        validate_project_slug("/etc/passwd", fake_repo)


def test_validate_project_slug_rejects_flag_spoof(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match="must not start with '-'"):
        validate_project_slug("-rf", fake_repo)


def test_validate_project_slug_rejects_null_byte(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match="NUL"):
        validate_project_slug("template_code_project\x00", fake_repo)


def test_validate_project_slug_rejects_unknown(fake_repo: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        validate_project_slug("nonexistent_project_xyz", fake_repo)


def test_select_project_interactive_picks_by_index(fake_repo: Path) -> None:
    projects = discover_projects(fake_repo)
    out = io.StringIO()
    # Index 0 deterministically resolves to the first sorted project.
    picked = select_project_interactive(
        projects,
        current=projects[0].qualified_name,
        reader=lambda: "0",
        writer=out,
    )
    assert picked == projects[0].qualified_name
    assert "Available projects" in out.getvalue()


def test_select_project_interactive_picks_all(fake_repo: Path) -> None:
    projects = discover_projects(fake_repo)
    picked = select_project_interactive(
        projects,
        current=None,
        reader=lambda: "a",
        writer=None,
    )
    assert picked == "all"


def test_select_project_interactive_quit(fake_repo: Path) -> None:
    projects = discover_projects(fake_repo)
    picked = select_project_interactive(
        projects,
        current=None,
        reader=lambda: "q",
        writer=None,
    )
    assert picked is None


def test_select_project_interactive_retries_on_invalid(fake_repo: Path) -> None:
    projects = discover_projects(fake_repo)
    answers = iter(["", "999", "junk", "0"])
    picked = select_project_interactive(
        projects,
        current=None,
        reader=lambda: next(answers),
        writer=None,
    )
    assert picked == projects[0].qualified_name


def test_select_project_interactive_handles_empty() -> None:
    picked = select_project_interactive(
        [],
        current=None,
        reader=lambda: "0",
        writer=None,
    )
    assert picked is None


def test_select_project_interactive_handles_eof(fake_repo: Path) -> None:
    projects = discover_projects(fake_repo)

    def _eof() -> str:
        raise EOFError

    assert select_project_interactive(projects, reader=_eof, writer=None) is None

"""Shared fixtures for orchestration tests.

These fixtures build minimal real project trees on disk so the discovery
and CLI code paths exercise the actual filesystem layout (no mocks, per
the repo's no-mocks policy).
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _make_project(repo: Path, name: str) -> Path:
    """Create a minimum-viable project skeleton (src/, tests/) under repo."""
    proj = repo / "projects" / name
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (proj / "tests").mkdir(parents=True, exist_ok=True)
    (proj / "src" / "__init__.py").write_text("", encoding="utf-8")
    (proj / "tests" / "__init__.py").write_text("", encoding="utf-8")
    return proj


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Repository root containing the 3 canonical templates and one rotating project.

    Layout::

        <tmp>/projects/template_code_project/
        <tmp>/projects/template_prose_project/
        <tmp>/projects/template_search_project/
        <tmp>/projects/some_rotating_project/
    """
    (tmp_path / "projects").mkdir(parents=True)
    for name in (
        "template_code_project",
        "template_prose_project",
        "template_search_project",
        "some_rotating_project",
    ):
        _make_project(tmp_path, name)
    return tmp_path

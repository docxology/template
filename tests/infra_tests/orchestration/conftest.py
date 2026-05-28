"""Shared fixtures for orchestration tests.

These fixtures build minimal real project trees on disk so the discovery
and CLI code paths exercise the actual filesystem layout (no mocks, per
the repo's no-mocks policy).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._support.projects import make_repo


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Repository root containing canonical template slugs and one rotating project.

    Layout::

        <tmp>/projects/template_code_project/
        <tmp>/projects/template_prose_project/
        <tmp>/projects/template_search_project/
        <tmp>/projects/some_rotating_project/
    """
    return make_repo(
        tmp_path,
        (
            "template_code_project",
            "template_prose_project",
            "template_search_project",
            "some_rotating_project",
        ),
    )

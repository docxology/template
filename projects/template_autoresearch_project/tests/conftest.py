"""Project test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_root(project_root: Path) -> Path:
    """Return the template repository root."""
    return project_root.parents[1]

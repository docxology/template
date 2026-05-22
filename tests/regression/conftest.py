"""Shared fixtures for the regression test tier.

Provides a ``pinned_values`` fixture that loads per-project pinned ground-truth
JSON from ``tests/regression/pinned_values/<project>.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

_PINNED_DIR = Path(__file__).parent / "pinned_values"


@pytest.fixture(scope="session")
def pinned_values_root() -> Path:
    """Absolute path to the directory holding per-project pinned-values JSON."""

    return _PINNED_DIR


@pytest.fixture(scope="session")
def load_pinned_values(pinned_values_root: Path):
    """Factory fixture that returns a function loading pinned values for a given project.

    Usage in a test::

        def test_something(load_pinned_values):
            pinned = load_pinned_values("template_code_project")
            value = pinned["figure_03_panel_b"]["value"]
    """

    def _load(project_name: str) -> dict[str, Any]:
        path = pinned_values_root / f"{project_name}.json"
        if not path.exists():
            pytest.skip(
                f"No pinned values committed yet for project {project_name!r} "
                f"(expected at {path}). See docs/maintenance/regression-testing.md."
            )
        return json.loads(path.read_text())

    return _load

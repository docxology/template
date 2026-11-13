"""Shared fixtures and fail-closed collection contract for the regression tier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


_REGRESSION_ROOT = Path(__file__).resolve().parent
_MANIFEST_PATH = _REGRESSION_ROOT / "manifest.json"
_PINNED_DIR = _REGRESSION_ROOT / "pinned_values"


@pytest.fixture(scope="session")
def pinned_values_root() -> Path:
    """Absolute path to the directory holding per-project pinned-values JSON."""
    return _PINNED_DIR


@pytest.fixture(scope="session")
def load_pinned_values(pinned_values_root: Path):
    """Return a loader for one project's committed regression pins."""

    def _load(project_name: str) -> dict[str, Any]:
        path = pinned_values_root / f"{project_name}.json"
        if not path.exists():
            pytest.skip(f"No pinned values committed for {project_name!r} (expected at {path})")
        return json.loads(path.read_text(encoding="utf-8"))

    return _load


def _manifest() -> dict[str, object]:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def pytest_collection_finish(session: pytest.Session) -> None:
    """Reject mandatory regression files that contributed no selected cases."""
    manifest = _manifest()
    required = {str(path) for path in manifest["required_test_files"]}  # type: ignore[index]
    selected = {
        item.path.relative_to(_REGRESSION_ROOT).as_posix()
        for item in session.items
        if item.path.is_relative_to(_REGRESSION_ROOT)
    }
    missing = sorted(required - selected)
    if missing:
        pytest.exit(
            "regression manifest violation: required files without selected cases: " + ", ".join(missing),
            returncode=1,
        )

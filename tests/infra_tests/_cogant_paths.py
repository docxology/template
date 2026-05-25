"""Shared COGANT path resolution for private-project infra tests."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_STAGING = _REPO_ROOT / "projects_in_progress/cogant"
_FIXTURE = _REPO_ROOT / "tests/fixtures/private_project/cogant"


def cogant_root() -> Path:
    """Return COGANT staging tree when present, else the committed fixture fallback."""
    if (_STAGING / "tools").is_dir():
        return _STAGING
    return _FIXTURE

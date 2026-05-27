"""Shared test helpers for locating the Layer-1 template repository root."""

from __future__ import annotations

from pathlib import Path


def resolve_template_repo_root(start: Path | None = None) -> Path:
    """Walk parents from *start* until ``infrastructure/`` and ``pyproject.toml`` exist."""
    resolved = (start or Path(__file__).resolve().parent.parent).resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    sibling = resolved.parents[2] / "template"
    if (sibling / "infrastructure").is_dir() and (sibling / "pyproject.toml").is_file():
        return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {resolved}")


REPO_ROOT = resolve_template_repo_root()
PROJECT_DIR = Path(__file__).resolve().parent.parent

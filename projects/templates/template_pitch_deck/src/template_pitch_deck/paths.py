"""Repository root discovery for template_pitch_deck scripts."""

from __future__ import annotations

from pathlib import Path


def locate_repo_root(from_path: Path) -> Path:
    """Return the template repository root containing ``infrastructure/``."""
    resolved = from_path.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    # Standalone-checkout convention: a fork's own repo may sit as a sibling
    # directory named "template" under any ancestor of ``from_path``. Walk all
    # ancestors so the fallback works regardless of how deep the caller sits
    # (e.g. ``src/<pkg>/<module>.py`` vs a shallow script path).
    for ancestor in resolved.parents:
        sibling = ancestor / "template"
        if (sibling / "infrastructure").is_dir():
            return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {from_path}")


def project_root() -> Path:
    """Return this project's own root directory (``.../template_pitch_deck``)."""
    return Path(__file__).resolve().parents[2]


__all__ = ["locate_repo_root", "project_root"]

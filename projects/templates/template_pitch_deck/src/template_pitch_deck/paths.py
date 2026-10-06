"""Repository root discovery for template_pitch_deck scripts."""

from __future__ import annotations

from pathlib import Path

from infrastructure.project.public_reference_session import ReferenceSession

_REFERENCE = ReferenceSession()


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


def data_repo_root(from_path: Path, *, explicit_root: Path | None = None) -> Path:
    """Select a complete bound DATA reference or retain ordinary source discovery."""
    reference = _REFERENCE.current(explicit_root=explicit_root)
    if reference is not None:
        return reference.root
    return locate_repo_root(explicit_root if explicit_root is not None else from_path)


def reference_tracked_paths(repo_root: Path) -> tuple[str, ...] | None:
    """Use the selected complete reference's original Root Git inventory."""
    return _REFERENCE.tracked_paths(explicit_root=repo_root)


def verify_reference_inputs() -> None:
    """Recheck a bound reference before accepting producer/test results."""
    _REFERENCE.verify()


__all__ = ["locate_repo_root", "project_root", "data_repo_root", "reference_tracked_paths", "verify_reference_inputs"]

"""Repository root discovery for template_template scripts."""

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
    sibling = resolved.parents[2] / "template"
    if (sibling / "infrastructure").is_dir():
        return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {from_path}")


def data_repo_root(from_path: Path, *, explicit_root: Path | None = None) -> Path:
    """Select a complete bound DATA reference or retain ordinary source discovery."""
    reference = _REFERENCE.current(explicit_root=explicit_root)
    if reference is not None:
        return reference.root
    return locate_repo_root(explicit_root if explicit_root is not None else from_path)


def verify_reference_inputs() -> None:
    """Recheck a bound reference before accepting producer/test results."""
    _REFERENCE.verify()


__all__ = ["locate_repo_root", "data_repo_root", "verify_reference_inputs"]

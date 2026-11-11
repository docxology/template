"""Shared source and resource eligibility for exemplar export workflows."""

from __future__ import annotations

import fnmatch
from pathlib import Path
import tomllib


_IGNORED_NAMES = frozenset(
    {
        ".DS_Store",
        ".cache",
        ".lake",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "lake-packages",
        "output",
        "rendered",
        "venv",
    }
)
_IGNORED_PATTERNS = ("*.egg-info", "*.pyc", "*.pyo")


def declared_resource_dependencies(source_root: Path) -> tuple[str, ...]:
    """Read validated cross-root resource declarations from ``export.toml``."""
    config_path = source_root / "export.toml"
    if not config_path.is_file():
        return ()
    payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config = payload.get("template_export", {})
    if not isinstance(config, dict):
        raise ValueError(f"[template_export] must be a table: {config_path}")
    raw = config.get("cross_root_dependencies", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError("template_export.cross_root_dependencies must be a list of strings")
    dependencies = tuple(raw)
    allowed = {"fonds/templates", "rules/templates", "tools/templates", "infrastructure"}
    invalid = sorted(set(dependencies) - allowed)
    if invalid:
        raise ValueError(f"unsupported cross-root resource dependencies: {', '.join(invalid)}")
    if len(dependencies) != len(set(dependencies)):
        raise ValueError("cross-root resource dependencies must be unique")
    return dependencies


def is_clean_resource_path(path: Path, dependency: str) -> bool:
    """Apply artifact exclusions without hiding Layer-1 ``output`` source."""
    for part in path.parts:
        if part in _IGNORED_NAMES and not (dependency == "infrastructure" and part == "output"):
            return False
        if any(fnmatch.fnmatch(part, pattern) for pattern in _IGNORED_PATTERNS):
            return False
    return True


def is_clean_source_path(path: Path) -> bool:
    for part in path.parts:
        if part in _IGNORED_NAMES:
            return False
        if any(fnmatch.fnmatch(part, pattern) for pattern in _IGNORED_PATTERNS):
            return False
    return True

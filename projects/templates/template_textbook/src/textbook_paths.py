"""Path discovery helpers for standalone and template-hosted checkouts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SRC = PROJECT / "src"
SCRIPTS_DIR = PROJECT / "scripts"
MANUSCRIPT = PROJECT / "manuscript"


def ensure_project_paths(*, include_scripts: bool = False) -> Path:
    """Insert ``src/``, optional ``scripts/``, and the template root on ``sys.path``."""
    if include_scripts:
        scripts_str = str(SCRIPTS_DIR)
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)

    src_str = str(SRC)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    root = discover_template_root(PROJECT)
    if root is not None:
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    return PROJECT


def template_root() -> Path | None:
    """Return the discovered template repository root, if any."""
    return discover_template_root(PROJECT)


def is_template_root(path: Path) -> bool:
    """Return true when ``path`` looks like the template repository root."""
    return (path / "infrastructure" / "validation").is_dir() and (path / "infrastructure" / "rendering").is_dir()


def discover_template_root(start: Path) -> Path | None:
    """Find a nearby template root without assuming a fixed checkout layout."""
    env_value = os.environ.get("TEMPLATE_TEXTBOOK_TEMPLATE_ROOT")
    if env_value:
        env_path = Path(env_value).expanduser().resolve()
        if is_template_root(env_path):
            return env_path

    current = start.resolve()
    if current.is_file():
        current = current.parent

    for ancestor in (current, *current.parents):
        if is_template_root(ancestor):
            return ancestor
    return None

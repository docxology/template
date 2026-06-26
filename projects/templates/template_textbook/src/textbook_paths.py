"""Path discovery helpers for standalone and template-hosted checkouts.

Three levels of path are exposed:

* ``PROJECT`` — the root directory of this textbook project
  (parent of ``src/``, ``manuscript/``, ``scripts/``).
* ``SRC`` — the ``src/`` package directory added to ``sys.path`` so project
  modules are importable without installation.
* ``MANUSCRIPT`` — the ``manuscript/`` directory (config, chapters, labs, etc.)

:func:`ensure_project_paths` is the canonical bootstrap call; scripts should
call it before importing any project module when running outside the normal
``uv run`` / pytest paths.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SRC = PROJECT / "src"
SCRIPTS_DIR = PROJECT / "scripts"
MANUSCRIPT = PROJECT / "manuscript"


def ensure_project_paths(*, include_scripts: bool = False) -> Path:
    """Insert ``src/``, optional ``scripts/``, and the template root on ``sys.path``.

    Idempotent: calling multiple times with the same arguments is safe and does
    not produce duplicate entries.

    Args:
        include_scripts: When ``True``, also prepend ``scripts/`` so script
            helpers (thin orchestrators) are importable.

    Returns:
        The project root directory (:data:`PROJECT`).
    """
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
    """Return the discovered template repository root, if any.

    Convenience wrapper around :func:`discover_template_root` that always
    starts the search from :data:`PROJECT`.
    """
    return discover_template_root(PROJECT)


def is_template_root(path: Path) -> bool:
    """Return ``True`` when ``path`` looks like the template repository root.

    A valid root must have both ``infrastructure/validation/`` and
    ``infrastructure/rendering/`` subdirectories.
    """
    return (path / "infrastructure" / "validation").is_dir() and (path / "infrastructure" / "rendering").is_dir()


def discover_template_root(start: Path) -> Path | None:
    """Find a nearby template root without assuming a fixed checkout layout.

    Search order:

    1. ``TEMPLATE_TEXTBOOK_TEMPLATE_ROOT`` environment variable (if set and
       valid according to :func:`is_template_root`).
    2. Walk ancestors of ``start`` (or ``start.parent`` when ``start`` is a
       file) and return the first ancestor that passes :func:`is_template_root`.
    3. Return ``None`` if no valid root is found (standalone checkout).

    Args:
        start: Directory (or file) from which to begin the ancestor walk.

    Returns:
        Resolved root path, or ``None``.
    """
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


__all__ = [
    "MANUSCRIPT",
    "PROJECT",
    "SCRIPTS_DIR",
    "SRC",
    "discover_template_root",
    "ensure_project_paths",
    "is_template_root",
    "template_root",
]

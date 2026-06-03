"""Shared ``sys.path`` bootstrap for template_textbook scripts."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
_PROJECT = _SCRIPTS.parent
_SRC = _PROJECT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from textbook_paths import (  # noqa: E402
    PROJECT,
    SCRIPTS_DIR,
    SRC,
    ensure_project_paths,
    template_root,
)

__all__ = [
    "PROJECT",
    "SCRIPTS_DIR",
    "SRC",
    "ensure_project_paths",
    "template_root",
]

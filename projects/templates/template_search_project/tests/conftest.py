"""Pytest configuration for template_search_project tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Add repo root + project src/ to path so tests can import infrastructure
# and the project package by name.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
REPO_ROOT = PROJECT_ROOT.parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "template_search_project"))

# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

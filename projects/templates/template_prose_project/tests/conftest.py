"""Pytest configuration for template_prose_project tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force headless backend for matplotlib in tests — must run before any matplotlib import.
# `docs/rendering_pipeline.md` documents this file as pinning MPLBACKEND=Agg; keep them in sync.
os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
REPO_ROOT = PROJECT_ROOT.parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "template_prose_project"))
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

# TEST-ISOLATION-SYSPATH-1: expose the unique nested source package.
import os as _os
import sys as _sys

_SRC = _os.path.join(_os.path.dirname(__file__), "..", "src")
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)

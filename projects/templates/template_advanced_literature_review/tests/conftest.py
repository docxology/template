"""Pytest configuration for template_advanced_literature_review tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ and scripts/ so tests resolve project modules the same way whether
# pytest is invoked from the repository root (documented AGENTS.md verification
# command) or standalone from this project directory (STANDALONE.md fork
# workflow). Mirrors the sibling conftest.py pattern in
# template_literature_meta_analysis/tests/conftest.py.
_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
_REPO_ROOT = _ROOT.parents[2]
for _path in (str(_REPO_ROOT), str(_SCRIPTS), str(_SRC)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

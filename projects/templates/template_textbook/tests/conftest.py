"""Pytest configuration for template_textbook tests.

Pins the headless matplotlib backend before any pyplot import and wires the
template-hosted checkout onto ``sys.path`` so ``src/`` modules import the same
way under standalone pytest and the repository pipeline.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Force headless backend for matplotlib — must run before any matplotlib import.
os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parent.parent.parent

for path in (REPO_ROOT, PROJECT_ROOT, PROJECT_ROOT / "src"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

"""Pytest configuration for template_sia."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]

for path in (REPO_ROOT, PROJECT_ROOT, PROJECT_ROOT / "src"):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

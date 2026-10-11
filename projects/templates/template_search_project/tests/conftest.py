"""Pytest configuration for template_search_project tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Expose only the own domain source; the selected environment supplies Root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

"""Pytest configuration for template_code_project tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the repo root to path so the documented per-project pytest command
# works from a clean environment. The project pyproject's `pythonpath` is
# project-relative and omits the repo root, so without this the suite cannot import
# `infrastructure` (tests collect-error). The project lives at
# projects/templates/<name>/, so the repo root is three levels above ROOT.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
for _path in (REPO_ROOT, SRC):
    if _path not in sys.path:
        sys.path.insert(0, _path)

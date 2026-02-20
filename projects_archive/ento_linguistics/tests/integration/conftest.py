"""Pytest configuration for integration tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add template root to path so we can import infrastructure modules
# integration/ -> tests/ -> ento_linguistics/ -> projects_archive/ -> template/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)  # For infrastructure.* imports

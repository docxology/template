"""Pytest configuration for template infrastructure tests."""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add infrastructure/ to path for infrastructure module imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INFRASTRUCTURE = os.path.join(ROOT, "infrastructure")
if INFRASTRUCTURE not in sys.path:
    sys.path.insert(0, INFRASTRUCTURE)

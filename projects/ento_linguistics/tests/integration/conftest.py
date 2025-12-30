"""Pytest configuration for integration tests."""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ to path so we can import project modules
# From project/tests/integration/, go up to project/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(PROJECT_ROOT, "src")
REPO_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
if SRC not in sys.path:
    sys.path.insert(0, SRC)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)  # For infrastructure.* imports


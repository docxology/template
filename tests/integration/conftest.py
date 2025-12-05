"""Pytest configuration for integration tests."""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ to path so we can import infrastructure and scientific modules
# (if src/ directory exists - it may not in all project structures)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if os.path.exists(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)





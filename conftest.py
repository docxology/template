"""Root-level pytest configuration - MUST run before any test imports."""
import os
import sys

# CRITICAL: Add paths BEFORE any imports can occur
ROOT = os.path.dirname(os.path.abspath(__file__))

# Add root to sys.path so infrastructure/ and project/ are importable as packages
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Force headless backend for all matplotlib usage
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

"""Pytest configuration for infrastructure layer tests."""
import os

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

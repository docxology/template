"""Pytest configuration for template tests.

This file:
- Forces headless matplotlib (MPLBACKEND=Agg)
- Inserts repository roots (infrastructure/, project/src/) ahead of tests/ to avoid shadowing
- Keeps imports consistent for both infrastructure and project test suites
"""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add ROOT to path so we can import infrastructure as a package
# Ensure ROOT is FIRST in path to avoid shadowing by tests/infrastructure
if ROOT in sys.path:
    sys.path.remove(ROOT)
sys.path.insert(0, ROOT)

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = os.path.join(ROOT, "tests")
if TESTS_DIR in sys.path:
    sys.path.remove(TESTS_DIR)

# Add src/ to path for scientific modules (if it exists)
SRC = os.path.join(ROOT, "src")
if os.path.exists(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add project/src/ to path for project modules
PROJECT_SRC = os.path.join(ROOT, "project", "src")
if os.path.exists(PROJECT_SRC) and PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)

"""Pytest configuration for template infrastructure tests."""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INFRASTRUCTURE = os.path.join(ROOT, "infrastructure")
SRC = os.path.join(ROOT, "src")
PROJECT_ROOT = os.path.join(ROOT, "project")

# Add infrastructure/ to path (infrastructure modules are at root level)
if INFRASTRUCTURE not in sys.path:
    sys.path.insert(0, INFRASTRUCTURE)

# Add src/ to path for scientific modules
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add project/src/ to path for project modules
PROJECT_SRC = os.path.join(PROJECT_ROOT, "src")
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)

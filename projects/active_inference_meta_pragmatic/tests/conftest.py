"""Pytest configuration for active_inference_meta_pragmatic project tests.

This file:
- Forces headless matplotlib (MPLBACKEND=Agg)
- Inserts project/src/ ahead of tests/ to avoid shadowing
- Keeps imports consistent for project test suite
"""

import os
import sys
from pathlib import Path

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent
REPO_ROOT = PROJECT_ROOT.parent

# Add project src/ to path so we can import src modules
PROJECT_SRC = PROJECT_ROOT / "src"
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = PROJECT_ROOT / "tests"
if TESTS_DIR in sys.path:
    sys.path.remove(str(TESTS_DIR))
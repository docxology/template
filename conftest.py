"""Root-level pytest configuration - MUST run before any test imports.

This configuration enables:
1. Infrastructure module imports (infrastructure/)
2. Project source imports (projects/{name}/src/)
3. Project test imports (projects/{name}/tests/)
4. Headless matplotlib rendering

Path configuration is CRITICAL and must happen before any test imports.

Pytest and coverage settings are defined in pyproject.toml:
- [tool.pytest.ini_options] - Test discovery and execution
- [tool.coverage.run] - Coverage collection settings
- [tool.coverage.report] - Coverage report configuration
"""
import os
import sys

# CRITICAL: Add paths BEFORE any imports can occur
ROOT = os.path.dirname(os.path.abspath(__file__))

# Add root to sys.path so infrastructure/ and project/ are importable as packages
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Add projects/*/src for project-specific imports
PROJECT_SRC = os.path.join(ROOT, "projects", "project", "src")
if PROJECT_SRC not in sys.path:
    sys.path.insert(1, PROJECT_SRC)

SMALL_CODE_SRC = os.path.join(ROOT, "projects", "code_project", "src")
if SMALL_CODE_SRC not in sys.path:
    sys.path.insert(1, SMALL_CODE_SRC)

SMALL_PROSE_SRC = os.path.join(ROOT, "projects", "prose_project", "src")
if SMALL_PROSE_SRC not in sys.path:
    sys.path.insert(1, SMALL_PROSE_SRC)

# Force headless backend for all matplotlib usage
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Set project root for scripts
os.environ.setdefault("PROJECT_ROOT", ROOT)

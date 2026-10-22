"""Pytest configuration for template_code_project tests."""

import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add src/ AND the repo root to path so the documented per-project pytest command
# works from a clean environment. The project pyproject's `pythonpath` is
# project-relative and omits the repo root, so without this the suite cannot import
# `infrastructure` (tests collect-error). The project lives at
# projects/templates/<name>/, so the repo root is three levels above ROOT.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")


def _find_repo_root(project_root: str) -> str | None:
    """Locate the template repository root without assuming a fixed depth.

    The bundle layout nests this project under ``<bundle>/source/``, so a
    hard-coded three-level walk lands outside any repository. Search upward
    for the infrastructure package + pyproject.toml markers instead; return
    ``None`` when the project is standalone.
    """
    current = os.path.abspath(project_root)
    while True:
        if os.path.isdir(os.path.join(current, "infrastructure")) and os.path.isfile(
            os.path.join(current, "pyproject.toml")
        ):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


REPO_ROOT = _find_repo_root(ROOT)
for _path in ([REPO_ROOT] if REPO_ROOT else []) + [SRC]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

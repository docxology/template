"""Pytest configuration for template_sia."""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]

for path in (REPO_ROOT, PROJECT_ROOT, PROJECT_ROOT / "src"):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

# Volatile/derived paths that must never be copied into a test sandbox: copying a
# live coverage DB while pytest-cov rewrites it raises a mid-copy FileNotFoundError
# (a real flaky failure that broke the render's Project-Tests stage). Copy source only.
_COPY_IGNORE = shutil.ignore_patterns(
    ".coverage*",
    "coverage_project.json",
    "htmlcov",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "output",
    "*.egg-info",
)


@pytest.fixture
def copy_project_sandbox() -> Callable[[Path], Path]:
    """Return a helper that copies the project into a sandbox directory.

    The helper excludes volatile/derived artifacts (coverage DBs, caches, the
    output tree) so a mid-write coverage file cannot trigger a flaky copy error.
    Exposed as a fixture so every test module shares one guarded copy routine
    without import-time coupling to this module.

    Returns:
        A callable ``copy(dst) -> dst`` that populates ``dst`` from the project tree.
    """

    def _copy(dst: Path) -> Path:
        shutil.copytree(PROJECT_ROOT, dst, ignore=_COPY_IGNORE)
        return dst

    return _copy

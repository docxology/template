"""Support for direct recompute-module tests: isolated project-tree copies.

The heavy recompute modules (``roadmap_tracks.fixed_point``,
``roadmap_tracks.supplemental``, ``roadmap_tracks.formal_interop``,
``manuscript.refresh``, ``manuscript.sheaf.semantic_refresh``) historically
received coverage only when gate tests judged the tracked ``output/`` snapshot
stale and rebuilt it. That made the 90% coverage floor depend on which Python
version last regenerated the snapshot (py3.12-fresh snapshot -> py3.12 CI leg
takes fast paths and drops below the floor). The ``test_*_direct.py`` files
exercise those writers directly against a copy of the project tree, so their
coverage is deterministic on every leg and the tracked snapshot is never
rewritten (tests/AGENTS.md: tests must not leave canonical gate artifacts
stale, and standard runs must not churn the committed snapshot).
"""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_COPY_DIRS = ("manuscript", "gnn", "lean", "data", "docs", "output", "scripts", "src", "tests")
_COPY_IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".coverage*")


def copy_project_tree(target: Path) -> Path:
    """Copy the project's source/data/output tree into ``target``.

    Real writers run against this copy; the git-tracked tree stays untouched.
    ``.git`` does not exist below the project dir, so provenance helpers that
    shell out to git degrade to their documented ``"unknown"`` fallback.
    """
    target.mkdir(parents=True, exist_ok=True)
    for entry in _COPY_DIRS:
        source = PROJECT_ROOT / entry
        if source.is_dir():
            shutil.copytree(source, target / entry, ignore=_COPY_IGNORE, dirs_exist_ok=True)
    for entry in PROJECT_ROOT.iterdir():
        if entry.is_file():
            shutil.copy2(entry, target / entry.name)
    return target

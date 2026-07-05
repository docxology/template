"""Shared sys.path bootstrap for thin project scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_paths(project_root: Path) -> Path:
    """Insert project, src, and repo roots on ``sys.path`` and return repo root."""
    project_root = project_root.resolve()
    repo_root = project_root.parents[2].resolve()
    for path in (project_root, project_root / "src", repo_root):
        path_text = str(path)
        if path_text not in sys.path:
            sys.path.insert(0, path_text)
    return repo_root

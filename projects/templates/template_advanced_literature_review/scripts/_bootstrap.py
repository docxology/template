"""Shared sys.path bootstrap for project orchestrator scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    """Locate the monorepo root (the directory that holds ``infrastructure/``).

    A fixed ``parents[N]`` hop is fragile: a project nested at
    ``projects/templates/<name>`` sits one level deeper than one at
    ``projects/<name>``. Prefer the render pipeline's ``TEMPLATE_REPO_ROOT`` env
    var, then walk upward looking for the ``infrastructure/`` marker, and only
    fall back to a fixed hop if neither is available.
    """
    env_root = os.environ.get("TEMPLATE_REPO_ROOT")
    if env_root and (Path(env_root) / "infrastructure").is_dir():
        return Path(env_root)
    for parent in (start, *start.parents):
        if (parent / "infrastructure").is_dir():
            return parent
    return start.parent.parent


def bootstrap_project(*, include_infrastructure: bool = False) -> Path:
    """Insert ``src/`` (and optionally template repo root) on ``sys.path``.

    Returns:
        Project root directory (parent of ``scripts/``).
    """
    root = Path(__file__).resolve().parent.parent
    _consume_project_argument(root)
    src = root / "src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
    if include_infrastructure:
        repo_text = str(_find_repo_root(root))
        if repo_text not in sys.path:
            sys.path.insert(0, repo_text)
    return root


def _consume_project_argument(project_root: Path) -> None:
    """Validate and remove the shared ``--project`` context argument.

    Project-local scripts historically inferred their root from ``__file__``.
    The repository methods contract now passes an explicit qualified project
    name to every stage command, so these wrappers accept that argument while
    retaining their existing script-specific argparse surfaces.
    """
    try:
        index = sys.argv.index("--project")
    except ValueError:
        return
    if index + 1 >= len(sys.argv):
        raise SystemExit("--project requires a qualified project name")
    supplied = Path(sys.argv[index + 1]).name
    if supplied != project_root.name:
        raise SystemExit(
            f"this project-local entrypoint only supports {project_root.name!r}; received {sys.argv[index + 1]!r}"
        )
    del sys.argv[index : index + 2]

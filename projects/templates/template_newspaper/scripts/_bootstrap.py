"""Shared path/logging bootstrap for the newspaper analysis scripts.

Each ``scripts/NN_*.py`` is a thin orchestrator the pipeline's Stage 02 runs in
lexicographic order. They must work two ways: invoked by the repository
orchestrator (where ``infrastructure`` is importable) and run standalone during
development. This helper makes both paths robust by locating the project root
and the repo root by walking up the tree, and by providing a logger that falls
back to the standard library when ``infrastructure`` is unavailable.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """The template_newspaper project directory."""
    return Path(__file__).resolve().parent.parent


def find_repo_root(start: Path | None = None) -> Path | None:
    """Walk up from ``start`` until a directory containing ``infrastructure/``."""
    p = (start or project_root())
    for _ in range(10):
        if (p / "infrastructure").is_dir():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def setup_paths() -> None:
    """Put the project ``src/`` and (if found) the repo root on ``sys.path``."""
    root = project_root()
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    repo = find_repo_root(root)
    if repo and str(repo) not in sys.path:
        sys.path.insert(0, str(repo))


def get_logger(name: str) -> Any:
    """Return the infrastructure logger if available, else a stdlib logger."""
    try:
        from infrastructure.core.logging.utils import get_logger as _infra_logger  # type: ignore

        return _infra_logger(name)
    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
        )
        return logging.getLogger(name)

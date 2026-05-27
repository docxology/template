#!/usr/bin/env python3
"""Architecture visualization generator — Thin Orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


def _locate_repo_root(project_dir: Path) -> Path:
    resolved = project_dir.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "infrastructure").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    sibling = resolved.parents[2] / "template"
    if (sibling / "infrastructure").is_dir():
        return sibling.resolve()
    raise FileNotFoundError(f"Could not locate template repo root from {project_dir}")


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = _locate_repo_root(PROJECT_DIR)
SRC_DIR = PROJECT_DIR / "src"
for path_str in (str(REPO_ROOT), str(SRC_DIR)):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from infrastructure.core.logging.utils import get_logger
from template_template import generate_all_architecture_figures

logger = get_logger(__name__)


def main() -> None:
    """Generate all architecture figures via src/template module logic."""
    logger.info("Starting architecture visualization generation...")
    paths = generate_all_architecture_figures(REPO_ROOT, PROJECT_DIR)
    logger.info("Architecture visualization generation complete")
    for path in paths:
        logger.info("  • %s", path)


if __name__ == "__main__":
    main()

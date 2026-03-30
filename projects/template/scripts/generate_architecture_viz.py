#!/usr/bin/env python3
"""Architecture visualization generator — Thin Orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = PROJECT_DIR.parent.parent
SRC_DIR = PROJECT_DIR / "src"
for path_str in (str(REPO_ROOT), str(SRC_DIR)):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from infrastructure.core.logging.utils import get_logger
from template import generate_all_architecture_figures

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

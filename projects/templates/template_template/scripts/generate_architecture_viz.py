#!/usr/bin/env python3
"""Architecture visualization generator — Thin Orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")


PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from template_template.paths import locate_repo_root  # noqa: E402

REPO_ROOT = locate_repo_root(PROJECT_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402
from template_template import generate_all_architecture_figures  # noqa: E402

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

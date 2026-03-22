#!/usr/bin/env python3
"""Generate masthead PNG — thin orchestrator."""

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

from infrastructure.core.logging_utils import get_logger
from newspaper.masthead import render_masthead_png

logger = get_logger(__name__)


def main() -> None:
    """Write ``output/figures/masthead.png`` and print the path for the manifest."""
    out = PROJECT_DIR / "output" / "figures" / "masthead.png"
    title = os.environ.get("NEWSPAPER_TITLE", "TEMPLATE GAZETTE")
    tagline = os.environ.get("NEWSPAPER_TAGLINE", "All the news that fits the pipeline")
    logger.info("Rendering masthead to %s", out)
    render_masthead_png(out, title=title, tagline=tagline)
    logger.info("Masthead written")
    print(out.resolve())


if __name__ == "__main__":
    main()

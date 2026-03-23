#!/usr/bin/env python3
"""Generate B&W word-count bar chart from manuscript_stats.json — thin orchestrator."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent))
REPO_ROOT = PROJECT_DIR.parent.parent
SRC_DIR = PROJECT_DIR / "src"
for path_str in (str(REPO_ROOT), str(SRC_DIR)):
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from infrastructure.core.logging_utils import get_logger
from newspaper.visualization import render_wordcount_chart_from_stats_file

logger = get_logger(__name__)


def main() -> None:
    """Write ``output/figures/wordcount_bars_bw.png`` and print its path."""
    stats_path = PROJECT_DIR / "output" / "data" / "manuscript_stats.json"
    out = PROJECT_DIR / "output" / "figures" / "wordcount_bars_bw.png"
    if not stats_path.is_file():
        logger.error("Missing %s; run report_manuscript_stats.py first (analysis script order).", stats_path)
        sys.exit(1)
    logger.info("Rendering word-count chart from %s", stats_path)
    render_wordcount_chart_from_stats_file(stats_path, out)
    logger.info("Word-count chart written")
    print(out.resolve())


if __name__ == "__main__":
    main()

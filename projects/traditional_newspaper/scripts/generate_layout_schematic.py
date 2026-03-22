#!/usr/bin/env python3
"""Generate layout schematic PNG — thin orchestrator."""

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
from newspaper.layout_figure import render_layout_schematic_png

logger = get_logger(__name__)


def main() -> None:
    """Write ``output/figures/layout_schematic.png`` and print the path for the manifest."""
    out = PROJECT_DIR / "output" / "figures" / "layout_schematic.png"
    logger.info("Rendering layout schematic to %s", out)
    render_layout_schematic_png(out)
    logger.info("Layout schematic written")
    print(out.resolve())


if __name__ == "__main__":
    main()

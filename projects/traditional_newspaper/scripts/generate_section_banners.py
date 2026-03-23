#!/usr/bin/env python3
"""Emit B&W section banner PNGs for each interior/supplemental folio — thin orchestrator."""

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
from newspaper.section_graphics import render_section_banner_bw, section_banner_filename
from newspaper.sections import section_banner_targets

logger = get_logger(__name__)


def main() -> None:
    """Write ``output/figures/section_banner_*.png`` for each banner target; print paths."""
    out_dir = PROJECT_DIR / "output" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for stem, title in section_banner_targets():
        name = section_banner_filename(stem)
        dest = out_dir / name
        logger.info("Rendering banner for stem %s", stem)
        render_section_banner_bw(dest, stem, title)
        paths.append(dest.resolve())
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()

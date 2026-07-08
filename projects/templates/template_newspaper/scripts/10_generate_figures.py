#!/usr/bin/env python3
"""Stage-02 analysis: generate the edition's figures.

Produces the halftone engravings and grayscale charts the pages reference, into
``output/figures/``. Runs before the render script (lexicographic order) so the
PDF embeds real images rather than placeholders.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("newspaper.figures")


def main() -> int:
    """CLI entry point."""
    root = project_root()
    from newspaper.config import load_newspaper_config
    from newspaper.figures import generate_all

    config = load_newspaper_config(root / "content")
    out_dir = root / config.figures_dir
    paths = generate_all(out_dir)
    for p in paths:
        logger.info("  figure: %s (%d bytes)", p.name, p.stat().st_size)
    logger.info("Generated %d figures into %s", len(paths), out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Wrapper script for rendering all formats."""
import sys
from pathlib import Path

# Add root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from infrastructure.core.logging_utils import get_logger
from infrastructure.rendering import RenderManager

logger = get_logger(__name__)


def main() -> None:
    """Render all formats for all manuscript files."""
    manager = RenderManager()

    # Find sources
    manuscript_dir = Path("manuscript")
    if not manuscript_dir.exists():
        logger.error("No manuscript directory found.")
        sys.exit(1)

    for source in manuscript_dir.glob("*.tex"):
        logger.info(f"Rendering {source}...")
        outputs = manager.render_all(source)
        for out in outputs:
            logger.info(f"  Generated: {out}")


if __name__ == "__main__":
    main()

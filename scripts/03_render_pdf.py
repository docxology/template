#!/usr/bin/env python3
"""PDF rendering orchestrator script.

This thin orchestrator coordinates the PDF rendering stage using the
infrastructure rendering module:
1. Discovers manuscript files
2. Uses RenderManager for multi-format rendering
3. Validates generated outputs
4. Reports rendering results

Stage 03 of the pipeline orchestration.

Exit codes:
    0: PDF/web/slides rendering completed for all manuscript sections
    1: Rendering pipeline failed (missing LaTeX, pandoc, or source files)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path for infrastructure imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.core.logging.utils import get_logger, log_header
from infrastructure.rendering.pipeline import execute_render_pipeline

# Set up logger for this module
logger = get_logger(__name__)


def main() -> int:
    """Execute PDF rendering orchestration."""
    import argparse

    parser = argparse.ArgumentParser(description="Render PDF manuscript")
    parser.add_argument(
        "--project",
        default="project",
        help="Project directory name; resolves projects/<name> first, else projects_in_progress/<name>",
    )
    args = parser.parse_args()

    log_header(f"STAGE 03: Render PDF (Project: {args.project})", logger)

    try:
        # Run rendering pipeline
        exit_code = execute_render_pipeline(args.project)
        return exit_code

    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

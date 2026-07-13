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
# Bootstrap: add repo root so the centralized helper itself is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

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
        help="Project directory name; resolves projects/active/<name> first, else projects/working/<name>",
    )
    parser.add_argument(
        "--skip-manuscript-hydration",
        action="store_true",
        help="Skip the (slow) manuscript-variable hydration step before rendering "
        "(for fast title-page/metadata re-renders)",
    )
    args = parser.parse_args()

    log_header(f"STAGE 03: Render PDF (Project: {args.project})", logger)

    try:
        # Run rendering pipeline
        exit_code = execute_render_pipeline(args.project, skip_manuscript_hydration=args.skip_manuscript_hydration)
        return exit_code

    except Exception as e:
        logger.error(f"Render pipeline error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

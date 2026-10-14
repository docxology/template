#!/usr/bin/env python3
"""Inject computed pipeline variables into the advanced manuscript."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project(include_infrastructure=True)

from infrastructure.core.logging.utils import get_logger, log_operation
from infrastructure.rendering.manuscript_injection import (
    hydrate_manuscript_tree,
    validate_hydration_paths,
    validate_project_selection,
)

from config import PROJECT_NAME
from manuscript.variables import compute_variables, inject_variables

logger = get_logger(__name__)


def main() -> int:
    """Compute variables and render manuscript Markdown files."""
    parser = argparse.ArgumentParser(description="Inject pipeline variables into manuscript templates")
    parser.add_argument("--project", default=PROJECT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    validate_project_selection(PROJECT_ROOT, args.project)

    manuscript_dir = PROJECT_ROOT / "manuscript"
    output_dir = PROJECT_ROOT / "output"
    if not manuscript_dir.is_dir():
        logger.error("Manuscript directory not found: %s", manuscript_dir)
        return 1
    if not output_dir.is_dir():
        logger.error("Output directory not found: %s", output_dir)
        return 1

    validate_hydration_paths(PROJECT_ROOT)

    with log_operation("Manuscript variable injection"):
        variables = compute_variables(output_dir)

        def render(filename: str, content: str) -> str:
            return inject_variables(
                content, variables, filename=filename, lenient=filename == "02e_methods_viz_injection.md"
            )

        files_changed, total_injected = hydrate_manuscript_tree(PROJECT_ROOT, render, dry_run=args.dry_run)

        logger.info(
            "Variable injection complete: %d variables across %d files",
            total_injected,
            files_changed,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

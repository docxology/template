#!/usr/bin/env python3
"""Manuscript variable injection script (thin wrapper)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project(include_infrastructure=True)

from template_literature_meta_analysis.config import PROJECT_NAME
from infrastructure.core.logging.utils import get_logger, log_operation
from infrastructure.rendering.manuscript_injection import (
    hydrate_manuscript_tree,
    validate_hydration_paths,
    validate_project_selection,
)
from template_literature_meta_analysis.manuscript.variables import compute_variables, inject_variables

logger = get_logger(__name__)


def resolve_project_dir(project_name: str) -> Path:
    """Validate this project-local script's explicit owner context."""
    return validate_project_selection(PROJECT_ROOT, project_name)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Inject pipeline variables into manuscript templates")
    parser.add_argument("--project", default=PROJECT_NAME)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_dir = resolve_project_dir(args.project)
    manuscript_dir = project_dir / "manuscript"
    output_dir = project_dir / "output"

    if not manuscript_dir.exists():
        logger.error("Manuscript directory not found: %s", manuscript_dir)
        return 1
    if not output_dir.exists():
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
            "Variable injection complete: %d variables injected across %d files",
            total_injected,
            files_changed,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

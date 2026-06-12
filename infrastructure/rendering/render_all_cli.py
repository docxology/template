#!/usr/bin/env python3
"""Wrapper script for rendering all formats."""

from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.project.discovery import resolve_project_root
from infrastructure.rendering import RenderManager

logger = get_logger(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_manuscript_dir(project: str | None) -> Path:
    if project:
        project_root = resolve_project_root(REPO_ROOT, project)
        manuscript_dir = project_root / "manuscript"
        if manuscript_dir.is_dir():
            return manuscript_dir
        logger.error("No manuscript directory for project %r: %s", project, manuscript_dir)
        raise SystemExit(1)

    legacy = Path("manuscript")
    if legacy.is_dir():
        return legacy

    logger.error("No manuscript directory found.")
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    """Render all formats for all manuscript files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        default=None,
        help="Qualified project name (for example template_code_project or templates/template_code_project)",
    )
    args = parser.parse_args([] if argv is None else argv)

    manuscript_dir = _resolve_manuscript_dir(args.project)
    manager = RenderManager()

    for source in manuscript_dir.glob("*.tex"):
        logger.info(f"Rendering {source}...")
        outputs = manager.render_all(source)
        for out in outputs:
            logger.info(f"  Generated: {out}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])

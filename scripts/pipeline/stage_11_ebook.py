#!/usr/bin/env python3
"""Pipeline stage 11: Generate ebook artifacts (EPUB, PDF) from rendered manuscript content."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.rendering.ebook_stage import run_ebook_generation  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate ebook formats from combined manuscript markdown")
    parser.add_argument(
        "--project",
        default="project",
        help="Project directory name or qualified path (e.g. templates/template_code_project); "
        "resolves projects/active/<name> first, else projects/working/<name>",
    )
    parser.add_argument(
        "--skip-formats",
        default="",
        help="Comma-separated list of formats to skip (epub,mobi,docx). Example: --skip-formats mobi,docx",
    )
    parser.add_argument(
        "--cover-image",
        default=None,
        help="Path to a cover image file to embed in the EPUB/MOBI output",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    return run_ebook_generation(
        repo_root,
        args.project,
        skip_formats_arg=args.skip_formats,
        cover_image_arg=args.cover_image,
    )


if __name__ == "__main__":
    sys.exit(main())

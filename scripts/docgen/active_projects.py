#!/usr/bin/env python3
"""Write docs/_generated/active_projects.md for the public template scope."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.documentation.active_projects_doc import render_active_projects_doc, write_active_projects_doc  # noqa: E402
from infrastructure.project.public_scope import public_project_names  # noqa: E402

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Check or regenerate the public active-projects document."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="compare generated content without writing")
    mode.add_argument("--write", action="store_true", help="write the generated document (default)")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_path = repo_root / "docs" / "_generated" / "active_projects.md"
    log_header("Generate Active Projects Documentation", logger)
    expected = render_active_projects_doc(repo_root)
    if args.check:
        if not output_path.is_file():
            logger.error("Generated document is missing: %s", output_path)
            return 1
        if output_path.read_text(encoding="utf-8") != expected:
            logger.error("Generated document is stale: %s", output_path)
            return 1
        log_success(f"Checked {output_path} ({len(public_project_names(repo_root))} project(s))", logger)
        return 0
    out_path = write_active_projects_doc(repo_root)
    log_success(f"Wrote {out_path} ({len(public_project_names(repo_root))} project(s))", logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

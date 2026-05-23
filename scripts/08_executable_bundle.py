#!/usr/bin/env python3
"""Executable-bundle stage orchestrator (Stage 10 — opt-in via [bundle] tag)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.core.logging.utils import get_logger, log_header, log_success  # noqa: E402
from infrastructure.publishing.executable_bundle import bundle_project  # noqa: E402

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a project's executable bundle.")
    parser.add_argument("--project", required=True, help="Project name under projects/")
    parser.add_argument(
        "--python-version",
        default="3.12",
        help="Python version tag for the Dockerfile base (default: 3.12)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    log_header(f"Stage: Executable Bundle (project: {args.project})")

    output_dir = bundle_project(
        repo_root,
        args.project,
        python_version=args.python_version,
    )
    log_success(f"Bundle written to: {output_dir}")
    print(str(output_dir))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

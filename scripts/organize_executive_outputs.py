#!/usr/bin/env python3
"""Organize executive and multi-project summary outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.reporting.executive_outputs import (  # noqa: E402
    ExecutiveOutputOptions,
    run_executive_output_organization,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reorganize executive summary and multi-project summary outputs by file type"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--executive-only", action="store_true", help="Only organize executive summary outputs")
    parser.add_argument("--multi-project-only", action="store_true", help="Only organize multi-project summary outputs")
    return parser.parse_args()


def main() -> int:
    """Run the executive output organization orchestrator."""
    args = _parse_args()
    try:
        run_executive_output_organization(
            Path(__file__).resolve().parent.parent,
            ExecutiveOutputOptions(
                dry_run=args.dry_run,
                executive_only=args.executive_only,
                multi_project_only=args.multi_project_only,
            ),
        )
        return 0
    except Exception as exc:  # pragma: no cover - top-level script guard
        from infrastructure.core.logging.utils import get_logger

        get_logger(__name__).error(f"Reorganization failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

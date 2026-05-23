#!/usr/bin/env python3
"""Thin CLI for template drift detection — logic lives in infrastructure.project.drift."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.drift import (  # noqa: E402
    DEFAULT_PROJECT_NAMES,
    exit_code_for_report,
    print_github_report,
    print_human_report,
    run_drift_checks,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        choices=list(DEFAULT_PROJECT_NAMES) + ["all"],
        default="all",
        help="Which exemplar to check (default: all).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARNINGs as ERRORs.",
    )
    parser.add_argument(
        "--format",
        choices=("human", "github"),
        default="human",
        help="Output format (default: human; 'github' emits ::error/::warning lines).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    projects = list(DEFAULT_PROJECT_NAMES) if args.project == "all" else [args.project]
    report = run_drift_checks(REPO_ROOT, projects)
    if args.format == "github":
        print_github_report(report)
    else:
        print_human_report(report)
    return exit_code_for_report(report, strict=args.strict)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

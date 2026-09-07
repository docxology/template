#!/usr/bin/env python3
"""Fail when the subsystem verification ledger has gone stale.

Thin orchestrator over :mod:`infrastructure.validation.status_freshness`:
parses CLI flags, runs :func:`validate_status_file` on ``<repo>/STATUS.md``,
prints the findings, and maps them to an exit code. All parsing and findings
logic lives in the infrastructure module (tested); this script only wires
arguments and exits.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from infrastructure.validation.status_freshness import validate_status_file

REPO_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    """Run the status freshness gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="Evaluation date in YYYY-MM-DD format (defaults to today).",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=183,
        help="Maximum permitted ledger age (default: 183 days / six months).",
    )
    args = parser.parse_args(argv)
    findings = validate_status_file(
        args.repo_root.resolve() / "STATUS.md",
        as_of=args.as_of,
        max_age_days=args.max_age_days,
    )
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        return 1
    print(f"STATUS.md freshness: OK (max age {args.max_age_days} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

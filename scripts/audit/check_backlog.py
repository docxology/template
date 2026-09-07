#!/usr/bin/env python3
"""Validate the future-work contract for root and public exemplar backlogs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.documentation.backlog import format_backlog_report, validate_public_backlogs  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run the backlog validator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat advisory findings as blocking errors.")
    args = parser.parse_args(argv)
    report = validate_public_backlogs(REPO_ROOT)
    print(format_backlog_report(report))
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

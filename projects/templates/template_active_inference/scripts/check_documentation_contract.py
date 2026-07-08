#!/usr/bin/env python3
"""Check project documentation contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gates.documentation_contract import check_documentation_contract  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI parser for documentation contract checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run documentation contract checks and exit nonzero on violations.",
    )
    return parser


def main() -> int:
    """CLI entry point."""
    build_parser().parse_args()
    issues = check_documentation_contract(PROJECT_ROOT)
    if issues:
        for issue in issues:
            print(issue.format(), file=sys.stderr)
        return 1
    print("documentation_contract: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

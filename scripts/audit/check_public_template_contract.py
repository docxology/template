#!/usr/bin/env python3
"""Check the non-empty structural contract for all public exemplars."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.project.public_template_contract import (
    format_public_template_contract,
    validate_public_template_contract,
)


def main(argv: list[str] | None = None) -> int:
    """Run the public-template contract audit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", help="emit the typed report as JSON")
    parser.add_argument("--strict", action="store_true", help="return non-zero when findings exist")
    args = parser.parse_args(argv)
    report = validate_public_template_contract(args.repo_root)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(format_public_template_contract(report))
    return 1 if args.strict and not report.passed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

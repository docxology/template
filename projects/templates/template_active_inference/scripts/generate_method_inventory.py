#!/usr/bin/env python3
"""Generate the method inventory documentation report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gates.method_inventory import (
    DEFAULT_OUTPUT,
    collect_method_entries,
    render_method_inventory_markdown,
    write_method_inventory,
)


def build_parser() -> argparse.ArgumentParser:
    """Return the CLI parser for method-inventory generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when docs/reference/method-inventory.md is stale without rewriting it.",
    )
    return parser


def main() -> int:
    """CLI entry point."""
    args = build_parser().parse_args()
    if args.check:
        destination = PROJECT_ROOT / DEFAULT_OUTPUT
        expected = render_method_inventory_markdown(collect_method_entries(PROJECT_ROOT))
        if not destination.is_file():
            print(f"method_inventory: missing {destination}", file=sys.stderr)
            return 1
        if destination.read_text(encoding="utf-8") != expected:
            print(f"method_inventory: stale {destination}", file=sys.stderr)
            return 1
        print(f"method_inventory: current {destination}")
        return 0

    path = write_method_inventory(PROJECT_ROOT)
    print(f"method_inventory: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

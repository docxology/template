#!/usr/bin/env python3
"""Merge pytest supplement files into a canonical test module."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.validation.test_supplements import merge_supplements  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("canonical", type=Path)
    parser.add_argument("supplements", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run the supplement merge orchestrator."""
    args = _parse_args()
    merge_supplements(args.canonical, args.supplements, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

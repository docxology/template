#!/usr/bin/env python3
"""Thin orchestrator — apply mechanical Python improvements to a source tree.

Wraps :mod:`infrastructure.core.source_improve`. The script itself
contains no business logic — it only parses arguments, dispatches to the
infrastructure function, and prints a summary.

Usage:
    uv run python scripts/batch_cogsec_improve.py <src_root_dir>
    uv run python scripts/batch_cogsec_improve.py --help
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so ``infrastructure`` imports cleanly
# when this file is run directly (``python scripts/batch_cogsec_improve.py``).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from infrastructure.core.source_improve import improve_tree  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Batch-apply mechanical Python improvements (add __future__ import, "
            "fix bare excepts, insert minimal module docstring) to a source tree."
        )
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Source-root directory to walk recursively (e.g. projects/<name>/src).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root: Path = args.root
    if not root.exists():
        print(f"Error: {root} not found", file=sys.stderr)
        return 1

    summary = improve_tree(root)

    print("=== BATCH IMPROVE SUMMARY ===")
    print(f"Root: {root}")
    print(f"Files scanned: {summary['files']}")
    print(f"Files modified: {summary['modified']}")
    print(f"  Added __future__: {summary['future']}")
    print(f"  Added docstrings: {summary['docstring']}")
    print(f"  Fixed bare excepts: {summary['except_']}")
    for err in summary["errors"]:
        print(f"ERROR in {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate the canonical source-safe redaction audit and release ledger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from redacted_report import ReleaseInputError, write_release_artifacts  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "example_segments.json",
        help="Typed release fixture JSON.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "output",
        help="Root containing reports/ and data/ artifact directories.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Load, audit, and serialize the declared release fixture."""
    args = build_parser().parse_args(argv)
    try:
        paths = write_release_artifacts(args.input, args.output_root)
    except (FileNotFoundError, ReleaseInputError, RuntimeError) as exc:
        print(f"release artifact generation failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "redaction_audit": paths.redaction_audit.as_posix(),
                "release_ledger": paths.release_ledger.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

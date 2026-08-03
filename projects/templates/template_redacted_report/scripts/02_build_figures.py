#!/usr/bin/env python3
"""Generate the deterministic redaction exemplar figures and registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from redacted_report import build_figures  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "output" / "figures",
        help="Directory for generated PNG/SVG figures and figure_registry.json.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Write both figures plus the registry and print the manifest."""
    args = build_parser().parse_args(argv)
    registry = build_figures(args.output_dir)
    print(
        json.dumps(
            {
                "figures": sorted(registry),
                "output_dir": args.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

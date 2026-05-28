#!/usr/bin/env python3
"""Opt-in belief-trajectory GIF extension (placeholder frames from SI figure)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a deterministic placeholder GIF for the animation extension track.",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Exit 0 without writing output (default pipeline path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.skip:
        print("render_animation.py: skipped (--skip)")
        return 0

    from visualizations.animation import write_belief_trajectory_gif

    try:
        out = write_belief_trajectory_gif(PROJECT_ROOT)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

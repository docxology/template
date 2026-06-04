#!/usr/bin/env python3
"""Render belief-trajectory GIF extension from trace artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a deterministic trace-derived GIF for the animation extension track.",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Exit 0 without writing output (manual dry-run path)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.skip:
        print("render_animation.py: skipped (--skip)")
        return 0

    from visualizations.animation import write_animation_frame_deltas, write_belief_trajectory_gif

    try:
        out = write_belief_trajectory_gif(PROJECT_ROOT)
        deltas = write_animation_frame_deltas(PROJECT_ROOT)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(out)
    print(deltas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

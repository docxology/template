#!/usr/bin/env python3
"""Opt-in belief-trajectory GIF extension (placeholder frames from SI figure)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def write_placeholder_gif(project_root: Path) -> Path:
    from PIL import Image

    root = project_root.resolve()
    source = root / "output" / "figures" / "si_belief_entropy_curve.png"
    if not source.is_file():
        raise FileNotFoundError(
            f"missing {source.relative_to(root)} — run generate_figures.py after simulate_si_tmaze.py"
        )
    out = root / "output" / "figures" / "si_belief_trajectory.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    frame = Image.open(source).convert("RGBA")
    frame.save(
        out,
        save_all=True,
        append_images=[frame.copy()],
        duration=500,
        loop=0,
    )
    return out


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.skip:
        print("render_animation.py: skipped (--skip)")
        return 0
    try:
        out = write_placeholder_gif(PROJECT_ROOT)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

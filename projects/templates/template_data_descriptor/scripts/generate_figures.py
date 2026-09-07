#!/usr/bin/env python3
"""Thin entry point for the source-owned descriptor figure pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(PROJECT_ROOT / "src"), str(PROJECT_ROOT.parents[2])]

import data_descriptor as dd  # noqa: E402


def generate_figures(project_root: Path | None = None) -> list[Path]:
    """Render the canonical figures through the reusable source API."""
    run = dd.render_descriptor_figures(project_root or PROJECT_ROOT)
    return list(run.rendered_paths)


def main(project_root: Path | None = None) -> list[Path]:
    """Render, publish, and report the complete figure asset set."""
    written = list(dd.generate_descriptor_figure_assets(project_root or PROJECT_ROOT))
    print("\n".join(str(path) for path in written))
    return written


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Figure generation orchestrator (thin wrapper)."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

bootstrap_project(include_infrastructure=True)

from config import DATA_DIR as DEFAULT_DATA_DIR, DEFAULT_DPI, FIGURES_DIR as DEFAULT_FIGURES_DIR
from visualization.figure_runner import generate_all_figures


def parse_args() -> argparse.Namespace:
    """Parse args."""
    parser = argparse.ArgumentParser(description="Generate all figures for the literature meta-analysis.")
    parser.add_argument("--input-dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_FIGURES_DIR))
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    generate_all_figures(args)


if __name__ == "__main__":
    main()

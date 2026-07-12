"""Thin orchestrator: run the worked models and emit a small data artifact.

Demonstrates the thin-orchestrator rule — all maths comes from
``textbook.models``; this script only orchestrates I/O. Writes a JSON summary to
``<project_root>/output/data/`` and prints the path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT as PROJECT_DIR, ensure_project_paths

ensure_project_paths()


def main() -> int:
    """CLI entry point."""
    from textbook.analysis import build_worked_model_summary
    from textbook_io import write_text_atomic
    from textbook_logging import get_logger

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Compute worked-model summary data")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "output" / "data")
    args = parser.parse_args()

    summary = build_worked_model_summary(PROJECT_DIR / "manuscript" / "assets" / "data" / "sample_dataset.csv")
    out_path = args.output_dir / "worked_model_summary.json"
    write_text_atomic(out_path, json.dumps(summary, indent=2, sort_keys=True))
    logger.info("wrote %s", out_path)
    print(f"  ✓ {out_path}")
    print(f"[analysis] worked-model summary → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

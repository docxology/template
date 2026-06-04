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
    import numpy as np

    from textbook import models
    from textbook_io import write_text_atomic
    from textbook_logging import get_logger

    logger = get_logger(__name__)
    parser = argparse.ArgumentParser(description="Compute worked-model summary data")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "output" / "data")
    args = parser.parse_args()

    t = np.linspace(0, 10, 11)
    growth = models.logistic_growth(t, r=0.8, carrying_capacity=100.0, initial=5.0)
    decay = models.exponential_decay(t, initial=100.0, rate=0.5)
    summary = {
        "logistic_growth": {
            "t": t.tolist(),
            "N": growth.tolist(),
            "stats": models.descriptive_statistics(growth),
        },
        "exponential_decay": {
            "t": t.tolist(),
            "y": decay.tolist(),
            "half_life": models.half_life(0.5),
        },
    }
    out_path = args.output_dir / "worked_model_summary.json"
    write_text_atomic(out_path, json.dumps(summary, indent=2, sort_keys=True))
    logger.info("wrote %s", out_path)
    print(f"  ✓ {out_path}")
    print(f"[analysis] worked-model summary → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

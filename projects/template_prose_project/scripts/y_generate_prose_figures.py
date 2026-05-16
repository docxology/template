#!/usr/bin/env python3
"""Generate figures from a completed prose-pipeline run.

Reads ``output/manuscript_report.json`` and emits three PNGs into
``output/figures/``.

Exit codes:
    0   figures written
    2   no manuscript report present — graceful skip
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
_repo_root = _project_root.parent.parent
sys.path.insert(0, str(_project_root))
sys.path.insert(0, str(_project_root / "src"))
sys.path.insert(0, str(_repo_root))

from infrastructure.core.logging.utils import get_logger

from src.figures import generate_all_figures, load_manuscript_report

logger = get_logger(__name__)


def main() -> int:
    report_path = _project_root / "output" / "manuscript_report.json"
    if not report_path.exists():
        logger.warning("No %s; run run_prose_pipeline.py first.", report_path)
        return 2
    report = load_manuscript_report(report_path)
    figures_dir = _project_root / "output" / "figures"
    paths = generate_all_figures(report, figures_dir)
    for p in paths:
        print(str(p))
    logger.info("Wrote %d figure(s)", len(paths))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

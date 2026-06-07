#!/usr/bin/env python3
"""Generate figures from a completed prose-pipeline run.

Reads ``<project_root>/output/manuscript_report.json`` and emits three
PNGs into ``<project_root>/output/figures/``.

Exit codes:
    0   figures written
    2   no manuscript report present — graceful skip
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_PROJECT_ROOT = _SCRIPT_DIR.parent
# Project lives at projects/templates/<name>/; repo root is three levels up.
_REPO_ROOT = _DEFAULT_PROJECT_ROOT.parents[2]

sys.path.insert(0, str(_DEFAULT_PROJECT_ROOT))
sys.path.insert(0, str(_DEFAULT_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT))

from infrastructure.core.logging.utils import get_logger  # noqa: E402

from infrastructure.prose.report import load_report_json  # noqa: E402

from src.figures import generate_all_figures  # noqa: E402

logger = get_logger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=_DEFAULT_PROJECT_ROOT,
        help="Project root directory (default: the bundled template_prose_project).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    project_root: Path = args.project_root.resolve()
    report_path = project_root / "output" / "manuscript_report.json"
    if not report_path.exists():
        logger.warning("No %s; run run_prose_pipeline.py first.", report_path)
        return 2
    report = load_report_json(report_path)
    figures_dir = project_root / "output" / "figures"
    paths = generate_all_figures(report, figures_dir)
    for p in paths:
        print(str(p))
    logger.info("Wrote %d figure(s)", len(paths))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

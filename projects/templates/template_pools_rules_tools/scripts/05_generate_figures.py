#!/usr/bin/env python3
"""05_generate_figures.py — Render all manuscript figures + cover art.

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/05_generate_figures.py
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import sys

_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))

from src.figures import all_figures
from src.integration import derive_dashboard_data, run_integration_demo

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_FIGURES_DIR = _PROJECT_DIR / "manuscript" / "figures"
_OUTPUT_FIGURES_DIR = _PROJECT_DIR / "output" / "figures"


def main() -> int:
    """CLI entry point."""
    results = run_integration_demo()
    counts, statuses = derive_dashboard_data(results)
    figures = all_figures(
        output_dir=_FIGURES_DIR,
        integration_result=results,
        counts=counts,
        statuses=statuses,
    )

    if figures is None:
        logger.warning("matplotlib unavailable — no figures generated")
        return 0

    # manuscript/figures/ is the git-tracked canonical location (resolved by
    # the combined-PDF render via its manuscript-dir resource path). Mirror a
    # disposable copy to output/figures/ too, since the Beamer slide renderer
    # (infrastructure/rendering/slides_renderer.py) hard-codes that location
    # when rewriting \includegraphics paths for per-section slide decks.
    _OUTPUT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, path in figures.items():
        print(f"{name}: {path}")
        if path is not None:
            shutil.copy2(path, _OUTPUT_FIGURES_DIR / path.name)

    return 0


if __name__ == "__main__":
    sys.exit(main())

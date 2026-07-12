#!/usr/bin/env python3
"""05_generate_figures.py — Render all manuscript figures + cover art.

Run from the repository root:
    uv run python projects/templates/template_pools_rules_tools/scripts/05_generate_figures.py
"""

from __future__ import annotations

import logging
import pathlib
import sys

_PROJECT_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR.parents[2]))

from infrastructure.documentation.generated_figure_registry import (  # noqa: E402
    publish_generated_figures,
)

from src.figures import FIGURE_REGISTRY_SCHEMA, INTEGRATION_FIGURE_SPECS, all_figures  # noqa: E402
from src.integration import derive_dashboard_data, run_integration_demo  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

_FIGURES_DIR = _PROJECT_DIR / "manuscript" / "figures"
_OUTPUT_FIGURES_DIR = _PROJECT_DIR / "output" / "figures"


def publish_output_figures(
    figures: dict[str, pathlib.Path | None],
    output_figures_dir: pathlib.Path,
) -> list[pathlib.Path]:
    """Mirror a complete generated set and write its deterministic registry."""
    return publish_generated_figures(
        output_figures_dir,
        INTEGRATION_FIGURE_SPECS,
        [path for path in figures.values() if path is not None],
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )


def generate_assets(
    figures_dir: pathlib.Path = _FIGURES_DIR,
    output_figures_dir: pathlib.Path = _OUTPUT_FIGURES_DIR,
) -> list[pathlib.Path]:
    """Run the real integration figure pipeline and publish its artifacts."""
    results = run_integration_demo()
    counts, statuses = derive_dashboard_data(results)
    figures = all_figures(
        output_dir=figures_dir,
        integration_result=results,
        counts=counts,
        statuses=statuses,
    )

    if figures is None:
        raise RuntimeError("matplotlib unavailable — required figures were not generated")

    published = publish_output_figures(figures, output_figures_dir)
    return [*(path for path in figures.values() if path is not None), *published]


def main() -> int:
    """CLI entry point."""
    written = generate_assets()

    # manuscript/figures/ is the git-tracked canonical location (resolved by
    # the combined-PDF render via its manuscript-dir resource path). Mirror a
    # disposable copy to output/figures/ too, since the Beamer slide renderer
    # (infrastructure/rendering/slides_renderer.py) hard-codes that location
    # when rewriting \includegraphics paths for per-section slide decks.
    for path in written:
        print(path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

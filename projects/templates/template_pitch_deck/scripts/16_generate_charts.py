#!/usr/bin/env python3
"""Stage-02 analysis: render real matplotlib charts from live repo data.

Companion to ``15_generate_diagrams.py`` (Mermaid flowcharts) — this script
covers three different data-driven chart families, deliberately varied so
the deck doesn't repeat one visual language for every figure: a coverage bar
chart, a test-count-vs-coverage scatter, and an infrastructure/ subpackage
donut. All three fetch real data (`coverage_chart_data`, `infra_facts`) and
delegate the actual plotting to `src/chart_rendering.py` — this script only
coordinates fetch → render → save, per the thin-orchestrator rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import get_logger, project_root, setup_paths  # noqa: E402

setup_paths()
logger = get_logger("pitch_deck.charts")


def main(argv: list[str] | None = None) -> int:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from chart_rendering import (
        render_coverage_bar_chart,
        render_infra_subpackage_donut,
        render_test_count_vs_coverage_scatter,
    )
    from coverage_chart_data import read_all_exemplar_coverage
    from infra_facts import infra_subpackage_python_counts
    from paths import locate_repo_root
    from render_orchestration import _resolve_theme, load_deck_config

    root = project_root()
    repo_root = locate_repo_root(root)
    theme = _resolve_theme(load_deck_config(root))
    figures_dir = root / "output" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    coverage_rows = read_all_exemplar_coverage(repo_root)
    coverage_path = figures_dir / "coverage_by_exemplar.png"
    n_exemplars = render_coverage_bar_chart(plt, theme, coverage_rows, coverage_path)
    logger.info("Wrote chart: %s (%d exemplars)", coverage_path, n_exemplars)
    print(coverage_path)

    scatter_path = figures_dir / "test_count_vs_coverage.png"
    n_points = render_test_count_vs_coverage_scatter(plt, theme, coverage_rows, scatter_path)
    logger.info("Wrote chart: %s (%d points)", scatter_path, n_points)
    print(scatter_path)

    infra_rows = infra_subpackage_python_counts(repo_root)
    donut_path = figures_dir / "infra_subpackage_sizes.png"
    n_subpackages = render_infra_subpackage_donut(plt, theme, infra_rows, donut_path)
    logger.info("Wrote chart: %s (%d subpackages)", donut_path, n_subpackages)
    print(donut_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

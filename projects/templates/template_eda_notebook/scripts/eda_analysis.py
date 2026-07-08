#!/usr/bin/env python3
"""Thin orchestrator: run the EDA and emit figures + a summary table.

Follows the thin-orchestrator contract: all computation lives in ``src.eda``;
this script only loads data, calls the tested library, draws figures with a
headless matplotlib backend, writes a summary CSV, and prints every output path
to stdout for manifest collection. It contains no business logic.

Run from the monorepo root::

    uv run python projects/templates/template_eda_notebook/scripts/eda_analysis.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Headless backend MUST be set before importing pyplot.
os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

import matplotlib.pyplot as plt  # noqa: E402

from src.eda import (  # noqa: E402
    clean_dataset,
    correlation_heatmap_data,
    group_count_data,
    histogram_data,
    load_dataset,
    summary_statistics,
)
from src.project_paths import project_output_dirs  # noqa: E402


def run_eda(project_root: Path | None = None) -> list[Path]:
    """Execute the EDA pipeline and return the list of written output paths.

    Args:
        project_root: Optional project root override (used by tests with a
            temporary directory). Defaults to the real project root.

    Returns:
        Paths to every artifact written (figures + summary CSV).
    """
    dirs = project_output_dirs(project_root)
    figures_dir = dirs["figures"]
    data_dir = dirs["data"]
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    cleaned, _report = clean_dataset(load_dataset())
    written: list[Path] = []

    # 1. Histogram of the first numeric feature.
    hist = histogram_data(cleaned, "height_cm", bins=10)
    fig, ax = plt.subplots()
    ax.bar(hist.edges[:-1], hist.counts, width=[b - a for a, b in zip(hist.edges, hist.edges[1:])], align="edge")
    ax.set_title("Height distribution")
    ax.set_xlabel("height_cm")
    ax.set_ylabel("count")
    hist_path = figures_dir / "height_histogram.png"
    fig.savefig(hist_path, dpi=120)
    plt.close(fig)
    written.append(hist_path)

    # 2. Correlation heatmap.
    heat = correlation_heatmap_data(cleaned)
    fig, ax = plt.subplots()
    ax.imshow(heat.values, vmin=-1.0, vmax=1.0, cmap="coolwarm")
    ax.set_xticks(range(len(heat.labels)), heat.labels, rotation=45, ha="right")
    ax.set_yticks(range(len(heat.labels)), heat.labels)
    ax.set_title("Feature correlation")
    heat_path = figures_dir / "correlation_heatmap.png"
    fig.savefig(heat_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    written.append(heat_path)

    # 3. Group counts.
    groups = group_count_data(cleaned)
    fig, ax = plt.subplots()
    ax.bar(groups.labels, groups.counts)
    ax.set_title("Rows per group")
    group_path = figures_dir / "group_counts.png"
    fig.savefig(group_path, dpi=120)
    plt.close(fig)
    written.append(group_path)

    # 4. Summary statistics table as CSV.
    summary_path = data_dir / "summary_statistics.csv"
    lines = ["column,count,mean,std,minimum,median,maximum"]
    for stat in summary_statistics(cleaned):
        lines.append(
            f"{stat.column},{stat.count},{stat.mean:.6f},{stat.std:.6f},"
            f"{stat.minimum:.6f},{stat.median:.6f},{stat.maximum:.6f}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(summary_path)

    return written


def main() -> None:
    """CLI entry point."""
    for path in run_eda():
        print(path)


if __name__ == "__main__":
    main()

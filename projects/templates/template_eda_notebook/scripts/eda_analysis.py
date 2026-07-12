#!/usr/bin/env python3
"""Run tested EDA preparers and emit figures, summary data, and provenance."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for _path in (PROJECT_ROOT, PROJECT_ROOT / "src", PROJECT_ROOT.parents[2]):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)

import matplotlib.pyplot as plt  # noqa: E402

from infrastructure.documentation.generated_figure_registry import (  # noqa: E402
    write_generated_figure_registry,
)
from src.eda import (  # noqa: E402
    CORRELATION_COLOR_LIMITS,
    EDA_FIGURE_SPECS,
    FIGURE_REGISTRY_SCHEMA,
    clean_dataset,
    correlation_heatmap_data,
    eda_figure_spec,
    group_count_data,
    histogram_data,
    load_dataset,
    summary_statistics,
)
from src.project_paths import project_output_dirs  # noqa: E402


def run_eda(project_root: Path | None = None) -> list[Path]:
    """Execute the EDA pipeline, optionally against an isolated project root."""
    dirs = project_output_dirs(project_root)
    figures_dir = dirs["figures"]
    data_dir = dirs["data"]
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    cleaned, _report = clean_dataset(load_dataset())
    written: list[Path] = []

    hist = histogram_data(cleaned, "height_cm", bins=10)
    fig, ax = plt.subplots()
    ax.bar(hist.edges[:-1], hist.counts, width=[b - a for a, b in zip(hist.edges, hist.edges[1:])], align="edge")
    ax.set_title("Height distribution")
    ax.set_xlabel("height_cm")
    ax.set_ylabel("count")
    hist_path = figures_dir / eda_figure_spec("fig:height_histogram").filename
    fig.savefig(hist_path, dpi=120)
    plt.close(fig)
    written.append(hist_path)

    heat = correlation_heatmap_data(cleaned)
    fig, ax = plt.subplots()
    ax.imshow(
        heat.values,
        vmin=CORRELATION_COLOR_LIMITS[0],
        vmax=CORRELATION_COLOR_LIMITS[1],
        cmap="coolwarm",
    )
    ax.set_xticks(range(len(heat.labels)), heat.labels, rotation=45, ha="right")
    ax.set_yticks(range(len(heat.labels)), heat.labels)
    ax.set_title("Feature correlation")
    heat_path = figures_dir / eda_figure_spec("fig:correlation_heatmap").filename
    fig.savefig(heat_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    written.append(heat_path)

    groups = group_count_data(cleaned)
    fig, ax = plt.subplots()
    ax.bar(groups.labels, groups.counts)
    ax.set_title("Rows per group")
    group_path = figures_dir / eda_figure_spec("fig:group_counts").filename
    fig.savefig(group_path, dpi=120)
    plt.close(fig)
    written.append(group_path)

    summary_path = data_dir / "summary_statistics.csv"
    lines = ["column,count,mean,std,minimum,median,maximum"]
    for stat in summary_statistics(cleaned):
        lines.append(
            f"{stat.column},{stat.count},{stat.mean:.6f},{stat.std:.6f},"
            f"{stat.minimum:.6f},{stat.median:.6f},{stat.maximum:.6f}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(summary_path)

    registry_path = write_generated_figure_registry(
        figures_dir / "figure_registry.json",
        EDA_FIGURE_SPECS,
        [hist_path, heat_path, group_path],
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )
    written.append(registry_path)

    return written


def main() -> None:
    """CLI entry point."""
    for path in run_eda():
        print(path)


if __name__ == "__main__":
    main()

"""Line plot of SIA metric progression."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..generation_records import generation_metrics, load_run_summary
from ..loop_config import load_sia_settings
from .figure_registry import FIGURE_SPECS, figure_path


def write_sia_metric_progression(project_root: Path) -> Path:
    """Plot accuracy (or primary metric) vs generation index."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    metrics = generation_metrics(summary)
    spec = FIGURE_SPECS[0]
    out = figure_path(project_root, spec)
    out.parent.mkdir(parents=True, exist_ok=True)

    generations = [int(row["generation"]) for row in metrics]
    values = [float(row["metric_value"]) for row in metrics if row.get("metric_value") is not None]
    metric_name = metrics[0].get("metric_name", "metric") if metrics else "metric"

    fig, axis = plt.subplots(figsize=(5.0, 3.2))
    axis.plot(generations[: len(values)], values, marker="o", color="#0f766e")
    axis.set_xlabel("Generation")
    axis.set_ylabel(str(metric_name))
    axis.set_title("SIA metric progression")
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return out


__all__ = ["write_sia_metric_progression"]

"""Dashboard chart helpers — pipeline duration charts."""

from __future__ import annotations

from typing import Any

try:
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    Axes = Any  # type: ignore[misc, assignment]
    Figure = Any  # type: ignore[misc, assignment]

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import (
    ProjectMetrics,
)

logger = get_logger(__name__)


def draw_pipeline_duration_on_axes(
    ax: Axes,
    projects: list[ProjectMetrics],
    *,
    stacked: bool = True,
    title: str = "Pipeline Duration by Project",
) -> None:
    """Plot pipeline duration on ``ax``."""
    project_names = [p.name for p in projects]
    durations = [p.pipeline.total_duration for p in projects]
    x = range(len(projects))

    if stacked:
        bottleneck_durations = [p.pipeline.bottleneck_duration for p in projects]
        other_durations = [d - b for d, b in zip(durations, bottleneck_durations, strict=True)]
        ax.bar(x, other_durations, label="Other Stages", color=COLORS["secondary"])
        ax.bar(
            x,
            bottleneck_durations,
            bottom=other_durations,
            label="Bottleneck Stage",
            color=COLORS["danger"],
        )
        ax.legend()
    else:
        ax.bar(x, durations, color=COLORS["warning"], alpha=0.8)

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Duration (seconds)", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)
    if durations:
        max_d = max(durations)
        for i, duration in enumerate(durations):
            ax.text(i, duration + max_d * 0.02, f"{duration:.0f}s", ha="center", fontweight="bold")


def create_pipeline_duration_chart(
    projects: list[ProjectMetrics],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create chart showing pipeline durations by project."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_pipeline_duration_on_axes(ax, projects, stacked=True)
        ax.set_title("Pipeline Duration by Project", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_pipeline_duration_on_axes(
        ax,
        projects,
        stacked=False,
        title="Pipeline Execution Time",
    )
    return None


def create_performance_timeline_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create timeline chart showing performance trends.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    project_names = [p.name for p in projects]

    # Pipeline duration comparison
    durations = [p.pipeline.total_duration for p in projects]
    bars = ax1.bar(range(len(projects)), durations, color=COLORS["primary"], alpha=0.7)
    ax1.set_xlabel("Project", fontweight="bold")
    ax1.set_ylabel("Duration (seconds)", fontweight="bold")
    ax1.set_title("Pipeline Execution Time", fontweight="bold")
    ax1.set_xticks(range(len(projects)))
    ax1.set_xticklabels(project_names, rotation=45, ha="right")
    ax1.grid(True, alpha=0.3, axis="y")

    # Add duration labels
    for bar, duration in zip(bars, durations):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + max(durations) * 0.02,
            f"{duration:.0f}s",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # Test execution time vs coverage
    test_times = [p.tests.execution_time for p in projects]
    coverages = [p.tests.coverage_percent for p in projects]

    ax2.scatter(test_times, coverages, s=100, c=range(len(projects)), cmap="viridis", alpha=0.7)
    for i, name in enumerate(project_names):
        ax2.annotate(
            name,
            (test_times[i], coverages[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    ax2.set_xlabel("Test Execution Time (s)", fontweight="bold")
    ax2.set_ylabel("Test Coverage (%)", fontweight="bold")
    ax2.set_title("Test Efficiency: Coverage vs Time", fontweight="bold")
    ax2.grid(True, alpha=0.3)

    # Output generation performance
    pdf_sizes = [p.outputs.pdf_size_mb for p in projects]
    pdf_counts = [p.outputs.pdf_files for p in projects]

    ax3.scatter(pdf_counts, pdf_sizes, color=COLORS["success"], s=100, alpha=0.7)
    for i, name in enumerate(project_names):
        ax3.annotate(
            name,
            (pdf_counts[i], pdf_sizes[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    ax3.set_xlabel("Number of PDFs", fontweight="bold")
    ax3.set_ylabel("Total PDF Size (MB)", fontweight="bold")
    ax3.set_title("Output Volume vs Size", fontweight="bold")
    ax3.grid(True, alpha=0.3)

    # Performance efficiency (output per time)
    if durations and pdf_counts:
        efficiency = [count / duration if duration > 0 else 0 for count, duration in zip(pdf_counts, durations)]

        bars = ax4.bar(range(len(projects)), efficiency, color=COLORS["warning"], alpha=0.7)
        ax4.set_xlabel("Project", fontweight="bold")
        ax4.set_ylabel("PDFs per Second", fontweight="bold")
        ax4.set_title("Pipeline Efficiency", fontweight="bold")
        ax4.set_xticks(range(len(projects)))
        ax4.set_xticklabels(project_names, rotation=45, ha="right")
        ax4.grid(True, alpha=0.3, axis="y")

        # Add efficiency labels
        for bar, eff in zip(bars, efficiency):
            height = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(efficiency) * 0.02,
                f"{eff:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    fig.suptitle("Performance Analysis Dashboard", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout()
    return fig

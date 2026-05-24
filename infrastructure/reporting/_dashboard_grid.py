"""Multi-panel dashboard grid composition for executive reporting."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from infrastructure.reporting._dashboard_charts import (
    draw_coverage_on_axes,
    draw_executive_summary_on_axes,
    draw_manuscript_complexity_scatter_on_axes,
    draw_output_distribution_on_axes,
    draw_pipeline_duration_on_axes,
    draw_test_count_on_axes,
)
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    calculate_project_health_score,
)

PanelBuilder = Callable[[Axes], None]


def compose_grid(
    panel_builders: Sequence[PanelBuilder],
    rows: int,
    cols: int,
    *,
    figsize: tuple[float, float] = (20, 16),
) -> Figure:
    """Lay out panel plotters on a fixed rows×cols grid."""
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    flat_axes = axes.flatten() if hasattr(axes, "flatten") else [axes]
    for ax, builder in zip(flat_axes, panel_builders, strict=False):
        builder(ax)
    for ax in flat_axes[len(panel_builders) :]:
        ax.axis("off")
    return fig


def _plot_efficiency_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    x = range(len(projects))
    durations = [p.pipeline.total_duration for p in projects]
    pdf_counts = [p.outputs.pdf_files for p in projects]
    efficiency = [
        count / duration if duration > 0 else 0 for count, duration in zip(pdf_counts, durations, strict=True)
    ]
    ax.bar(x, efficiency, color=COLORS["success"], alpha=0.8)
    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("PDFs per Second", fontweight="bold")
    ax.set_title("Pipeline Efficiency", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)
    if efficiency:
        max_eff = max(efficiency)
        for i, eff in enumerate(efficiency):
            ax.text(
                i,
                eff + max_eff * 0.02 if max_eff else 0.02,
                f"{eff:.2f}",
                ha="center",
                fontweight="bold",
            )


def _plot_health_scores_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    x = range(len(projects))
    health_scores = [calculate_project_health_score(p)["percentage"] for p in projects]
    ax.bar(x, health_scores, color=COLORS["primary"], alpha=0.8)
    ax.axhline(y=85, color=COLORS["success"], linestyle="--", linewidth=2, label="Excellent (85%)")
    ax.axhline(y=70, color=COLORS["warning"], linestyle="--", linewidth=2, label="Good (70%)")
    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Health Score (%)", fontweight="bold")
    ax.set_title("Project Health Scores", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    for i, score in enumerate(health_scores):
        ax.text(i, score + 1, f"{score:.0f}%", ha="center", fontweight="bold")


def _plot_test_efficiency_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    test_times = [p.tests.execution_time for p in projects]
    coverages = [p.tests.coverage_percent for p in projects]
    ax.scatter(test_times, coverages, s=100, c=range(len(projects)), cmap="viridis", alpha=0.8)
    for i, name in enumerate(project_names):
        ax.annotate(
            name,
            (test_times[i], coverages[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xlabel("Test Time (s)", fontweight="bold")
    ax.set_ylabel("Coverage (%)", fontweight="bold")
    ax.set_title("Test Efficiency Matrix", fontweight="bold")
    ax.grid(True, alpha=0.3)


def build_dashboard_panel_builders(summary: ExecutiveSummary) -> list[PanelBuilder]:
    """Return the nine panel plotters for the executive dashboard grid."""
    projects = summary.project_metrics
    outputs = summary.aggregate_metrics.get("outputs", {})
    return [
        lambda ax: draw_test_count_on_axes(ax, projects, include_failed=False, title="Test Results by Project"),
        lambda ax: draw_coverage_on_axes(ax, projects, compact=True),
        lambda ax: draw_pipeline_duration_on_axes(ax, projects, stacked=False, title="Pipeline Execution Time"),
        lambda ax: draw_manuscript_complexity_scatter_on_axes(ax, projects),
        lambda ax: draw_output_distribution_on_axes(ax, outputs),
        lambda ax: _plot_efficiency_panel(ax, projects),
        lambda ax: _plot_health_scores_panel(ax, projects),
        lambda ax: _plot_test_efficiency_panel(ax, projects),
        lambda ax: draw_executive_summary_on_axes(ax, summary),
    ]


def compose_executive_dashboard(summary: ExecutiveSummary) -> Figure:
    """Build the 3×3 executive dashboard figure."""
    return compose_grid(build_dashboard_panel_builders(summary), rows=3, cols=3)

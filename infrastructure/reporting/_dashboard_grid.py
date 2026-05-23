"""Multi-panel dashboard grid composition for executive reporting."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

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


def _plot_test_results_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    x = range(len(projects))
    width = 0.25
    ax.bar(
        [i - width for i in x],
        [p.tests.total_tests for p in projects],
        width,
        label="Total",
        color=COLORS["primary"],
        alpha=0.8,
    )
    ax.bar(
        x,
        [p.tests.passed for p in projects],
        width,
        label="Passed",
        color=COLORS["success"],
        alpha=0.8,
    )
    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Test Count", fontweight="bold")
    ax.set_title("Test Results by Project", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def _plot_coverage_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    x = range(len(projects))
    coverage = [p.tests.coverage_percent for p in projects]
    ax.bar(x, coverage, color=COLORS["primary"], alpha=0.8)
    ax.axhline(y=90, color=COLORS["success"], linestyle="--", linewidth=2, label="Excellent (90%)")
    ax.axhline(y=70, color=COLORS["warning"], linestyle="--", linewidth=2, label="Adequate (70%)")
    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Coverage (%)", fontweight="bold")
    ax.set_title("Test Coverage by Project", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def _plot_pipeline_duration_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    x = range(len(projects))
    durations = [p.pipeline.total_duration for p in projects]
    ax.bar(x, durations, color=COLORS["warning"], alpha=0.8)
    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Duration (seconds)", fontweight="bold")
    ax.set_title("Pipeline Execution Time", fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)
    if durations:
        max_d = max(durations)
        for i, duration in enumerate(durations):
            ax.text(i, duration + max_d * 0.02, f"{duration:.0f}s", ha="center", fontweight="bold")


def _plot_manuscript_complexity_panel(ax: Axes, projects: list[ProjectMetrics]) -> None:
    project_names = [p.name for p in projects]
    word_counts = [p.manuscript.total_words for p in projects]
    equations = [p.manuscript.equations for p in projects]
    ax.scatter(word_counts, equations, s=100, c=range(len(projects)), cmap="viridis", alpha=0.8)
    for i, name in enumerate(project_names):
        ax.annotate(
            name,
            (word_counts[i], equations[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xlabel("Word Count", fontweight="bold")
    ax.set_ylabel("Equations", fontweight="bold")
    ax.set_title("Manuscript Complexity", fontweight="bold")
    ax.grid(True, alpha=0.3)


def _plot_output_distribution_panel(ax: Axes, outputs: dict[str, Any]) -> None:
    labels = ["PDFs", "Figures", "Slides", "Web"]
    sizes = [
        outputs.get("total_pdfs", 0),
        outputs.get("total_figures", 0),
        outputs.get("total_slides", 0),
        outputs.get("total_web", 0),
    ]
    colors = [COLORS["primary"], COLORS["success"], COLORS["warning"], COLORS["secondary"]]
    filtered_labels: list[str] = []
    filtered_sizes: list[int] = []
    filtered_colors: list[str] = []
    for label, size, color in zip(labels, sizes, colors, strict=True):
        if size > 0:
            filtered_labels.append(label)
            filtered_sizes.append(size)
            filtered_colors.append(color)
    if filtered_sizes:
        ax.pie(
            filtered_sizes,
            labels=filtered_labels,
            colors=filtered_colors,
            autopct="%1.1f%%",
            startangle=90,
            textprops={"fontweight": "bold"},
        )
        ax.set_title("Output File Distribution", fontweight="bold")
    else:
        ax.text(
            0.5,
            0.5,
            "No outputs\ngenerated",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12,
            fontweight="bold",
        )


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


def _plot_executive_summary_table(ax: Axes, summary: ExecutiveSummary) -> None:
    ax.axis("off")
    headers = ["Project", "Health", "Words", "Tests", "Coverage"]
    rows: list[list[str]] = []
    for p in summary.project_metrics:
        health = calculate_project_health_score(p)
        rows.append(
            [
                p.name,
                f"{health['percentage']:.0f}%",
                f"{p.manuscript.total_words:,}",
                str(p.tests.total_tests),
                f"{p.tests.coverage_percent:.1f}%",
            ]
        )
    agg = summary.aggregate_metrics
    manuscript_agg = agg.get("manuscript", {})
    tests_agg = agg.get("tests", {})
    words_stats = manuscript_agg.get("words_stats", {})
    coverage_stats = tests_agg.get("coverage_stats", {})
    rows.append(
        [
            "**TOTAL**",
            "**N/A**",
            f"**{manuscript_agg.get('total_words', 0):,}**\n({words_stats.get('mean', 0):,.0f} avg)",
            f"**{tests_agg.get('total_tests', 0)}**",
            f"**{tests_agg.get('average_coverage', 0):.1f}%**\n({coverage_stats.get('mean', 0):.1f} avg)",
        ]
    )
    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.8)
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor(COLORS["primary"])
        cell.set_text_props(weight="bold", color="white")
    for i in range(len(headers)):
        cell = table[(len(rows), i)]
        cell.set_facecolor(COLORS["light"])
        cell.set_text_props(weight="bold")
    ax.set_title("Executive Summary", fontweight="bold", fontsize=12, pad=20)


def build_dashboard_panel_builders(summary: ExecutiveSummary) -> list[PanelBuilder]:
    """Return the nine panel plotters for the executive dashboard grid."""
    projects = summary.project_metrics
    outputs = summary.aggregate_metrics.get("outputs", {})
    return [
        lambda ax: _plot_test_results_panel(ax, projects),
        lambda ax: _plot_coverage_panel(ax, projects),
        lambda ax: _plot_pipeline_duration_panel(ax, projects),
        lambda ax: _plot_manuscript_complexity_panel(ax, projects),
        lambda ax: _plot_output_distribution_panel(ax, outputs),
        lambda ax: _plot_efficiency_panel(ax, projects),
        lambda ax: _plot_health_scores_panel(ax, projects),
        lambda ax: _plot_test_efficiency_panel(ax, projects),
        lambda ax: _plot_executive_summary_table(ax, summary),
    ]


def compose_executive_dashboard(summary: ExecutiveSummary) -> Figure:
    """Build the 3×3 executive dashboard figure."""
    return compose_grid(build_dashboard_panel_builders(summary), rows=3, cols=3)

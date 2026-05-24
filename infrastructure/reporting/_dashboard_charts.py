"""Base chart generators and multi-panel dashboard for executive reporting.

Extracted from ``_dashboard_matplotlib.py`` — standalone chart functions
(test counts, coverage, pipeline duration, output distribution, manuscript
size/complexity, performance timeline, summary table) plus the multi-panel
``generate_matplotlib_dashboard()`` generator.
"""

from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    Axes = Any  # type: ignore[misc, assignment]

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import (
    ExecutiveSummary,
    ProjectMetrics,
    calculate_project_health_score,
)
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)


def draw_test_count_on_axes(
    ax: Axes,
    projects: list[ProjectMetrics],
    *,
    include_failed: bool = True,
    title: str = "Test Counts by Project",
) -> None:
    """Plot test count bars on ``ax``."""
    project_names = [p.name for p in projects]
    total_tests = [p.tests.total_tests for p in projects]
    passed_tests = [p.tests.passed for p in projects]
    failed_tests = [p.tests.failed for p in projects]
    x = range(len(projects))
    width = 0.25

    ax.bar(
        [i - width for i in x],
        total_tests,
        width,
        label="Total",
        color=COLORS["primary"],
        alpha=0.8,
    )
    ax.bar(x, passed_tests, width, label="Passed", color=COLORS["success"], alpha=0.8)
    if include_failed:
        ax.bar(
            [i + width for i in x],
            failed_tests,
            width,
            label="Failed",
            color=COLORS["danger"],
            alpha=0.8,
        )

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Test Count", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


def draw_coverage_on_axes(
    ax: Axes,
    projects: list[ProjectMetrics],
    *,
    title: str = "Test Coverage by Project",
    compact: bool = False,
) -> None:
    """Plot coverage bars on ``ax``."""
    project_names = [p.name for p in projects]
    coverage = [p.tests.coverage_percent for p in projects]
    x = range(len(projects))

    if compact:
        ax.bar(x, coverage, color=COLORS["primary"], alpha=0.8)
        ax.axhline(y=90, color=COLORS["success"], linestyle="--", linewidth=2, label="Excellent (90%)")
        ax.axhline(y=70, color=COLORS["warning"], linestyle="--", linewidth=2, label="Adequate (70%)")
    else:
        colors = []
        for cov in coverage:
            if cov >= 95:
                colors.append(COLORS["success"])
            elif cov >= 90:
                colors.append(COLORS["warning"])
            else:
                colors.append(COLORS["danger"])
        ax.bar(x, coverage, color=colors)
        ax.axhline(y=90, color=COLORS["danger"], linestyle="--", linewidth=2, label="90% Threshold")
        for i, cov in enumerate(coverage):
            ax.text(i, cov + 1, f"{cov:.1f}%", ha="center", fontweight="bold")

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Coverage (%)", fontweight="bold")
    ax.set_title(title, fontweight="bold")
    ax.set_xticks(list(x))
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)


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


def draw_output_distribution_on_axes(ax: Axes, outputs: dict[str, Any]) -> None:
    """Plot output file distribution pie chart on ``ax``."""
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


def draw_manuscript_complexity_scatter_on_axes(ax: Axes, projects: list[ProjectMetrics]) -> None:
    """Plot equations vs word count scatter on ``ax``."""
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


def draw_executive_summary_on_axes(ax: Axes, summary: ExecutiveSummary) -> None:
    """Plot compact executive summary table on ``ax``."""
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


def create_test_count_chart(
    projects: list[ProjectMetrics],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create bar chart showing test counts by project."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_test_count_on_axes(ax, projects)
        ax.set_title("Test Counts by Project", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_test_count_on_axes(ax, projects, include_failed=False, title="Test Results by Project")
    return None


def create_coverage_chart(
    projects: list[ProjectMetrics],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create bar chart showing coverage percentages by project."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        draw_coverage_on_axes(ax, projects)
        ax.set_title("Test Coverage by Project", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_coverage_on_axes(ax, projects, compact=True)
    return None


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


def create_output_distribution_chart(
    aggregate: dict[str, Any],
    *,
    ax: Axes | None = None,
) -> Figure | None:
    """Create pie chart showing distribution of output types."""
    outputs = aggregate.get("outputs", {})
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))
        draw_output_distribution_on_axes(ax, outputs)
        ax.set_title("Output File Distribution", fontweight="bold", fontsize=14)
        plt.tight_layout()
        return fig
    draw_output_distribution_on_axes(ax, outputs)
    return None


def create_manuscript_size_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create bar chart showing manuscript word counts by project.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    project_names = [p.name for p in projects]
    word_counts = [p.manuscript.total_words for p in projects]

    x = range(len(projects))
    ax.bar(x, word_counts, color=COLORS["primary"])

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Word Count", fontweight="bold")
    ax.set_title("Manuscript Size by Project", fontweight="bold", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)

    # Add word count labels on bars
    for i, count in enumerate(word_counts):
        ax.text(
            i,
            count + max(word_counts) * 0.02,
            f"{count:,}",
            ha="center",
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


def create_manuscript_complexity_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create chart showing manuscript complexity metrics.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    project_names = [p.name for p in projects]

    # Equations vs word count
    equations = [p.manuscript.equations for p in projects]
    word_counts = [p.manuscript.total_words for p in projects]

    ax1.scatter(word_counts, equations, color=COLORS["primary"], s=100, alpha=0.7)
    for i, name in enumerate(project_names):
        ax1.annotate(
            name,
            (word_counts[i], equations[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )
    ax1.set_xlabel("Word Count", fontweight="bold")
    ax1.set_ylabel("Equations", fontweight="bold")
    ax1.set_title("Manuscript Complexity: Equations vs Length", fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Figures vs sections
    figures = [p.manuscript.figures for p in projects]
    sections = [p.manuscript.sections for p in projects]

    ax2.scatter(sections, figures, color=COLORS["success"], s=100, alpha=0.7)
    for i, name in enumerate(project_names):
        ax2.annotate(
            name,
            (sections[i], figures[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )
    ax2.set_xlabel("Sections", fontweight="bold")
    ax2.set_ylabel("Figures", fontweight="bold")
    ax2.set_title("Manuscript Structure: Figures vs Sections", fontweight="bold")
    ax2.grid(True, alpha=0.3)

    # References distribution
    references = [p.manuscript.references for p in projects]
    bars = ax3.bar(range(len(projects)), references, color=COLORS["warning"], alpha=0.7)
    ax3.set_xlabel("Project", fontweight="bold")
    ax3.set_ylabel("References", fontweight="bold")
    ax3.set_title("Citation Density", fontweight="bold")
    ax3.set_xticks(range(len(projects)))
    ax3.set_xticklabels(project_names, rotation=45, ha="right")
    ax3.grid(True, alpha=0.3, axis="y")

    # Add value labels on bars
    for bar, ref in zip(bars, references):
        height = bar.get_height()
        ax3.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + max(references) * 0.02,
            f"{ref}",
            ha="center",
            va="bottom",
            fontweight="bold",
        )

    # Complexity radar chart (simplified)
    # Normalize values for comparison
    max_words = max(word_counts) if word_counts else 1
    max_eqs = max(equations) if equations else 1
    max_figs = max(figures) if figures else 1
    max_refs = max(references) if references else 1

    normalized_data = []
    for p in projects:
        normalized_data.append(
            {
                "words": p.manuscript.total_words / max_words,
                "equations": p.manuscript.equations / max_eqs,
                "figures": p.manuscript.figures / max_figs,
                "references": p.manuscript.references / max_refs,
            }
        )

    # Create radar chart for first project as example
    if projects:
        angles = [0, 90, 180, 270]
        angles += angles[:1]  # Close the circle

        ax4.set_title(
            "Manuscript Complexity Profile\n(Example: First Project)",
            fontweight="bold",
            pad=20,
        )

        # Only show for first project to avoid clutter
        first_project = normalized_data[0]
        values = [
            first_project["words"],
            first_project["equations"],
            first_project["figures"],
            first_project["references"],
        ]
        values += values[:1]  # Close the circle

        ax4.plot(angles, values, "o-", linewidth=2, color=COLORS["primary"], alpha=0.7)
        ax4.fill(angles, values, alpha=0.3, color=COLORS["primary"])
        ax4.set_xticks(angles[:-1])
        ax4.set_xticklabels(["Words", "Equations", "Figures", "References"])
        ax4.set_ylim(0, 1.1)
        ax4.grid(True, alpha=0.3)

    fig.suptitle("Manuscript Complexity Analysis", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout()
    return fig


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


def create_summary_table(projects: list[ProjectMetrics], aggregate: dict[str, Any]) -> Figure:
    """Create enhanced summary table with key metrics and health scores.

    Args:
        projects: List of ProjectMetrics
        aggregate: Aggregate metrics dictionary

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")

    headers = [
        "Project",
        "Health\nScore",
        "Grade",
        "Words",
        "Tests",
        "Coverage",
        "Duration",
        "PDFs",
        "Figures",
    ]
    rows = []

    for p in projects:
        health = calculate_project_health_score(p)
        rows.append(
            [
                p.name,
                f"{health['percentage']:.0f}%",
                health["grade"],
                f"{p.manuscript.total_words:,}",
                str(p.tests.total_tests),
                f"{p.tests.coverage_percent:.1f}%",
                f"{p.pipeline.total_duration:.0f}s",
                str(p.outputs.pdf_files),
                str(p.outputs.figures),
            ]
        )

    # Add aggregate statistics row
    manuscript_stats = aggregate.get("manuscript", {}).get("words_stats", {})
    coverage_stats = aggregate.get("tests", {}).get("coverage_stats", {})
    duration_stats = aggregate.get("pipeline", {}).get("duration_stats", {})

    rows.append(
        [
            "**AGGREGATE**",
            "**N/A**",
            "**N/A**",
            f"**{aggregate['manuscript']['total_words']:,}**\n({manuscript_stats.get('mean', 0):,.0f} avg)",  # noqa: E501
            f"**{aggregate['tests']['total_tests']}**",
            f"**{aggregate['tests']['average_coverage']:.1f}%**\n({coverage_stats.get('mean', 0):.1f} avg)",  # noqa: E501
            f"**{aggregate['pipeline']['total_duration']:.0f}s**\n({duration_stats.get('mean', 0):.0f} avg)",  # noqa: E501
            f"**{aggregate['outputs']['total_pdfs']}**",
            f"**{aggregate['outputs']['total_figures']}**",
        ]
    )

    table = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)

    # Style header row
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor(COLORS["primary"])
        cell.set_text_props(weight="bold", color="white")

    # Style aggregate row
    for i in range(len(headers)):
        cell = table[(len(rows), i)]
        cell.set_facecolor(COLORS["light"])
        cell.set_text_props(weight="bold")

    # Color-code health scores
    for row_idx in range(1, len(rows)):  # Skip header
        if row_idx < len(rows):  # Skip aggregate row
            health_cell = table[(row_idx, 1)]  # Health score column
            grade_cell = table[(row_idx, 2)]  # Grade column

            grade_text = rows[row_idx - 1][2] if row_idx - 1 < len(rows) - 1 else ""
            if grade_text == "A":
                health_cell.set_facecolor("#d4edda")  # Light green
                grade_cell.set_facecolor("#d4edda")
            elif grade_text == "B":
                health_cell.set_facecolor("#fff3cd")  # Light yellow
                grade_cell.set_facecolor("#fff3cd")
            elif grade_text == "C":
                health_cell.set_facecolor("#ffeaa7")  # Light orange
                grade_cell.set_facecolor("#ffeaa7")
            else:  # D, F
                health_cell.set_facecolor("#f8d7da")  # Light red
                grade_cell.set_facecolor("#f8d7da")

    ax.set_title("Comprehensive Project Metrics Summary", fontweight="bold", fontsize=16, pad=30)

    return fig


def generate_matplotlib_dashboard(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
    """Generate complete dashboard using matplotlib (PNG and PDF).

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    from infrastructure.reporting._dashboard_grid import compose_executive_dashboard

    logger.info("Generating matplotlib dashboard...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files: dict[str, Path] = {}

    try:
        fig = compose_executive_dashboard(summary)

        png_path = organizer.get_output_path("dashboard.png", output_dir, FileType.PNG)
        plt.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
        saved_files["png"] = png_path
        logger.info(f"Saved PNG dashboard: {png_path}")

        pdf_path = organizer.get_output_path("dashboard.pdf", output_dir, FileType.PDF)
        plt.savefig(pdf_path, format="pdf", bbox_inches="tight", facecolor="white")
        saved_files["pdf"] = pdf_path
        logger.info(f"Saved PDF dashboard: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Error generating matplotlib dashboard: {e}")
        plt.close("all")

    return saved_files

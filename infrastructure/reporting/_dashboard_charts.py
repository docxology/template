"""Base chart generators and multi-panel dashboard for executive reporting.

Extracted from ``_dashboard_matplotlib.py`` — standalone chart functions
(test counts, coverage, pipeline duration, output distribution, manuscript
size/complexity, performance timeline, summary table) plus the multi-panel
``generate_matplotlib_dashboard()`` generator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary, ProjectMetrics
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)

# Professional color scheme
COLORS = {
    "primary": "#2E86AB",
    "success": "#06A77D",
    "warning": "#F77F00",
    "danger": "#D62828",
    "secondary": "#6C757D",
    "light": "#F8F9FA",
}

def create_test_count_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create bar chart showing test counts by project.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

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
    )
    ax.bar(x, passed_tests, width, label="Passed", color=COLORS["success"])
    ax.bar(
        [i + width for i in x],
        failed_tests,
        width,
        label="Failed",
        color=COLORS["danger"],
    )

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Test Count", fontweight="bold")
    ax.set_title("Test Counts by Project", fontweight="bold", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    return fig


def create_coverage_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create bar chart showing coverage percentages by project.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    project_names = [p.name for p in projects]
    coverage = [p.tests.coverage_percent for p in projects]

    # Color bars based on coverage thresholds
    colors = []
    for cov in coverage:
        if cov >= 95:
            colors.append(COLORS["success"])
        elif cov >= 90:
            colors.append(COLORS["warning"])
        else:
            colors.append(COLORS["danger"])

    x = range(len(projects))
    ax.bar(x, coverage, color=colors)

    # Add threshold line at 90%
    ax.axhline(y=90, color=COLORS["danger"], linestyle="--", linewidth=2, label="90% Threshold")

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Coverage (%)", fontweight="bold")
    ax.set_title("Test Coverage by Project", fontweight="bold", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.set_ylim(0, 105)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Add percentage labels on bars
    for i, cov in enumerate(coverage):
        ax.text(i, cov + 1, f"{cov:.1f}%", ha="center", fontweight="bold")

    plt.tight_layout()
    return fig


def create_pipeline_duration_chart(projects: list[ProjectMetrics]) -> Figure:
    """Create stacked bar chart showing pipeline durations by project.

    Args:
        projects: List of ProjectMetrics

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    project_names = [p.name for p in projects]
    durations = [p.pipeline.total_duration for p in projects]
    bottleneck_durations = [p.pipeline.bottleneck_duration for p in projects]
    other_durations = [d - b for d, b in zip(durations, bottleneck_durations)]

    x = range(len(projects))

    ax.bar(x, other_durations, label="Other Stages", color=COLORS["secondary"])
    ax.bar(
        x,
        bottleneck_durations,
        bottom=other_durations,
        label="Bottleneck Stage",
        color=COLORS["danger"],
    )

    ax.set_xlabel("Project", fontweight="bold")
    ax.set_ylabel("Duration (seconds)", fontweight="bold")
    ax.set_title("Pipeline Duration by Project", fontweight="bold", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Add total duration labels
    for i, duration in enumerate(durations):
        ax.text(i, duration + 1, f"{duration:.0f}s", ha="center", fontweight="bold")

    plt.tight_layout()
    return fig


def create_output_distribution_chart(aggregate: dict[str, Any]) -> Figure:
    """Create pie chart showing distribution of output types.

    Args:
        aggregate: Aggregate metrics dictionary

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(8, 8))

    outputs = aggregate.get("outputs", {})
    labels = ["PDFs", "Figures", "Slides", "Web Pages"]
    sizes = [
        outputs.get("total_pdfs", 0),
        outputs.get("total_figures", 0),
        outputs.get("total_slides", 0),
        outputs.get("total_web", 0),
    ]

    colors = [
        COLORS["primary"],
        COLORS["success"],
        COLORS["warning"],
        COLORS["secondary"],
    ]

    # Only plot non-zero values
    filtered_labels = []
    filtered_sizes = []
    filtered_colors = []
    for label, size, color in zip(labels, sizes, colors):
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
        ax.set_title("Output File Distribution", fontweight="bold", fontsize=14)
    else:
        ax.text(
            0.5,
            0.5,
            "No outputs generated",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=14,
            fontweight="bold",
        )

    plt.tight_layout()
    return fig


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
        efficiency = [
            count / duration if duration > 0 else 0
            for count, duration in zip(pdf_counts, durations)
        ]

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

    # Import health score calculation
    from infrastructure.reporting.executive_reporter import calculate_project_health_score

    # Prepare table data with more columns
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
            f"**{aggregate['manuscript']['total_words']:,}**\n({manuscript_stats.get('avg', 0):,.0f} avg)",  # noqa: E501
            f"**{aggregate['tests']['total_tests']}**",
            f"**{aggregate['tests']['average_coverage']:.1f}%**\n({coverage_stats.get('avg', 0):.1f} avg)",  # noqa: E501
            f"**{aggregate['pipeline']['total_duration']:.0f}s**\n({duration_stats.get('avg', 0):.0f} avg)",  # noqa: E501
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
    logger.info("Generating matplotlib dashboard...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        # Create comprehensive multi-panel figure (3x3 grid)
        fig, axes = plt.subplots(3, 3, figsize=(20, 16))

        projects = summary.project_metrics
        project_names = [p.name for p in projects]
        x = range(len(projects))

        # Row 1: Core metrics
        # Test counts and coverage
        ax1 = axes[0, 0]
        total_tests = [p.tests.total_tests for p in projects]
        passed_tests = [p.tests.passed for p in projects]
        width = 0.25
        ax1.bar(
            [i - width for i in x],
            total_tests,
            width,
            label="Total",
            color=COLORS["primary"],
            alpha=0.8,
        )
        ax1.bar(
            x,
            passed_tests,
            width,
            label="Passed",
            color=COLORS["success"],
            alpha=0.8,
        )
        ax1.set_xlabel("Project", fontweight="bold")
        ax1.set_ylabel("Test Count", fontweight="bold")
        ax1.set_title("Test Results by Project", fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(project_names, rotation=45, ha="right")
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # Coverage with thresholds
        ax2 = axes[0, 1]
        coverage = [p.tests.coverage_percent for p in projects]
        ax2.bar(x, coverage, color=COLORS["primary"], alpha=0.8)
        ax2.axhline(
            y=90,
            color=COLORS["success"],
            linestyle="--",
            linewidth=2,
            label="Excellent (90%)",
        )
        ax2.axhline(
            y=70,
            color=COLORS["warning"],
            linestyle="--",
            linewidth=2,
            label="Adequate (70%)",
        )
        ax2.set_xlabel("Project", fontweight="bold")
        ax2.set_ylabel("Coverage (%)", fontweight="bold")
        ax2.set_title("Test Coverage by Project", fontweight="bold")
        ax2.set_xticks(x)
        ax2.set_xticklabels(project_names, rotation=45, ha="right")
        ax2.set_ylim(0, 105)
        ax2.legend()
        ax2.grid(axis="y", alpha=0.3)

        # Pipeline performance
        ax3 = axes[0, 2]
        durations = [p.pipeline.total_duration for p in projects]
        ax3.bar(x, durations, color=COLORS["warning"], alpha=0.8)
        ax3.set_xlabel("Project", fontweight="bold")
        ax3.set_ylabel("Duration (seconds)", fontweight="bold")
        ax3.set_title("Pipeline Execution Time", fontweight="bold")
        ax3.set_xticks(x)
        ax3.set_xticklabels(project_names, rotation=45, ha="right")
        ax3.grid(axis="y", alpha=0.3)

        # Add duration labels
        for i, duration in enumerate(durations):
            ax3.text(
                i,
                duration + max(durations) * 0.02,
                f"{duration:.0f}s",
                ha="center",
                fontweight="bold",
            )

        # Row 2: Manuscript and output analysis
        # Manuscript complexity
        ax4 = axes[1, 0]
        word_counts = [p.manuscript.total_words for p in projects]
        equations = [p.manuscript.equations for p in projects]
        ax4.scatter(
            word_counts,
            equations,
            s=100,
            c=range(len(projects)),
            cmap="viridis",
            alpha=0.8,
        )
        for i, name in enumerate(project_names):
            ax4.annotate(
                name,
                (word_counts[i], equations[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )
        ax4.set_xlabel("Word Count", fontweight="bold")
        ax4.set_ylabel("Equations", fontweight="bold")
        ax4.set_title("Manuscript Complexity", fontweight="bold")
        ax4.grid(True, alpha=0.3)

        # Output distribution
        ax5 = axes[1, 1]
        outputs = summary.aggregate_metrics.get("outputs", {})
        labels = ["PDFs", "Figures", "Slides", "Web"]
        sizes = [
            outputs.get("total_pdfs", 0),
            outputs.get("total_figures", 0),
            outputs.get("total_slides", 0),
            outputs.get("total_web", 0),
        ]

        colors = [
            COLORS["primary"],
            COLORS["success"],
            COLORS["warning"],
            COLORS["secondary"],
        ]
        filtered_labels = []
        filtered_sizes = []
        filtered_colors = []
        for label, size, color in zip(labels, sizes, colors):
            if size > 0:
                filtered_labels.append(label)
                filtered_sizes.append(size)
                filtered_colors.append(color)

        if filtered_sizes:
            ax5.pie(
                filtered_sizes,
                labels=filtered_labels,
                colors=filtered_colors,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"fontweight": "bold"},
            )
            ax5.set_title("Output File Distribution", fontweight="bold")
        else:
            ax5.text(
                0.5,
                0.5,
                "No outputs\ngenerated",
                ha="center",
                va="center",
                transform=ax5.transAxes,
                fontsize=12,
                fontweight="bold",
            )

        # Performance efficiency
        ax6 = axes[1, 2]
        pdf_counts = [p.outputs.pdf_files for p in projects]
        efficiency = [
            count / duration if duration > 0 else 0
            for count, duration in zip(pdf_counts, durations)
        ]

        ax6.bar(x, efficiency, color=COLORS["success"], alpha=0.8)
        ax6.set_xlabel("Project", fontweight="bold")
        ax6.set_ylabel("PDFs per Second", fontweight="bold")
        ax6.set_title("Pipeline Efficiency", fontweight="bold")
        ax6.set_xticks(x)
        ax6.set_xticklabels(project_names, rotation=45, ha="right")
        ax6.grid(axis="y", alpha=0.3)

        # Add efficiency labels
        for i, eff in enumerate(efficiency):
            ax6.text(
                i,
                eff + max(efficiency) * 0.02 if efficiency else 0.02,
                f"{eff:.2f}",
                ha="center",
                fontweight="bold",
            )

        # Row 3: Comparative analysis and summary
        # Health scores comparison
        ax7 = axes[2, 0]
        from infrastructure.reporting.executive_reporter import calculate_project_health_score

        health_scores = [calculate_project_health_score(p)["percentage"] for p in projects]
        ax7.bar(x, health_scores, color=COLORS["primary"], alpha=0.8)
        ax7.axhline(
            y=85,
            color=COLORS["success"],
            linestyle="--",
            linewidth=2,
            label="Excellent (85%)",
        )
        ax7.axhline(
            y=70,
            color=COLORS["warning"],
            linestyle="--",
            linewidth=2,
            label="Good (70%)",
        )
        ax7.set_xlabel("Project", fontweight="bold")
        ax7.set_ylabel("Health Score (%)", fontweight="bold")
        ax7.set_title("Project Health Scores", fontweight="bold")
        ax7.set_xticks(x)
        ax7.set_xticklabels(project_names, rotation=45, ha="right")
        ax7.set_ylim(0, 105)
        ax7.legend()
        ax7.grid(axis="y", alpha=0.3)

        # Add health score labels
        for i, score in enumerate(health_scores):
            ax7.text(i, score + 1, f"{score:.0f}%", ha="center", fontweight="bold")

        # Test efficiency (coverage vs time)
        ax8 = axes[2, 1]
        test_times = [p.tests.execution_time for p in projects]
        coverages = [p.tests.coverage_percent for p in projects]
        ax8.scatter(
            test_times,
            coverages,
            s=100,
            c=range(len(projects)),
            cmap="viridis",
            alpha=0.8,
        )
        for i, name in enumerate(project_names):
            ax8.annotate(
                name,
                (test_times[i], coverages[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )
        ax8.set_xlabel("Test Time (s)", fontweight="bold")
        ax8.set_ylabel("Coverage (%)", fontweight="bold")
        ax8.set_title("Test Efficiency Matrix", fontweight="bold")
        ax8.grid(True, alpha=0.3)

        # Enhanced summary table
        ax9 = axes[2, 2]
        ax9.axis("off")

        headers = ["Project", "Health", "Words", "Tests", "Coverage"]
        rows = []
        for p in projects:
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

        # Add aggregate row
        agg = summary.aggregate_metrics
        manuscript_agg = agg.get("manuscript", {})
        tests_agg = agg.get("tests", {})
        words_stats = manuscript_agg.get("words_stats", {})
        coverage_stats = tests_agg.get("coverage_stats", {})

        rows.append(
            [
                "**TOTAL**",
                "**N/A**",
                f"**{manuscript_agg.get('total_words', 0):,}**\n({words_stats.get('avg', 0):,.0f} avg)",  # noqa: E501
                f"**{tests_agg.get('total_tests', 0)}**",
                f"**{tests_agg.get('average_coverage', 0):.1f}%**\n({coverage_stats.get('avg', 0):.1f} avg)",  # noqa: E501
            ]
        )

        table = ax9.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.8)

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

        ax9.set_title("Executive Summary", fontweight="bold", fontsize=12, pad=20)

        # Save as PNG (high resolution)
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path("dashboard.png", output_dir, FileType.PNG)
        plt.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
        saved_files["png"] = png_path
        logger.info(f"Saved PNG dashboard: {png_path}")

        # Save as PDF (vector graphics)
        pdf_path = organizer.get_output_path("dashboard.pdf", output_dir, FileType.PDF)
        plt.savefig(pdf_path, format="pdf", bbox_inches="tight", facecolor="white")
        saved_files["pdf"] = pdf_path
        logger.info(f"Saved PDF dashboard: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Error generating matplotlib dashboard: {e}")
        plt.close("all")

    return saved_files


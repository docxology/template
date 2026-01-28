"""Dashboard generator for visual reports and charts.

This module generates visual dashboards in multiple formats (PNG, PDF, HTML)
using matplotlib for static charts and plotly for interactive visualizations.

Part of the infrastructure reporting layer (Layer 1) - reusable across projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import csv

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from infrastructure.core.logging_utils import get_logger
from infrastructure.reporting.executive_reporter import (ExecutiveSummary,
                                                         ProjectMetrics)
from infrastructure.reporting.manuscript_overview import \
    generate_all_manuscript_overviews
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


def create_test_count_chart(projects: List[ProjectMetrics]) -> Figure:
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
    ax.bar([i for i in x], passed_tests, width, label="Passed", color=COLORS["success"])
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


def create_coverage_chart(projects: List[ProjectMetrics]) -> Figure:
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
    ax.axhline(
        y=90, color=COLORS["danger"], linestyle="--", linewidth=2, label="90% Threshold"
    )

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


def create_pipeline_duration_chart(projects: List[ProjectMetrics]) -> Figure:
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


def create_output_distribution_chart(aggregate: Dict[str, Any]) -> Figure:
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


def create_manuscript_size_chart(projects: List[ProjectMetrics]) -> Figure:
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


def create_manuscript_complexity_chart(projects: List[ProjectMetrics]) -> Figure:
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

    fig.suptitle(
        "Manuscript Complexity Analysis", fontsize=16, fontweight="bold", y=0.98
    )
    plt.tight_layout()
    return fig


def create_performance_timeline_chart(projects: List[ProjectMetrics]) -> Figure:
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

    scatter = ax2.scatter(
        test_times, coverages, s=100, c=range(len(projects)), cmap="viridis", alpha=0.7
    )
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

        bars = ax4.bar(
            range(len(projects)), efficiency, color=COLORS["warning"], alpha=0.7
        )
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

    fig.suptitle(
        "Performance Analysis Dashboard", fontsize=16, fontweight="bold", y=0.98
    )
    plt.tight_layout()
    return fig


def create_summary_table(
    projects: List[ProjectMetrics], aggregate: Dict[str, Any]
) -> Figure:
    """Create enhanced summary table with key metrics and health scores.

    Args:
        projects: List of ProjectMetrics
        aggregate: Aggregate metrics dictionary

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("tight")
    ax.axis("off")

    # Import health score calculation
    from infrastructure.reporting.executive_reporter import \
        calculate_project_health_score

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
            f"**{aggregate['manuscript']['total_words']:,}**\n({manuscript_stats.get('avg', 0):,.0f} avg)",
            f"**{aggregate['tests']['total_tests']}**",
            f"**{aggregate['tests']['average_coverage']:.1f}%**\n({coverage_stats.get('avg', 0):.1f} avg)",
            f"**{aggregate['pipeline']['total_duration']:.0f}s**\n({duration_stats.get('avg', 0):.0f} avg)",
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

    ax.set_title(
        "Comprehensive Project Metrics Summary", fontweight="bold", fontsize=16, pad=30
    )

    plt.tight_layout()
    return fig


def generate_matplotlib_dashboard(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
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
            [i for i in x],
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
        bars = ax2.bar(x, coverage, color=COLORS["primary"], alpha=0.8)
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
        bars = ax3.bar(x, durations, color=COLORS["warning"], alpha=0.8)
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
        scatter = ax4.scatter(
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

        bars = ax6.bar(x, efficiency, color=COLORS["success"], alpha=0.8)
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
        from infrastructure.reporting.executive_reporter import \
            calculate_project_health_score

        health_scores = [
            calculate_project_health_score(p)["percentage"] for p in projects
        ]
        bars = ax7.bar(x, health_scores, color=COLORS["primary"], alpha=0.8)
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
        scatter = ax8.scatter(
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
        ax9.axis("tight")
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
                f"**{manuscript_agg.get('total_words', 0):,}**\n({words_stats.get('avg', 0):,.0f} avg)",
                f"**{tests_agg.get('total_tests', 0)}**",
                f"**{tests_agg.get('average_coverage', 0):.1f}%**\n({coverage_stats.get('avg', 0):.1f} avg)",
            ]
        )

        table = ax9.table(
            cellText=rows, colLabels=headers, loc="center", cellLoc="center"
        )
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

        plt.tight_layout()

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

    except Exception as e:
        logger.error(f"Error generating matplotlib dashboard: {e}")
        plt.close("all")

    return saved_files


def generate_plotly_dashboard(summary: ExecutiveSummary, output_dir: Path) -> Path:
    """Generate interactive HTML dashboard using plotly.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Path to saved HTML file
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        logger.warning(
            "Plotly not installed, skipping interactive dashboard generation"
        )
        return None

    logger.info("Generating interactive plotly dashboard...")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Create subplots
    fig = make_subplots(
        rows=2,
        cols=3,
        subplot_titles=(
            "Test Counts by Project",
            "Coverage by Project",
            "Pipeline Duration",
            "Output Distribution",
            "Manuscript Size",
            "Summary Table",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "bar"}, {"type": "table"}],
        ],
    )

    projects = summary.project_metrics
    project_names = [p.name for p in projects]

    # Test counts chart
    fig.add_trace(
        go.Bar(
            name="Total",
            x=project_names,
            y=[p.tests.total_tests for p in projects],
            marker_color=COLORS["primary"],
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            name="Passed",
            x=project_names,
            y=[p.tests.passed for p in projects],
            marker_color=COLORS["success"],
        ),
        row=1,
        col=1,
    )

    # Coverage chart
    coverage_values = [p.tests.coverage_percent for p in projects]
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=coverage_values,
            marker_color=COLORS["primary"],
            text=[f"{c:.1f}%" for c in coverage_values],
            textposition="outside",
        ),
        row=1,
        col=2,
    )

    # Pipeline duration chart
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=[p.pipeline.total_duration for p in projects],
            marker_color=COLORS["warning"],
            text=[f"{p.pipeline.total_duration:.0f}s" for p in projects],
            textposition="outside",
        ),
        row=1,
        col=3,
    )

    # Output distribution pie chart
    outputs = summary.aggregate_metrics.get("outputs", {})
    fig.add_trace(
        go.Pie(
            labels=["PDFs", "Figures", "Slides", "Web"],
            values=[
                outputs.get("total_pdfs", 0),
                outputs.get("total_figures", 0),
                outputs.get("total_slides", 0),
                outputs.get("total_web", 0),
            ],
            marker=dict(
                colors=[
                    COLORS["primary"],
                    COLORS["success"],
                    COLORS["warning"],
                    COLORS["secondary"],
                ]
            ),
        ),
        row=2,
        col=1,
    )

    # Manuscript size chart
    fig.add_trace(
        go.Bar(
            x=project_names,
            y=[p.manuscript.total_words for p in projects],
            marker_color=COLORS["primary"],
            text=[f"{p.manuscript.total_words:,}" for p in projects],
            textposition="outside",
        ),
        row=2,
        col=2,
    )

    # Summary table
    table_data = {
        "Project": project_names + ["TOTAL"],
        "Words": [f"{p.manuscript.total_words:,}" for p in projects]
        + [f"{summary.aggregate_metrics['manuscript']['total_words']:,}"],
        "Tests": [str(p.tests.total_tests) for p in projects]
        + [str(summary.aggregate_metrics["tests"]["total_tests"])],
        "Coverage": [f"{p.tests.coverage_percent:.1f}%" for p in projects]
        + [f"{summary.aggregate_metrics['tests']['average_coverage']:.1f}%"],
    }

    fig.add_trace(
        go.Table(
            header=dict(
                values=list(table_data.keys()),
                fill_color=COLORS["primary"],
                font=dict(color="white", size=12),
            ),
            cells=dict(
                values=list(table_data.values()), fill_color="white", align="left"
            ),
        ),
        row=2,
        col=3,
    )

    # Update layout
    fig.update_layout(
        title_text="Executive Dashboard - All Projects",
        title_font_size=20,
        showlegend=True,
        height=1000,
        template="plotly_white",
    )

    # Save HTML
    html_path = output_dir / "dashboard.html"
    fig.write_html(html_path)
    logger.info(f"Saved interactive HTML dashboard: {html_path}")

    return html_path


def generate_health_radar_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate radar chart for health score factors.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating health score radar chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        # Prepare data for radar chart
        projects = summary.project_metrics
        if not projects:
            logger.warning("No project metrics available for health radar chart")
            return saved_files

        # Health score factors (normalized to 0-100 scale)
        factors = ["test_coverage", "test_failures", "manuscript_size", "outputs"]
        factor_labels = ["Test Coverage", "Test Integrity", "Manuscript", "Outputs"]

        # Create radar chart
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection="polar"))

        # Plot each project
        colors = ["#2E86AB", "#06A77D", "#F77F00", "#D62828", "#9B59B6", "#E74C3C"]
        angles = np.linspace(0, 2 * np.pi, len(factors), endpoint=False).tolist()
        angles += angles[:1]  # Close the polygon

        for i, project in enumerate(projects):
            health = summary.health_scores.get(project.name, {})
            if not health.get("factors"):
                continue

            # Extract factor scores (convert to 0-100 scale)
            scores = []
            for factor in factors:
                factor_data = health["factors"].get(factor, {})
                score = factor_data.get("score", 0)
                if factor == "test_coverage":
                    # Convert to 0-40 scale as in health calculation
                    score = min(score, 40)
                elif factor == "test_failures":
                    # Convert to 0-30 scale
                    score = min(score, 30)
                elif factor == "manuscript_size":
                    # Convert to 0-20 scale
                    score = min(score, 20)
                elif factor == "outputs":
                    # Convert to 0-10 scale
                    score = min(score, 10)
                scores.append(score)

            scores += scores[:1]  # Close the polygon

            # Plot the radar chart
            ax.fill(angles, scores, alpha=0.25, color=colors[i % len(colors)])
            ax.plot(
                angles,
                scores,
                "o-",
                linewidth=2,
                label=project.name,
                color=colors[i % len(colors)],
                markersize=6,
            )

        # Configure the chart
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(factor_labels)
        ax.set_ylim(0, 50)  # Scale to show relative importance
        ax.set_title(
            "Project Health Score Analysis", size=16, fontweight="bold", pad=20
        )
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.0))
        ax.grid(True, alpha=0.3)

        # Add center label
        ax.text(
            0,
            0,
            "Health\nFactors",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            alpha=0.7,
        )

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "health_scores_radar.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Health radar chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "health_scores_radar.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Health radar chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate health radar chart: {e}")

    return saved_files


def generate_health_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate health score comparison bar chart.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating health score comparison chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Extract health scores
        project_names = []
        overall_scores = []
        factor_scores = {
            "coverage": [],
            "integrity": [],
            "manuscript": [],
            "outputs": [],
        }

        for project in projects:
            health = summary.health_scores.get(project.name, {})
            if health.get("percentage") is not None:
                project_names.append(project.name)
                overall_scores.append(health["percentage"])

                # Extract individual factor scores
                factors = health.get("factors", {})
                factor_scores["coverage"].append(
                    factors.get("test_coverage", {}).get("score", 0)
                )
                factor_scores["integrity"].append(
                    factors.get("test_failures", {}).get("score", 0)
                )
                factor_scores["manuscript"].append(
                    factors.get("manuscript_size", {}).get("score", 0)
                )
                factor_scores["outputs"].append(
                    factors.get("outputs", {}).get("score", 0)
                )

        if not project_names:
            return saved_files

        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Overall health scores
        bars = ax1.bar(
            project_names, overall_scores, color=COLORS["primary"], alpha=0.8
        )
        ax1.set_ylabel("Overall Health Score (%)", fontweight="bold")
        ax1.set_title("Project Health Scores Overview", fontweight="bold")
        ax1.set_ylim(0, 105)
        ax1.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, score in zip(bars, overall_scores):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{score:.0f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Factor breakdown
        x = np.arange(len(project_names))
        width = 0.2

        ax2.bar(
            x - 1.5 * width,
            factor_scores["coverage"],
            width,
            label="Test Coverage (40%)",
            color="#2E86AB",
            alpha=0.8,
        )
        ax2.bar(
            x - 0.5 * width,
            factor_scores["integrity"],
            width,
            label="Test Integrity (30%)",
            color="#06A77D",
            alpha=0.8,
        )
        ax2.bar(
            x + 0.5 * width,
            factor_scores["manuscript"],
            width,
            label="Manuscript (20%)",
            color="#F77F00",
            alpha=0.8,
        )
        ax2.bar(
            x + 1.5 * width,
            factor_scores["outputs"],
            width,
            label="Outputs (10%)",
            color="#D62828",
            alpha=0.8,
        )

        ax2.set_ylabel("Factor Score", fontweight="bold")
        ax2.set_title("Health Score Factor Breakdown", fontweight="bold")
        ax2.set_xticks(x)
        ax2.set_xticklabels(project_names)
        ax2.legend()
        ax2.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "health_scores_comparison.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Health comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "health_scores_comparison.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Health comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate health comparison chart: {e}")

    return saved_files


def generate_project_breakdowns(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate individual dashboard for each project.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating individual project dashboards...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        for project in projects:
            # Create individual dashboard for this project
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(
                f"Project Dashboard: {project.name}", fontsize=16, fontweight="bold"
            )

            # Manuscript metrics
            ax1 = axes[0, 0]
            manuscript_data = [
                project.manuscript.total_words,
                project.manuscript.sections,
                project.manuscript.equations,
                project.manuscript.figures,
            ]
            manuscript_labels = ["Words", "Sections", "Equations", "Figures"]
            bars = ax1.bar(
                manuscript_labels, manuscript_data, color=COLORS["primary"], alpha=0.8
            )
            ax1.set_title("Manuscript Metrics", fontweight="bold")
            ax1.set_ylabel("Count", fontweight="bold")
            ax1.grid(axis="y", alpha=0.3)

            # Add value labels
            for bar, value in zip(bars, manuscript_data):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(manuscript_data) * 0.02,
                    f"{value:,}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            # Codebase metrics
            ax2 = axes[0, 1]
            codebase_data = [
                project.codebase.source_lines,
                project.codebase.methods,
                project.codebase.classes,
                project.codebase.scripts,
            ]
            codebase_labels = ["Source Lines", "Methods", "Classes", "Scripts"]
            bars = ax2.bar(
                codebase_labels, codebase_data, color=COLORS["success"], alpha=0.8
            )
            ax2.set_title("Codebase Metrics", fontweight="bold")
            ax2.set_ylabel("Count", fontweight="bold")
            ax2.grid(axis="y", alpha=0.3)

            # Add value labels
            for bar, value in zip(bars, codebase_data):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(codebase_data) * 0.02,
                    f"{value:,}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )

            # Output metrics (pie chart)
            ax3 = axes[1, 0]
            output_labels = ["PDFs", "Figures", "Slides", "Web", "Data Files"]
            output_sizes = [
                project.outputs.pdf_files,
                project.outputs.figures,
                project.outputs.slides,
                project.outputs.web_outputs,
                project.outputs.data_files,
            ]

            # Filter out zero values
            filtered_labels = []
            filtered_sizes = []
            for label, size in zip(output_labels, output_sizes):
                if size > 0:
                    filtered_labels.append(label)
                    filtered_sizes.append(size)

            if filtered_sizes:
                colors_pie = [
                    COLORS["primary"],
                    COLORS["success"],
                    COLORS["warning"],
                    COLORS["secondary"],
                    "#9B59B6",
                ]
                ax3.pie(
                    filtered_sizes,
                    labels=filtered_labels,
                    autopct="%1.1f%%",
                    colors=colors_pie[: len(filtered_sizes)],
                    startangle=90,
                )
                ax3.set_title("Output Distribution", fontweight="bold")
            else:
                ax3.text(
                    0.5,
                    0.5,
                    "No Outputs\nGenerated",
                    ha="center",
                    va="center",
                    transform=ax3.transAxes,
                    fontsize=14,
                    fontweight="bold",
                )
                ax3.set_title("Output Distribution", fontweight="bold")

            # Pipeline metrics
            ax4 = axes[1, 1]
            # All possible pipeline stages (9 stages total)
            stages = [
                "Clean",
                "Setup",
                "Infra Tests",
                "Project Tests",
                "Analysis",
                "Render",
                "Validate",
                "LLM Review",
                "LLM Translations",
                "Copy",
            ]
            durations = [
                1.0,
                1.0,
                5.0,
                project.pipeline.total_duration * 0.1,
                5.0,
                15.0,
                2.0,
                10.0,
                10.0,
                1.0,
            ]  # Estimated

            bars = ax4.bar(stages, durations, color=COLORS["warning"], alpha=0.8)
            ax4.set_title("Pipeline Stages", fontweight="bold")
            ax4.set_ylabel("Duration (seconds)", fontweight="bold")
            ax4.set_xticks(range(len(stages)))
            ax4.set_xticklabels(stages, rotation=45, ha="right")
            ax4.grid(axis="y", alpha=0.3)

            # Highlight bottleneck stage with flexible matching
            bottleneck_idx = -1
            if project.pipeline.bottleneck_stage:
                bottleneck_name = project.pipeline.bottleneck_stage.lower()
                # Create mapping for flexible stage name matching
                stage_mapping = {
                    "clean output": "Clean",
                    "environment setup": "Setup",
                    "setup": "Setup",
                    "infrastructure tests": "Infra Tests",
                    "infra tests": "Infra Tests",
                    "project tests": "Project Tests",
                    "tests": "Project Tests",
                    "project analysis": "Analysis",
                    "analysis": "Analysis",
                    "pdf rendering": "Render",
                    "render": "Render",
                    "output validation": "Validate",
                    "validate": "Validate",
                    "llm scientific review": "LLM Review",
                    "llm review": "LLM Review",
                    "llm translations": "LLM Translations",
                    "translations": "LLM Translations",
                    "copy outputs": "Copy",
                    "copy": "Copy",
                }
                # Try to find matching stage
                matched_stage = stage_mapping.get(bottleneck_name)
                if matched_stage and matched_stage in stages:
                    try:
                        bottleneck_idx = stages.index(matched_stage)
                    except ValueError:
                        bottleneck_idx = -1
                else:
                    # Fallback: try case-insensitive partial match
                    for i, stage in enumerate(stages):
                        if (
                            bottleneck_name in stage.lower()
                            or stage.lower() in bottleneck_name
                        ):
                            bottleneck_idx = i
                            break

            if bottleneck_idx >= 0:
                bars[bottleneck_idx].set_color(COLORS["danger"])
                bars[bottleneck_idx].set_alpha(1.0)

            plt.tight_layout()

            # Save PNG
            organizer = OutputOrganizer()
            safe_name = project.name.replace("_", "").replace("-", "").lower()
            png_filename = f"project_dashboard_{safe_name}.png"
            png_path = organizer.get_output_path(png_filename, output_dir, FileType.PNG)
            fig.savefig(png_path, dpi=300, bbox_inches="tight")
            saved_files[f"{safe_name}_png"] = png_path
            logger.info(f"Project dashboard ({project.name} PNG) saved: {png_path}")

            # Save PDF
            pdf_filename = f"project_dashboard_{safe_name}.pdf"
            pdf_path = organizer.get_output_path(pdf_filename, output_dir, FileType.PDF)
            fig.savefig(pdf_path, bbox_inches="tight")
            saved_files[f"{safe_name}_pdf"] = pdf_path
            logger.info(f"Project dashboard ({project.name} PDF) saved: {pdf_path}")

            plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate project breakdowns: {e}")

    return saved_files


def generate_pipeline_efficiency_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate pipeline efficiency and bottleneck analysis chart.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating pipeline efficiency analysis chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Create comprehensive pipeline analysis
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Pipeline Efficiency Analysis", fontsize=16, fontweight="bold")

        # Chart 1: Pipeline duration comparison
        project_names = [p.name for p in projects]
        durations = [p.pipeline.total_duration for p in projects]

        bars = ax1.bar(project_names, durations, color=COLORS["warning"], alpha=0.8)
        ax1.set_ylabel("Total Duration (seconds)", fontweight="bold")
        ax1.set_title("Pipeline Execution Times", fontweight="bold")
        ax1.set_xticks(range(len(project_names)))
        ax1.set_xticklabels(project_names, rotation=45, ha="right")
        ax1.grid(axis="y", alpha=0.3)

        # Add duration labels
        for bar, duration in zip(bars, durations):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(durations) * 0.02,
                f"{duration:.0f}s",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Chart 2: Bottleneck analysis
        bottlenecks = {}
        for project in projects:
            stage = project.pipeline.bottleneck_stage or "Unknown"
            if stage not in bottlenecks:
                bottlenecks[stage] = []
            bottlenecks[stage].append(project.pipeline.bottleneck_duration)

        if bottlenecks:
            bottleneck_labels = list(bottlenecks.keys())
            bottleneck_means = [
                np.mean(durations) for durations in bottlenecks.values()
            ]
            bottleneck_stds = [np.std(durations) for durations in bottlenecks.values()]

            bars = ax2.bar(
                bottleneck_labels,
                bottleneck_means,
                yerr=bottleneck_stds,
                capsize=5,
                color=COLORS["danger"],
                alpha=0.8,
            )
            ax2.set_ylabel("Bottleneck Duration (seconds)", fontweight="bold")
            ax2.set_title("Pipeline Bottlenecks by Stage", fontweight="bold")
            ax2.set_xticks(range(len(bottleneck_labels)))
            ax2.set_xticklabels(bottleneck_labels, rotation=45, ha="right")
            ax2.grid(axis="y", alpha=0.3)

        # Chart 3: Stages passed comparison
        stages_passed = [p.pipeline.stages_passed for p in projects]
        bars = ax3.bar(project_names, stages_passed, color=COLORS["success"], alpha=0.8)
        ax3.set_ylabel("Stages Passed", fontweight="bold")
        ax3.set_title("Pipeline Completion", fontweight="bold")
        ax3.set_xticks(range(len(project_names)))
        ax3.set_xticklabels(project_names, rotation=45, ha="right")
        ax3.set_ylim(0, 8)  # Typical pipeline has 6-7 stages
        ax3.grid(axis="y", alpha=0.3)

        # Add stage count labels
        for bar, stages in zip(bars, stages_passed):
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                f"{stages}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Chart 4: Efficiency metrics (outputs per second)
        outputs_per_second = []
        for project in projects:
            total_outputs = (
                project.outputs.pdf_files
                + project.outputs.figures
                + project.outputs.slides
                + project.outputs.web_outputs
            )
            if project.pipeline.total_duration > 0:
                efficiency = total_outputs / project.pipeline.total_duration
            else:
                efficiency = 0
            outputs_per_second.append(efficiency)

        bars = ax4.bar(
            project_names, outputs_per_second, color=COLORS["primary"], alpha=0.8
        )
        ax4.set_ylabel("Outputs per Second", fontweight="bold")
        ax4.set_title("Pipeline Efficiency", fontweight="bold")
        ax4.set_xticks(range(len(project_names)))
        ax4.set_xticklabels(project_names, rotation=45, ha="right")
        ax4.grid(axis="y", alpha=0.3)

        # Add efficiency labels
        for bar, efficiency in zip(bars, outputs_per_second):
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(outputs_per_second) * 0.02,
                f"{efficiency:.3f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "pipeline_efficiency.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Pipeline efficiency chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "pipeline_efficiency.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Pipeline efficiency chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate pipeline efficiency chart: {e}")

    return saved_files


def generate_pipeline_bottlenecks_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate detailed pipeline bottlenecks visualization.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating pipeline bottlenecks chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Collect bottleneck data
        bottleneck_data = {}
        for project in projects:
            stage = project.pipeline.bottleneck_stage or "Unknown"
            duration = project.pipeline.bottleneck_duration
            percent = project.pipeline.bottleneck_percent

            if stage not in bottleneck_data:
                bottleneck_data[stage] = []
            bottleneck_data[stage].append((project.name, duration, percent))

        if not bottleneck_data:
            return saved_files

        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        fig.suptitle("Pipeline Bottleneck Analysis", fontsize=16, fontweight="bold")

        # Chart 1: Bottleneck duration by stage
        stages = list(bottleneck_data.keys())
        avg_durations = [
            np.mean([d[1] for d in data]) for data in bottleneck_data.values()
        ]
        std_durations = [
            np.std([d[1] for d in data]) for data in bottleneck_data.values()
        ]

        bars = ax1.bar(
            stages,
            avg_durations,
            yerr=std_durations,
            capsize=5,
            color=COLORS["danger"],
            alpha=0.8,
        )
        ax1.set_ylabel("Average Bottleneck Duration (seconds)", fontweight="bold")
        ax1.set_title("Bottleneck Duration by Stage", fontweight="bold")
        ax1.set_xticks(range(len(stages)))
        ax1.set_xticklabels(stages, rotation=45, ha="right")
        ax1.grid(axis="y", alpha=0.3)

        # Chart 2: Bottleneck percentage of total pipeline time
        avg_percentages = [
            np.mean([d[2] for d in data]) for data in bottleneck_data.values()
        ]
        std_percentages = [
            np.std([d[2] for d in data]) for data in bottleneck_data.values()
        ]

        bars = ax2.bar(
            stages,
            avg_percentages,
            yerr=std_percentages,
            capsize=5,
            color=COLORS["warning"],
            alpha=0.8,
        )
        ax2.set_ylabel("Bottleneck Percentage (%)", fontweight="bold")
        ax2.set_title("Bottleneck Impact on Total Time", fontweight="bold")
        ax2.set_xticks(range(len(stages)))
        ax2.set_xticklabels(stages, rotation=45, ha="right")
        ax2.set_ylim(0, 100)
        ax2.grid(axis="y", alpha=0.3)

        # Add percentage labels
        for bar, percentage in zip(bars, avg_percentages):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                f"{percentage:.1f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "pipeline_bottlenecks.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Pipeline bottlenecks chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "pipeline_bottlenecks.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Pipeline bottlenecks chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate pipeline bottlenecks chart: {e}")

    return saved_files


def generate_output_distribution_charts(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate output distribution and comparison charts.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating output distribution charts...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Create comprehensive output analysis
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Output Analysis and Distribution", fontsize=16, fontweight="bold")

        # Chart 1: Total outputs by type (stacked bar)
        project_names = [p.name for p in projects]
        pdf_counts = [p.outputs.pdf_files for p in projects]
        figure_counts = [p.outputs.figures for p in projects]
        slide_counts = [p.outputs.slides for p in projects]
        web_counts = [p.outputs.web_outputs for p in projects]

        ax1.bar(
            project_names, pdf_counts, label="PDFs", color=COLORS["primary"], alpha=0.8
        )
        ax1.bar(
            project_names,
            figure_counts,
            bottom=pdf_counts,
            label="Figures",
            color=COLORS["success"],
            alpha=0.8,
        )
        ax1.bar(
            project_names,
            slide_counts,
            bottom=[pdf + fig for pdf, fig in zip(pdf_counts, figure_counts)],
            label="Slides",
            color=COLORS["warning"],
            alpha=0.8,
        )
        ax1.bar(
            project_names,
            web_counts,
            bottom=[
                pdf + fig + slide
                for pdf, fig, slide in zip(pdf_counts, figure_counts, slide_counts)
            ],
            label="Web",
            color=COLORS["secondary"],
            alpha=0.8,
        )

        ax1.set_ylabel("Output Count", fontweight="bold")
        ax1.set_title("Outputs by Type and Project", fontweight="bold")
        ax1.set_xticks(range(len(project_names)))
        ax1.set_xticklabels(project_names, rotation=45, ha="right")
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # Chart 2: Output efficiency (outputs per pipeline minute)
        outputs_per_minute = []
        for project in projects:
            total_outputs = (
                project.outputs.pdf_files
                + project.outputs.figures
                + project.outputs.slides
                + project.outputs.web_outputs
            )
            if project.pipeline.total_duration > 0:
                efficiency = total_outputs / (
                    project.pipeline.total_duration / 60
                )  # per minute
            else:
                efficiency = 0
            outputs_per_minute.append(efficiency)

        bars = ax2.bar(
            project_names, outputs_per_minute, color=COLORS["primary"], alpha=0.8
        )
        ax2.set_ylabel("Outputs per Minute", fontweight="bold")
        ax2.set_title("Output Generation Efficiency", fontweight="bold")
        ax2.set_xticks(range(len(project_names)))
        ax2.set_xticklabels(project_names, rotation=45, ha="right")
        ax2.grid(axis="y", alpha=0.3)

        # Add efficiency labels
        for bar, efficiency in zip(bars, outputs_per_minute):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(outputs_per_minute) * 0.02,
                f"{efficiency:.2f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Chart 3: File size analysis
        pdf_sizes = [p.outputs.pdf_size_mb for p in projects]
        bars = ax3.bar(project_names, pdf_sizes, color=COLORS["warning"], alpha=0.8)
        ax3.set_ylabel("PDF Size (MB)", fontweight="bold")
        ax3.set_title("PDF File Sizes", fontweight="bold")
        ax3.set_xticks(range(len(project_names)))
        ax3.set_xticklabels(project_names, rotation=45, ha="right")
        ax3.grid(axis="y", alpha=0.3)

        # Add size labels
        for bar, size in zip(bars, pdf_sizes):
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(pdf_sizes) * 0.02,
                f"{size:.1f}MB",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Chart 4: Output completeness radar
        # Show how complete each project's outputs are
        completeness_scores = []
        for project in projects:
            # Calculate a completeness score based on expected outputs
            expected_pdfs = 1  # At least one PDF
            expected_figures = max(
                1, project.manuscript.figures
            )  # At least as many as references
            expected_slides = 4  # Standard slide count
            expected_web = 4  # Standard web count

            pdf_score = (
                min(project.outputs.pdf_files / expected_pdfs, 1.0)
                if expected_pdfs > 0
                else 1.0
            )
            figure_score = (
                min(project.outputs.figures / expected_figures, 1.0)
                if expected_figures > 0
                else 1.0
            )
            slide_score = (
                min(project.outputs.slides / expected_slides, 1.0)
                if expected_slides > 0
                else 1.0
            )
            web_score = (
                min(project.outputs.web_outputs / expected_web, 1.0)
                if expected_web > 0
                else 1.0
            )

            avg_completeness = (pdf_score + figure_score + slide_score + web_score) / 4
            completeness_scores.append(avg_completeness * 100)  # Convert to percentage

        bars = ax4.bar(
            project_names, completeness_scores, color=COLORS["success"], alpha=0.8
        )
        ax4.set_ylabel("Completeness (%)", fontweight="bold")
        ax4.set_title("Output Completeness", fontweight="bold")
        ax4.set_xticks(range(len(project_names)))
        ax4.set_xticklabels(project_names, rotation=45, ha="right")
        ax4.set_ylim(0, 105)
        ax4.grid(axis="y", alpha=0.3)

        # Add completeness labels
        for bar, completeness in zip(bars, completeness_scores):
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                f"{completeness:.0f}%",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "output_distribution.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Output distribution chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "output_distribution.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Output distribution chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate output distribution charts: {e}")

    return saved_files


def generate_output_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate detailed output comparison visualization.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating output comparison chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Create comparison chart
        fig, ax = plt.subplots(figsize=(14, 8))

        # Prepare data
        project_names = [p.name for p in projects]
        output_types = ["PDFs", "Figures", "Slides", "Web", "Data Files"]
        data = []

        for project in projects:
            project_data = [
                project.outputs.pdf_files,
                project.outputs.figures,
                project.outputs.slides,
                project.outputs.web_outputs,
                project.outputs.data_files,
            ]
            data.append(project_data)

        # Create grouped bar chart
        x = np.arange(len(project_names))
        width = 0.15
        colors = [
            COLORS["primary"],
            COLORS["success"],
            COLORS["warning"],
            COLORS["secondary"],
            "#9B59B6",
        ]

        for i, (output_type, color) in enumerate(zip(output_types, colors)):
            values = [project_data[i] for project_data in data]
            bars = ax.bar(
                x + i * width, values, width, label=output_type, color=color, alpha=0.8
            )

            # Add value labels
            for bar, value in zip(bars, values):
                if value > 0:  # Only label non-zero values
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(max(d) for d in data) * 0.01,
                        f"{value}",
                        ha="center",
                        va="bottom",
                        fontweight="bold",
                        fontsize=9,
                    )

        ax.set_ylabel("Count", fontweight="bold")
        ax.set_title(
            "Output Comparison by Type and Project", fontweight="bold", fontsize=14
        )
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(project_names, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "output_comparison.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Output comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "output_comparison.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Output comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate output comparison chart: {e}")

    return saved_files


def generate_codebase_complexity_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate codebase complexity visualization.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating codebase complexity chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Create complexity analysis
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle("Codebase Complexity Analysis", fontsize=16, fontweight="bold")

        # Chart 1: Lines of code comparison
        project_names = [p.name for p in projects]
        source_lines = [p.codebase.source_lines for p in projects]
        script_lines = [p.codebase.script_lines for p in projects]

        x = np.arange(len(project_names))
        width = 0.35

        bars1 = ax1.bar(
            x - width / 2,
            source_lines,
            width,
            label="Source Lines",
            color=COLORS["primary"],
            alpha=0.8,
        )
        bars2 = ax1.bar(
            x + width / 2,
            script_lines,
            width,
            label="Script Lines",
            color=COLORS["success"],
            alpha=0.8,
        )

        ax1.set_ylabel("Lines of Code", fontweight="bold")
        ax1.set_title("Code Volume by Project", fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(project_names, rotation=45, ha="right")
        ax1.legend()
        ax1.grid(axis="y", alpha=0.3)

        # Add value labels
        for bars, values in [(bars1, source_lines), (bars2, script_lines)]:
            for bar, value in zip(bars, values):
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(source_lines + script_lines) * 0.02,
                    f"{value:,}",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                    fontsize=9,
                )

        # Chart 2: Methods vs Classes scatter
        methods = [p.codebase.methods for p in projects]
        classes = [p.codebase.classes for p in projects]

        scatter = ax2.scatter(
            methods,
            classes,
            s=100,
            c=range(len(projects)),
            cmap="viridis",
            alpha=0.8,
            edgecolors="black",
            linewidth=1,
        )

        for i, name in enumerate(project_names):
            ax2.annotate(
                name,
                (methods[i], classes[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
            )

        ax2.set_xlabel("Methods", fontweight="bold")
        ax2.set_ylabel("Classes", fontweight="bold")
        ax2.set_title("Code Structure Complexity", fontweight="bold")
        ax2.grid(True, alpha=0.3)

        # Chart 3: Scripts comparison
        scripts = [p.codebase.scripts for p in projects]
        bars = ax3.bar(project_names, scripts, color=COLORS["warning"], alpha=0.8)
        ax3.set_ylabel("Script Files", fontweight="bold")
        ax3.set_title("Script Count by Project", fontweight="bold")
        ax3.set_xticks(range(len(project_names)))
        ax3.set_xticklabels(project_names, rotation=45, ha="right")
        ax3.grid(axis="y", alpha=0.3)

        # Add script count labels
        for bar, script_count in zip(bars, scripts):
            ax3.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(scripts) * 0.02,
                f"{script_count}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        # Chart 4: Complexity ratio (methods per 100 lines)
        complexity_ratios = []
        for project in projects:
            total_lines = project.codebase.source_lines
            if total_lines > 0:
                ratio = (
                    project.codebase.methods / total_lines
                ) * 100  # methods per 100 lines
            else:
                ratio = 0
            complexity_ratios.append(ratio)

        bars = ax4.bar(
            project_names, complexity_ratios, color=COLORS["secondary"], alpha=0.8
        )
        ax4.set_ylabel("Methods per 100 Lines", fontweight="bold")
        ax4.set_title("Code Density Metric", fontweight="bold")
        ax4.set_xticks(range(len(project_names)))
        ax4.set_xticklabels(project_names, rotation=45, ha="right")
        ax4.grid(axis="y", alpha=0.3)

        # Add ratio labels
        for bar, ratio in zip(bars, complexity_ratios):
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(complexity_ratios) * 0.02,
                f"{ratio:.1f}",
                ha="center",
                va="bottom",
                fontweight="bold",
            )

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "codebase_complexity.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Codebase complexity chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "codebase_complexity.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Codebase complexity chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate codebase complexity chart: {e}")

    return saved_files


def generate_codebase_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate detailed codebase comparison visualization.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved file paths
    """
    logger.info("Generating codebase comparison chart...")

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    saved_files = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Create comprehensive codebase comparison
        fig, ax = plt.subplots(figsize=(14, 8))

        # Prepare data for grouped bar chart
        project_names = [p.name for p in projects]
        metrics = ["Source Files", "Source Lines", "Methods", "Classes", "Scripts"]
        data = []

        for project in projects:
            project_data = [
                project.codebase.source_files,
                project.codebase.source_lines,
                project.codebase.methods,
                project.codebase.classes,
                project.codebase.scripts,
            ]
            data.append(project_data)

        # Create grouped bar chart
        x = np.arange(len(project_names))
        width = 0.15
        colors = [
            COLORS["primary"],
            COLORS["success"],
            COLORS["warning"],
            COLORS["secondary"],
            "#9B59B6",
        ]

        for i, (metric, color) in enumerate(zip(metrics, colors)):
            values = [project_data[i] for project_data in data]
            bars = ax.bar(
                x + i * width, values, width, label=metric, color=color, alpha=0.8
            )

            # Add value labels for non-zero values
            for bar, value in zip(bars, values):
                if value > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(max(d) for d in data) * 0.01,
                        f"{value:,}",
                        ha="center",
                        va="bottom",
                        fontweight="bold",
                        fontsize=8,
                    )

        ax.set_ylabel("Count", fontweight="bold")
        ax.set_title(
            "Codebase Comparison by Metric and Project", fontweight="bold", fontsize=14
        )
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(project_names, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        # Use log scale for y-axis if there's a large range
        all_values = [val for project_data in data for val in project_data]
        if max(all_values) / min([v for v in all_values if v > 0]) > 100:
            ax.set_yscale("log")
            ax.set_ylabel("Count (log scale)", fontweight="bold")

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path(
            "codebase_comparison.png", output_dir, FileType.PNG
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Codebase comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "codebase_comparison.pdf", output_dir, FileType.PDF
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Codebase comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:
        logger.error(f"Failed to generate codebase comparison chart: {e}")

    return saved_files


def generate_detailed_project_breakdown_csv(
    summary: ExecutiveSummary, output_dir: Path
) -> Path:
    """Generate detailed project breakdown CSV with all metrics and explanations."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path(
        "detailed_project_breakdown.csv", output_dir, FileType.CSV
    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header with explanations
        writer.writerow(
            [
                "Project",
                "Category",
                "Metric",
                "Value",
                "Unit",
                "Description",
                "Health_Impact",
                "Recommended_Range",
            ]
        )

        for project in summary.project_metrics:
            # Manuscript metrics
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Total_Words",
                    project.manuscript.total_words,
                    "words",
                    "Total words in manuscript sections",
                    "High",
                    "1000-20000 words",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Sections",
                    project.manuscript.sections,
                    "count",
                    "Number of manuscript sections",
                    "Medium",
                    "3-20 sections",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Equations",
                    project.manuscript.equations,
                    "count",
                    "Mathematical equations in manuscript",
                    "Low",
                    "0-50 equations",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Figures",
                    project.manuscript.figures,
                    "count",
                    "Figure references in manuscript",
                    "Low",
                    "0-20 figures",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "References",
                    project.manuscript.references,
                    "count",
                    "Citation references",
                    "Medium",
                    "10-200 references",
                ]
            )

            # Codebase metrics
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Files",
                    project.codebase.source_files,
                    "files",
                    "Python source files",
                    "Medium",
                    "1-20 files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Lines",
                    project.codebase.source_lines,
                    "lines",
                    "Lines of source code",
                    "Medium",
                    "100-5000 lines",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Methods",
                    project.codebase.methods,
                    "count",
                    "Function/method definitions",
                    "Medium",
                    "10-500 methods",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Classes",
                    project.codebase.classes,
                    "count",
                    "Class definitions",
                    "Low",
                    "0-50 classes",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Scripts",
                    project.codebase.scripts,
                    "files",
                    "Analysis scripts",
                    "Low",
                    "0-10 scripts",
                ]
            )

            # Test metrics
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Test_Files",
                    project.tests.test_files,
                    "files",
                    "Test files discovered",
                    "High",
                    "1+ files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Total_Tests",
                    project.tests.total_tests,
                    "tests",
                    "Total test cases (-1 = unavailable)",
                    "High",
                    "10-1000 tests",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Coverage_Percent",
                    project.tests.coverage_percent,
                    "percent",
                    "Code coverage percentage",
                    "High",
                    "90-100%",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Testing",
                    "Execution_Time",
                    project.tests.execution_time,
                    "seconds",
                    "Test execution time",
                    "Low",
                    "1-300 seconds",
                ]
            )

            # Output metrics
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "PDF_Files",
                    project.outputs.pdf_files,
                    "files",
                    "Generated PDF documents",
                    "High",
                    "1+ files",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "PDF_Size_MB",
                    f"{project.outputs.pdf_size_mb:.2f}",
                    "MB",
                    "Total PDF file size",
                    "Low",
                    "0.1-10 MB",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Figures",
                    project.outputs.figures,
                    "files",
                    "Generated figure files",
                    "Medium",
                    "0-50 figures",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Slides",
                    project.outputs.slides,
                    "files",
                    "Generated slide files",
                    "Medium",
                    "0-20 slide sets",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Web_Outputs",
                    project.outputs.web_outputs,
                    "files",
                    "Generated web files",
                    "Medium",
                    "0-20 web files",
                ]
            )

            # Pipeline metrics
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Total_Duration",
                    project.pipeline.total_duration,
                    "seconds",
                    "Total pipeline execution time",
                    "Medium",
                    "60-600 seconds",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Stages_Passed",
                    project.pipeline.stages_passed,
                    "stages",
                    "Pipeline stages completed successfully",
                    "High",
                    "6 stages",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Bottleneck_Stage",
                    project.pipeline.bottleneck_stage,
                    "stage_name",
                    "Slowest pipeline stage",
                    "Medium",
                    "Varies by project",
                ]
            )
            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Bottleneck_Duration",
                    project.pipeline.bottleneck_duration,
                    "seconds",
                    "Time spent in bottleneck stage",
                    "Medium",
                    "10-300 seconds",
                ]
            )

    logger.info(f"Detailed project breakdown CSV saved: {csv_path}")
    return csv_path


def generate_comparative_analysis_csv(
    summary: ExecutiveSummary, output_dir: Path
) -> Path:
    """Generate comparative analysis CSV with rankings and percentiles."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path(
        "comparative_analysis.csv", output_dir, FileType.CSV
    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Project",
                "Metric_Category",
                "Metric_Name",
                "Value",
                "Unit",
                "Rank",
                "Percentile",
                "vs_Average",
                "Performance_Rating",
            ]
        )

        projects = summary.project_metrics
        if not projects:
            return csv_path

        # Calculate comparative statistics for each metric
        metrics_data = {
            "manuscript_words": [p.manuscript.total_words for p in projects],
            "manuscript_sections": [p.manuscript.sections for p in projects],
            "codebase_lines": [p.codebase.source_lines for p in projects],
            "codebase_methods": [p.codebase.methods for p in projects],
            "pipeline_duration": [p.pipeline.total_duration for p in projects],
            "output_total": [p.outputs.total_outputs for p in projects],
        }

        def calculate_percentile_and_rank(value, values_list, higher_is_better=True):
            """Calculate percentile rank for a value in a list."""
            if not values_list:
                return (
                    50,
                    len(
                        [
                            v
                            for v in values_list
                            if (v > value if higher_is_better else v < value)
                        ]
                    )
                    + 1,
                )

            sorted_values = sorted(values_list, reverse=higher_is_better)
            try:
                rank = sorted_values.index(value) + 1
                percentile = (
                    (len(values_list) - rank) / (len(values_list) - 1) * 100
                    if len(values_list) > 1
                    else 100
                )
            except ValueError:
                # Handle ties or missing values
                rank = (
                    len(
                        [
                            v
                            for v in values_list
                            if (v > value if higher_is_better else v < value)
                        ]
                    )
                    + 1
                )
                percentile = (rank - 1) / len(values_list) * 100

            return percentile, rank

        def get_performance_rating(percentile, higher_is_better=True):
            """Convert percentile to performance rating."""
            if higher_is_better:
                if percentile >= 80:
                    return "Excellent"
                elif percentile >= 60:
                    return "Good"
                elif percentile >= 40:
                    return "Average"
                elif percentile >= 20:
                    return "Below Average"
                else:
                    return "Poor"
            else:
                # Lower is better (like duration)
                if percentile >= 80:
                    return "Poor"
                elif percentile >= 60:
                    return "Below Average"
                elif percentile >= 40:
                    return "Average"
                elif percentile >= 20:
                    return "Good"
                else:
                    return "Excellent"

        # Generate comparative data for each project and metric
        for project in projects:
            # Manuscript metrics
            percentile, rank = calculate_percentile_and_rank(
                project.manuscript.total_words,
                metrics_data["manuscript_words"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["manuscript_words"]) / len(
                metrics_data["manuscript_words"]
            )
            vs_avg = (
                ((project.manuscript.total_words - avg) / avg * 100) if avg > 0 else 0
            )

            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Total_Words",
                    project.manuscript.total_words,
                    "words",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            percentile, rank = calculate_percentile_and_rank(
                project.manuscript.sections,
                metrics_data["manuscript_sections"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["manuscript_sections"]) / len(
                metrics_data["manuscript_sections"]
            )
            vs_avg = ((project.manuscript.sections - avg) / avg * 100) if avg > 0 else 0

            writer.writerow(
                [
                    project.name,
                    "Manuscript",
                    "Sections",
                    project.manuscript.sections,
                    "count",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            # Codebase metrics
            percentile, rank = calculate_percentile_and_rank(
                project.codebase.source_lines,
                metrics_data["codebase_lines"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["codebase_lines"]) / len(
                metrics_data["codebase_lines"]
            )
            vs_avg = (
                ((project.codebase.source_lines - avg) / avg * 100) if avg > 0 else 0
            )

            writer.writerow(
                [
                    project.name,
                    "Codebase",
                    "Source_Lines",
                    project.codebase.source_lines,
                    "lines",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

            # Pipeline metrics
            percentile, rank = calculate_percentile_and_rank(
                project.pipeline.total_duration,
                metrics_data["pipeline_duration"],
                higher_is_better=False,
            )
            avg = sum(metrics_data["pipeline_duration"]) / len(
                metrics_data["pipeline_duration"]
            )
            vs_avg = (
                ((project.pipeline.total_duration - avg) / avg * 100) if avg > 0 else 0
            )

            writer.writerow(
                [
                    project.name,
                    "Pipeline",
                    "Duration",
                    project.pipeline.total_duration,
                    "seconds",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, False),
                ]
            )

            # Output metrics
            percentile, rank = calculate_percentile_and_rank(
                project.outputs.total_outputs,
                metrics_data["output_total"],
                higher_is_better=True,
            )
            avg = sum(metrics_data["output_total"]) / len(metrics_data["output_total"])
            vs_avg = (
                ((project.outputs.total_outputs - avg) / avg * 100) if avg > 0 else 0
            )

            writer.writerow(
                [
                    project.name,
                    "Outputs",
                    "Total_Files",
                    project.outputs.total_outputs,
                    "files",
                    rank,
                    f"{percentile:.1f}%",
                    f"{vs_avg:+.1f}%",
                    get_performance_rating(percentile, True),
                ]
            )

    logger.info(f"Comparative analysis CSV saved: {csv_path}")
    return csv_path


def generate_prioritized_recommendations_csv(
    summary: ExecutiveSummary, output_dir: Path
) -> Path:
    """Generate prioritized recommendations CSV with impact and effort estimates."""
    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_path = organizer.get_output_path(
        "recommendations_prioritized.csv", output_dir, FileType.CSV
    )

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Priority_Level",
                "Priority_Score",
                "Category",
                "Recommendation",
                "Impact_Level",
                "Effort_Level",
                "Time_Estimate",
                "Affected_Projects",
                "Rationale",
                "Next_Steps",
            ]
        )

        # Categorize recommendations with priority scoring
        recommendations_data = []

        for rec in summary.recommendations:
            # Determine priority based on keywords and content
            priority_score = 1  # Default low
            priority_level = "Low"
            impact_level = "Low"
            effort_level = "Low"
            time_estimate = "1-2 hours"
            category = "General"
            affected_projects = "All"
            next_steps = "Review and implement as appropriate"

            if any(
                keyword in rec.lower()
                for keyword in ["critical", "immediate", "failing", "broken"]
            ):
                priority_score = 5
                priority_level = "High"
                impact_level = "High"
                effort_level = "Medium"
                time_estimate = "1-2 days"
            elif any(
                keyword in rec.lower() for keyword in ["below", "improve", "consider"]
            ):
                priority_score = 3
                priority_level = "Medium"
                impact_level = "Medium"
                effort_level = "Low"
                time_estimate = "4-8 hours"

            # Categorize by content
            if "test" in rec.lower():
                category = "Testing"
            elif "coverage" in rec.lower():
                category = "Code Quality"
            elif "manuscript" in rec.lower() or "research" in rec.lower():
                category = "Content"
            elif "pipeline" in rec.lower():
                category = "Performance"
            elif "output" in rec.lower():
                category = "Deliverables"

            # Extract affected projects from recommendation text
            if "project," in rec.lower():
                # Parse project names from recommendation
                affected_projects = "Multiple"
            elif any(proj.name in rec for proj in summary.project_metrics):
                affected_projects = next(
                    (proj.name for proj in summary.project_metrics if proj.name in rec),
                    "All",
                )

            recommendations_data.append(
                {
                    "rec": rec,
                    "priority_score": priority_score,
                    "priority_level": priority_level,
                    "category": category,
                    "impact_level": impact_level,
                    "effort_level": effort_level,
                    "time_estimate": time_estimate,
                    "affected_projects": affected_projects,
                    "next_steps": next_steps,
                }
            )

        # Sort by priority score (highest first)
        recommendations_data.sort(key=lambda x: x["priority_score"], reverse=True)

        # Write sorted recommendations
        for item in recommendations_data:
            writer.writerow(
                [
                    item["priority_level"],
                    item["priority_score"],
                    item["category"],
                    item["rec"],
                    item["impact_level"],
                    item["effort_level"],
                    item["time_estimate"],
                    item["affected_projects"],
                    f"Priority {item['priority_level']} - {item['impact_level']} impact",
                    item["next_steps"],
                ]
            )

    logger.info(f"Prioritized recommendations CSV saved: {csv_path}")
    return csv_path


def generate_csv_data_tables(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate CSV data tables for dashboard data export.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of saved CSV file paths
    """
    import csv

    from infrastructure.reporting.executive_reporter import \
        calculate_project_health_score

    organizer = OutputOrganizer()
    organizer.ensure_directory_structure(output_dir)
    csv_files = {}

    # Project metrics CSV
    organizer = OutputOrganizer()
    metrics_csv = organizer.get_output_path(
        "project_metrics.csv", output_dir, FileType.CSV
    )
    with open(metrics_csv, "w", newline="") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(
            [
                "Project",
                "Health_Score",
                "Health_Grade",
                "Manuscript_Words",
                "Manuscript_Sections",
                "Manuscript_Equations",
                "Manuscript_Figures",
                "Test_Total",
                "Test_Passed",
                "Test_Failed",
                "Test_Coverage_Pct",
                "Test_Execution_Time",
                "Pipeline_Duration",
                "Pipeline_Stages_Passed",
                "Pipeline_Bottleneck_Stage",
                "Pipeline_Bottleneck_Duration",
                "Output_PDFs",
                "Output_PDF_Size_MB",
                "Output_Figures",
                "Output_Slides",
                "Output_Web",
                "Output_Total",
            ]
        )

        # Data rows
        for project in summary.project_metrics:
            health = calculate_project_health_score(project)
            writer.writerow(
                [
                    project.name,
                    health["percentage"],
                    health["grade"],
                    project.manuscript.total_words,
                    project.manuscript.sections,
                    project.manuscript.equations,
                    project.manuscript.figures,
                    project.tests.total_tests,
                    project.tests.passed,
                    project.tests.failed,
                    project.tests.coverage_percent,
                    project.tests.execution_time,
                    project.pipeline.total_duration,
                    project.pipeline.stages_passed,
                    project.pipeline.bottleneck_stage,
                    project.pipeline.bottleneck_duration,
                    project.outputs.pdf_files,
                    project.outputs.pdf_size_mb,
                    project.outputs.figures,
                    project.outputs.slides,
                    project.outputs.web_outputs,
                    project.outputs.total_outputs,
                ]
            )

    csv_files["metrics"] = metrics_csv
    logger.info(f"Generated CSV metrics table: {metrics_csv}")

    # Aggregate metrics CSV
    aggregate_csv = organizer.get_output_path(
        "aggregate_metrics.csv", output_dir, FileType.CSV
    )
    with open(aggregate_csv, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["Category", "Metric", "Value", "Unit"])

        agg = summary.aggregate_metrics

        # Manuscript aggregates
        manuscript = agg.get("manuscript", {})
        writer.writerow(
            ["Manuscript", "Total_Words", manuscript.get("total_words", 0), "words"]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_Sections",
                manuscript.get("total_sections", 0),
                "sections",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_Equations",
                manuscript.get("total_equations", 0),
                "equations",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_Figures",
                manuscript.get("total_figures", 0),
                "figures",
            ]
        )
        writer.writerow(
            [
                "Manuscript",
                "Total_References",
                manuscript.get("total_references", 0),
                "references",
            ]
        )

        # Test aggregates
        tests = agg.get("tests", {})
        writer.writerow(["Tests", "Total_Tests", tests.get("total_tests", 0), "tests"])
        writer.writerow(
            ["Tests", "Total_Passed", tests.get("total_passed", 0), "tests"]
        )
        writer.writerow(
            ["Tests", "Total_Failed", tests.get("total_failed", 0), "tests"]
        )
        writer.writerow(
            ["Tests", "Average_Coverage", tests.get("average_coverage", 0), "percent"]
        )
        writer.writerow(
            [
                "Tests",
                "Total_Execution_Time",
                tests.get("total_execution_time", 0),
                "seconds",
            ]
        )

        # Pipeline aggregates
        pipeline = agg.get("pipeline", {})
        writer.writerow(
            ["Pipeline", "Total_Duration", pipeline.get("total_duration", 0), "seconds"]
        )
        writer.writerow(
            [
                "Pipeline",
                "Average_Duration",
                pipeline.get("average_duration", 0),
                "seconds",
            ]
        )
        writer.writerow(
            [
                "Pipeline",
                "Total_Stages_Passed",
                pipeline.get("total_stages_passed", 0),
                "stages",
            ]
        )
        writer.writerow(
            [
                "Pipeline",
                "Total_Stages_Failed",
                pipeline.get("total_stages_failed", 0),
                "stages",
            ]
        )

        # Output aggregates
        outputs = agg.get("outputs", {})
        writer.writerow(
            ["Outputs", "Total_PDFs", outputs.get("total_pdfs", 0), "files"]
        )
        writer.writerow(
            ["Outputs", "Total_Size_MB", outputs.get("total_size_mb", 0), "MB"]
        )
        writer.writerow(
            ["Outputs", "Total_Figures", outputs.get("total_figures", 0), "files"]
        )
        writer.writerow(
            ["Outputs", "Total_Slides", outputs.get("total_slides", 0), "files"]
        )
        writer.writerow(["Outputs", "Total_Web", outputs.get("total_web", 0), "files"])

    csv_files["aggregates"] = aggregate_csv
    logger.info(f"Generated CSV aggregates table: {aggregate_csv}")

    # Health scores CSV
    health_csv = organizer.get_output_path(
        "health_scores.csv", output_dir, FileType.CSV
    )
    with open(health_csv, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "Project",
                "Overall_Score",
                "Overall_Percentage",
                "Overall_Grade",
                "Overall_Status",
                "Test_Coverage_Score",
                "Test_Coverage_Grade",
                "Test_Failures_Score",
                "Test_Failures_Grade",
                "Manuscript_Size_Score",
                "Manuscript_Size_Grade",
                "Outputs_Score",
                "Outputs_Grade",
            ]
        )

        for project_name, health in summary.health_scores.items():
            writer.writerow(
                [
                    project_name,
                    health["score"],
                    health["percentage"],
                    health["grade"],
                    health["status"],
                    health["factors"]["test_coverage"]["score"],
                    health["factors"]["test_coverage"]["grade"],
                    health["factors"]["test_failures"]["score"],
                    health["factors"]["test_failures"]["grade"],
                    health["factors"]["manuscript_size"]["score"],
                    health["factors"]["manuscript_size"]["grade"],
                    health["factors"]["outputs"]["score"],
                    health["factors"]["outputs"]["grade"],
                ]
            )

    csv_files["health"] = health_csv
    logger.info(f"Generated CSV health scores table: {health_csv}")

    return csv_files


def generate_all_dashboards(
    summary: ExecutiveSummary, output_dir: Path
) -> Dict[str, Path]:
    """Generate all dashboard formats including CSV data exports.

    Args:
        summary: ExecutiveSummary instance
        output_dir: Output directory path

    Returns:
        Dictionary of all saved file paths
    """
    logger.info("Generating all dashboard formats...")

    all_files = {}

    # Generate matplotlib dashboards (PNG + PDF)
    matplotlib_files = generate_matplotlib_dashboard(summary, output_dir)
    all_files.update(matplotlib_files)

    # Generate health score visualizations
    try:
        health_radar_files = generate_health_radar_chart(summary, output_dir)
        all_files.update(health_radar_files)
    except Exception as e:
        logger.warning(f"Could not generate health radar chart: {e}")

    try:
        health_comparison_files = generate_health_comparison_chart(summary, output_dir)
        all_files.update(health_comparison_files)
    except Exception as e:
        logger.warning(f"Could not generate health comparison chart: {e}")

    # Generate individual project dashboards
    try:
        project_dashboard_files = generate_project_breakdowns(summary, output_dir)
        all_files.update(project_dashboard_files)
    except Exception as e:
        logger.warning(f"Could not generate project dashboards: {e}")

    # Generate pipeline efficiency visualizations
    try:
        pipeline_efficiency_files = generate_pipeline_efficiency_chart(
            summary, output_dir
        )
        all_files.update(pipeline_efficiency_files)
    except Exception as e:
        logger.warning(f"Could not generate pipeline efficiency chart: {e}")

    try:
        pipeline_bottlenecks_files = generate_pipeline_bottlenecks_chart(
            summary, output_dir
        )
        all_files.update(pipeline_bottlenecks_files)
    except Exception as e:
        logger.warning(f"Could not generate pipeline bottlenecks chart: {e}")

    # Generate output analysis visualizations
    try:
        output_distribution_files = generate_output_distribution_charts(
            summary, output_dir
        )
        all_files.update(output_distribution_files)
    except Exception as e:
        logger.warning(f"Could not generate output distribution charts: {e}")

    try:
        output_comparison_files = generate_output_comparison_chart(summary, output_dir)
        all_files.update(output_comparison_files)
    except Exception as e:
        logger.warning(f"Could not generate output comparison chart: {e}")

    # Generate codebase analysis visualizations
    try:
        codebase_complexity_files = generate_codebase_complexity_chart(
            summary, output_dir
        )
        all_files.update(codebase_complexity_files)
    except Exception as e:
        logger.warning(f"Could not generate codebase complexity chart: {e}")

    try:
        codebase_comparison_files = generate_codebase_comparison_chart(
            summary, output_dir
        )
        all_files.update(codebase_comparison_files)
    except Exception as e:
        logger.warning(f"Could not generate codebase comparison chart: {e}")

    # Generate plotly dashboard (HTML)
    try:
        plotly_file = generate_plotly_dashboard(summary, output_dir)
        if plotly_file:
            all_files["html"] = plotly_file
    except Exception as e:
        logger.warning(f"Could not generate interactive dashboard: {e}")

    # Generate CSV data tables
    try:
        # Existing aggregate CSV
        aggregate_csv = generate_csv_data_tables(summary, output_dir)
        all_files.update(aggregate_csv)

        # New detailed CSVs
        detailed_csv = generate_detailed_project_breakdown_csv(summary, output_dir)
        all_files["detailed_breakdown_csv"] = detailed_csv

        comparative_csv = generate_comparative_analysis_csv(summary, output_dir)
        all_files["comparative_analysis_csv"] = comparative_csv

        recommendations_csv = generate_prioritized_recommendations_csv(
            summary, output_dir
        )
        all_files["recommendations_csv"] = recommendations_csv

    except Exception as e:
        logger.warning(f"Could not generate CSV data tables: {e}")

    # Generate manuscript overviews for each project
    try:
        manuscript_overview_files = generate_all_manuscript_overviews(
            summary, output_dir, Path(".")
        )
        all_files.update(manuscript_overview_files)
    except Exception as e:
        logger.warning(f"Could not generate manuscript overviews: {e}")

    logger.info(f"Generated {len(all_files)} dashboard and data file(s)")
    return all_files

"""Specialized dashboard visualizations for executive reporting.

Extracted from ``_dashboard_matplotlib.py`` — health radar, pipeline efficiency,
codebase complexity, and output distribution chart generators.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting.executive_reporter import ExecutiveSummary
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

def generate_health_radar_chart(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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
        ax.set_title("Project Health Score Analysis", size=16, fontweight="bold", pad=20)
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
        png_path = organizer.get_output_path("health_scores_radar.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Health radar chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("health_scores_radar.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Health radar chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate health radar chart: {e}", exc_info=True)

    return saved_files


def generate_health_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Extract health scores
        project_names = []
        overall_scores = []
        factor_scores: dict[str, float] = {
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
                factor_scores["coverage"].append(factors.get("test_coverage", {}).get("score", 0))
                factor_scores["integrity"].append(factors.get("test_failures", {}).get("score", 0))
                factor_scores["manuscript"].append(
                    factors.get("manuscript_size", {}).get("score", 0)
                )
                factor_scores["outputs"].append(factors.get("outputs", {}).get("score", 0))

        if not project_names:
            return saved_files

        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # Overall health scores
        bars = ax1.bar(project_names, overall_scores, color=COLORS["primary"], alpha=0.8)
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
            "health_scores_comparison.png",  # type: ignore[arg-type]
            output_dir,
            FileType.PNG,
        )
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Health comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path(
            "health_scores_comparison.pdf",  # type: ignore[arg-type]
            output_dir,
            FileType.PDF,
        )
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Health comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate health comparison chart: {e}", exc_info=True)

    return saved_files


def generate_project_breakdowns(summary: ExecutiveSummary, output_dir: Path) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        for project in projects:
            # Create individual dashboard for this project
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle(f"Project Dashboard: {project.name}", fontsize=16, fontweight="bold")

            # Manuscript metrics
            ax1 = axes[0, 0]
            manuscript_data = [
                project.manuscript.total_words,
                project.manuscript.sections,
                project.manuscript.equations,
                project.manuscript.figures,
            ]
            manuscript_labels = ["Words", "Sections", "Equations", "Figures"]
            bars = ax1.bar(manuscript_labels, manuscript_data, color=COLORS["primary"], alpha=0.8)
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
            bars = ax2.bar(codebase_labels, codebase_data, color=COLORS["success"], alpha=0.8)
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
                        if bottleneck_name in stage.lower() or stage.lower() in bottleneck_name:
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

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate project breakdowns: {e}", exc_info=True)

    return saved_files


def generate_pipeline_efficiency_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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
        bottlenecks: dict[str, Any] = {}
        for project in projects:
            stage = project.pipeline.bottleneck_stage or "Unknown"
            if stage not in bottlenecks:
                bottlenecks[stage] = []
            bottlenecks[stage].append(project.pipeline.bottleneck_duration)

        if bottlenecks:
            bottleneck_labels = list(bottlenecks.keys())
            bottleneck_means = [np.mean(durations) for durations in bottlenecks.values()]
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

        bars = ax4.bar(project_names, outputs_per_second, color=COLORS["primary"], alpha=0.8)
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
        png_path = organizer.get_output_path("pipeline_efficiency.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Pipeline efficiency chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("pipeline_efficiency.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Pipeline efficiency chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate pipeline efficiency chart: {e}", exc_info=True)

    return saved_files


def generate_pipeline_bottlenecks_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

    try:
        projects = summary.project_metrics
        if not projects:
            return saved_files

        # Collect bottleneck data
        bottleneck_data: dict[str, Any] = {}
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
        avg_durations = [np.mean([d[1] for d in data]) for data in bottleneck_data.values()]
        std_durations = [np.std([d[1] for d in data]) for data in bottleneck_data.values()]

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
        avg_percentages = [np.mean([d[2] for d in data]) for data in bottleneck_data.values()]
        std_percentages = [np.std([d[2] for d in data]) for data in bottleneck_data.values()]

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
        png_path = organizer.get_output_path("pipeline_bottlenecks.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Pipeline bottlenecks chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("pipeline_bottlenecks.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Pipeline bottlenecks chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate pipeline bottlenecks chart: {e}", exc_info=True)

    return saved_files


def generate_output_distribution_charts(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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

        ax1.bar(project_names, pdf_counts, label="PDFs", color=COLORS["primary"], alpha=0.8)
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
                efficiency = total_outputs / (project.pipeline.total_duration / 60)  # per minute
            else:
                efficiency = 0
            outputs_per_minute.append(efficiency)

        bars = ax2.bar(project_names, outputs_per_minute, color=COLORS["primary"], alpha=0.8)
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
            expected_figures = max(1, project.manuscript.figures)  # At least as many as references
            expected_slides = 4  # Standard slide count
            expected_web = 4  # Standard web count

            pdf_score = (
                min(project.outputs.pdf_files / expected_pdfs, 1.0) if expected_pdfs > 0 else 1.0
            )
            figure_score = (
                min(project.outputs.figures / expected_figures, 1.0)
                if expected_figures > 0
                else 1.0
            )
            slide_score = (
                min(project.outputs.slides / expected_slides, 1.0) if expected_slides > 0 else 1.0
            )
            web_score = (
                min(project.outputs.web_outputs / expected_web, 1.0) if expected_web > 0 else 1.0
            )

            avg_completeness = (pdf_score + figure_score + slide_score + web_score) / 4
            completeness_scores.append(avg_completeness * 100)  # Convert to percentage

        bars = ax4.bar(project_names, completeness_scores, color=COLORS["success"], alpha=0.8)
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
        png_path = organizer.get_output_path("output_distribution.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Output distribution chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("output_distribution.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Output distribution chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate output distribution charts: {e}", exc_info=True)

    return saved_files


def generate_output_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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
            bars = ax.bar(x + i * width, values, width, label=output_type, color=color, alpha=0.8)

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
        ax.set_title("Output Comparison by Type and Project", fontweight="bold", fontsize=14)
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(project_names, rotation=45, ha="right")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        # Save PNG
        organizer = OutputOrganizer()
        png_path = organizer.get_output_path("output_comparison.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Output comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("output_comparison.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Output comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate output comparison chart: {e}", exc_info=True)

    return saved_files


def generate_codebase_complexity_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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

        ax2.scatter(
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
                ratio = (project.codebase.methods / total_lines) * 100  # methods per 100 lines
            else:
                ratio = 0
            complexity_ratios.append(ratio)

        bars = ax4.bar(project_names, complexity_ratios, color=COLORS["secondary"], alpha=0.8)
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
        png_path = organizer.get_output_path("codebase_complexity.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Codebase complexity chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("codebase_complexity.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Codebase complexity chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate codebase complexity chart: {e}", exc_info=True)

    return saved_files


def generate_codebase_comparison_chart(
    summary: ExecutiveSummary, output_dir: Path
) -> dict[str, Path]:
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
    saved_files: dict[str, Path] = {}

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
            bars = ax.bar(x + i * width, values, width, label=metric, color=color, alpha=0.8)

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
        ax.set_title("Codebase Comparison by Metric and Project", fontweight="bold", fontsize=14)
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
        png_path = organizer.get_output_path("codebase_comparison.png", output_dir, FileType.PNG)
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        saved_files["png"] = png_path
        logger.info(f"Codebase comparison chart (PNG) saved: {png_path}")

        # Save PDF
        pdf_path = organizer.get_output_path("codebase_comparison.pdf", output_dir, FileType.PDF)
        fig.savefig(pdf_path, bbox_inches="tight")
        saved_files["pdf"] = pdf_path
        logger.info(f"Codebase comparison chart (PDF) saved: {pdf_path}")

        plt.close(fig)

    except Exception as e:  # noqa: BLE001 — matplotlib may raise any exception type
        logger.error(f"Failed to generate codebase comparison chart: {e}", exc_info=True)

    return saved_files



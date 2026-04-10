"""Health-score dashboard charts: radar, comparison, per-project breakdowns.

Extracted from the former ``_dashboard_specialized.py`` monolith. This module is
responsible for health-score visualizations only; pipeline, output, and codebase
charts live in sibling modules (``_dashboard_pipeline``, ``_dashboard_outputs``,
``_dashboard_codebase``).
"""

from __future__ import annotations

from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)


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

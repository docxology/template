"""Pipeline efficiency and bottleneck charts."""

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
from infrastructure.reporting._dashboard_constants import COLORS
from infrastructure.reporting.executive_reporter import ExecutiveSummary
from infrastructure.reporting.output_organizer import FileType, OutputOrganizer

logger = get_logger(__name__)

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

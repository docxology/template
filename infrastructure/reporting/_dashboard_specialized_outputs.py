"""Output distribution and comparison charts."""

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

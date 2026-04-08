"""Codebase complexity and comparison charts."""

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



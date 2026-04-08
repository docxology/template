"""Health radar and health comparison charts for executive dashboards."""

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

#!/usr/bin/env python3
"""Generate 2x2 Quadrant Matrix Visualization.

This script creates a comprehensive visualization of the 2×2 quadrant framework:
- X-axis: Data vs Meta-Data
- Y-axis: Cognitive vs Meta-Cognitive
- Four quadrants with detailed descriptions and examples

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import src/ modules
from quadrant_framework import QuadrantFramework
from utils.figure_manager import FigureManager
# Local imports
from utils.logging import get_logger
from visualization import VisualizationEngine

logger = get_logger(__name__)


def main() -> None:
    """Generate the quadrant matrix visualization."""
    logger.info("Generating 2×2 Quadrant Matrix visualization...")

    # Setup output directory
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    quadrant_framework = QuadrantFramework()
    viz_engine = VisualizationEngine(output_dir=str(output_dir))
    figure_manager = FigureManager()

    # Get quadrant matrix data
    matrix_data = quadrant_framework.create_quadrant_matrix_visualization()

    # Create the visualization
    logger.info("Creating quadrant matrix diagram...")
    fig = viz_engine.create_quadrant_matrix_plot(matrix_data)

    # Save the figure
    saved = viz_engine.save_figure(fig, "quadrant_matrix")
    logger.info(f"Saved quadrant matrix: {saved['png']}")

    # Register with figure manager for cross-referencing
    fig_meta = figure_manager.register_figure(
        filename="quadrant_matrix.png",
        caption="2×2 Quadrant Framework: Data/Meta-Data × Cognitive/Meta-Cognitive processing levels in Active Inference",
        section="methodology",
        generated_by="generate_quadrant_matrix.py",
    )
    logger.info(f"Registered figure: {fig_meta.label}")

    # Enhanced matrix with detailed quadrant information
    create_enhanced_quadrant_diagram(viz_engine, quadrant_framework, figure_manager)

    logger.info("✅ Quadrant matrix visualization completed")


def create_enhanced_quadrant_diagram(
    viz_engine: VisualizationEngine,
    quadrant_framework: QuadrantFramework,
    figure_manager: FigureManager,
) -> None:
    """Create an enhanced quadrant diagram with detailed information."""
    import matplotlib.pyplot as plt

    # Create larger figure for detailed information
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Active Inference Meta-Pragmatic Framework:\n2×2 Quadrant Analysis",
        fontsize=18,
        fontweight="bold",
        y=0.95,
    )

    quadrant_names = [
        "Q1_data_cognitive",
        "Q2_metadata_cognitive",
        "Q3_data_metacognitive",
        "Q4_metadata_metacognitive",
    ]

    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]  # axes positions

    colors = [
        "#E8F4FD",
        "#FFF3E0",
        "#F3E5F5",
        "#E8F5E8",
    ]  # Light colors for each quadrant

    for i, (quadrant_id, (row, col)) in enumerate(zip(quadrant_names, positions)):
        ax = axes[row, col]

        # Get quadrant information
        quadrant_info = quadrant_framework.get_quadrant(quadrant_id)

        # Set background color
        ax.add_patch(
            plt.Rectangle(
                (0, 0),
                1,
                1,
                transform=ax.transAxes,
                facecolor=colors[i],
                alpha=0.3,
                zorder=-1,
            )
        )

        # Add quadrant title
        ax.text(
            0.5,
            0.95,
            quadrant_info["name"],
            ha="center",
            va="top",
            fontsize=16,
            fontweight="bold",
            transform=ax.transAxes,
        )

        # Add description
        description = quadrant_info["description"][:200] + "..."  # Truncate for space
        ax.text(
            0.5,
            0.7,
            description,
            ha="center",
            va="top",
            fontsize=12,
            wrap=True,
            transform=ax.transAxes,
        )

        # Add examples
        if "examples" in quadrant_info:
            examples_text = "Examples:\n"
            for key, example in quadrant_info["examples"].items():
                examples_text += f"• {example[:100]}...\n"

            ax.text(
                0.5,
                0.3,
                examples_text,
                ha="center",
                va="top",
                fontsize=11,
                transform=ax.transAxes,
            )

        # Remove axes
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

    # Add axis labels
    fig.text(
        0.5,
        0.02,
        "Information Type: Data → Meta-Data",
        ha="center",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.02,
        0.5,
        "Processing Level: Cognitive → Meta-Cognitive",
        va="center",
        rotation="vertical",
        fontsize=16,
        fontweight="bold",
    )

    plt.tight_layout()

    # Save enhanced diagram
    saved = viz_engine.save_figure(fig, "quadrant_matrix_enhanced")
    logger.info(f"Saved enhanced quadrant diagram: {saved['png']}")

    # Register enhanced version
    figure_manager.register_figure(
        filename="quadrant_matrix_enhanced.png",
        caption="Enhanced 2×2 Quadrant Framework with detailed descriptions and examples",
        section="methodology",
        generated_by="generate_quadrant_matrix.py",
    )


if __name__ == "__main__":
    main()

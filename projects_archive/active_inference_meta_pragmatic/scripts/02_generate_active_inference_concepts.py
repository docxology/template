#!/usr/bin/env python3
"""Generate Active Inference Concepts Visualization.

This script creates visualizations of core Active Inference concepts:
- Expected Free Energy (EFE) decomposition
- Perception as inference loop
- Generative model structure
- Meta-pragmatic and meta-epistemic aspects

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Ensure src/ is on path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import src/ modules
from active_inference import demonstrate_active_inference_concepts
from generative_models import create_simple_generative_model
from utils.figure_manager import FigureManager
# Local imports
from utils.logging import get_logger
from visualization import VisualizationEngine

logger = get_logger(__name__)


def main() -> None:
    """Generate Active Inference concepts visualizations."""
    logger.info("Generating Active Inference concepts visualizations...")

    # Setup output directory
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize components
    viz_engine = VisualizationEngine(output_dir=str(output_dir))
    figure_manager = FigureManager()

    # Generate EFE decomposition visualization
    create_efe_decomposition_diagram(viz_engine, figure_manager)

    # Generate perception-action loop
    create_perception_action_loop(viz_engine, figure_manager)

    # Generate generative model structure
    create_generative_model_structure(viz_engine, figure_manager)

    # Generate meta-level concepts
    create_meta_level_concepts(viz_engine, figure_manager)

    logger.info("✅ Active Inference concepts visualizations completed")


def create_efe_decomposition_diagram(
    viz_engine: VisualizationEngine, figure_manager: FigureManager
) -> None:
    """Create EFE decomposition visualization."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Left: EFE components
    ax1.set_title("Expected Free Energy (EFE) Decomposition", fontweight="bold")

    # Create EFE breakdown
    components = ["Epistemic\nAffordance", "Pragmatic\nValue"]
    values = [0.6, 0.4]
    colors = ["#1f77b4", "#ff7f0e"]

    bars = ax1.bar(components, values, color=colors, alpha=0.7)
    ax1.set_ylabel("EFE Contribution")
    ax1.set_ylim(0, 1)

    # Add value labels
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{value:.1f}",
            ha="center",
            va="bottom",
        )

    # Right: Mathematical formulation
    ax2.set_title("Mathematical Formulation", fontweight="bold")
    ax2.axis("off")

    equations = [
        r"$\mathcal{F}(s,\pi) = \sum_{\tau=t+1}^{T} \mathbb{E}_{q(s_\tau)}[\log q(s_\tau) - \log p(s_\tau|\pi)]$",
        r"$\quad + \sum_{\tau=t}^{T} \mathbb{E}_{q(s_\tau)}[\log p(o_\tau|s_\tau) + \log p(s_\tau) - \log q(s_\tau)]$",
        r"$\text{EFE}(\pi) = G(\pi) + H[Q(\pi)]$",
    ]

    y_pos = 0.8
    for eq in equations:
        ax2.text(
            0.05,
            y_pos,
            eq,
            fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.1),
        )
        y_pos -= 0.25

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "efe_decomposition")
    logger.info(f"Saved EFE decomposition: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="efe_decomposition.png",
        caption="Expected Free Energy decomposition into epistemic and pragmatic components",
        section="methodology",
        generated_by="generate_active_inference_concepts.py",
    )


def create_perception_action_loop(
    viz_engine: VisualizationEngine, figure_manager: FigureManager
) -> None:
    """Create perception-action loop visualization."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Active Inference: Perception-Action Loop", fontweight="bold", pad=20)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.set_aspect("equal")
    ax.axis("off")

    # Draw main loop
    center_x, center_y = 5, 4
    radius = 2.5

    # Draw circular arrow
    theta = np.linspace(0, 2 * np.pi, 100)
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    ax.plot(x, y, "k-", linewidth=2, alpha=0.7)

    # Add arrowhead
    arrow_theta = np.pi / 4
    arrow_x = center_x + radius * np.cos(arrow_theta)
    arrow_y = center_y + radius * np.sin(arrow_theta)
    ax.arrow(
        arrow_x,
        arrow_y,
        0.3 * np.cos(arrow_theta),
        0.3 * np.sin(arrow_theta),
        head_width=0.2,
        head_length=0.3,
        fc="k",
        ec="k",
    )

    # Add process labels around the circle
    processes = [
        ("Observations\n(o)", 0, radius + 0.5),
        ("Perception\nas Inference", np.pi / 2, radius + 0.5),
        ("Policy\nSelection", np.pi, radius + 0.5),
        ("Action\nExecution", -np.pi / 2, radius + 0.5),
    ]

    for label, angle, r in processes:
        x_pos = center_x + r * np.cos(angle)
        y_pos = center_y + r * np.sin(angle)
        ha = (
            "center"
            if abs(np.cos(angle)) < 0.5
            else ("right" if np.cos(angle) > 0 else "left")
        )
        va = (
            "center"
            if abs(np.sin(angle)) < 0.5
            else ("top" if np.sin(angle) > 0 else "bottom")
        )
        ax.text(x_pos, y_pos, label, ha=ha, va=va, fontsize=11, fontweight="bold")

    # Add internal components
    ax.text(
        center_x,
        center_y,
        "Generative\nModel",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.3),
    )

    # Add EFE calculation
    ax.text(
        center_x,
        center_y - 1.5,
        "EFE(π) = G(π) + H[Q(π)]",
        ha="center",
        va="center",
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.5),
    )

    # Add explanatory arrows
    ax.annotate(
        "Minimize EFE",
        xy=(center_x, center_y + 0.5),
        xytext=(center_x + 1.5, center_y + 1.5),
        arrowprops=dict(arrowstyle="->", color="red", alpha=0.7),
        fontsize=10,
        color="red",
        ha="center",
    )

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "perception_action_loop")
    logger.info(f"Saved perception-action loop: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="perception_action_loop.png",
        caption="Active Inference perception-action loop showing how perception drives action through EFE minimization",
        section="methodology",
        generated_by="generate_active_inference_concepts.py",
    )


def create_generative_model_structure(
    viz_engine: VisualizationEngine, figure_manager: FigureManager
) -> None:
    """Create generative model structure visualization."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title(
        "Generative Model Structure in Active Inference", fontweight="bold", pad=20
    )
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # Create matrix representations
    matrices = [
        {"name": "A\nObservation Likelihood\nP(o|s)", "pos": (2, 5), "shape": (3, 2)},
        {"name": "B\nState Transitions\nP(s'|s,a)", "pos": (6, 5), "shape": (2, 2)},
        {"name": "C\nPreferences\n(log priors)", "pos": (10, 5), "shape": (3,)},
        {"name": "D\nPrior Beliefs\nP(s)", "pos": (2, 1), "shape": (2,)},
    ]

    for matrix in matrices:
        x, y = matrix["pos"]
        name = matrix["name"]
        shape = matrix["shape"]

        # Draw matrix box
        width, height = 1.5, 1.2
        ax.add_patch(
            plt.Rectangle(
                (x - width / 2, y - height / 2),
                width,
                height,
                facecolor="lightblue",
                alpha=0.3,
                edgecolor="blue",
                linewidth=2,
            )
        )

        # Add matrix name
        ax.text(x, y, name, ha="center", va="center", fontsize=10, fontweight="bold")

        # Add shape annotation
        shape_str = (
            f"shape: {shape}" if isinstance(shape, tuple) else f"shape: ({shape},)"
        )
        ax.text(
            x, y - 0.8, shape_str, ha="center", va="center", fontsize=8, style="italic"
        )

    # Draw connections
    connections = [
        ((2, 3.4), (6, 3.4), "Policy Selection"),
        ((6, 3.4), (10, 3.4), "Expected Outcomes"),
        ((10, 3.4), (6, 3.4), "EFE Calculation"),
        ((2, 2.6), (2, 3.4), "Perception"),
    ]

    for (x1, y1), (x2, y2), label in connections:
        ax.arrow(
            x1,
            y1,
            x2 - x1,
            y2 - y1,
            head_width=0.1,
            head_length=0.2,
            fc="gray",
            ec="gray",
            alpha=0.7,
            length_includes_head=True,
        )
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mid_x,
                mid_y + 0.2,
                label,
                ha="center",
                va="center",
                fontsize=9,
                style="italic",
            )

    # Add explanatory text
    explanation = """
    Generative models encode probabilistic relationships:
    • A: How hidden states generate observations (epistemic)
    • B: How actions influence state transitions (causal)
    • C: Preferred outcomes and goals (pragmatic)
    • D: Initial beliefs about states (priors)
    """
    ax.text(
        6,
        2,
        explanation,
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.3),
    )

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "generative_model_structure")
    logger.info(f"Saved generative model structure: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="generative_model_structure.png",
        caption="Structure of generative models in Active Inference showing A, B, C, D matrices",
        section="methodology",
        generated_by="generate_active_inference_concepts.py",
    )


def create_meta_level_concepts(
    viz_engine: VisualizationEngine, figure_manager: FigureManager
) -> None:
    """Create meta-level concepts visualization."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Meta-Pragmatic and Meta-Epistemic Aspects of Active Inference",
        fontsize=14,
        fontweight="bold",
        y=0.95,
    )

    concepts = [
        {
            "title": "Meta-Epistemic",
            "description": "Modeler specifies epistemic frameworks",
            "examples": [
                "Observation likelihoods (A matrix)",
                "Prior belief structures (D matrix)",
                "Inference algorithms and rules",
            ],
            "position": (0, 0),
            "color": "#1f77b4",
        },
        {
            "title": "Meta-Pragmatic",
            "description": "Modeler specifies pragmatic frameworks",
            "examples": [
                "Preference/goal structures (C matrix)",
                "Value hierarchies and trade-offs",
                "Decision-making frameworks",
            ],
            "position": (0, 1),
            "color": "#ff7f0e",
        },
        {
            "title": "Epistemic Specification",
            "description": "What the agent can know and how",
            "examples": [
                "Sensory information availability",
                "Knowledge representation structures",
                "Learning and belief updating rules",
            ],
            "position": (1, 0),
            "color": "#2ca02c",
        },
        {
            "title": "Pragmatic Specification",
            "description": "What matters to the agent",
            "examples": [
                "Goal and reward structures",
                "Utility functions and preferences",
                "Action selection criteria",
            ],
            "position": (1, 1),
            "color": "#d62728",
        },
    ]

    for concept in concepts:
        row, col = concept["position"]
        ax = axes[row, col]

        # Set background color
        ax.add_patch(
            plt.Rectangle(
                (0, 0),
                1,
                1,
                transform=ax.transAxes,
                facecolor=concept["color"],
                alpha=0.1,
            )
        )

        # Add title
        ax.text(
            0.5,
            0.9,
            concept["title"],
            ha="center",
            va="top",
            fontsize=12,
            fontweight="bold",
            transform=ax.transAxes,
        )

        # Add description
        ax.text(
            0.5,
            0.7,
            concept["description"],
            ha="center",
            va="top",
            fontsize=10,
            wrap=True,
            transform=ax.transAxes,
        )

        # Add examples
        examples_text = "Examples:\n" + "\n".join(
            f"• {ex}" for ex in concept["examples"]
        )
        ax.text(
            0.5,
            0.4,
            examples_text,
            ha="center",
            va="top",
            fontsize=9,
            transform=ax.transAxes,
        )

        # Remove axes
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.tight_layout()

    # Save figure
    saved = viz_engine.save_figure(fig, "meta_level_concepts")
    logger.info(f"Saved meta-level concepts: {saved['png']}")

    # Register figure
    figure_manager.register_figure(
        filename="meta_level_concepts.png",
        caption="Meta-pragmatic and meta-epistemic aspects showing modeler specification power",
        section="methodology",
        generated_by="generate_active_inference_concepts.py",
    )


if __name__ == "__main__":
    main()

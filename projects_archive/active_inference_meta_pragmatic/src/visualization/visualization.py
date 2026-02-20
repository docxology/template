"""Visualization Engine for Active Inference Meta-Pragmatic Framework.

This module provides visualization capabilities for the Active Inference concepts,
including the 2x2 quadrant matrix, generative model structures, and meta-cognitive
processes. It extends the infrastructure visualization capabilities with
domain-specific plotting functions.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle
from numpy.typing import NDArray
from ..utils.exceptions import ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class VisualizationEngine:
    """Enhanced visualization engine for Active Inference concepts.

    Provides publication-quality visualizations for the meta-pragmatic framework,
    including quadrant matrices, generative model structures, and cognitive processes.
    """

    def __init__(
        self,
        output_dir: Union[str, Path] = "output/figures",
        style: str = "publication",
    ) -> None:
        """Initialize visualization engine.

        Args:
            output_dir: Directory for saving figures
            style: Plotting style ('publication', 'presentation', 'draft')
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.style = style

        # Set up matplotlib parameters
        self._setup_matplotlib_style()

        logger.info(f"Initialized visualization engine with style: {style}")

    def _setup_matplotlib_style(self) -> None:
        """Set up matplotlib style parameters."""
        if self.style == "publication":
            plt.rcParams.update(
                {
                    "font.size": 16,
                    "font.family": "serif",
                    "axes.labelsize": 16,
                    "axes.titlesize": 18,
                    "xtick.labelsize": 14,
                    "ytick.labelsize": 14,
                    "legend.fontsize": 14,
                    "figure.dpi": 300,
                    "savefig.dpi": 300,
                    "savefig.bbox": "tight",
                    "savefig.pad_inches": 0.1,
                }
            )
        elif self.style == "presentation":
            plt.rcParams.update(
                {
                    "font.size": 14,
                    "font.family": "sans-serif",
                    "axes.labelsize": 14,
                    "axes.titlesize": 16,
                    "xtick.labelsize": 12,
                    "ytick.labelsize": 12,
                    "legend.fontsize": 12,
                    "figure.dpi": 150,
                }
            )

    def create_figure(
        self, figsize: Tuple[float, float] = (8, 6)
    ) -> Tuple[plt.Figure, plt.Axes]:
        """Create a new figure with proper styling.

        Args:
            figsize: Figure size in inches

        Returns:
            Tuple of (figure, axes) objects
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Apply consistent styling
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)

        return fig, ax

    def apply_publication_style(
        self,
        ax: plt.Axes,
        title: str,
        xlabel: str,
        ylabel: str,
        grid: bool = True,
        legend: bool = False,
    ) -> None:
        """Apply publication-style formatting to axes.

        Args:
            ax: Matplotlib axes object
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            legend: Whether to show legend
        """
        ax.set_title(title, pad=15, fontweight="bold")
        ax.set_xlabel(xlabel, labelpad=10)
        ax.set_ylabel(ylabel, labelpad=10)

        if grid:
            ax.grid(True, alpha=0.3, linestyle="--")

        if legend:
            ax.legend(framealpha=0.9, fancybox=True, shadow=True)

        # Remove top and right spines for cleaner look
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    def get_color(self, index: int) -> str:
        """Get color from publication-ready color palette.

        Args:
            index: Color index

        Returns:
            Hex color string
        """
        colors = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
        return colors[index % len(colors)]

    def save_figure(
        self, fig: plt.Figure, filename: str, formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """Save figure in multiple formats.

        Args:
            fig: Matplotlib figure object
            filename: Base filename (without extension)
            formats: List of formats to save (png, pdf, svg, eps)

        Returns:
            Dictionary mapping format to file path
        """
        if formats is None:
            formats = ["png", "pdf"]

        saved_files = {}

        try:
            for fmt in formats:
                filepath = self.output_dir / f"{filename}.{fmt}"
                filepath.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(filepath, format=fmt, dpi=300, bbox_inches="tight")
                saved_files[fmt] = filepath

            # Basic quality checks
            for path in saved_files.values():
                if not path.exists() or path.stat().st_size == 0:
                    raise RuntimeError(f"Figure save failed for {path}")

            logger.info(f"Saved figure: {filename} ({', '.join(formats)})")
            return saved_files

        except Exception as e:
            logger.error(f"Error saving figure {filename}: {e}")
            raise ValidationError(f"Figure saving failed: {e}") from e

    def create_quadrant_matrix_plot(self, matrix_data: Dict) -> plt.Figure:
        """Create visualization of the 2x2 quadrant matrix.

        Args:
            matrix_data: Dictionary containing matrix visualization data

        Returns:
            Matplotlib figure object
        """
        fig, ax = self.create_figure(figsize=(10, 8))

        # Remove axes
        ax.set_xlim(0, 2)
        ax.set_ylim(0, 2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")

        # Handle different input formats
        if "quadrants" in matrix_data:
            # Old format with quadrants dict
            quadrants = matrix_data["quadrants"]
            title = matrix_data.get("title", "Quadrant Matrix")
            subtitle = matrix_data.get("subtitle", "")
            y_axis_labels = matrix_data.get("y_axis", {}).get(
                "categories", ["Low", "High"]
            )
            x_axis_labels = matrix_data.get("x_axis", {}).get(
                "categories", ["Low", "High"]
            )
        elif "matrix" in matrix_data and "labels" in matrix_data:
            # New format from tests - convert to quadrants format
            matrix = matrix_data["matrix"]
            labels = matrix_data["labels"]

            # Create quadrants dict from matrix and labels
            quadrants = {
                "bottom_left": {
                    "id": "Q1",
                    "name": labels[0] if len(labels) > 0 else "Q1",
                    "color": "#1f77b4",
                },
                "bottom_right": {
                    "id": "Q2",
                    "name": labels[1] if len(labels) > 1 else "Q2",
                    "color": "#ff7f0e",
                },
                "top_left": {
                    "id": "Q3",
                    "name": labels[2] if len(labels) > 2 else "Q3",
                    "color": "#2ca02c",
                },
                "top_right": {
                    "id": "Q4",
                    "name": labels[3] if len(labels) > 3 else "Q4",
                    "color": "#d62728",
                },
            }
            title = matrix_data.get("title", "Quadrant Matrix")
            subtitle = matrix_data.get("subtitle", "")
            y_axis_labels = ["Data", "Cognitive"]  # Default for test format
            x_axis_labels = ["Low", "High"]  # Default for test format
        else:
            raise ValidationError(
                "matrix_data must contain either 'quadrants' or 'matrix' and 'labels' keys"
            )

        # Bottom-left (Q1)
        ax.add_patch(
            Rectangle(
                (0, 0),
                1,
                1,
                fill=True,
                alpha=0.1,
                color=quadrants["bottom_left"]["color"],
            )
        )
        ax.text(
            0.5,
            0.5,
            f"{quadrants['bottom_left']['id']}\n{quadrants['bottom_left']['name']}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Bottom-right (Q2)
        ax.add_patch(
            Rectangle(
                (1, 0),
                1,
                1,
                fill=True,
                alpha=0.1,
                color=quadrants["bottom_right"]["color"],
            )
        )
        ax.text(
            1.5,
            0.5,
            f"{quadrants['bottom_right']['id']}\n{quadrants['bottom_right']['name']}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Top-left (Q3)
        ax.add_patch(
            Rectangle(
                (0, 1), 1, 1, fill=True, alpha=0.1, color=quadrants["top_left"]["color"]
            )
        )
        ax.text(
            0.5,
            1.5,
            f"{quadrants['top_left']['id']}\n{quadrants['top_left']['name']}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Top-right (Q4)
        ax.add_patch(
            Rectangle(
                (1, 1),
                1,
                1,
                fill=True,
                alpha=0.1,
                color=quadrants["top_right"]["color"],
            )
        )
        ax.text(
            1.5,
            1.5,
            f"{quadrants['top_right']['id']}\n{quadrants['top_right']['name']}",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Add axis labels
        ax.text(
            -0.1,
            1,
            y_axis_labels[1],
            ha="center",
            va="center",
            rotation=90,
            fontsize=16,
            fontweight="bold",
        )
        ax.text(
            -0.1,
            0,
            y_axis_labels[0],
            ha="center",
            va="center",
            rotation=90,
            fontsize=16,
            fontweight="bold",
        )

        ax.text(
            0.5,
            -0.1,
            x_axis_labels[0],
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )
        ax.text(
            1.5,
            -0.1,
            x_axis_labels[1],
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Add main title
        ax.set_title(
            title + ("\n" + subtitle if subtitle else ""),
            fontsize=18,
            fontweight="bold",
            pad=20,
        )

        # Remove all spines
        for spine in ax.spines.values():
            spine.set_visible(False)

        return fig

    def create_generative_model_diagram(self, model_structure: Dict) -> plt.Figure:
        """Create diagram of generative model structure.

        Args:
            model_structure: Dictionary containing model structure information

        Returns:
            Matplotlib figure object
        """
        fig, ax = self.create_figure(figsize=(12, 8))

        # Remove axes
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")

        # Draw matrices as boxes
        matrices = [
            {
                "name": "A\nObservation\nLikelihoods",
                "pos": (0.5, 2),
                "color": "#1f77b4",
            },
            {"name": "B\nState\nTransitions", "pos": (1.5, 2), "color": "#ff7f0e"},
            {"name": "C\nPreferences", "pos": (2.5, 2), "color": "#2ca02c"},
            {"name": "D\nPrior\nBeliefs", "pos": (3.5, 2), "color": "#d62728"},
        ]

        for matrix in matrices:
            # Draw matrix box
            ax.add_patch(
                FancyBboxPatch(
                    (matrix["pos"][0] - 0.3, matrix["pos"][1] - 0.3),
                    0.6,
                    0.6,
                    boxstyle="round,pad=0.1",
                    facecolor=matrix["color"],
                    alpha=0.7,
                )
            )

            # Add matrix label
            ax.text(
                matrix["pos"][0],
                matrix["pos"][1],
                matrix["name"],
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white",
            )

        # Draw connections between matrices
        connections = [
            ((0.8, 2), (1.2, 2), "State → Observation"),
            ((1.8, 2), (2.2, 2), "Action → Transition"),
            ((2.8, 2), (3.2, 2), "Outcome → Preference"),
            ((3.5, 1.7), (3.5, 1.3), "Initial Beliefs"),
        ]

        for start, end, label in connections:
            ax.arrow(
                start[0],
                start[1],
                end[0] - start[0],
                end[1] - start[1],
                head_width=0.05,
                head_length=0.1,
                fc="black",
                ec="black",
                alpha=0.7,
                length_includes_head=True,
            )
            if label:
                ax.text(
                    (start[0] + end[0]) / 2,
                    (start[1] + end[1]) / 2 + 0.1,
                    label,
                    ha="center",
                    va="center",
                    fontsize=14,
                )

        # Add title and description
        ax.set_title(
            "Generative Model Structure (A, B, C, D Matrices)",
            fontsize=18,
            fontweight="bold",
            pad=20,
        )

        # Add explanatory text
        explanation = """
        A: P(o|s) - How hidden states generate observations
        B: P(s'|s,a) - How actions change states
        C: Preferences - Desired outcomes (log probabilities)
        D: P(s) - Initial state beliefs
        """
        ax.text(
            2,
            0.5,
            explanation,
            ha="center",
            va="center",
            fontsize=14,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5),
        )

        return fig

    def create_meta_cognitive_diagram(self, meta_cog_data: Dict) -> plt.Figure:
        """Create diagram of meta-cognitive processes.

        Args:
            meta_cog_data: Dictionary containing meta-cognitive process data

        Returns:
            Matplotlib figure object
        """
        fig, ax = self.create_figure(figsize=(10, 6))

        # Create a flow diagram of meta-cognitive processes
        processes = [
            {"name": "Observation\nInput", "pos": (0.1, 0.8), "color": "#1f77b4"},
            {"name": "Inference\nProcess", "pos": (0.3, 0.8), "color": "#ff7f0e"},
            {"name": "Confidence\nAssessment", "pos": (0.5, 0.8), "color": "#2ca02c"},
            {
                "name": "Meta-Cognitive\nEvaluation",
                "pos": (0.7, 0.8),
                "color": "#d62728",
            },
            {"name": "Strategy\nAdjustment", "pos": (0.9, 0.8), "color": "#9467bd"},
        ]

        # Draw process boxes
        for process in processes:
            ax.add_patch(
                FancyBboxPatch(
                    (process["pos"][0] - 0.08, process["pos"][1] - 0.08),
                    0.16,
                    0.16,
                    boxstyle="round,pad=0.05",
                    facecolor=process["color"],
                    alpha=0.7,
                )
            )

            ax.text(
                process["pos"][0],
                process["pos"][1],
                process["name"],
                ha="center",
                va="center",
                fontsize=14,
                fontweight="bold",
                color="white",
            )

        # Draw flow arrows
        for i in range(len(processes) - 1):
            start = processes[i]["pos"]
            end = processes[i + 1]["pos"]
            ax.arrow(
                start[0] + 0.08,
                start[1],
                end[0] - start[0] - 0.16,
                0,
                head_width=0.02,
                head_length=0.03,
                fc="black",
                ec="black",
                alpha=0.7,
                length_includes_head=True,
            )

        # Add feedback loop
        ax.arrow(
            0.82,
            0.72,
            -0.6,
            -0.4,
            head_width=0.02,
            head_length=0.03,
            fc="red",
            ec="red",
            alpha=0.7,
            length_includes_head=True,
        )
        ax.text(
            0.5,
            0.3,
            "Feedback Loop:\nAdaptive Control",
            ha="center",
            va="center",
            fontsize=14,
            color="red",
            fontweight="bold",
        )

        # Add title
        ax.set_title(
            "Meta-Cognitive Process Flow", fontsize=18, fontweight="bold", pad=20
        )

        # Set limits and remove axes
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

        return fig

    def create_fep_visualization(self, fep_data: Dict) -> plt.Figure:
        """Create visualization of Free Energy Principle concepts.

        Args:
            fep_data: Dictionary containing FEP visualization data

        Returns:
            Matplotlib figure object
        """
        fig, ax = self.create_figure(figsize=(10, 8))

        # Remove axes
        ax.set_xlim(0, 4)
        ax.set_ylim(0, 3)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_aspect("equal")

        # Draw system boundary (Markov blanket)
        # Internal states
        ax.add_patch(
            FancyBboxPatch(
                (1.5, 1.5),
                1,
                1,
                boxstyle="round,pad=0.1",
                facecolor="#1f77b4",
                alpha=0.3,
            )
        )
        ax.text(
            2,
            2,
            "Internal\nStates",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Sensory states
        ax.add_patch(
            FancyBboxPatch(
                (0.5, 1),
                1,
                0.8,
                boxstyle="round,pad=0.1",
                facecolor="#ff7f0e",
                alpha=0.3,
            )
        )
        ax.text(
            1,
            1.4,
            "Sensory\nStates",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Active states
        ax.add_patch(
            FancyBboxPatch(
                (2.5, 1),
                1,
                0.8,
                boxstyle="round,pad=0.1",
                facecolor="#2ca02c",
                alpha=0.3,
            )
        )
        ax.text(
            3,
            1.4,
            "Active\nStates",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # External states
        ax.add_patch(
            FancyBboxPatch(
                (1.5, 0.2),
                1,
                0.6,
                boxstyle="round,pad=0.1",
                facecolor="#d62728",
                alpha=0.3,
            )
        )
        ax.text(
            2,
            0.5,
            "External\nStates",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
        )

        # Draw Markov blanket boundary
        ax.add_patch(
            FancyBboxPatch(
                (0.3, 0.8),
                3.4,
                1.4,
                boxstyle="round,pad=0.2",
                facecolor="none",
                edgecolor="black",
                linewidth=2,
            )
        )
        ax.text(
            2,
            2.3,
            "Markov Blanket",
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            color="black",
        )

        # Add flow arrows
        # Internal to active
        ax.arrow(
            2.5,
            1.9,
            0.5,
            0,
            head_width=0.05,
            head_length=0.1,
            fc="blue",
            ec="blue",
            alpha=0.7,
        )
        # External to sensory
        ax.arrow(
            2,
            0.8,
            -0.5,
            0.2,
            head_width=0.05,
            head_length=0.1,
            fc="red",
            ec="red",
            alpha=0.7,
        )
        # Sensory to internal
        ax.arrow(
            1.5,
            1.4,
            0.5,
            0.4,
            head_width=0.05,
            head_length=0.1,
            fc="orange",
            ec="orange",
            alpha=0.7,
        )

        # Add title and description
        ax.set_title(
            "Free Energy Principle: System Boundaries and Markov Blanket",
            fontsize=18,
            fontweight="bold",
            pad=20,
        )

        explanation = """
        The Markov Blanket separates internal states from external states.
        Systems minimize free energy to maintain structural integrity.
        Sensory and active states form the blanket's boundary.
        """
        ax.text(
            2,
            0.1,
            explanation,
            ha="center",
            va="center",
            fontsize=14,
            style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5),
        )

        return fig

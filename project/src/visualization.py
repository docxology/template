"""Visualization for Boundary Logic Forms.

This module provides visualization tools for boundary forms,
including nested boundary diagrams, form trees, and publication-quality
figures for the Laws of Form.

Visualization types:
- Nested circles/rectangles for containment
- Tree structures for form hierarchy
- Step-by-step reduction animations
- Boolean circuit equivalents
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

from src.forms import Form, make_void, make_mark


@dataclass
class VisualizationStyle:
    """Style configuration for form visualization.
    
    Attributes:
        boundary_color: Color for boundaries
        fill_color: Fill color for marks
        void_color: Color for void regions
        line_width: Boundary line width
        font_size: Label font size
        spacing: Spacing between elements
    """
    boundary_color: str = "#2c3e50"
    fill_color: str = "#e8f4f8"
    void_color: str = "#ffffff"
    mark_color: str = "#3498db"
    line_width: float = 2.0
    font_size: int = 12
    spacing: float = 0.2
    dpi: int = 150


class FormVisualizer:
    """Visualizer for boundary forms.
    
    Creates visual representations of forms using matplotlib.
    """
    
    def __init__(self, style: VisualizationStyle = None) -> None:
        """Initialize visualizer.
        
        Args:
            style: Visualization style configuration
        """
        self.style = style or VisualizationStyle()
    
    def visualize(
        self,
        form: Form,
        title: str = None,
        figsize: Tuple[float, float] = (8, 6)
    ) -> plt.Figure:
        """Visualize a boundary form.
        
        Args:
            form: Form to visualize
            title: Optional figure title
            figsize: Figure size
            
        Returns:
            matplotlib Figure
        """
        fig, ax = plt.subplots(1, 1, figsize=figsize, dpi=self.style.dpi)
        
        # Draw the form
        self._draw_form(ax, form, x=0, y=0, size=2.0)
        
        # Configure axes
        ax.set_aspect('equal')
        ax.axis('off')
        
        if title:
            ax.set_title(title, fontsize=self.style.font_size + 4)
        
        # Add form notation
        ax.text(
            0, -1.5, str(form) if not form.is_void() else "∅",
            ha='center', va='top',
            fontsize=self.style.font_size + 2,
            fontfamily='monospace'
        )
        
        plt.tight_layout()
        return fig
    
    def _draw_form(
        self,
        ax: plt.Axes,
        form: Form,
        x: float,
        y: float,
        size: float
    ) -> None:
        """Draw a form recursively.
        
        Args:
            ax: Matplotlib axes
            form: Form to draw
            x, y: Center position
            size: Size of the form
        """
        if form.is_void():
            # Draw void (empty space - just a light circle)
            circle = Circle(
                (x, y), size * 0.4,
                fill=True,
                facecolor=self.style.void_color,
                edgecolor=self.style.boundary_color,
                linewidth=self.style.line_width * 0.5,
                linestyle=':'
            )
            ax.add_patch(circle)
            ax.text(x, y, "∅", ha='center', va='center',
                   fontsize=self.style.font_size)
            return
        
        if form.is_simple_mark():
            # Draw simple mark (filled circle)
            circle = Circle(
                (x, y), size * 0.4,
                fill=True,
                facecolor=self.style.mark_color,
                edgecolor=self.style.boundary_color,
                linewidth=self.style.line_width,
                alpha=0.6
            )
            ax.add_patch(circle)
            return
        
        if form.is_marked:
            # Draw enclosure boundary
            circle = Circle(
                (x, y), size * 0.45,
                fill=True,
                facecolor=self.style.fill_color,
                edgecolor=self.style.boundary_color,
                linewidth=self.style.line_width
            )
            ax.add_patch(circle)
            
            # Draw contents
            if form.contents:
                n_contents = len(form.contents)
                for i, content in enumerate(form.contents):
                    # Position contents within the enclosure
                    angle = 2 * np.pi * i / n_contents if n_contents > 1 else 0
                    offset = size * 0.2 if n_contents > 1 else 0
                    cx = x + offset * np.cos(angle)
                    cy = y + offset * np.sin(angle)
                    child_size = size * 0.4 / np.sqrt(n_contents) if n_contents > 1 else size * 0.4
                    self._draw_form(ax, content, cx, cy, child_size)
        else:
            # Juxtaposition (draw contents side by side)
            n_contents = len(form.contents)
            if n_contents == 0:
                return
            
            total_width = n_contents * size * 0.4 + (n_contents - 1) * self.style.spacing
            start_x = x - total_width / 2 + size * 0.2
            
            for i, content in enumerate(form.contents):
                cx = start_x + i * (size * 0.4 + self.style.spacing)
                self._draw_form(ax, content, cx, y, size * 0.4)
    
    def save(
        self,
        form: Form,
        filepath: str,
        title: str = None,
        figsize: Tuple[float, float] = (8, 6)
    ) -> Path:
        """Save form visualization to file.
        
        Args:
            form: Form to visualize
            filepath: Output file path
            title: Optional title
            figsize: Figure size
            
        Returns:
            Path to saved file
        """
        fig = self.visualize(form, title, figsize)
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=self.style.dpi, bbox_inches='tight')
        plt.close(fig)
        return path


class ReductionVisualizer:
    """Visualizer for form reduction steps.
    
    Creates step-by-step visualization of form reduction.
    """
    
    def __init__(self, style: VisualizationStyle = None) -> None:
        """Initialize visualizer.
        
        Args:
            style: Visualization style
        """
        self.style = style or VisualizationStyle()
        self.form_viz = FormVisualizer(self.style)
    
    def visualize_reduction(
        self,
        form: Form,
        figsize_per_step: Tuple[float, float] = (4, 3)
    ) -> plt.Figure:
        """Visualize reduction process.
        
        Args:
            form: Form to reduce
            figsize_per_step: Size per reduction step
            
        Returns:
            matplotlib Figure with all steps
        """
        from src.reduction import reduce_with_trace
        
        trace = reduce_with_trace(form)
        n_steps = len(trace.steps) + 1  # Original + steps
        
        # Create figure with subplots
        n_cols = min(4, n_steps)
        n_rows = (n_steps + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(
            n_rows, n_cols,
            figsize=(figsize_per_step[0] * n_cols, figsize_per_step[1] * n_rows),
            dpi=self.style.dpi
        )
        
        if n_rows == 1 and n_cols == 1:
            axes = [[axes]]
        elif n_rows == 1:
            axes = [axes]
        elif n_cols == 1:
            axes = [[ax] for ax in axes]
        
        # Draw original
        ax = axes[0][0]
        self._draw_step(ax, trace.original, "Original", 0)
        
        # Draw each step
        for i, step in enumerate(trace.steps):
            row = (i + 1) // n_cols
            col = (i + 1) % n_cols
            ax = axes[row][col]
            self._draw_step(ax, step.after, step.rule.value, i + 1)
        
        # Hide unused axes
        for i in range(n_steps, n_rows * n_cols):
            row = i // n_cols
            col = i % n_cols
            axes[row][col].axis('off')
        
        plt.suptitle(f"Reduction: {trace.original} → {trace.canonical}",
                    fontsize=self.style.font_size + 2)
        plt.tight_layout()
        return fig
    
    def _draw_step(
        self,
        ax: plt.Axes,
        form: Form,
        rule: str,
        step_num: int
    ) -> None:
        """Draw a single reduction step.
        
        Args:
            ax: Matplotlib axes
            form: Form at this step
            rule: Rule applied
            step_num: Step number
        """
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Draw form
        self.form_viz._draw_form(ax, form, 0, 0, 1.5)
        
        # Labels
        ax.set_title(f"Step {step_num}: {rule}", fontsize=self.style.font_size)
        ax.text(0, -1.2, str(form) if not form.is_void() else "∅",
               ha='center', va='top', fontsize=self.style.font_size - 2,
               fontfamily='monospace')


def visualize_form(form: Form, title: str = None) -> plt.Figure:
    """Convenience function to visualize a form.
    
    Args:
        form: Form to visualize
        title: Optional title
        
    Returns:
        matplotlib Figure
    """
    viz = FormVisualizer()
    return viz.visualize(form, title)


def save_form_figure(
    form: Form,
    filepath: str,
    title: str = None
) -> Path:
    """Save form visualization to file.
    
    Args:
        form: Form to visualize
        filepath: Output path
        title: Optional title
        
    Returns:
        Path to saved file
    """
    viz = FormVisualizer()
    return viz.save(form, filepath, title)


def visualize_reduction(form: Form) -> plt.Figure:
    """Visualize the reduction of a form.
    
    Args:
        form: Form to reduce and visualize
        
    Returns:
        matplotlib Figure showing reduction steps
    """
    viz = ReductionVisualizer()
    return viz.visualize_reduction(form)


def create_axiom_diagram() -> plt.Figure:
    """Create a diagram showing both axioms.
    
    Returns:
        matplotlib Figure with axiom illustrations
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=150)
    
    viz = FormVisualizer()
    
    # Axiom J1 (Calling)
    ax = axes[0]
    double_mark = Form.enclose(Form.enclose(make_mark()))
    viz._draw_form(ax, double_mark, -0.5, 0, 1.0)
    ax.text(0, 0, "=", fontsize=20, ha='center', va='center')
    viz._draw_form(ax, make_mark(), 0.5, 0, 1.0)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Axiom J1 (Calling): ⟨⟨a⟩⟩ = a", fontsize=14)
    
    # Axiom J2 (Crossing)
    ax = axes[1]
    two_marks = Form.juxtapose(make_mark(), make_mark())
    viz._draw_form(ax, two_marks, -0.7, 0, 0.8)
    ax.text(0, 0, "=", fontsize=20, ha='center', va='center')
    viz._draw_form(ax, make_mark(), 0.7, 0, 0.8)
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("Axiom J2 (Crossing): ⟨ ⟩⟨ ⟩ = ⟨ ⟩", fontsize=14)
    
    plt.tight_layout()
    return fig


def create_boolean_correspondence_diagram() -> plt.Figure:
    """Create a diagram showing Boolean algebra correspondence.
    
    Returns:
        matplotlib Figure
    """
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), dpi=150)
    
    viz = FormVisualizer()
    correspondences = [
        (make_mark(), "TRUE", "⟨ ⟩"),
        (make_void(), "FALSE", "∅"),
        (Form.enclose(make_mark()), "NOT TRUE", "⟨⟨ ⟩⟩ = ∅"),
        (Form.enclose(make_void()), "NOT FALSE", "⟨∅⟩ = ⟨ ⟩"),
        (Form.juxtapose(make_mark(), make_mark()), "TRUE AND TRUE", "⟨ ⟩⟨ ⟩ = ⟨ ⟩"),
        (Form.juxtapose(make_mark(), make_void()), "TRUE AND FALSE", "⟨ ⟩∅ = ∅"),
    ]
    
    for idx, (form, boolean, notation) in enumerate(correspondences):
        row = idx // 3
        col = idx % 3
        ax = axes[row][col]
        
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect('equal')
        ax.axis('off')
        
        viz._draw_form(ax, form, 0, 0.2, 1.0)
        ax.set_title(boolean, fontsize=12)
        ax.text(0, -1.0, notation, ha='center', va='top',
               fontsize=10, fontfamily='monospace')
    
    plt.suptitle("Boolean Algebra in Boundary Logic", fontsize=16)
    plt.tight_layout()
    return fig


# =============================================================================
# Generic Visualization Engine for Scientific Plotting
# =============================================================================

class VisualizationEngine:
    """Central visualization engine for publication-quality figures.
    
    Provides a unified interface for creating, styling, and saving
    matplotlib figures with consistent publication-ready formatting.
    
    Attributes:
        output_dir: Directory for saving figures
        style: Style preset name
        color_palette: Color palette name
        colors: List of colors in the current palette
    """
    
    # Default color palettes
    COLOR_PALETTES = {
        "default": [
            "#1f77b4",  # Blue
            "#ff7f0e",  # Orange
            "#2ca02c",  # Green
            "#d62728",  # Red
            "#9467bd",  # Purple
            "#8c564b",  # Brown
            "#e377c2",  # Pink
            "#7f7f7f",  # Gray
            "#bcbd22",  # Olive
            "#17becf",  # Cyan
        ],
        "colorblind": [
            "#0072B2",  # Blue
            "#E69F00",  # Orange
            "#009E73",  # Green
            "#CC79A7",  # Pink
            "#F0E442",  # Yellow
            "#56B4E9",  # Sky blue
            "#D55E00",  # Vermillion
            "#000000",  # Black
        ],
        "grayscale": [
            "#000000",
            "#333333",
            "#555555",
            "#777777",
            "#999999",
            "#BBBBBB",
            "#DDDDDD",
        ],
    }
    
    def __init__(
        self,
        output_dir: str = "output/figures",
        style: str = "publication",
        color_palette: str = "default"
    ) -> None:
        """Initialize visualization engine.
        
        Args:
            output_dir: Directory for saving figures
            style: Style preset name
            color_palette: Color palette name
        """
        self.output_dir = Path(output_dir)
        self.style = style
        self.color_palette = color_palette
        self.colors = self.COLOR_PALETTES.get(color_palette, self.COLOR_PALETTES["default"])
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_figure(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: Optional[Tuple[float, float]] = None
    ) -> Tuple[plt.Figure, Any]:
        """Create a new figure with subplots.
        
        Args:
            nrows: Number of subplot rows
            ncols: Number of subplot columns
            figsize: Figure size as (width, height)
            
        Returns:
            Tuple of (figure, axes)
        """
        if figsize is None:
            figsize = (8, 6)
        
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
        
        # Flatten axes for consistent access
        if nrows == 1 and ncols == 1:
            # Single subplot - return as-is
            return fig, axes
        elif nrows == 1 or ncols == 1:
            # Single row or column - already 1D array
            return fig, axes.flatten() if hasattr(axes, 'flatten') else [axes]
        else:
            # Multiple rows and columns - flatten 2D array
            return fig, axes.flatten()
    
    def save_figure(
        self,
        fig: plt.Figure,
        name: str,
        formats: Optional[List[str]] = None
    ) -> Dict[str, Path]:
        """Save figure in multiple formats.
        
        Args:
            fig: Figure to save
            name: Base filename (without extension)
            formats: List of formats to save (default: ["png", "pdf"])
            
        Returns:
            Dictionary mapping format to saved path
        """
        if formats is None:
            formats = ["png", "pdf"]
        
        saved_files = {}
        for fmt in formats:
            filepath = self.output_dir / f"{name}.{fmt}"
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            saved_files[fmt] = filepath
        
        return saved_files
    
    def apply_publication_style(
        self,
        ax: plt.Axes,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        grid: bool = False,
        legend: bool = False
    ) -> None:
        """Apply publication-quality styling to axes.
        
        Args:
            ax: Axes to style
            title: Optional title
            xlabel: Optional x-axis label
            ylabel: Optional y-axis label
            grid: Whether to show grid
            legend: Whether to show legend
        """
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)
        
        if grid:
            ax.grid(True, alpha=0.3, linestyle='--')
        
        if legend:
            ax.legend(frameon=True, framealpha=0.9)
        
        # Apply spine styling
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
    
    def get_color(self, index: int) -> str:
        """Get color from palette by index.
        
        Args:
            index: Color index (wraps around if exceeds palette size)
            
        Returns:
            Color hex string
        """
        return self.colors[index % len(self.colors)]


def create_multi_panel_figure(
    n_panels: int,
    layout: Optional[Tuple[int, int]] = None,
    figsize: Optional[Tuple[float, float]] = None
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """Create a multi-panel figure with optimal layout.
    
    Args:
        n_panels: Number of panels needed
        layout: Optional (nrows, ncols) layout override
        figsize: Optional figure size override
        
    Returns:
        Tuple of (figure, list of axes)
    """
    if layout is None:
        # Calculate optimal layout
        ncols = min(4, n_panels)
        nrows = (n_panels + ncols - 1) // ncols
    else:
        nrows, ncols = layout
    
    if figsize is None:
        figsize = (4 * ncols, 3 * nrows)
    
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    
    # Convert axes to list for consistent handling
    if nrows == 1 and ncols == 1:
        axes_list = [axes]
    elif nrows == 1 or ncols == 1:
        axes_list = list(axes.flatten()) if hasattr(axes, 'flatten') else [axes]
    else:
        axes_list = list(axes.flatten())
    
    # Hide extra axes
    total_subplots = nrows * ncols
    for i in range(n_panels, total_subplots):
        axes_list[i].axis('off')
    
    # Return only the requested number of panels
    return fig, axes_list[:n_panels]

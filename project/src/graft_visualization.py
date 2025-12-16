"""Visualization engine for tree grafting figures.

This module provides figure generation with consistent styling,
multi-panel figures, publication-quality formatting, and export capabilities
for grafting-related visualizations.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Set backend for headless operation
matplotlib.use('Agg')


class GraftVisualizationEngine:
    """Engine for generating publication-quality grafting figures."""
    
    # Publication-quality style settings
    STYLE_CONFIG = {
        "figure.dpi": 300,
        "figure.figsize": (8, 6),
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "lines.linewidth": 1.5,
        "lines.markersize": 6,
        "axes.linewidth": 1.0,
        "grid.alpha": 0.3,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.1
    }
    
    # Color palettes
    COLOR_PALETTES = {
        "default": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
        "colorblind": ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9"],
        "grayscale": ["#000000", "#404040", "#808080", "#C0C0C0", "#E0E0E0"]
    }
    
    def __init__(
        self,
        style: str = "publication",
        color_palette: str = "default",
        output_dir: Optional[str] = None
    ):
        """Initialize visualization engine.
        
        Args:
            style: Style preset (publication, presentation, draft)
            color_palette: Color palette name
            output_dir: Output directory for figures
        """
        self.style = style
        self.color_palette = color_palette
        self.output_dir = Path(output_dir) if output_dir else Path("output/figures")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Apply style
        self._apply_style()
        
        # Get color palette
        self.colors = self.COLOR_PALETTES.get(color_palette, self.COLOR_PALETTES["default"])
    
    def _apply_style(self) -> None:
        """Apply publication-quality style settings."""
        plt.rcParams.update(self.STYLE_CONFIG)
    
    def create_figure(
        self,
        nrows: int = 1,
        ncols: int = 1,
        figsize: Optional[Tuple[float, float]] = None,
        **kwargs
    ) -> Tuple[plt.Figure, np.ndarray]:
        """Create a new figure with subplots.
        
        Args:
            nrows: Number of rows
            ncols: Number of columns
            figsize: Figure size (width, height)
            **kwargs: Additional arguments for plt.subplots
            
        Returns:
            Tuple of (figure, axes array)
        """
        if figsize is None:
            figsize = (8 * ncols, 6 * nrows)
        
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
        
        # Handle single subplot case
        if nrows == 1 and ncols == 1:
            return fig, axes
        elif nrows == 1 or ncols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        return fig, axes
    
    def save_figure(
        self,
        figure: plt.Figure,
        filename: str,
        formats: Optional[List[str]] = None,
        dpi: int = 300
    ) -> Dict[str, Path]:
        """Save figure in multiple formats.
        
        Args:
            figure: Matplotlib figure
            filename: Base filename (without extension)
            formats: List of formats (png, pdf, svg, eps)
            dpi: Resolution for raster formats
            
        Returns:
            Dictionary mapping format to file path
        """
        if formats is None:
            formats = ["png", "pdf"]
        
        saved_files = {}
        
        for fmt in formats:
            filepath = self.output_dir / f"{filename}.{fmt}"
            figure.savefig(filepath, format=fmt, dpi=dpi, bbox_inches='tight')
            saved_files[fmt] = filepath
        
        # Basic quality checks
        for path in saved_files.values():
            if not path.exists() or path.stat().st_size == 0:
                raise RuntimeError(f"Figure save failed for {path}")
        return saved_files
    
    def apply_publication_style(
        self,
        ax: plt.Axes,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        grid: bool = True,
        legend: bool = False
    ) -> None:
        """Apply publication-quality styling to axes.
        
        Args:
            ax: Matplotlib axes
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            grid: Whether to show grid
            legend: Whether to show legend
        """
        if title:
            ax.set_title(title, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        
        if grid:
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    def get_color(self, index: int) -> str:
        """Get color from palette.
        
        Args:
            index: Color index
            
        Returns:
            Color string
        """
        return self.colors[index % len(self.colors)]


def create_multi_panel_graft_figure(
    n_panels: int,
    layout: Optional[Tuple[int, int]] = None,
    figsize: Optional[Tuple[float, float]] = None
) -> Tuple[plt.Figure, List[plt.Axes]]:
    """Create a multi-panel figure for grafting visualizations.
    
    Args:
        n_panels: Number of panels
        layout: (nrows, ncols) layout (auto-calculated if None)
        figsize: Figure size
        
    Returns:
        Tuple of (figure, list of axes)
    """
    if layout is None:
        # Auto-calculate layout
        ncols = int(np.ceil(np.sqrt(n_panels)))
        nrows = int(np.ceil(n_panels / ncols))
    else:
        nrows, ncols = layout
    
    if figsize is None:
        figsize = (4 * ncols, 3 * nrows)
    
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    
    # Flatten axes array
    if nrows == 1 and ncols == 1:
        axes_list = [axes]
    elif nrows == 1 or ncols == 1:
        axes_list = axes.tolist()
    else:
        axes_list = axes.flatten().tolist()
    
    # Hide extra subplots
    for i in range(n_panels, len(axes_list)):
        axes_list[i].set_visible(False)
    
    return fig, axes_list[:n_panels]


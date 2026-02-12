"""Comprehensive tests for src/visualization.py to ensure 100% coverage."""

import os
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from src.visualization.visualization import VisualizationEngine, create_multi_panel_figure


class TestVisualizationEngine:
    """Test VisualizationEngine class."""

    def test_initialization(self, tmp_path):
        """Test engine initialization."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        assert engine.output_dir == tmp_path
        assert engine.style == "publication"
        assert engine.color_palette == "default"

    def test_create_figure(self, tmp_path):
        """Test creating figure."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure(nrows=1, ncols=1)
        assert fig is not None
        # Single subplot returns axes object directly, not array
        assert hasattr(ax, "plot")  # Check it's an axes object
        plt.close(fig)

    def test_create_figure_with_figsize(self, tmp_path):
        """Test creating figure with custom figsize (branch 95->98)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure(nrows=1, ncols=1, figsize=(10, 8))
        assert fig.get_figwidth() == 10
        assert fig.get_figheight() == 8
        plt.close(fig)

    def test_create_figure_single_row(self, tmp_path):
        """Test creating figure with single row (line 105)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, axes = engine.create_figure(nrows=1, ncols=3)
        # Single row should flatten axes
        assert len(axes) == 3
        plt.close(fig)

    def test_create_figure_single_col(self, tmp_path):
        """Test creating figure with single column."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, axes = engine.create_figure(nrows=3, ncols=1)
        # Single column should flatten axes
        assert len(axes) == 3
        plt.close(fig)

    def test_create_multi_subplot_figure(self, tmp_path):
        """Test creating multi-subplot figure."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, axes = engine.create_figure(nrows=2, ncols=2)
        # Multi-subplot returns flattened array
        assert len(axes) == 4
        assert hasattr(axes[0], "plot")  # Check first element is axes object
        plt.close(fig)

    def test_save_figure(self, tmp_path):
        """Test saving figure."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        # ax is a single axes object for nrows=1, ncols=1
        ax.plot([1, 2, 3], [1, 2, 3])
        saved_files = engine.save_figure(fig, "test_figure", formats=["png"])
        assert "png" in saved_files
        assert saved_files["png"].exists()
        plt.close(fig)

    def test_save_figure_default_formats(self, tmp_path):
        """Test saving figure with default formats (line 131)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        ax.plot([1, 2, 3], [1, 2, 3])
        saved_files = engine.save_figure(fig, "test_figure", formats=None)
        # Should default to ["png", "pdf"]
        assert "png" in saved_files
        assert "pdf" in saved_files
        plt.close(fig)

    def test_save_multiple_formats(self, tmp_path):
        """Test saving in multiple formats."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        # ax is a single axes object for nrows=1, ncols=1
        ax.plot([1, 2, 3], [1, 2, 3])
        saved_files = engine.save_figure(fig, "test_figure", formats=["png", "pdf"])
        assert "png" in saved_files
        assert "pdf" in saved_files
        plt.close(fig)

    def test_apply_publication_style(self, tmp_path):
        """Test applying publication style."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        # ax is a single axes object for nrows=1, ncols=1
        engine.apply_publication_style(
            ax, title="Test", xlabel="X", ylabel="Y", grid=True, legend=True
        )
        assert ax.get_title() == "Test"
        assert ax.get_xlabel() == "X"
        assert ax.get_ylabel() == "Y"
        plt.close(fig)

    def test_apply_publication_style_no_title(self, tmp_path):
        """Test applying style without title (branch 161->163)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        engine.apply_publication_style(ax, title=None, xlabel="X", ylabel="Y")
        assert ax.get_xlabel() == "X"
        assert ax.get_ylabel() == "Y"
        plt.close(fig)

    def test_apply_publication_style_no_xlabel(self, tmp_path):
        """Test applying style without xlabel (branch 163->165)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        engine.apply_publication_style(ax, title="Test", xlabel=None, ylabel="Y")
        assert ax.get_title() == "Test"
        assert ax.get_ylabel() == "Y"
        plt.close(fig)

    def test_apply_publication_style_no_ylabel(self, tmp_path):
        """Test applying style without ylabel (branch 165->168)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        engine.apply_publication_style(ax, title="Test", xlabel="X", ylabel=None)
        assert ax.get_title() == "Test"
        assert ax.get_xlabel() == "X"
        plt.close(fig)

    def test_apply_publication_style_no_grid(self, tmp_path):
        """Test applying style without grid (branch 168->171)."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        engine.apply_publication_style(ax, title="Test", grid=False)
        assert ax.get_title() == "Test"
        plt.close(fig)

    def test_get_color(self, tmp_path):
        """Test getting color from palette."""
        engine = VisualizationEngine(output_dir=str(tmp_path))
        color = engine.get_color(0)
        assert isinstance(color, str)
        assert color in engine.colors


class TestCreateMultiPanelFigure:
    """Test multi-panel figure creation."""

    def test_auto_layout(self):
        """Test automatic layout calculation."""
        fig, axes = create_multi_panel_figure(4)
        assert len(axes) == 4
        plt.close(fig)

    def test_custom_layout(self):
        """Test custom layout."""
        fig, axes = create_multi_panel_figure(6, layout=(2, 3))
        assert len(axes) == 6
        plt.close(fig)

    def test_custom_figsize(self):
        """Test custom figure size."""
        fig, axes = create_multi_panel_figure(4, figsize=(12, 8))
        assert fig.get_figwidth() == 12
        assert fig.get_figheight() == 8
        plt.close(fig)

    def test_multi_panel_single_subplot(self):
        """Test multi-panel with single subplot (line 215)."""
        fig, axes = create_multi_panel_figure(1)
        assert len(axes) == 1
        assert hasattr(axes[0], "plot")
        plt.close(fig)

    def test_multi_panel_single_row(self):
        """Test multi-panel with single row (line 217)."""
        fig, axes = create_multi_panel_figure(3, layout=(1, 3))
        assert len(axes) == 3
        plt.close(fig)

    def test_multi_panel_single_col(self):
        """Test multi-panel with single column."""
        fig, axes = create_multi_panel_figure(3, layout=(3, 1))
        assert len(axes) == 3
        plt.close(fig)

    def test_multi_panel_hide_extra(self):
        """Test multi-panel hides extra subplots (line 223)."""
        fig, axes = create_multi_panel_figure(
            3, layout=(2, 2)
        )  # 4 subplots, only 3 used
        assert len(axes) == 3
        # The 4th subplot should be hidden
        plt.close(fig)

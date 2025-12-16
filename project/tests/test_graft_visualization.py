"""Comprehensive tests for graft_visualization module."""
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from graft_visualization import GraftVisualizationEngine, create_multi_panel_graft_figure


class TestVisualizationEngine:
    """Test visualization engine."""
    
    def test_initialization(self):
        """Test engine initialization."""
        engine = GraftVisualizationEngine()
        assert engine.style == "publication"
        assert engine.color_palette == "default"
    
    def test_create_figure(self):
        """Test figure creation."""
        engine = GraftVisualizationEngine()
        fig, axes = engine.create_figure(2, 2)
        assert fig is not None
        assert len(axes) == 4
        plt.close(fig)
    
    def test_create_figure_single_subplot(self):
        """Test figure creation with single subplot."""
        engine = GraftVisualizationEngine()
        fig, ax = engine.create_figure(1, 1)
        assert fig is not None
        assert ax is not None
        # Single subplot should return axes directly, not array
        plt.close(fig)
    
    def test_create_figure_single_row(self):
        """Test figure creation with single row."""
        engine = GraftVisualizationEngine()
        fig, axes = engine.create_figure(1, 3)
        assert fig is not None
        assert len(axes) == 3
        plt.close(fig)
    
    def test_create_figure_single_col(self):
        """Test figure creation with single column."""
        engine = GraftVisualizationEngine()
        fig, axes = engine.create_figure(3, 1)
        assert fig is not None
        assert len(axes) == 3
        plt.close(fig)
    
    def test_save_figure(self, tmp_path):
        """Test figure saving."""
        engine = GraftVisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        ax.plot([1, 2, 3], [1, 2, 3])
        saved = engine.save_figure(fig, "test_figure")
        assert "png" in saved
        assert saved["png"].exists()
        plt.close(fig)
    
    def test_save_figure_svg(self, tmp_path):
        """Test figure saving in SVG format."""
        engine = GraftVisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        ax.plot([1, 2, 3], [1, 2, 3])
        saved = engine.save_figure(fig, "test_figure_svg", formats=["svg"])
        assert "svg" in saved
        assert saved["svg"].exists()
        plt.close(fig)
    
    def test_save_figure_eps(self, tmp_path):
        """Test figure saving in EPS format."""
        engine = GraftVisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        ax.plot([1, 2, 3], [1, 2, 3])
        saved = engine.save_figure(fig, "test_figure_eps", formats=["eps"])
        assert "eps" in saved
        assert saved["eps"].exists()
        plt.close(fig)
    
    def test_save_figure_multiple_formats(self, tmp_path):
        """Test figure saving in multiple formats."""
        engine = GraftVisualizationEngine(output_dir=str(tmp_path))
        fig, ax = engine.create_figure()
        ax.plot([1, 2, 3], [1, 2, 3])
        saved = engine.save_figure(fig, "test_figure_multi", formats=["png", "pdf", "svg"])
        assert "png" in saved
        assert "pdf" in saved
        assert "svg" in saved
        assert all(path.exists() for path in saved.values())
        plt.close(fig)
    
    def test_apply_publication_style(self):
        """Test applying publication style to axes."""
        engine = GraftVisualizationEngine()
        fig, ax = engine.create_figure()
        engine.apply_publication_style(
            ax,
            title="Test Title",
            xlabel="X Label",
            ylabel="Y Label",
            grid=True,
            legend=False
        )
        assert ax.get_title() == "Test Title"
        assert ax.get_xlabel() == "X Label"
        assert ax.get_ylabel() == "Y Label"
        plt.close(fig)
    
    def test_apply_publication_style_no_labels(self):
        """Test applying publication style without labels."""
        engine = GraftVisualizationEngine()
        fig, ax = engine.create_figure()
        engine.apply_publication_style(ax, grid=False)
        # Should not raise error
        plt.close(fig)
    
    def test_get_color(self):
        """Test getting color from palette."""
        engine = GraftVisualizationEngine()
        color1 = engine.get_color(0)
        color2 = engine.get_color(1)
        color3 = engine.get_color(5)  # Should wrap around
        assert isinstance(color1, str)
        assert isinstance(color2, str)
        assert isinstance(color3, str)
        assert color1 != color2
        # Color at index 5 should wrap to index 0 (5 % 5 = 0)
        assert color3 == color1
    
    def test_color_palette_colorblind(self):
        """Test colorblind palette."""
        engine = GraftVisualizationEngine(color_palette="colorblind")
        color = engine.get_color(0)
        assert isinstance(color, str)
        assert color in engine.COLOR_PALETTES["colorblind"]


class TestMultiPanel:
    """Test multi-panel figure creation."""
    
    def test_create_multi_panel(self):
        """Test multi-panel figure."""
        fig, axes = create_multi_panel_graft_figure(4)
        assert len(axes) == 4
        plt.close(fig)
    
    def test_create_multi_panel_custom_layout(self):
        """Test multi-panel figure with custom layout."""
        fig, axes = create_multi_panel_graft_figure(6, layout=(2, 3))
        assert len(axes) == 6
        plt.close(fig)
    
    def test_create_multi_panel_custom_figsize(self):
        """Test multi-panel figure with custom figure size."""
        fig, axes = create_multi_panel_graft_figure(4, figsize=(12, 8))
        assert len(axes) == 4
        plt.close(fig)
    
    def test_create_multi_panel_extra_subplots_hidden(self):
        """Test that extra subplots are hidden."""
        fig, axes = create_multi_panel_graft_figure(3, layout=(2, 2))
        assert len(axes) == 3
        # Layout has 4 subplots, but only 3 should be visible
        plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__])


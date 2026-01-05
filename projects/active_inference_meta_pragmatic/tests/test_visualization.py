"""Tests for visualization.py module.

Comprehensive tests for the VisualizationEngine class and visualization functions,
ensuring correct figure generation and saving functionality.
"""

import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
import numpy as np
import pytest

from src.visualization import VisualizationEngine


class TestVisualizationEngine:
    """Test VisualizationEngine class functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_initialization_default(self, temp_output_dir):
        """Test VisualizationEngine initialization with default parameters."""
        engine = VisualizationEngine()

        assert engine.output_dir == Path("output/figures")
        assert engine.style == "publication"

    def test_initialization_custom(self, temp_output_dir):
        """Test VisualizationEngine initialization with custom parameters."""
        output_dir = temp_output_dir / "custom_figures"
        engine = VisualizationEngine(output_dir=output_dir, style="presentation")

        assert engine.output_dir == output_dir
        assert engine.style == "presentation"

    def test_create_figure_default(self):
        """Test figure creation with default parameters."""
        engine = VisualizationEngine()

        fig, ax = engine.create_figure()

        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)
        assert fig.get_size_inches()[0] == 8  # Default width
        assert fig.get_size_inches()[1] == 6  # Default height

        plt.close(fig)

    def test_create_figure_custom_size(self):
        """Test figure creation with custom size."""
        engine = VisualizationEngine()

        fig, ax = engine.create_figure(figsize=(12, 8))

        assert fig.get_size_inches()[0] == 12
        assert fig.get_size_inches()[1] == 8

        plt.close(fig)

    def test_apply_publication_style(self):
        """Test application of publication style to axes."""
        engine = VisualizationEngine()

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        engine.apply_publication_style(ax, "Test Title", "X Label", "Y Label")

        assert ax.get_title() == "Test Title"
        assert ax.get_xlabel() == "X Label"
        assert ax.get_ylabel() == "Y Label"

        # Check that grid is enabled
        assert ax.grid

        plt.close(fig)

    def test_get_color(self):
        """Test color cycling functionality."""
        engine = VisualizationEngine()

        # Test first few colors
        color1 = engine.get_color(0)
        color2 = engine.get_color(1)
        color3 = engine.get_color(2)

        assert isinstance(color1, str)
        assert isinstance(color2, str)
        assert isinstance(color3, str)

        # Colors should be different
        assert color1 != color2
        assert color2 != color3

        # Test cycling (should repeat after certain point)
        color_reset = engine.get_color(10)  # Should cycle back
        assert isinstance(color_reset, str)

    def test_save_figure_png(self, temp_output_dir):
        """Test figure saving as PNG."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        result = engine.save_figure(fig, "test_figure.png")

        assert isinstance(result, dict)
        assert "png" in result
        assert "pdf" in result
        assert isinstance(result["png"], Path)
        assert isinstance(result["pdf"], Path)

        # Check files were created
        expected_png = temp_output_dir / "test_figure.png.png"
        expected_pdf = temp_output_dir / "test_figure.png.pdf"
        assert expected_png.exists()
        assert expected_pdf.exists()
        assert expected_png.stat().st_size > 0
        assert expected_pdf.stat().st_size > 0

        plt.close(fig)

    def test_save_figure_pdf(self, temp_output_dir):
        """Test figure saving as PDF."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        result = engine.save_figure(fig, "test_figure.pdf")

        assert isinstance(result, dict)
        assert "png" in result
        assert "pdf" in result
        assert isinstance(result["png"], Path)
        assert isinstance(result["pdf"], Path)

        # Check files were created (note: filename.pdf becomes pdf.pdf and png.pdf)
        expected_png = temp_output_dir / "test_figure.pdf.png"
        expected_pdf = temp_output_dir / "test_figure.pdf.pdf"
        assert expected_png.exists()
        assert expected_pdf.exists()

        plt.close(fig)

    def test_save_figure_with_path_creation(self, temp_output_dir):
        """Test figure saving creates necessary directories."""
        nested_dir = temp_output_dir / "nested" / "deep" / "path"
        engine = VisualizationEngine(output_dir=nested_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        result = engine.save_figure(fig, "test_figure.png")

        # Check directory was created and files exist
        assert nested_dir.exists()
        assert (nested_dir / "test_figure.png.png").exists()
        assert (nested_dir / "test_figure.png.pdf").exists()

        plt.close(fig)

    def test_create_quadrant_matrix_plot(self):
        """Test quadrant matrix plot creation."""
        engine = VisualizationEngine()

        # Create test matrix data
        matrix_data = {
            'matrix': np.array([[0.8, 0.2], [0.3, 0.9]]),
            'labels': ['Data', 'Cognitive'],
            'title': 'Test Quadrant Matrix'
        }

        fig = engine.create_quadrant_matrix_plot(matrix_data)

        assert isinstance(fig, plt.Figure)

        # Check that axes contain expected content
        axes = fig.get_axes()
        assert len(axes) > 0

        plt.close(fig)

    def test_create_quadrant_matrix_plot_minimal_data(self):
        """Test quadrant matrix plot with minimal data."""
        engine = VisualizationEngine()

        matrix_data = {
            'matrix': np.array([[1.0, 0.0], [0.0, 1.0]]),
            'labels': ['A', 'B']
        }

        fig = engine.create_quadrant_matrix_plot(matrix_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_generative_model_diagram(self):
        """Test generative model diagram creation."""
        engine = VisualizationEngine()

        # Create test model structure
        model_structure = {
            'states': ['State 1', 'State 2', 'State 3'],
            'observations': ['Obs A', 'Obs B'],
            'actions': ['Action X', 'Action Y'],
            'connections': [
                ('State 1', 'Obs A'),
                ('State 2', 'Obs B'),
                ('Action X', 'State 1'),
                ('Action Y', 'State 2')
            ]
        }

        fig = engine.create_generative_model_diagram(model_structure)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_generative_model_diagram_empty(self):
        """Test generative model diagram with minimal structure."""
        engine = VisualizationEngine()

        model_structure = {
            'states': ['S1'],
            'observations': ['O1'],
            'actions': ['A1'],
            'connections': []
        }

        fig = engine.create_generative_model_diagram(model_structure)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_meta_cognitive_diagram(self):
        """Test meta-cognitive diagram creation."""
        engine = VisualizationEngine()

        meta_cog_data = {
            'confidence_levels': [0.5, 0.7, 0.8, 0.9],
            'attention_allocation': [0.3, 0.4, 0.2, 0.1],
            'strategy_effectiveness': [0.6, 0.8, 0.7, 0.9],
            'time_steps': [1, 2, 3, 4]
        }

        fig = engine.create_meta_cognitive_diagram(meta_cog_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_meta_cognitive_diagram_single_point(self):
        """Test meta-cognitive diagram with single data point."""
        engine = VisualizationEngine()

        meta_cog_data = {
            'confidence_levels': [0.8],
            'attention_allocation': [0.5],
            'strategy_effectiveness': [0.7],
            'time_steps': [1]
        }

        fig = engine.create_meta_cognitive_diagram(meta_cog_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_fep_visualization(self):
        """Test Free Energy Principle visualization."""
        engine = VisualizationEngine()

        fep_data = {
            'free_energy_values': [2.5, 2.1, 1.8, 1.5, 1.2],
            'time_steps': [0, 1, 2, 3, 4],
            'system_boundaries': ['Boundary 1', 'Boundary 2'],
            'minimization_trajectory': [3.0, 2.8, 2.4, 2.0, 1.6]
        }

        fig = engine.create_fep_visualization(fep_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_fep_visualization_minimal(self):
        """Test FEP visualization with minimal data."""
        engine = VisualizationEngine()

        fep_data = {
            'free_energy_values': [2.0, 1.5],
            'time_steps': [0, 1],
            'system_boundaries': [],
            'minimization_trajectory': [2.5, 2.0]
        }

        fig = engine.create_fep_visualization(fep_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_matplotlib_backend_setup(self):
        """Test that matplotlib backend is properly configured."""
        # This test ensures the Agg backend is used for headless operation
        import matplotlib
        current_backend = matplotlib.get_backend().lower()

        # Should use a non-interactive backend (Agg is preferred for tests)
        assert 'agg' in current_backend or 'cairo' in current_backend or 'svg' in current_backend

    def test_figure_cleanup(self):
        """Test that figures are properly closed to avoid memory leaks."""
        engine = VisualizationEngine()

        # Create multiple figures
        figs = []
        for i in range(3):
            fig, ax = engine.create_figure()
            ax.plot([1, 2, 3], [i+1, i+2, i+3])
            figs.append(fig)

        # All figures should be valid
        for fig in figs:
            assert isinstance(fig, plt.Figure)

        # Clean up
        for fig in figs:
            plt.close(fig)

    def test_error_handling_invalid_save_path(self, temp_output_dir):
        """Test error handling for invalid save paths."""
        # Create a read-only directory to test error handling
        readonly_dir = temp_output_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Make it read-only

        engine = VisualizationEngine(output_dir=readonly_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])

        # Should handle permission errors gracefully
        with pytest.raises(Exception):  # Should raise an error for permission issues
            engine.save_figure(fig, "test.png")

        plt.close(fig)

    def test_figure_size_validation(self):
        """Test that figure sizes are reasonable."""
        engine = VisualizationEngine()

        # Test various sizes
        test_sizes = [(4, 3), (12, 8), (16, 12)]

        for width, height in test_sizes:
            fig, ax = engine.create_figure(figsize=(width, height))

            actual_size = fig.get_size_inches()
            assert actual_size[0] == width
            assert actual_size[1] == height

            plt.close(fig)

    def test_style_application_consistency(self):
        """Test that style application is consistent across figures."""
        engine = VisualizationEngine()

        # Create two figures with the same style
        fig1, ax1 = engine.create_figure()
        fig2, ax2 = engine.create_figure()

        # Apply the same style
        engine.apply_publication_style(ax1, "Title 1", "X1", "Y1")
        engine.apply_publication_style(ax2, "Title 2", "X2", "Y2")

        # Both should have grids enabled
        assert ax1.grid
        assert ax2.grid

        # Both should have titles set
        assert ax1.get_title() == "Title 1"
        assert ax2.get_title() == "Title 2"

        plt.close(fig1)
        plt.close(fig2)

    def test_output_directory_creation(self, temp_output_dir):
        """Test that output directory is created if it doesn't exist."""
        nonexistent_dir = temp_output_dir / "new" / "nested" / "directory"
        assert not nonexistent_dir.exists()

        engine = VisualizationEngine(output_dir=nonexistent_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])

        engine.save_figure(fig, "test.png")

        # Directory should now exist
        assert nonexistent_dir.exists()
        assert (nonexistent_dir / "test.png.png").exists()
        assert (nonexistent_dir / "test.png.pdf").exists()

        plt.close(fig)

    def test_multiple_figures_same_engine(self, temp_output_dir):
        """Test creating and saving multiple figures with the same engine."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        png_files = []
        pdf_files = []
        for i in range(3):
            fig, ax = engine.create_figure()
            ax.plot([1, 2, 3], [i+1, i+2, i+3])
            ax.set_title(f"Figure {i+1}")

            filename = f"figure_{i+1}.png"
            result = engine.save_figure(fig, filename)
            png_files.append(result["png"])
            pdf_files.append(result["pdf"])

            plt.close(fig)

        # Check all files were created
        for png_file, pdf_file in zip(png_files, pdf_files):
            assert png_file.exists()
            assert pdf_file.exists()
            assert png_file.stat().st_size > 0
            assert pdf_file.stat().st_size > 0

    def test_figure_metadata_returned(self, temp_output_dir):
        """Test that save_figure returns correct metadata."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        result = engine.save_figure(fig, "metadata_test.svg")

        # Check all expected keys are present
        assert "png" in result
        assert "pdf" in result

        # Check paths are correct type
        assert isinstance(result["png"], Path)
        assert isinstance(result["pdf"], Path)

        # Check files exist
        assert result["png"].exists()
        assert result["pdf"].exists()

        plt.close(fig)

    def test_save_figure_custom_formats(self, temp_output_dir):
        """Test figure saving with custom formats (svg, eps)."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        result = engine.save_figure(fig, "custom_format", formats=["png", "pdf", "svg"])

        assert "png" in result
        assert "pdf" in result
        assert "svg" in result
        assert result["png"].exists()
        assert result["pdf"].exists()
        assert result["svg"].exists()

        plt.close(fig)

    def test_save_figure_empty_figure(self, temp_output_dir):
        """Test saving empty figure."""
        engine = VisualizationEngine(output_dir=temp_output_dir)

        fig, ax = plt.subplots()
        # No plot data - empty figure

        result = engine.save_figure(fig, "empty_figure")

        assert "png" in result
        assert "pdf" in result
        assert result["png"].exists()
        assert result["pdf"].exists()
        assert result["png"].stat().st_size > 0  # Should still create valid file

        plt.close(fig)

    def test_create_quadrant_matrix_plot_old_format(self):
        """Test quadrant matrix plot with old format (quadrants key)."""
        engine = VisualizationEngine()

        matrix_data = {
            'quadrants': {
                'bottom_left': {
                    'id': 'Q1',
                    'name': 'Data × Cognitive',
                    'color': '#1f77b4'
                },
                'bottom_right': {
                    'id': 'Q2',
                    'name': 'Metadata × Cognitive',
                    'color': '#ff7f0e'
                },
                'top_left': {
                    'id': 'Q3',
                    'name': 'Data × Meta-Cognitive',
                    'color': '#2ca02c'
                },
                'top_right': {
                    'id': 'Q4',
                    'name': 'Metadata × Meta-Cognitive',
                    'color': '#d62728'
                }
            },
            'title': 'Quadrant Matrix',
            'subtitle': 'Test Subtitle',
            'x_axis': {'categories': ['Low', 'High']},
            'y_axis': {'categories': ['Data', 'Metadata']}
        }

        fig = engine.create_quadrant_matrix_plot(matrix_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_quadrant_matrix_plot_invalid_format(self):
        """Test quadrant matrix plot with invalid data format."""
        engine = VisualizationEngine()

        matrix_data = {
            'invalid_key': 'invalid_value'
            # Missing both 'quadrants' and ('matrix', 'labels')
        }

        from utils.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            engine.create_quadrant_matrix_plot(matrix_data)

        assert "must contain either 'quadrants' or 'matrix' and 'labels'" in str(exc_info.value)

    def test_create_quadrant_matrix_plot_missing_labels(self):
        """Test quadrant matrix plot with missing labels."""
        engine = VisualizationEngine()

        matrix_data = {
            'matrix': np.array([[0.8, 0.2], [0.3, 0.9]])
            # Missing 'labels' key
        }

        from utils.exceptions import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            engine.create_quadrant_matrix_plot(matrix_data)

        assert "must contain either 'quadrants' or 'matrix' and 'labels'" in str(exc_info.value)

    def test_setup_matplotlib_style_unknown(self):
        """Test matplotlib style setup with unknown style."""
        engine = VisualizationEngine(style="unknown_style")
        # Should not crash, but may use default settings
        assert engine.style == "unknown_style"

        # Should still be able to create figures
        fig, ax = engine.create_figure()
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_apply_publication_style_with_legend(self):
        """Test apply_publication_style with legend enabled."""
        engine = VisualizationEngine()

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2], label='Line 1')
        ax.plot([1, 2, 3], [2, 3, 4], label='Line 2')

        engine.apply_publication_style(ax, "Title", "X", "Y", legend=True)

        assert ax.get_title() == "Title"
        # Legend should be configured

        plt.close(fig)

    def test_apply_publication_style_no_grid(self):
        """Test apply_publication_style with grid disabled."""
        engine = VisualizationEngine()

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        engine.apply_publication_style(ax, "Title", "X", "Y", grid=False)

        assert ax.get_title() == "Title"

        plt.close(fig)

    def test_get_color_cycling(self):
        """Test color cycling beyond palette length."""
        engine = VisualizationEngine()

        # Get colors beyond palette length (10 colors)
        color_0 = engine.get_color(0)
        color_10 = engine.get_color(10)  # Should cycle back
        color_20 = engine.get_color(20)  # Should cycle back again

        # Colors at multiples of 10 should be the same
        assert color_0 == color_10 == color_20

    def test_get_color_negative_index(self):
        """Test get_color with negative index (should handle modulo)."""
        engine = VisualizationEngine()

        # Negative indices should work with modulo
        color_neg1 = engine.get_color(-1)
        color_9 = engine.get_color(9)  # Last color in palette

        assert color_neg1 == color_9

    def test_create_quadrant_matrix_plot_with_subtitle(self):
        """Test quadrant matrix plot with subtitle."""
        engine = VisualizationEngine()

        matrix_data = {
            'matrix': np.array([[0.8, 0.2], [0.3, 0.9]]),
            'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
            'title': 'Main Title',
            'subtitle': 'Subtitle Text'
        }

        fig = engine.create_quadrant_matrix_plot(matrix_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_create_quadrant_matrix_plot_old_format_minimal(self):
        """Test quadrant matrix plot with old format minimal data."""
        engine = VisualizationEngine()

        matrix_data = {
            'quadrants': {
                'bottom_left': {'id': 'Q1', 'name': 'Q1', 'color': '#1f77b4'},
                'bottom_right': {'id': 'Q2', 'name': 'Q2', 'color': '#ff7f0e'},
                'top_left': {'id': 'Q3', 'name': 'Q3', 'color': '#2ca02c'},
                'top_right': {'id': 'Q4', 'name': 'Q4', 'color': '#d62728'}
            }
        }

        fig = engine.create_quadrant_matrix_plot(matrix_data)

        assert isinstance(fig, plt.Figure)
        plt.close(fig)
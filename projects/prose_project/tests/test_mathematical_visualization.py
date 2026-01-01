"""Tests for mathematical_visualization module."""
import numpy as np
import matplotlib.pyplot as plt
import pytest
from pathlib import Path
import tempfile

from src.mathematical_visualization import (
    plot_function_comparison,
    plot_convergence_analysis,
    plot_statistical_distribution,
    plot_growth_rates,
    plot_theoretical_convergence,
    save_figure,
    create_comprehensive_visualization,
)


class TestMathematicalVisualization:
    """Test mathematical visualization functions."""

    def test_plot_function_comparison(self):
        """Test function comparison plotting."""
        functions = {
            'Linear': lambda x: x,
            'Quadratic': lambda x: x**2,
        }

        fig = plot_function_comparison(functions)

        assert isinstance(fig, plt.Figure)
        # Should have lines for each function
        assert len(fig.axes[0].lines) == 2

        plt.close(fig)

    def test_plot_convergence_analysis(self):
        """Test convergence analysis plotting."""
        convergence_data = {
            'Method1': [1.0, 0.5, 0.25, 0.125],
            'Method2': [1.0, 0.8, 0.64, 0.512],
        }

        fig = plot_convergence_analysis(convergence_data)

        assert isinstance(fig, plt.Figure)
        assert len(fig.axes[0].lines) == 2

        plt.close(fig)

    def test_plot_statistical_distribution(self):
        """Test statistical distribution plotting."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)

        fig = plot_statistical_distribution(data)

        assert isinstance(fig, plt.Figure)
        # Should have histogram bars and vertical lines for mean/median
        ax = fig.axes[0]
        assert len(ax.patches) > 0  # Histogram bars
        assert len(ax.lines) >= 2   # Mean and median lines

        plt.close(fig)

    def test_plot_growth_rates(self):
        """Test growth rates plotting."""
        growth_functions = {
            'Linear': lambda x: x,
            'Quadratic': lambda x: x**2,
        }

        fig = plot_growth_rates(growth_functions)

        assert isinstance(fig, plt.Figure)
        assert len(fig.axes[0].lines) == 2

        plt.close(fig)

    def test_plot_theoretical_convergence(self):
        """Test theoretical convergence plotting."""
        convergence_functions = {
            'Linear': lambda x: 1 - 0.1 * x,
            'Quadratic': lambda x: np.exp(-x),
        }

        fig = plot_theoretical_convergence(convergence_functions)

        assert isinstance(fig, plt.Figure)
        assert len(fig.axes[0].lines) == 2

        plt.close(fig)

    def test_save_figure(self):
        """Test figure saving functionality."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            filepath = save_figure(fig, 'test_plot', output_dir)

            assert filepath.exists()
            assert filepath.suffix == '.png'
            assert 'test_plot' in str(filepath)

    def test_create_comprehensive_visualization(self):
        """Test comprehensive visualization creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            saved_files = create_comprehensive_visualization(output_dir)

            # Should create 5 different visualizations
            assert len(saved_files) == 5

            # All files should exist
            for filepath in saved_files.values():
                assert filepath.exists()
                assert filepath.suffix == '.png'

    def test_function_comparison_edge_cases(self):
        """Test function comparison with edge cases."""
        # Empty functions dict
        fig = plot_function_comparison({})
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

        # Function that raises exception
        def bad_function(x):
            raise ValueError("Bad function")

        functions = {'Good': lambda x: x, 'Bad': bad_function}
        fig = plot_function_comparison(functions)
        # Should still create figure even with bad function
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_convergence_analysis_log_scale(self):
        """Test convergence analysis with log scale."""
        convergence_data = {
            'Fast': [1.0, 0.1, 0.01, 0.001],
        }

        fig = plot_convergence_analysis(convergence_data, use_log_scale=True)
        assert isinstance(fig, plt.Figure)
        assert fig.axes[0].get_yscale() == 'log'
        plt.close(fig)

    def test_growth_rates_custom_range(self):
        """Test growth rates with custom range."""
        growth_functions = {
            'Linear': lambda x: x,
        }

        fig = plot_growth_rates(growth_functions, x_range=(1, 10), num_points=20)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_figure_custom_dpi(self):
        """Test figure saving with custom DPI."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            filepath = save_figure(fig, 'test_dpi', output_dir, dpi=150)

            assert filepath.exists()
            # Note: We can't easily test DPI in saved file without additional libraries
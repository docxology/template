"""Tests for mathematical_visualization module."""
import numpy as np
import matplotlib.pyplot as plt
import pytest
from pathlib import Path
import tempfile
import builtins
import sys
import importlib

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

    def test_save_figure_with_explicit_output_dir(self):
        """Test save_figure with explicit output_dir parameter (covers line 364)."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])

        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_dir = Path(temp_dir) / "custom_output"
            filepath = save_figure(fig, 'explicit_dir_test', explicit_dir)

            assert filepath.exists()
            assert filepath.parent == explicit_dir
            assert filepath.suffix == '.png'

    def test_plot_convergence_analysis_linear_scale(self):
        """Test convergence analysis with linear scale (use_log_scale=False)."""
        convergence_data = {
            'Method1': [1.0, 0.5, 0.25, 0.125],
            'Method2': [1.0, 0.8, 0.64, 0.512],
        }

        fig = plot_convergence_analysis(convergence_data, use_log_scale=False)
        assert isinstance(fig, plt.Figure)
        # Should use linear scale, not log scale
        assert fig.axes[0].get_yscale() != 'log'
        plt.close(fig)

    def test_plot_function_comparison_with_exception_and_logging(self):
        """Test exception handling in plot_function_comparison with logging available."""
        # Function that raises exception
        def bad_function(x):
            raise ValueError("Test exception for logging")

        functions = {
            'Good': lambda x: x,
            'Bad': bad_function,
            'AnotherGood': lambda x: x**2,
        }

        # Should handle exception gracefully and continue with other functions
        fig = plot_function_comparison(functions)
        assert isinstance(fig, plt.Figure)
        # Should have lines for good functions (at least 2)
        assert len(fig.axes[0].lines) >= 2
        plt.close(fig)

    def test_plot_growth_rates_with_exception_and_logging(self):
        """Test exception handling in plot_growth_rates with logging available."""
        # Function that raises exception
        def bad_growth_function(x):
            raise RuntimeError("Test exception for growth rates")

        growth_functions = {
            'Good': lambda x: x,
            'Bad': bad_growth_function,
            'AnotherGood': lambda x: np.sqrt(x),
        }

        # Should handle exception gracefully and continue with other functions
        fig = plot_growth_rates(growth_functions)
        assert isinstance(fig, plt.Figure)
        # Should have lines for good functions (at least 2)
        assert len(fig.axes[0].lines) >= 2
        plt.close(fig)

    def test_plot_theoretical_convergence_with_exception_and_logging(self):
        """Test exception handling in plot_theoretical_convergence with logging available."""
        # Function that raises exception
        def bad_convergence_function(x):
            raise TypeError("Test exception for convergence")

        convergence_functions = {
            'Good': lambda x: 1 - 0.1 * x,
            'Bad': bad_convergence_function,
            'AnotherGood': lambda x: np.exp(-x),
        }

        # Should handle exception gracefully and continue with other functions
        fig = plot_theoretical_convergence(convergence_functions)
        assert isinstance(fig, plt.Figure)
        # Should have lines for good functions (at least 2)
        assert len(fig.axes[0].lines) >= 2
        plt.close(fig)

    def test_module_works_without_logging(self, monkeypatch):
        """Test that module works when logging infrastructure is unavailable (lines 68-69)."""
        # Save original if it exists
        original_logging_utils = sys.modules.get('infrastructure.core.logging_utils')
        
        # Remove from sys.modules to force reimport
        if 'infrastructure.core.logging_utils' in sys.modules:
            del sys.modules['infrastructure.core.logging_utils']
        
        # Temporarily patch __import__ to raise ImportError for logging_utils
        original_import = builtins.__import__
        
        def restricted_import(name, *args, **kwargs):
            if name == 'infrastructure.core.logging_utils' or name.startswith('infrastructure.core.logging_utils'):
                raise ImportError("Logging module unavailable for testing")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr(builtins, '__import__', restricted_import)
        
        # Reload the module to trigger the ImportError path
        import src.mathematical_visualization as mv_module
        importlib.reload(mv_module)
        
        # Verify LOGGING_AVAILABLE is False
        assert mv_module.LOGGING_AVAILABLE is False
        
        # Verify functions still work without logging
        functions = {'Linear': lambda x: x}
        fig = mv_module.plot_function_comparison(functions)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
        
        # Test that exception handling still works (without logging)
        def bad_function(x):
            raise ValueError("Test")
        
        functions_with_bad = {'Good': lambda x: x, 'Bad': bad_function}
        fig = mv_module.plot_function_comparison(functions_with_bad)
        assert isinstance(fig, plt.Figure)
        # Should still work, just without logging the exception
        assert len(fig.axes[0].lines) >= 1  # At least the good function
        plt.close(fig)
        
        # Restore original module
        if original_logging_utils:
            sys.modules['infrastructure.core.logging_utils'] = original_logging_utils
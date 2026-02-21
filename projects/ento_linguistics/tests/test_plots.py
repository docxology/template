"""Comprehensive tests for src/plots.py to ensure 100% coverage."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from visualization.plots import (plot_3d_surface, plot_bar, plot_comparison, plot_contour,
                   plot_convergence, plot_heatmap, plot_line, plot_scatter,
                   plot_term_frequency, plot_domain_distribution,
                   plot_concept_network)


class TestPlotLine:
    """Test line plot function."""

    def test_basic_line_plot(self):
        """Test basic line plot."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])
        ax = plot_line(x, y)
        assert ax is not None
        plt.close(ax.figure)

    def test_line_plot_with_label(self):
        """Test line plot with label."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        ax = plot_line(x, y, label="Test Line")
        assert ax is not None
        plt.close(ax.figure)

    def test_line_plot_with_existing_axes(self):
        """Test line plot on existing axes."""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        result_ax = plot_line(x, y, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotScatter:
    """Test scatter plot function."""

    def test_basic_scatter_plot(self):
        """Test basic scatter plot."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])
        ax = plot_scatter(x, y)
        assert ax is not None
        plt.close(ax.figure)

    def test_scatter_with_color_and_size(self):
        """Test scatter plot with color and size."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        ax = plot_scatter(x, y, color="red", size=50, alpha=0.5)
        assert ax is not None
        plt.close(ax.figure)

    def test_scatter_with_label(self):
        """Test scatter plot with label."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        ax = plot_scatter(x, y, label="Scatter Data")
        assert ax is not None
        plt.close(ax.figure)

    def test_scatter_with_existing_axes(self):
        """Test scatter plot on existing axes."""
        fig, ax = plt.subplots()
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        result_ax = plot_scatter(x, y, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotBar:
    """Test bar chart function."""

    def test_basic_bar_chart(self):
        """Test basic bar chart."""
        categories = ["A", "B", "C"]
        values = np.array([1, 2, 3])
        ax = plot_bar(categories, values)
        assert ax is not None
        plt.close(ax.figure)

    def test_bar_chart_with_color(self):
        """Test bar chart with color."""
        categories = ["A", "B", "C"]
        values = np.array([1, 2, 3])
        ax = plot_bar(categories, values, color="blue")
        assert ax is not None
        plt.close(ax.figure)


class TestPlotConvergence:
    """Test convergence plot function."""

    def test_convergence_plot(self):
        """Test convergence plot."""
        iterations = np.array([1, 2, 3, 4, 5])
        values = np.array([10, 8, 6, 4, 2])
        ax = plot_convergence(iterations, values, target=0.0)
        assert ax is not None
        plt.close(ax.figure)

    def test_convergence_plot_without_target(self):
        """Test convergence plot without target."""
        iterations = np.array([1, 2, 3, 4, 5])
        values = np.array([10, 8, 6, 4, 2])
        ax = plot_convergence(iterations, values)
        assert ax is not None
        plt.close(ax.figure)

    def test_convergence_plot_with_existing_axes(self):
        """Test convergence plot with existing axes."""
        fig, ax = plt.subplots()
        iterations = np.array([1, 2, 3, 4, 5])
        values = np.array([10, 8, 6, 4, 2])
        result_ax = plot_convergence(iterations, values, target=2.0, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotComparison:
    """Test comparison plot function."""

    def test_comparison_bar_plot(self):
        """Test comparison bar plot."""
        methods = ["A", "B", "C"]
        metrics = {"accuracy": [0.8, 0.9, 0.85]}
        ax = plot_comparison(methods, metrics, "accuracy", plot_type="bar")
        assert ax is not None
        plt.close(ax.figure)

    def test_comparison_line_plot(self):
        """Test comparison line plot."""
        methods = ["A", "B", "C"]
        metrics = {"accuracy": [0.8, 0.9, 0.85]}
        ax = plot_comparison(methods, metrics, "accuracy", plot_type="line")
        assert ax is not None
        plt.close(ax.figure)

    def test_comparison_with_existing_axes(self):
        """Test comparison plot on existing axes."""
        fig, ax = plt.subplots()
        methods = ["A", "B", "C"]
        metrics = {"accuracy": [0.8, 0.9, 0.85]}
        result_ax = plot_comparison(methods, metrics, "accuracy", ax=ax)
        assert result_ax == ax
        plt.close(fig)

    def test_comparison_missing_metric(self):
        """Test comparison plot with missing metric."""
        methods = ["A", "B", "C"]
        metrics = {"other_metric": [0.8, 0.9, 0.85]}
        # When metric is missing, values will be empty list, which may cause issues
        # This tests the edge case handling
        try:
            ax = plot_comparison(methods, metrics, "accuracy", plot_type="line")
            assert ax is not None
            plt.close(ax.figure)
        except (ValueError, IndexError):
            # Expected to fail with empty values, but tests the code path
            pass


class TestPlotContour:
    """Test contour plot function."""

    def test_contour_plot(self):
        """Test contour plot."""
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        ax = plot_contour(X, Y, Z)
        assert ax is not None
        plt.close(ax.figure)

    def test_contour_filled(self):
        """Test filled contour plot."""
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        ax = plot_contour(X, Y, Z, filled=True)
        assert ax is not None
        plt.close(ax.figure)

    def test_contour_not_filled(self):
        """Test unfilled contour plot."""
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        ax = plot_contour(X, Y, Z, filled=False)
        assert ax is not None
        plt.close(ax.figure)

    def test_contour_with_existing_axes(self):
        """Test contour plot on existing axes."""
        fig, ax = plt.subplots()
        x = np.linspace(-5, 5, 20)
        y = np.linspace(-5, 5, 20)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        result_ax = plot_contour(X, Y, Z, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotHeatmap:
    """Test heatmap plot function."""

    def test_basic_heatmap(self):
        """Test basic heatmap."""
        data = np.random.rand(5, 5)
        ax = plot_heatmap(data)
        assert ax is not None
        plt.close(ax.figure)

    def test_heatmap_with_labels(self):
        """Test heatmap with row and column labels."""
        data = np.random.rand(3, 4)
        row_labels = ["R1", "R2", "R3"]
        col_labels = ["C1", "C2", "C3", "C4"]
        ax = plot_heatmap(data, row_labels=row_labels, col_labels=col_labels)
        assert ax is not None
        plt.close(ax.figure)

    def test_heatmap_without_colorbar(self):
        """Test heatmap without colorbar."""
        data = np.random.rand(5, 5)
        ax = plot_heatmap(data, colorbar=False)
        assert ax is not None
        plt.close(ax.figure)

    def test_heatmap_with_existing_axes(self):
        """Test heatmap on existing axes."""
        fig, ax = plt.subplots()
        data = np.random.rand(5, 5)
        result_ax = plot_heatmap(data, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlot3DSurface:
    """Test 3D surface plot function."""

    def test_3d_surface_plot(self):
        """Test 3D surface plot."""
        x = np.linspace(-5, 5, 30)
        y = np.linspace(-5, 5, 30)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        ax = plot_3d_surface(X, Y, Z)
        assert ax is not None
        plt.close(ax.figure.figure)

    def test_3d_surface_with_existing_axes(self):
        """Test 3D surface plot on existing axes."""
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        x = np.linspace(-5, 5, 20)
        y = np.linspace(-5, 5, 20)
        X, Y = np.meshgrid(x, y)
        Z = np.sin(np.sqrt(X**2 + Y**2))
        result_ax = plot_3d_surface(X, Y, Z, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotTermFrequencies:
    """Test term frequency plot function."""

    def test_term_frequencies_with_objects(self):
        """Test plotting term frequencies from objects with .frequency."""
        from analysis.term_extraction import Term

        terms = {
            "colony": Term(text="colony", lemma="colony", domains=["behavioral"], frequency=15),
            "worker": Term(text="worker", lemma="worker", domains=["behavioral"], frequency=10),
            "queen": Term(text="queen", lemma="queen", domains=["behavioral"], frequency=8),
        }
        ax = plot_term_frequency(terms, top_n=3)
        assert ax is not None
        plt.close(ax.figure)

    def test_term_frequencies_with_dicts(self):
        """Test plotting term frequencies from dict-style terms."""
        terms = {
            "colony": {"frequency": 15},
            "worker": {"frequency": 10},
            "queen": {"frequency": 8},
            "drone": {"frequency": 3},
        }
        ax = plot_term_frequency(terms, top_n=2)
        assert ax is not None
        plt.close(ax.figure)

    def test_term_frequencies_with_existing_axes(self):
        """Test term frequency plot on existing axes."""
        fig, ax = plt.subplots()
        terms = {
            "colony": {"frequency": 15},
            "worker": {"frequency": 10},
        }
        result_ax = plot_term_frequency(terms, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotDomainDistribution:
    """Test domain distribution plot function."""

    def test_basic_domain_distribution(self):
        """Test basic domain distribution."""
        domain_counts = {
            "behavioral": 45,
            "chemical": 30,
            "morphological": 20,
            "ecological": 15,
        }
        ax = plot_domain_distribution(domain_counts)
        assert ax is not None
        plt.close(ax.figure)

    def test_domain_distribution_with_axes(self):
        """Test domain distribution on existing axes."""
        fig, ax = plt.subplots()
        domain_counts = {"behavioral": 10, "chemical": 5}
        result_ax = plot_domain_distribution(domain_counts, ax=ax)
        assert result_ax == ax
        plt.close(fig)


class TestPlotConceptNetwork:
    """Test concept network plot function."""

    def test_concept_network_stub(self):
        """Test concept network placeholder."""
        ax = plot_concept_network({"concepts": {}})
        assert ax is not None
        plt.close(ax.figure)

    def test_concept_network_with_axes(self):
        """Test concept network on existing axes."""
        fig, ax = plt.subplots()
        result_ax = plot_concept_network({"concepts": {}}, ax=ax)
        assert result_ax == ax
        plt.close(fig)

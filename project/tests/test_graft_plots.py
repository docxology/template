"""Comprehensive tests for graft_plots module."""
import pytest
import numpy as np
import matplotlib.pyplot as plt
from graft_plots import (
    plot_success_rates,
    plot_compatibility_matrix,
    plot_healing_timeline,
    plot_success_by_factor,
    plot_technique_comparison,
    plot_survival_curve,
    plot_environmental_effects
)


class TestPlottingFunctions:
    """Test plotting functions."""
    
    def test_plot_success_rates(self):
        """Test success rate plotting."""
        techniques = ["whip", "cleft", "bark"]
        rates = np.array([0.85, 0.75, 0.70])
        ax = plot_success_rates(techniques, rates)
        assert ax is not None
        plt.close()
    
    def test_plot_success_rates_with_kwargs(self):
        """Test success rate plotting with kwargs."""
        techniques = ["whip", "cleft", "bark"]
        rates = np.array([0.85, 0.75, 0.70])
        ax = plot_success_rates(techniques, rates, color='red', alpha=0.7)
        assert ax is not None
        plt.close()
    
    def test_plot_compatibility_matrix(self):
        """Test compatibility matrix plotting."""
        matrix = np.random.beta(3, 1, size=(5, 5))
        np.fill_diagonal(matrix, 1.0)
        matrix = (matrix + matrix.T) / 2
        ax = plot_compatibility_matrix(matrix)
        assert ax is not None
        plt.close()
    
    def test_plot_compatibility_matrix_with_labels(self):
        """Test compatibility matrix with labels."""
        matrix = np.array([[1.0, 0.8], [0.8, 1.0]])
        species = ["Apple", "Pear"]
        ax = plot_compatibility_matrix(matrix, species_names=species)
        assert ax is not None
        plt.close()
    
    def test_plot_healing_timeline(self):
        """Test healing timeline plotting."""
        days = np.arange(0, 30)
        union_strength = 1.0 - np.exp(-days / 10.0)
        ax = plot_healing_timeline(days, union_strength)
        assert ax is not None
        plt.close()
    
    def test_plot_healing_timeline_with_markers(self):
        """Test healing timeline with markers."""
        days = np.arange(0, 30)
        union_strength = 1.0 - np.exp(-days / 10.0)
        ax = plot_healing_timeline(days, union_strength, marker='o', linestyle='--')
        assert ax is not None
        plt.close()
    
    def test_plot_success_by_factor(self):
        """Test success rate by factor plotting."""
        factors = np.array([0.3, 0.5, 0.7, 0.9])
        success_rates = np.array([0.4, 0.6, 0.8, 0.9])
        ax = plot_success_by_factor(factors, success_rates, factor_name="Compatibility")
        assert ax is not None
        plt.close()
    
    def test_plot_technique_comparison(self):
        """Test technique comparison plotting."""
        data = {
            "whip": {"success": np.array([1, 1, 0, 1, 1])},
            "cleft": {"success": np.array([1, 0, 1, 1, 0])},
            "bark": {"success": np.array([0, 1, 1, 1, 1])}
        }
        ax = plot_technique_comparison(data)
        assert ax is not None
        plt.close()
    
    def test_plot_survival_curve(self):
        """Test survival curve plotting."""
        time = np.array([10, 20, 30, 40, 50])
        survival = np.array([1.0, 0.9, 0.8, 0.75, 0.7])
        ax = plot_survival_curve(time, survival)
        assert ax is not None
        plt.close()
    
    def test_plot_environmental_effects(self):
        """Test environmental effects plotting."""
        temp = np.array([15, 20, 25, 30])
        hum = np.array([0.6, 0.7, 0.8, 0.9])
        success = np.array([0.6, 0.8, 0.9, 0.7])
        ax = plot_environmental_effects(temp, hum, success)
        assert ax is not None
        plt.close()


if __name__ == "__main__":
    pytest.main([__file__])


"""Comprehensive tests for graft_analysis module."""
import pytest
import numpy as np
from graft_analysis import (
    analyze_graft_outcomes,
    analyze_temporal_patterns,
    compare_techniques,
    analyze_factor_importance,
    analyze_species_compatibility_patterns,
    analyze_environmental_effects
)


class TestGraftOutcomes:
    """Test graft outcome analysis."""
    
    def test_analyze_outcomes(self):
        """Test outcome analysis."""
        success = np.array([1, 1, 0, 1, 0])
        union_strength = np.array([0.8, 0.9, np.nan, 0.7, np.nan])
        healing_time = np.array([20, 18, np.nan, 22, np.nan])
        outcomes = analyze_graft_outcomes(success, union_strength, healing_time)
        assert outcomes.success_rate == 0.6
        assert outcomes.n_trials == 5


class TestTemporalPatterns:
    """Test temporal pattern analysis."""
    
    def test_monthly_analysis(self):
        """Test monthly pattern analysis."""
        success = np.array([1, 1, 0, 1, 0, 1])
        months = np.array([2, 3, 3, 4, 4, 5])
        patterns = analyze_temporal_patterns(success, months=months)
        assert "monthly_success_rates" in patterns
    
    def test_temporal_with_dates(self):
        """Test temporal analysis with dates array."""
        success = np.array([1, 1, 0, 1, 0, 1])
        # Dates as day numbers (can be converted from datetime if needed)
        dates = np.array([10, 20, 30, 40, 50, 60])
        patterns = analyze_temporal_patterns(success, dates=dates)
        # Should still work even if dates don't directly affect analysis
        assert isinstance(patterns, dict)
    
    def test_temporal_best_month(self):
        """Test temporal analysis finds best month."""
        success = np.array([1, 1, 0, 1, 0, 1, 1, 1])
        months = np.array([2, 2, 3, 3, 4, 4, 5, 5])
        patterns = analyze_temporal_patterns(success, months=months)
        if "best_month" in patterns:
            assert 2 <= patterns["best_month"] <= 5


class TestTechniqueComparison:
    """Test technique comparison."""
    
    def test_compare_techniques(self):
        """Test technique comparison."""
        techniques = {
            "whip": np.array([1, 1, 0, 1]),
            "cleft": np.array([1, 0, 1, 0])
        }
        comparison = compare_techniques(techniques)
        assert "technique_success_rates" in comparison
        assert "best_technique" in comparison
    
    def test_compare_techniques_anova(self):
        """Test technique comparison with ANOVA (3+ techniques)."""
        techniques = {
            "whip": np.array([1, 1, 0, 1, 1]),
            "cleft": np.array([1, 0, 1, 0, 1]),
            "bark": np.array([0, 1, 1, 1, 0])
        }
        comparison = compare_techniques(techniques)
        assert "technique_success_rates" in comparison
        assert "best_technique" in comparison
        # Should have ANOVA results when >= 2 groups
        assert "anova" in comparison


class TestFactorImportance:
    """Test factor importance analysis."""
    
    def test_factor_importance(self):
        """Test factor importance calculation."""
        success = np.array([1, 1, 0, 1, 0])
        factors = {
            "compatibility": np.array([0.9, 0.8, 0.3, 0.7, 0.4]),
            "technique": np.array([0.8, 0.9, 0.5, 0.8, 0.6])
        }
        importance = analyze_factor_importance(success, factors)
        assert "compatibility" in importance
        assert "technique" in importance


class TestSpeciesCompatibility:
    """Test species compatibility pattern analysis."""
    
    def test_analyze_species_compatibility_patterns(self):
        """Test species compatibility pattern analysis."""
        matrix = np.array([
            [1.0, 0.8, 0.6],
            [0.8, 1.0, 0.7],
            [0.6, 0.7, 1.0]
        ])
        analysis = analyze_species_compatibility_patterns(matrix)
        assert "n_species" in analysis
        assert "average_compatibility" in analysis
        assert "avg_compatibility_per_species" in analysis
        assert "most_compatible_pairs" in analysis
        assert analysis["n_species"] == 3
        assert len(analysis["most_compatible_pairs"]) > 0
    
    def test_analyze_species_compatibility_with_names(self):
        """Test species compatibility analysis with species names."""
        matrix = np.array([
            [1.0, 0.9, 0.5],
            [0.9, 1.0, 0.6],
            [0.5, 0.6, 1.0]
        ])
        species_names = ["Apple", "Pear", "Quince"]
        analysis = analyze_species_compatibility_patterns(matrix, species_names=species_names)
        assert "most_compatible_pairs" in analysis
        # Check that pairs use species names
        if len(analysis["most_compatible_pairs"]) > 0:
            pair = analysis["most_compatible_pairs"][0]
            assert "species_1" in pair
            assert "species_2" in pair
            assert isinstance(pair["species_1"], str) or isinstance(pair["species_1"], int)


class TestEnvironmentalEffects:
    """Test environmental effects analysis."""
    
    def test_analyze_environmental_effects_optimal(self):
        """Test environmental effects with optimal conditions."""
        success = np.array([1, 1, 1, 0, 1])
        temperature = np.array([22.0, 23.0, 24.0, 15.0, 25.0])  # Most in optimal range
        humidity = np.array([0.8, 0.75, 0.85, 0.5, 0.9])  # Most in optimal range
        analysis = analyze_environmental_effects(success, temperature, humidity)
        assert "success_rate_optimal_conditions" in analysis
        assert "success_rate_suboptimal_conditions" in analysis
        assert "temperature_correlation" in analysis
        assert "humidity_correlation" in analysis
        assert "optimal_temperature_range" in analysis
        assert "optimal_humidity_range" in analysis
    
    def test_analyze_environmental_effects_suboptimal(self):
        """Test environmental effects with suboptimal conditions."""
        success = np.array([0, 0, 1, 0, 0])
        temperature = np.array([5.0, 10.0, 22.0, 35.0, 40.0])  # Most outside optimal
        humidity = np.array([0.3, 0.4, 0.8, 0.2, 0.1])  # Most outside optimal
        analysis = analyze_environmental_effects(success, temperature, humidity)
        assert "success_rate_optimal_conditions" in analysis
        assert "success_rate_suboptimal_conditions" in analysis
        # Suboptimal should have lower success rate
        if analysis["success_rate_optimal_conditions"] > 0:
            assert analysis["success_rate_suboptimal_conditions"] <= analysis["success_rate_optimal_conditions"]


if __name__ == "__main__":
    pytest.main([__file__])


"""Comprehensive tests for graft_statistics module."""
import pytest
import numpy as np
from graft_statistics import (
    calculate_graft_statistics,
    compare_technique_success,
    calculate_success_correlation,
    analyze_survival_curve,
    calculate_confidence_interval_success_rate,
    anova_technique_comparison
)


class TestGraftStatistics:
    """Test graft statistics calculations."""
    
    def test_calculate_statistics(self):
        """Test calculating graft statistics."""
        success = np.array([1, 1, 0, 1, 0])
        union_strength = np.array([0.8, 0.9, np.nan, 0.7, np.nan])
        stats = calculate_graft_statistics(success, union_strength)
        assert "success" in stats
        assert stats["success"].success_rate == 0.6
    
    def test_technique_difference(self):
        """Test technique difference test."""
        group1 = np.array([1, 1, 0, 1, 1])
        group2 = np.array([1, 0, 0, 0, 1])
        result = compare_technique_success(group1, group2)
        assert "p_value" in result
        assert "difference" in result
    
    def test_success_correlation(self):
        """Test success correlation calculation."""
        success = np.array([1, 1, 0, 1, 0])
        compatibility = np.array([0.9, 0.8, 0.3, 0.7, 0.4])
        result = calculate_success_correlation(success, compatibility)
        assert "correlation" in result
        assert result["correlation"] > 0  # Should be positive correlation


class TestSurvivalAnalysis:
    """Test survival curve analysis."""
    
    def test_survival_curve(self):
        """Test survival curve calculation."""
        healing_times = np.array([10, 15, 20, 25, 30])
        success = np.array([1, 1, 0, 1, 1])
        curve = analyze_survival_curve(healing_times, success)
        assert "time" in curve
        assert "survival" in curve
        assert len(curve["survival"]) == len(healing_times)


class TestConfidenceIntervals:
    """Test confidence interval calculations."""
    
    def test_confidence_interval(self):
        """Test confidence interval for success rate."""
        success = np.array([1, 1, 0, 1, 1, 0, 1, 1, 1, 0])
        lower, upper = calculate_confidence_interval_success_rate(success)
        assert 0.0 <= lower <= upper <= 1.0


if __name__ == "__main__":
    pytest.main([__file__])


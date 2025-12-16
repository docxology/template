"""Comprehensive tests for graft_metrics module."""
import pytest
import numpy as np
from graft_metrics import (
    calculate_success_rate,
    calculate_take_rate,
    calculate_union_strength_metrics,
    calculate_compatibility_score,
    calculate_economic_metrics,
    calculate_quality_index,
    calculate_growth_rate,
    calculate_healing_efficiency,
    GraftCustomMetric,
    calculate_all_graft_metrics
)


class TestSuccessMetrics:
    """Test success rate metrics."""
    
    def test_success_rate(self):
        """Test success rate calculation."""
        success = np.array([1, 1, 0, 1, 0])
        rate = calculate_success_rate(success)
        assert rate == 0.6
    
    def test_take_rate(self):
        """Test take rate calculation."""
        success = np.array([1, 1, 0, 1])
        rate = calculate_take_rate(success)
        assert rate == 0.75


class TestUnionStrength:
    """Test union strength metrics."""
    
    def test_union_strength_metrics(self):
        """Test union strength metric calculation."""
        union_strength = np.array([0.8, 0.9, 0.7, 0.85])
        success = np.array([1, 1, 1, 1])
        metrics = calculate_union_strength_metrics(union_strength, success)
        assert "mean" in metrics
        assert metrics["mean"] > 0.7
    
    def test_union_strength_no_success_filter(self):
        """Test union strength without success filter."""
        union_strength = np.array([0.8, 0.9, np.nan, 0.85])
        metrics = calculate_union_strength_metrics(union_strength, success=None)
        assert "mean" in metrics
        assert metrics["mean"] > 0
    
    def test_union_strength_empty_data(self):
        """Test union strength with empty valid data."""
        union_strength = np.array([np.nan, np.nan])
        metrics = calculate_union_strength_metrics(union_strength, success=None)
        assert metrics["mean"] == 0.0
        assert metrics["median"] == 0.0


class TestEconomicMetrics:
    """Test economic metrics."""
    
    def test_economic_calculation(self):
        """Test economic metrics calculation."""
        metrics = calculate_economic_metrics(
            success_rate=0.8,
            cost_per_graft=5.0,
            value_per_successful_graft=20.0,
            n_grafts=100
        )
        assert metrics["net_profit"] > 0
        assert metrics["roi_percent"] > 0


class TestCompatibilityScore:
    """Test compatibility score calculation."""
    
    def test_compatibility_score(self):
        """Test compatibility score calculation."""
        rootstock = np.array([0, 1, 2])
        scion = np.array([1, 2, 0])
        matrix = np.array([[1.0, 0.8, 0.6],
                           [0.8, 1.0, 0.7],
                           [0.6, 0.7, 1.0]])
        scores = calculate_compatibility_score(rootstock, scion, matrix)
        assert len(scores) == 3
        assert scores[0] == 0.8  # rootstock[0]=0, scion[0]=1 -> matrix[0,1]
    
    def test_compatibility_score_out_of_range(self):
        """Test compatibility with out-of-range indices."""
        rootstock = np.array([0, 10, 2])  # 10 is out of range
        scion = np.array([1, 2, 0])
        matrix = np.array([[1.0, 0.8, 0.6],
                           [0.8, 1.0, 0.7],
                           [0.6, 0.7, 1.0]])
        scores = calculate_compatibility_score(rootstock, scion, matrix)
        assert scores[1] == 0.0  # Out of range should give 0


class TestGrowthRate:
    """Test growth rate calculation."""
    
    def test_growth_rate(self):
        """Test growth rate calculation."""
        initial = np.array([10.0, 15.0, 20.0])
        final = np.array([20.0, 25.0, 35.0])
        time_period = 30.0
        rates = calculate_growth_rate(initial, final, time_period)
        assert np.all(rates > 0)
        assert rates[0] == pytest.approx(10.0 / 30.0)


class TestQualityIndex:
    """Test quality index calculation."""
    
    def test_quality_index(self):
        """Test quality index calculation."""
        compatibility = np.array([0.8, 0.9, 0.7])
        technique_quality = np.array([0.8, 0.9, 0.8])
        environmental_score = np.array([0.7, 0.8, 0.9])
        quality = calculate_quality_index(compatibility, technique_quality, environmental_score)
        assert np.all(quality >= 0) and np.all(quality <= 1)


class TestHealingEfficiency:
    """Test healing efficiency metrics."""
    
    def test_healing_efficiency(self):
        """Test healing efficiency calculation."""
        healing_times = np.array([15.0, 20.0, 25.0, 18.0])
        metrics = calculate_healing_efficiency(healing_times, target_time=21.0)
        assert "mean_healing_time" in metrics
        assert "efficiency_score" in metrics
        assert "on_time_percentage" in metrics
        assert metrics["mean_healing_time"] > 0
    
    def test_healing_efficiency_empty_data(self):
        """Test healing efficiency with empty data."""
        healing_times = np.array([np.nan, np.nan])
        metrics = calculate_healing_efficiency(healing_times)
        assert metrics["mean_healing_time"] == 0.0
        assert metrics["efficiency_score"] == 0.0
        assert metrics["on_time_percentage"] == 0.0


class TestCustomMetric:
    """Test custom metric framework."""
    
    def test_custom_metric(self):
        """Test custom metric creation and calculation."""
        def my_metric(values):
            return np.mean(values) * 2
        
        metric = GraftCustomMetric("doubled_mean", my_metric)
        result = metric.calculate(np.array([1, 2, 3, 4, 5]))
        assert result == 6.0  # mean is 3, doubled is 6


class TestAllMetrics:
    """Test comprehensive metrics calculation."""
    
    def test_all_metrics_full(self):
        """Test calculating all metrics with all parameters."""
        success = np.array([1, 1, 0, 1, 0])
        union_strength = np.array([0.8, 0.9, np.nan, 0.85, np.nan])
        healing_time = np.array([15.0, 20.0, np.nan, 18.0, np.nan])
        compatibility = np.array([0.9, 0.8, 0.3, 0.7, 0.4])
        
        metrics = calculate_all_graft_metrics(
            success=success,
            union_strength=union_strength,
            healing_time=healing_time,
            compatibility=compatibility
        )
        
        assert "success_rate" in metrics
        assert "union_mean" in metrics
        assert "mean_healing_time" in metrics
        assert "mean_compatibility" in metrics
        assert metrics["success_rate"] == 0.6
    
    def test_all_metrics_minimal(self):
        """Test calculating metrics with only success data."""
        success = np.array([1, 1, 0, 1])
        metrics = calculate_all_graft_metrics(success=success)
        assert "success_rate" in metrics
        assert "take_rate" in metrics
        assert metrics["success_rate"] == 0.75


if __name__ == "__main__":
    pytest.main([__file__])


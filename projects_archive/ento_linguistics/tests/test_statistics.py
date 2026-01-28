"""Comprehensive tests for src/statistics.py to ensure 100% coverage."""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add project src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.statistics import (DescriptiveStats, anova_test,
                            calculate_confidence_interval,
                            calculate_correlation, calculate_descriptive_stats,
                            fit_distribution, t_test)


class TestDescriptiveStats:
    """Test DescriptiveStats dataclass."""

    def test_stats_creation(self):
        """Test creating descriptive stats."""
        stats = DescriptiveStats(
            mean=1.0, std=0.5, median=1.0, min=0.0, max=2.0, q25=0.5, q75=1.5, count=10
        )
        assert stats.mean == 1.0
        assert stats.count == 10

    def test_to_dict(self):
        """Test converting to dictionary."""
        stats = DescriptiveStats(
            mean=1.0, std=0.5, median=1.0, min=0.0, max=2.0, q25=0.5, q75=1.5, count=10
        )
        stats_dict = stats.to_dict()
        assert stats_dict["mean"] == 1.0
        assert stats_dict["count"] == 10


class TestCalculateDescriptiveStats:
    """Test descriptive statistics calculation."""

    def test_basic_calculation(self):
        """Test basic descriptive stats calculation."""
        data = np.array([1, 2, 3, 4, 5])
        stats = calculate_descriptive_stats(data)
        assert stats.mean == 3.0
        assert stats.median == 3.0
        assert stats.min == 1.0
        assert stats.max == 5.0

    def test_2d_array(self):
        """Test with 2D array."""
        data = np.array([[1, 2], [3, 4], [5, 6]])
        stats = calculate_descriptive_stats(data)
        assert stats.count == 6


class TestTTest:
    """Test t-test functionality."""

    def test_one_sample_test(self):
        """Test one-sample t-test."""
        sample = np.array([1, 2, 3, 4, 5])
        result = t_test(sample, mu=3.0)
        assert "t_statistic" in result
        assert "p_value" in result
        assert "degrees_of_freedom" in result

    def test_one_sample_test_no_mu(self):
        """Test one-sample t-test with mu=None (line 83)."""
        sample = np.array([1, 2, 3, 4, 5])
        result = t_test(sample, sample2=None, mu=None)
        assert "t_statistic" in result
        assert "p_value" in result
        # mu should default to 0.0

    def test_two_sample_test(self):
        """Test two-sample t-test."""
        sample1 = np.array([1, 2, 3, 4, 5])
        sample2 = np.array([2, 3, 4, 5, 6])
        result = t_test(sample1, sample2)
        assert "t_statistic" in result
        assert "p_value" in result


class TestCalculateCorrelation:
    """Test correlation calculation."""

    def test_pearson_correlation(self):
        """Test Pearson correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        result = calculate_correlation(x, y, method="pearson")
        assert "correlation" in result
        assert result["method"] == "pearson"

    def test_spearman_correlation(self):
        """Test Spearman correlation (lines 140-142)."""
        try:
            from scipy.stats import spearmanr
        except ImportError:
            pytest.skip("scipy not available")
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        result = calculate_correlation(x, y, method="spearman")
        assert "correlation" in result
        assert "p_value" in result
        assert result["method"] == "spearman"

    def test_different_lengths(self):
        """Test error with different length arrays."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        with pytest.raises(ValueError):
            calculate_correlation(x, y)

    def test_invalid_method(self):
        """Test invalid method raises error."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])
        with pytest.raises(ValueError):
            calculate_correlation(x, y, method="invalid")


class TestCalculateConfidenceInterval:
    """Test confidence interval calculation."""

    def test_basic_ci(self):
        """Test basic confidence interval."""
        data = np.array([1, 2, 3, 4, 5])
        ci = calculate_confidence_interval(data, confidence=0.95)
        assert len(ci) == 2
        assert ci[0] < ci[1]


class TestFitDistribution:
    """Test distribution fitting."""

    def test_normal_distribution(self):
        """Test fitting normal distribution."""
        data = np.random.normal(0, 1, 100)
        result = fit_distribution(data, distribution="normal")
        assert result["distribution"] == "normal"
        assert "mean" in result
        assert "std" in result

    def test_exponential_distribution(self):
        """Test fitting exponential distribution."""
        data = np.random.exponential(1.0, 100)
        result = fit_distribution(data, distribution="exponential")
        assert result["distribution"] == "exponential"
        assert "scale" in result

    def test_uniform_distribution(self):
        """Test fitting uniform distribution (line 213)."""
        data = np.random.uniform(0, 10, 100)
        result = fit_distribution(data, distribution="uniform")
        assert result["distribution"] == "uniform"
        assert "min" in result
        assert "max" in result

    def test_invalid_distribution(self):
        """Test invalid distribution raises error."""
        data = np.array([1, 2, 3, 4, 5])
        with pytest.raises(ValueError):
            fit_distribution(data, distribution="invalid")


class TestAnovaTest:
    """Test ANOVA test."""

    def test_basic_anova(self):
        """Test basic ANOVA test."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        group3 = np.array([3, 4, 5, 6, 7])
        result = anova_test([group1, group2, group3])
        assert "f_statistic" in result
        assert "p_value" in result
        assert "df_between" in result
        assert "df_within" in result

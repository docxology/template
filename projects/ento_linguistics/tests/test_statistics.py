"""Comprehensive tests for src/statistics.py to ensure 100% coverage."""

import numpy as np
import pytest

from analysis.statistics import (DescriptiveStats, anova_test,
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
        """Test one-sample t-test with value assertions."""
        sample = np.array([1, 2, 3, 4, 5])
        result = t_test(sample, mu=3.0)
        assert "t_statistic" in result
        assert "p_value" in result
        assert "degrees_of_freedom" in result
        assert result["p_value"] > 0.5  # Mean equals mu, not significant
        assert result["degrees_of_freedom"] == 4  # n-1

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

    def test_identical_samples_high_pvalue(self):
        """Identical samples should produce p-value close to 1.0."""
        sample = np.array([3.0, 3.0, 3.0, 3.0, 3.0])
        result = t_test(sample, mu=3.0)
        # t-stat should be ~0, but std=0 causes nan; test with near-identical
        sample_near = np.array([3.0, 3.001, 2.999, 3.0, 3.0])
        result = t_test(sample_near, mu=3.0)
        assert result["p_value"] > 0.5  # Not significant at all

    def test_significant_difference_low_pvalue(self):
        """Strongly different samples should produce p-value < 0.05."""
        sample1 = np.array([1, 2, 3, 4, 5])
        sample2 = np.array([100, 101, 102, 103, 104])
        result = t_test(sample1, sample2)
        assert result["p_value"] < 0.05  # Significant difference

    def test_pvalue_not_hardcoded(self):
        """P-value must vary based on input data, not be constant 0.05."""
        result1 = t_test(np.array([1, 2, 3, 4, 5]), mu=3.0)
        result2 = t_test(np.array([1, 2, 3, 4, 5]), mu=100.0)
        assert result1["p_value"] != result2["p_value"]

    def test_one_sided_greater(self):
        """One-sided test (greater) should give half the two-sided p-value for positive t."""
        sample = np.array([10, 11, 12, 13, 14])
        r_two = t_test(sample, mu=5.0, alternative="two-sided")
        r_greater = t_test(sample, mu=5.0, alternative="greater")
        assert r_greater["p_value"] == pytest.approx(r_two["p_value"] / 2, abs=1e-6)

    def test_one_sided_less(self):
        """One-sided test (less) with sample mean > mu should give high p-value."""
        sample = np.array([10, 11, 12, 13, 14])
        result = t_test(sample, mu=5.0, alternative="less")
        assert result["p_value"] > 0.95  # Almost certainly not less


class TestCalculateCorrelation:
    """Test correlation calculation."""

    def test_pearson_correlation(self):
        """Test Pearson correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        result = calculate_correlation(x, y, method="pearson")
        assert "correlation" in result
        assert result["method"] == "pearson"

    def test_perfect_correlation_pvalue_near_zero(self):
        """Perfect correlation should give p-value near 0."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        result = calculate_correlation(x, y, method="pearson")
        assert abs(result["correlation"] - 1.0) < 1e-10
        assert result["p_value"] < 0.01

    def test_no_correlation_high_pvalue(self):
        """Uncorrelated data should give high p-value."""
        np.random.seed(42)
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        y = np.array([5.0, 3.0, 7.0, 1.0, 8.0, 2.0, 6.0, 4.0])
        result = calculate_correlation(x, y, method="pearson")
        assert result["p_value"] > 0.05  # Not significant

    def test_pearson_pvalue_not_hardcoded(self):
        """Pearson p-value must vary based on data."""
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        r1 = calculate_correlation(x, x * 2, method="pearson")
        r2 = calculate_correlation(x, np.array([5.0, 3.0, 1.0, 4.0, 2.0]), method="pearson")
        assert r1["p_value"] != r2["p_value"]

    def test_spearman_correlation(self):
        """Test Spearman correlation with value assertions."""
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
        assert result["correlation"] > 0.9  # Perfectly monotonic data
        assert result["p_value"] < 0.05  # Significant correlation

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

    def test_ci_contains_mean(self):
        """Confidence interval must contain the sample mean."""
        data = np.array([10, 12, 14, 16, 18])
        ci = calculate_confidence_interval(data, confidence=0.95)
        mean = np.mean(data)
        assert ci[0] < mean < ci[1]

    def test_wider_ci_at_higher_confidence(self):
        """99% CI should be wider than 95% CI."""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ci_95 = calculate_confidence_interval(data, confidence=0.95)
        ci_99 = calculate_confidence_interval(data, confidence=0.99)
        width_95 = ci_95[1] - ci_95[0]
        width_99 = ci_99[1] - ci_99[0]
        assert width_99 > width_95

    def test_ci_uses_t_distribution_not_z(self):
        """For small samples, t-distribution CI should be wider than z-based 1.96."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])  # n=5
        ci = calculate_confidence_interval(data, confidence=0.95)
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        n = len(data)
        # z-based margin (normal approximation)
        z_margin = 1.96 * (std / np.sqrt(n))
        actual_margin = mean - ci[0]
        # t-distribution margin should be larger for small n
        assert actual_margin > z_margin


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

    def test_identical_groups_high_pvalue(self):
        """Identical groups should give p-value close to 1.0."""
        group = np.array([3.0, 3.001, 2.999, 3.0, 3.0])
        result = anova_test([group, group.copy(), group.copy()])
        assert result["p_value"] > 0.9

    def test_very_different_groups_low_pvalue(self):
        """Very different groups should give p-value < 0.05."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([100, 101, 102, 103, 104])
        group3 = np.array([200, 201, 202, 203, 204])
        result = anova_test([group1, group2, group3])
        assert result["p_value"] < 0.01

    def test_anova_pvalue_not_hardcoded(self):
        """ANOVA p-value must vary based on input data."""
        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([2, 3, 4, 5, 6])
        group3 = np.array([100, 101, 102, 103, 104])
        r1 = anova_test([group1, group2, group1.copy()])
        r2 = anova_test([group1, group2, group3])
        assert r1["p_value"] != r2["p_value"]

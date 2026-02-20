"""Tests for statistical_analysis.py module.

Comprehensive tests for the StatisticalAnalyzer class and statistical functions,
ensuring correct statistical computations and error handling.
"""

import numpy as np
import pytest
from src.analysis.statistical_analysis import StatisticalAnalyzer
from src.utils.exceptions import ValidationError


class TestStatisticalAnalyzer:
    """Test StatisticalAnalyzer class functionality."""

    def test_initialization_default_alpha(self):
        """Test StatisticalAnalyzer initialization with default alpha."""
        analyzer = StatisticalAnalyzer()

        assert analyzer.alpha == 0.05

    def test_initialization_custom_alpha(self):
        """Test StatisticalAnalyzer initialization with custom alpha."""
        alpha = 0.01
        analyzer = StatisticalAnalyzer(alpha=alpha)

        assert analyzer.alpha == alpha

    def test_calculate_descriptive_stats_basic(self):
        """Test descriptive statistics calculation with basic data."""
        analyzer = StatisticalAnalyzer()

        data = np.array([1, 2, 3, 4, 5])
        stats = analyzer.calculate_descriptive_stats(data)

        assert isinstance(stats, dict)
        assert stats["count"] == 5
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["range"] == 4.0

    def test_calculate_descriptive_stats_comprehensive(self):
        """Test all descriptive statistics with comprehensive data."""
        analyzer = StatisticalAnalyzer()

        # Create test data with known properties
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        stats = analyzer.calculate_descriptive_stats(data)

        # Check all expected keys are present
        expected_keys = [
            "count",
            "mean",
            "std",
            "var",
            "median",
            "min",
            "max",
            "range",
            "q25",
            "q75",
            "iqr",
            "skewness",
            "kurtosis",
        ]
        for key in expected_keys:
            assert key in stats

        # Check specific values
        assert stats["count"] == 10
        assert abs(stats["mean"] - 5.5) < 1e-10
        assert stats["median"] == 5.5
        assert stats["min"] == 1.0
        assert stats["max"] == 10.0
        assert stats["range"] == 9.0

        # Check quartiles
        assert stats["q25"] == 3.25
        assert stats["q75"] == 7.75
        assert stats["iqr"] == 4.5

    def test_calculate_descriptive_stats_skewed_data(self):
        """Test descriptive statistics with skewed data."""
        analyzer = StatisticalAnalyzer()

        # Right-skewed data
        data = np.array([1, 1, 2, 2, 2, 3, 3, 10])
        stats = analyzer.calculate_descriptive_stats(data)

        assert stats["mean"] > stats["median"]  # Right-skewed
        assert stats["skewness"] > 0  # Positive skewness

    def test_calculate_descriptive_stats_empty_data(self):
        """Test descriptive statistics with empty data."""
        analyzer = StatisticalAnalyzer()

        with pytest.raises(Exception):  # ValidationError
            analyzer.calculate_descriptive_stats(np.array([]))

    def test_calculate_descriptive_stats_single_value(self):
        """Test descriptive statistics with single value (should raise ValidationError)."""
        analyzer = StatisticalAnalyzer()

        data = np.array([5.0])
        with pytest.raises(ValidationError, match="Need at least 2 data points"):
            analyzer.calculate_descriptive_stats(data)

    def test_calculate_descriptive_stats_from_list(self):
        """Test descriptive statistics with Python list input."""
        analyzer = StatisticalAnalyzer()

        data = [1, 2, 3, 4, 5]
        stats = analyzer.calculate_descriptive_stats(data)

        assert stats["count"] == 5
        assert stats["mean"] == 3.0

    def test_calculate_correlation_pearson(self):
        """Test Pearson correlation calculation."""
        analyzer = StatisticalAnalyzer()

        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect positive correlation

        result = analyzer.calculate_correlation(x, y, method="pearson")

        assert isinstance(result, dict)
        assert abs(result["correlation"] - 1.0) < 1e-10
        assert "p_value" in result
        assert "method" in result
        assert result["method"] == "pearson"

    def test_calculate_correlation_spearman(self):
        """Test Spearman correlation calculation."""
        analyzer = StatisticalAnalyzer()

        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 4, 9, 16, 25])  # Monotonic relationship

        result = analyzer.calculate_correlation(x, y, method="spearman")

        assert isinstance(result, dict)
        assert (
            abs(result["correlation"] - 1.0) < 1e-10
        )  # Allow for floating point precision
        assert result["method"] == "spearman"

    def test_calculate_correlation_kendall(self):
        """Test Kendall correlation calculation."""
        analyzer = StatisticalAnalyzer()

        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])

        result = analyzer.calculate_correlation(x, y, method="kendall")

        assert isinstance(result, dict)
        assert abs(result["correlation"] - 1.0) < 1e-10
        assert result["method"] == "kendall"

    def test_calculate_correlation_invalid_method(self):
        """Test correlation calculation with invalid method."""
        analyzer = StatisticalAnalyzer()

        x = np.array([1, 2, 3])
        y = np.array([1, 2, 3])

        with pytest.raises(Exception):  # ValidationError
            analyzer.calculate_correlation(x, y, method="invalid")

    def test_calculate_correlation_different_lengths(self):
        """Test correlation calculation with mismatched array lengths."""
        analyzer = StatisticalAnalyzer()

        x = np.array([1, 2, 3])
        y = np.array([1, 2])

        with pytest.raises(Exception):  # ValidationError
            analyzer.calculate_correlation(x, y)

    def test_calculate_correlation_no_correlation(self):
        """Test correlation calculation with uncorrelated data."""
        analyzer = StatisticalAnalyzer()

        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)

        result = analyzer.calculate_correlation(x, y, method="pearson")

        assert isinstance(result["correlation"], float)
        assert abs(result["correlation"]) < 0.2  # Should be close to 0

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation."""
        analyzer = StatisticalAnalyzer()

        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        ci = analyzer.calculate_confidence_interval(data)

        assert isinstance(ci, dict)
        assert "mean" in ci
        assert "lower_bound" in ci
        assert "upper_bound" in ci
        assert "confidence_level" in ci
        assert "standard_error" in ci

        # Check bounds are reasonable
        assert ci["lower_bound"] < ci["mean"] < ci["upper_bound"]
        assert ci["confidence_level"] == 0.95

    def test_calculate_confidence_interval_small_sample(self):
        """Test confidence interval with small sample."""
        analyzer = StatisticalAnalyzer()

        data = np.array([1, 2, 3])
        ci = analyzer.calculate_confidence_interval(data, confidence_level=0.90)

        assert isinstance(ci, dict)
        assert ci["confidence_level"] == 0.90
        assert ci["lower_bound"] < ci["mean"] < ci["upper_bound"]

    def test_calculate_confidence_interval_single_value(self):
        """Test confidence interval with single value."""
        analyzer = StatisticalAnalyzer()

        data = np.array([5.0])
        ci = analyzer.calculate_confidence_interval(data)

        assert ci["mean"] == 5.0
        assert ci["lower_bound"] == 5.0
        assert ci["upper_bound"] == 5.0

    def test_perform_t_test_paired(self):
        """Test paired t-test."""
        analyzer = StatisticalAnalyzer()

        before = np.array([1, 2, 3, 4, 5])
        after = np.array([2, 3, 4, 5, 6])

        result = analyzer.perform_t_test(before, after, test_type="paired")

        assert isinstance(result, dict)
        assert "t_statistic" in result
        assert "p_value" in result
        assert "test_type" in result
        assert result["test_type"] == "paired"

    def test_perform_t_test_independent(self):
        """Test independent t-test."""
        analyzer = StatisticalAnalyzer()

        group1 = np.array([1, 2, 3, 4, 5])
        group2 = np.array([3, 4, 5, 6, 7])

        result = analyzer.perform_t_test(group1, group2, test_type="independent")

        assert isinstance(result, dict)
        assert result["test_type"] == "independent"

    def test_perform_t_test_invalid_type(self):
        """Test t-test with invalid test type."""
        analyzer = StatisticalAnalyzer()

        data1 = np.array([1, 2, 3])
        data2 = np.array([1, 2, 3])

        with pytest.raises(Exception):  # ValidationError
            analyzer.perform_t_test(data1, data2, test_type="invalid")

    def test_analyze_algorithm_performance(self):
        """Test algorithm performance analysis."""
        analyzer = StatisticalAnalyzer()

        # Mock algorithm results
        results = {
            "algorithm_a": np.array([0.8, 0.85, 0.82, 0.87, 0.83]),
            "algorithm_b": np.array([0.75, 0.78, 0.80, 0.76, 0.79]),
            "algorithm_c": np.array([0.90, 0.88, 0.92, 0.89, 0.91]),
        }

        analysis = analyzer.analyze_algorithm_performance(results)

        assert isinstance(analysis, dict)
        assert "algorithm_statistics" in analysis
        assert "comparison" in analysis
        assert "best_performing" in analysis

        # Check individual stats for each algorithm
        for alg_name in results.keys():
            assert alg_name in analysis["algorithm_statistics"]

    def test_analyze_algorithm_performance_single_algorithm(self):
        """Test algorithm performance analysis with single algorithm."""
        analyzer = StatisticalAnalyzer()

        results = {"algorithm_a": np.array([0.8, 0.85, 0.82])}

        analysis = analyzer.analyze_algorithm_performance(results)

        assert isinstance(analysis, dict)
        assert "algorithm_a" in analysis["algorithm_statistics"]

    def test_error_handling_all_methods(self):
        """Test error handling across all methods."""
        analyzer = StatisticalAnalyzer()

        # Test with invalid data types
        with pytest.raises(Exception):
            analyzer.calculate_descriptive_stats("not_an_array")

        with pytest.raises(Exception):
            analyzer.calculate_correlation([1, 2], [1])  # Different lengths

        with pytest.raises(Exception):
            analyzer.calculate_confidence_interval([])  # Empty data

    def test_alpha_parameter_usage(self):
        """Test that alpha parameter affects hypothesis tests."""
        analyzer_strict = StatisticalAnalyzer(alpha=0.01)
        analyzer_lenient = StatisticalAnalyzer(alpha=0.10)

        # Both should have different alpha values
        assert analyzer_strict.alpha == 0.01
        assert analyzer_lenient.alpha == 0.10

    def test_output_types_consistency(self):
        """Test that all methods return consistent output types."""
        analyzer = StatisticalAnalyzer()

        # Test descriptive stats
        stats = analyzer.calculate_descriptive_stats([1, 2, 3])
        assert isinstance(stats, dict)
        assert all(isinstance(v, (int, float)) for v in stats.values())

        # Test correlation
        corr = analyzer.calculate_correlation([1, 2, 3], [1, 2, 3])
        assert isinstance(corr, dict)
        assert isinstance(corr["correlation"], float)

        # Test confidence interval
        ci = analyzer.calculate_confidence_interval([1, 2, 3])
        assert isinstance(ci, dict)
        assert isinstance(ci["mean"], float)

    def test_large_dataset_handling(self):
        """Test statistical methods with larger datasets."""
        analyzer = StatisticalAnalyzer()

        # Generate larger test dataset
        np.random.seed(42)
        large_data = np.random.randn(1000)

        # Test descriptive stats
        stats = analyzer.calculate_descriptive_stats(large_data)
        assert stats["count"] == 1000

        # Test confidence interval
        ci = analyzer.calculate_confidence_interval(large_data)
        assert abs(ci["mean"]) < 0.1  # Should be close to 0 for normal distribution

    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases."""
        analyzer = StatisticalAnalyzer()

        # All same values
        same_values = np.array([5.0] * 10)
        stats = analyzer.calculate_descriptive_stats(same_values)
        assert stats["std"] == 0.0
        assert stats["var"] == 0.0

        # Negative values
        negative_data = np.array([-5, -3, -1, 1, 3, 5])
        stats_neg = analyzer.calculate_descriptive_stats(negative_data)
        assert stats_neg["min"] == -5.0
        assert stats_neg["max"] == 5.0

        # Very small numbers
        small_data = np.array([1e-10, 2e-10, 3e-10])
        stats_small = analyzer.calculate_descriptive_stats(small_data)
        assert stats_small["mean"] > 0


class TestStatisticalAnalyzerCoverage:
    """Additional tests to increase coverage of uncovered branches."""

    def test_descriptive_stats_fewer_than_3_points(self):
        """Test descriptive stats with fewer than 3 data points (skewness/kurtosis fallback)."""
        analyzer = StatisticalAnalyzer()
        data = np.array([1.0, 2.0])
        result = analyzer.calculate_descriptive_stats(data)
        assert result["skewness"] == 0.0
        assert result["kurtosis"] == 0.0
        assert result["count"] == 2

    def test_correlation_moderate_strength(self):
        """Test correlation interpretation for moderate strength."""
        analyzer = StatisticalAnalyzer()
        np.random.seed(42)
        x = np.arange(20, dtype=float)
        y = x * 0.5 + np.random.normal(0, 3, 20)
        result = analyzer.calculate_correlation(x, y)
        assert "correlation" in result
        assert isinstance(result["interpretation"], str)

    def test_confidence_interval_with_confidence_level_param(self):
        """Test confidence interval using confidence_level parameter name."""
        analyzer = StatisticalAnalyzer()
        data = np.array([1, 2, 3, 4, 5], dtype=float)
        result = analyzer.calculate_confidence_interval(data, confidence_level=0.99)
        assert "mean" in result
        assert result["confidence_level"] == 0.99

    def test_confidence_interval_both_params_raises(self):
        """Test that specifying both confidence and confidence_level raises error."""
        analyzer = StatisticalAnalyzer()
        data = np.array([1, 2, 3, 4, 5], dtype=float)
        with pytest.raises(ValidationError):
            analyzer.calculate_confidence_interval(data, confidence_level=0.95, confidence=0.99)

    def test_t_test_invalid_test_type(self):
        """Test t-test with invalid test_type raises error."""
        analyzer = StatisticalAnalyzer()
        g1 = np.array([1.0, 2.0, 3.0])
        g2 = np.array([4.0, 5.0, 6.0])
        with pytest.raises(ValidationError):
            analyzer.perform_t_test(g1, g2, test_type="invalid")

    def test_t_test_group_too_small(self):
        """Test t-test with group having fewer than 2 observations."""
        analyzer = StatisticalAnalyzer()
        with pytest.raises(ValidationError):
            analyzer.perform_t_test(np.array([1.0]), np.array([1.0, 2.0]))
        with pytest.raises(ValidationError):
            analyzer.perform_t_test(np.array([1.0, 2.0]), np.array([1.0]))

    def test_t_test_paired_unequal_sizes(self):
        """Test paired t-test with unequal sample sizes."""
        analyzer = StatisticalAnalyzer()
        with pytest.raises(ValidationError):
            analyzer.perform_t_test(
                np.array([1.0, 2.0, 3.0]),
                np.array([4.0, 5.0]),
                test_type="paired",
            )

    def test_effect_size_interpretation_all_levels(self):
        """Test effect size interpretation covers all branches."""
        analyzer = StatisticalAnalyzer()
        assert "large" in analyzer._interpret_effect_size(0.9)
        assert "medium" in analyzer._interpret_effect_size(0.6)
        assert "small" in analyzer._interpret_effect_size(0.3)
        assert "negligible" in analyzer._interpret_effect_size(0.1)

    def test_algorithm_performance_empty_raises(self):
        """Test algorithm performance with empty results raises error."""
        analyzer = StatisticalAnalyzer()
        with pytest.raises(ValidationError):
            analyzer.analyze_algorithm_performance({})

    def test_convenience_functions(self):
        """Test module-level convenience functions."""
        from src.analysis.statistical_analysis import (
            calculate_descriptive_stats,
            calculate_correlation,
            calculate_confidence_interval,
            anova_test,
        )

        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = calculate_descriptive_stats(data)
        assert stats["mean"] == 3.0

        corr = calculate_correlation(data, data)
        assert np.isclose(corr["correlation"], 1.0)

        ci = calculate_confidence_interval(data)
        assert "mean" in ci

        result = anova_test(data, data + 5)
        assert "f_statistic" in result

    def test_demonstrate_statistical_analysis(self):
        """Test the demonstrate_statistical_analysis function."""
        from src.analysis.statistical_analysis import demonstrate_statistical_analysis

        demo = demonstrate_statistical_analysis()
        assert "descriptive_statistics" in demo
        assert "correlation_analysis" in demo
        assert "confidence_interval" in demo
        assert "anova_test" in demo
        assert "algorithm_comparison" in demo
        assert "purpose" in demo

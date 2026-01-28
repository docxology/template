"""Statistical Analysis for Active Inference Meta-Pragmatic Framework.

This module provides statistical analysis functions for evaluating Active Inference
algorithms, including descriptive statistics, hypothesis testing, correlation analysis,
and confidence interval calculations.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from utils.exceptions import ValidationError
from utils.logging import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer:
    """Statistical analysis toolkit for Active Inference research.

    Provides comprehensive statistical methods for analyzing algorithm performance,
    model comparisons, and theoretical validation.
    """

    def __init__(self, alpha: float = 0.05) -> None:
        """Initialize statistical analyzer.

        Args:
            alpha: Significance level for hypothesis tests
        """
        self.alpha = alpha
        logger.info(f"Initialized statistical analyzer with alpha={alpha}")

    def calculate_descriptive_stats(
        self, data: NDArray
    ) -> Dict[str, Union[float, int]]:
        """Calculate comprehensive descriptive statistics.

        Args:
            data: Input data array

        Returns:
            Dictionary containing descriptive statistics
        """
        try:
            data = np.asarray(data)
            if data.size == 0:
                raise ValidationError("Cannot calculate statistics for empty data")

            # Validate minimum sample size for meaningful statistics
            if data.size < 2:
                raise ValidationError(
                    f"Need at least 2 data points for statistical calculations, got {data.size}"
                )

            # Use ddof=1 for sample statistics, but only if we have enough data
            ddof = 1 if data.size > 1 else 0

            stats_dict = {
                "count": int(data.size),
                "mean": float(np.mean(data)),
                "std": float(np.std(data, ddof=ddof)),  # Sample standard deviation
                "var": float(np.var(data, ddof=ddof)),  # Sample variance
                "median": float(np.median(data)),
                "min": float(np.min(data)),
                "max": float(np.max(data)),
                "range": float(np.max(data) - np.min(data)),
                "q25": float(np.percentile(data, 25)),  # 25th percentile
                "q75": float(np.percentile(data, 75)),  # 75th percentile
                "iqr": float(np.subtract(*np.percentile(data, [75, 25]))),  # IQR
            }

            # Only calculate higher-order statistics if we have enough data to be meaningful
            if data.size >= 3:
                try:
                    stats_dict["skewness"] = float(stats.skew(data))
                    stats_dict["kurtosis"] = float(stats.kurtosis(data))
                except (ValueError, RuntimeWarning):
                    # Handle cases where skewness/kurtosis calculation fails
                    stats_dict["skewness"] = 0.0
                    stats_dict["kurtosis"] = 0.0
            else:
                stats_dict["skewness"] = 0.0
                stats_dict["kurtosis"] = 0.0

            logger.debug(
                f"Calculated descriptive statistics for {data.size} data points"
            )
            return stats_dict

        except Exception as e:
            logger.error(f"Error calculating descriptive statistics: {e}")
            raise ValidationError(
                f"Descriptive statistics calculation failed: {e}"
            ) from e

    def calculate_correlation(
        self, x: NDArray, y: NDArray, method: str = "pearson"
    ) -> Dict[str, Union[float, int]]:
        """Calculate correlation between two variables.

        Args:
            x: First variable data
            y: Second variable data
            method: Correlation method ('pearson', 'spearman', 'kendall')

        Returns:
            Dictionary containing correlation results
        """
        try:
            x, y = np.asarray(x), np.asarray(y)

            if len(x) != len(y):
                raise ValidationError("Correlation variables must have same length")

            if method == "pearson":
                corr_coef, p_value = stats.pearsonr(x, y)
            elif method == "spearman":
                corr_coef, p_value = stats.spearmanr(x, y)
            elif method == "kendall":
                corr_coef, p_value = stats.kendalltau(x, y)
            else:
                raise ValidationError(f"Unknown correlation method: {method}")

            correlation = {
                "correlation": float(corr_coef),
                "p_value": float(p_value),
                "method": method,
                "significant": p_value < self.alpha,
                "sample_size": len(x),
                "interpretation": self._interpret_correlation(corr_coef, p_value),
            }

            logger.debug(
                f"Calculated {method} correlation: r={corr_coef:.3f}, p={p_value:.3f}"
            )
            return correlation

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            raise ValidationError(f"Correlation calculation failed: {e}") from e

    def _interpret_correlation(self, coeff: float, p_value: float) -> str:
        """Interpret correlation results."""
        strength = "weak"
        if abs(coeff) >= 0.7:
            strength = "strong"
        elif abs(coeff) >= 0.3:
            strength = "moderate"

        direction = "positive" if coeff > 0 else "negative"

        significance = "significant" if p_value < self.alpha else "not significant"

        return f"{strength} {direction} correlation ({significance})"

    def calculate_confidence_interval(
        self,
        data: NDArray,
        confidence_level: Optional[float] = None,
        confidence: Optional[float] = None,
    ) -> Dict[str, Union[float, List[float]]]:
        """Calculate confidence interval for mean.

        Args:
            data: Input data array
            confidence: Confidence level (0.95 for 95% CI)

        Returns:
            Dictionary containing confidence interval results
        """
        try:
            data = np.asarray(data)

            # Validate input data
            if data.size == 0:
                raise ValidationError(
                    "Cannot calculate confidence interval for empty data"
                )

            # Handle parameter name compatibility
            if confidence_level is not None and confidence is not None:
                raise ValidationError(
                    "Cannot specify both 'confidence_level' and 'confidence' parameters"
                )
            elif confidence_level is not None:
                conf_level = confidence_level
            elif confidence is not None:
                conf_level = confidence
            else:
                conf_level = 0.95

            n = len(data)

            mean = np.mean(data)

            # Handle single value case
            if n == 1:
                # For single value, confidence interval bounds equal the mean
                confidence_interval = {
                    "mean": float(mean),
                    "confidence_level": conf_level,
                    "sample_size": n,
                    "standard_error": 0.0,
                    "margin_error": 0.0,
                    "lower_bound": float(mean),
                    "upper_bound": float(mean),
                    "ci_range": [float(mean), float(mean)],
                    "interpretation": f"{conf_level*100:.0f}% CI: [{mean:.3f}, {mean:.3f}] (single value)",
                }
                logger.debug(
                    f"Calculated {conf_level*100:.0f}% CI for single value: mean={mean:.3f}"
                )
                return confidence_interval

            if n < 2:
                raise ValidationError(
                    "Need at least 2 data points for confidence interval"
                )

            std_err = stats.sem(data)  # Standard error of the mean

            # t-distribution critical value
            t_crit = stats.t.ppf((1 + conf_level) / 2, n - 1)

            margin_error = t_crit * std_err
            ci_lower = mean - margin_error
            ci_upper = mean + margin_error

            confidence_interval = {
                "mean": float(mean),
                "confidence_level": conf_level,
                "sample_size": n,
                "standard_error": float(std_err),
                "margin_error": float(margin_error),
                "lower_bound": float(ci_lower),
                "upper_bound": float(ci_upper),
                "ci_range": [float(ci_lower), float(ci_upper)],
                "interpretation": f"{conf_level*100:.0f}% CI: [{ci_lower:.3f}, {ci_upper:.3f}]",
            }

            logger.debug(
                f"Calculated {conf_level*100:.0f}% CI: mean={mean:.3f}, range=[{ci_lower:.3f}, {ci_upper:.3f}]"
            )
            return confidence_interval

        except Exception as e:
            logger.error(f"Error calculating confidence interval: {e}")
            raise ValidationError(f"Confidence interval calculation failed: {e}") from e

    def anova_test(self, *groups: NDArray) -> Dict[str, Union[float, bool, str]]:
        """Perform one-way ANOVA test.

        Args:
            *groups: Variable number of data arrays (groups to compare)

        Returns:
            Dictionary containing ANOVA test results
        """
        try:
            if len(groups) < 2:
                raise ValidationError("ANOVA requires at least 2 groups")

            # Convert to list and validate
            group_data = [np.asarray(g) for g in groups]

            # Perform ANOVA
            f_stat, p_value = stats.f_oneway(*group_data)

            anova_result = {
                "test": "One-way ANOVA",
                "f_statistic": float(f_stat),
                "p_value": float(p_value),
                "significant": p_value < self.alpha,
                "n_groups": len(groups),
                "group_sizes": [len(g) for g in group_data],
                "total_sample_size": sum(len(g) for g in group_data),
                "interpretation": self._interpret_anova(p_value),
                "post_hoc_needed": p_value < self.alpha,
            }

            logger.debug(
                f"ANOVA test: F={f_stat:.3f}, p={p_value:.3f}, significant={p_value < self.alpha}"
            )
            return anova_result

        except Exception as e:
            logger.error(f"Error performing ANOVA test: {e}")
            raise ValidationError(f"ANOVA test failed: {e}") from e

    def _interpret_anova(self, p_value: float) -> str:
        """Interpret ANOVA results."""
        if p_value < self.alpha:
            return (
                "Significant differences found between groups (reject null hypothesis)"
            )
        else:
            return "No significant differences found between groups (fail to reject null hypothesis)"

    def perform_t_test(
        self, group1: NDArray, group2: NDArray, test_type: str = "independent"
    ) -> Dict[str, Union[float, bool, str]]:
        """Perform t-test between two groups.

        Args:
            group1: First group data
            group2: Second group data
            paired: Whether to perform paired t-test

        Returns:
            Dictionary containing t-test results
        """
        try:
            if test_type not in ["paired", "independent"]:
                raise ValidationError(
                    f"test_type must be 'paired' or 'independent', got '{test_type}'"
                )

            g1, g2 = np.asarray(group1), np.asarray(group2)

            # Validate minimum sample sizes to prevent degrees of freedom issues
            if len(g1) < 2:
                raise ValidationError(
                    f"Group 1 must have at least 2 observations, got {len(g1)}"
                )
            if len(g2) < 2:
                raise ValidationError(
                    f"Group 2 must have at least 2 observations, got {len(g2)}"
                )

            if test_type == "paired":
                if len(g1) != len(g2):
                    raise ValidationError(
                        f"Paired t-test requires equal sample sizes, got {len(g1)} vs {len(g2)}"
                    )
                t_stat, p_value = stats.ttest_rel(g1, g2)
                test_name = "Paired t-test"
            else:  # test_type == "independent"
                t_stat, p_value = stats.ttest_ind(
                    g1, g2, equal_var=False
                )  # Welch's t-test
                test_name = "Independent t-test (Welch)"

            # Calculate effect size (Cohen's d) with safe variance calculation
            mean_diff = np.mean(g1) - np.mean(g2)

            # Use ddof=1 for sample variance, but handle edge cases
            var1 = np.var(g1, ddof=1) if len(g1) > 1 else 0
            var2 = np.var(g2, ddof=1) if len(g2) > 1 else 0

            # Calculate pooled standard deviation safely
            pooled_var = (var1 + var2) / 2
            pooled_std = np.sqrt(pooled_var) if pooled_var > 0 else 0

            cohens_d = abs(mean_diff) / pooled_std if pooled_std > 0 else 0

            t_test_result = {
                "test": test_name,
                "test_type": test_type,
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < self.alpha,
                "mean_difference": float(mean_diff),
                "cohens_d": float(cohens_d),
                "group1_size": len(g1),
                "group2_size": len(g2),
                "effect_size_interpretation": self._interpret_effect_size(cohens_d),
                "interpretation": self._interpret_t_test(p_value, cohens_d),
            }

            logger.debug(
                f"{test_name}: t={t_stat:.3f}, p={p_value:.3f}, d={cohens_d:.3f}"
            )
            return t_test_result

        except Exception as e:
            logger.error(f"Error performing t-test: {e}")
            raise ValidationError(f"t-test failed: {e}") from e

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size."""
        if cohens_d >= 0.8:
            return "large effect"
        elif cohens_d >= 0.5:
            return "medium effect"
        elif cohens_d >= 0.2:
            return "small effect"
        else:
            return "negligible effect"

    def _interpret_t_test(self, p_value: float, cohens_d: float) -> str:
        """Interpret t-test results."""
        significance = "significant" if p_value < self.alpha else "not significant"
        effect = self._interpret_effect_size(cohens_d)

        return f"{significance} difference with {effect} (p={p_value:.3f}, d={cohens_d:.3f})"

    def analyze_algorithm_performance(
        self, algorithm_results: Dict[str, List[float]]
    ) -> Dict[str, Union[Dict, List]]:
        """Analyze performance of multiple algorithms.

        Args:
            algorithm_results: Dictionary mapping algorithm names to performance scores

        Returns:
            Dictionary containing comparative performance analysis
        """
        try:
            if not algorithm_results:
                raise ValidationError("No algorithm results provided")

            # Calculate statistics for each algorithm
            algorithm_stats = {}
            performance_data = []

            for name, scores in algorithm_results.items():
                stats_dict = self.calculate_descriptive_stats(scores)
                algorithm_stats[name] = stats_dict
                performance_data.append(scores)

            # Perform statistical comparison if multiple algorithms
            comparison = {}
            if len(algorithm_results) > 1:
                # ANOVA to test if algorithms differ
                anova_result = self.anova_test(*performance_data)
                comparison["anova"] = anova_result

                # Pairwise t-tests
                pairwise_tests = {}
                algorithm_names = list(algorithm_results.keys())

                for i, name1 in enumerate(algorithm_names[:-1]):
                    for name2 in algorithm_names[i + 1 :]:
                        t_test = self.perform_t_test(
                            algorithm_results[name1], algorithm_results[name2]
                        )
                        pairwise_tests[f"{name1}_vs_{name2}"] = t_test

                comparison["pairwise_t_tests"] = pairwise_tests

            analysis = {
                "algorithm_statistics": algorithm_stats,
                "comparison": comparison,
                "best_performing": max(
                    algorithm_stats.keys(), key=lambda k: algorithm_stats[k]["mean"]
                ),
                "ranking": sorted(
                    algorithm_stats.keys(),
                    key=lambda k: algorithm_stats[k]["mean"],
                    reverse=True,
                ),
                "sample_sizes": {
                    name: len(scores) for name, scores in algorithm_results.items()
                },
            }

            logger.info(f"Analyzed performance of {len(algorithm_results)} algorithms")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing algorithm performance: {e}")
            raise ValidationError(f"Algorithm performance analysis failed: {e}") from e


# Convenience functions for direct use
def calculate_descriptive_stats(data: NDArray) -> Dict[str, Union[float, int]]:
    """Convenience function for descriptive statistics."""
    analyzer = StatisticalAnalyzer()
    return analyzer.calculate_descriptive_stats(data)


def calculate_correlation(
    x: NDArray, y: NDArray, method: str = "pearson"
) -> Dict[str, Union[float, int]]:
    """Convenience function for correlation analysis."""
    analyzer = StatisticalAnalyzer()
    return analyzer.calculate_correlation(x, y, method)


def calculate_confidence_interval(
    data: NDArray, confidence: float = 0.95
) -> Dict[str, Union[float, List[float]]]:
    """Convenience function for confidence intervals."""
    analyzer = StatisticalAnalyzer()
    return analyzer.calculate_confidence_interval(data, confidence)


def anova_test(*groups: NDArray) -> Dict[str, Union[float, bool, str]]:
    """Convenience function for ANOVA testing."""
    analyzer = StatisticalAnalyzer()
    return analyzer.anova_test(*groups)


def demonstrate_statistical_analysis() -> Dict[str, Union[str, Dict]]:
    """Demonstrate statistical analysis capabilities.

    Returns:
        Dictionary containing statistical analysis demonstrations
    """
    analyzer = StatisticalAnalyzer()

    # Generate sample data
    np.random.seed(42)
    data1 = np.random.normal(10, 2, 50)
    data2 = np.random.normal(12, 2, 50)
    data3 = np.random.normal(8, 3, 50)

    # Demonstrate descriptive statistics
    desc_stats = analyzer.calculate_descriptive_stats(data1)

    # Demonstrate correlation
    correlation = analyzer.calculate_correlation(data1, data2)

    # Demonstrate confidence interval
    ci = analyzer.calculate_confidence_interval(data1)

    # Demonstrate ANOVA
    anova = analyzer.anova_test(data1, data2, data3)

    # Demonstrate algorithm comparison
    algorithm_results = {
        "Algorithm_A": np.random.normal(0.85, 0.05, 30),
        "Algorithm_B": np.random.normal(0.78, 0.08, 30),
        "Algorithm_C": np.random.normal(0.92, 0.03, 30),
    }
    performance_analysis = analyzer.analyze_algorithm_performance(algorithm_results)

    demonstration = {
        "descriptive_statistics": desc_stats,
        "correlation_analysis": correlation,
        "confidence_interval": ci,
        "anova_test": anova,
        "algorithm_comparison": performance_analysis,
        "purpose": """
        These statistical analysis functions enable rigorous evaluation of Active Inference
        algorithms, model comparisons, and theoretical validation with proper statistical
        significance testing and effect size calculations.
        """,
    }

    logger.info("Demonstrated statistical analysis capabilities")
    return demonstration

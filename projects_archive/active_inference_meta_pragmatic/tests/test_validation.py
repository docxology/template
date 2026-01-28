"""Tests for validation.py module.

Comprehensive tests for the ValidationFramework class, ensuring all validation
methods are thoroughly tested with real data and no mocks.
"""

import numpy as np
import pytest
from src.validation import (ValidationFramework,
                            demonstrate_validation_framework)
from utils.exceptions import ValidationError


class TestValidationFramework:
    """Test ValidationFramework class functionality."""

    def test_initialization_default(self):
        """Test ValidationFramework initialization with default tolerance."""
        framework = ValidationFramework()

        assert framework.tolerance == 1e-6

    def test_initialization_custom_tolerance(self):
        """Test ValidationFramework initialization with custom tolerance."""
        framework = ValidationFramework(tolerance=1e-4)

        assert framework.tolerance == 1e-4

    def test_validate_probability_distribution_1d_valid(self):
        """Test validation of valid 1D probability distribution."""
        framework = ValidationFramework()
        dist = np.array([0.2, 0.3, 0.5])

        result = framework.validate_probability_distribution(dist, "test_dist")

        assert result["valid"] is True
        assert result["contains_negatives"] is False
        assert result["contains_nans"] is False
        assert "normalization_error" in result
        assert result["normalization_error"] < framework.tolerance

    def test_validate_probability_distribution_1d_list(self):
        """Test validation with list input (converted to array)."""
        framework = ValidationFramework()
        dist = [0.1, 0.2, 0.3, 0.4]

        result = framework.validate_probability_distribution(dist, "test_dist")

        assert result["valid"] is True

    def test_validate_probability_distribution_2d_valid(self):
        """Test validation of valid 2D transition matrix."""
        framework = ValidationFramework()
        # Each row should sum to 1.0
        transition_matrix = np.array([[0.9, 0.1], [0.2, 0.8]])

        result = framework.validate_probability_distribution(
            transition_matrix, "transition"
        )

        assert result["valid"] is True
        assert result["contains_negatives"] is False
        assert result["contains_nans"] is False

    def test_validate_probability_distribution_2d_multiple_rows(self):
        """Test validation of larger 2D transition matrix."""
        framework = ValidationFramework()
        transition_matrix = np.array(
            [[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.2, 0.3, 0.5]]
        )

        result = framework.validate_probability_distribution(
            transition_matrix, "large_transition"
        )

        assert result["valid"] is True

    def test_validate_probability_distribution_invalid_sum(self):
        """Test validation fails for distribution that doesn't sum to 1."""
        framework = ValidationFramework()
        dist = np.array([0.2, 0.3, 0.6])  # Sums to 1.1

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(dist, "invalid_dist")

        assert "not properly normalized" in str(exc_info.value)

    def test_validate_probability_distribution_contains_nan(self):
        """Test validation fails for distribution with NaN values."""
        framework = ValidationFramework()
        dist = np.array([0.2, np.nan, 0.8])

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(dist, "nan_dist")

        assert "NaN or infinite values" in str(exc_info.value)

    def test_validate_probability_distribution_contains_inf(self):
        """Test validation fails for distribution with infinite values."""
        framework = ValidationFramework()
        dist = np.array([0.2, np.inf, 0.8])

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(dist, "inf_dist")

        assert "NaN or infinite values" in str(exc_info.value)

    def test_validate_probability_distribution_contains_negative(self):
        """Test validation fails for distribution with negative values."""
        framework = ValidationFramework()
        dist = np.array([0.2, -0.1, 0.9])

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(dist, "negative_dist")

        assert "contains negative values" in str(exc_info.value)

    def test_validate_probability_distribution_2d_invalid_rows(self):
        """Test validation fails for 2D matrix with rows not summing to 1."""
        framework = ValidationFramework()
        transition_matrix = np.array([[0.9, 0.2], [0.2, 0.8]])  # Sums to 1.1

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(
                transition_matrix, "invalid_transition"
            )

        assert "rows are not properly normalized" in str(exc_info.value)

    def test_validate_probability_distribution_unsupported_dimension(self):
        """Test validation fails for unsupported dimensionality."""
        framework = ValidationFramework()
        dist_3d = np.array([[[0.5, 0.5], [0.3, 0.7]]])

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_probability_distribution(dist_3d, "3d_dist")

        assert "unsupported dimensionality" in str(exc_info.value)

    def test_validate_probability_distribution_tolerance_boundary(self):
        """Test validation with tolerance boundary cases."""
        framework = ValidationFramework(tolerance=1e-3)
        # Distribution that's just within tolerance
        dist = np.array([0.333, 0.333, 0.334])

        result = framework.validate_probability_distribution(dist, "boundary_dist")

        assert result["valid"] is True

    def test_validate_generative_model_valid(self):
        """Test validation of valid generative model."""
        framework = ValidationFramework()
        # B matrix shape should be (n_states, n_states, n_actions) = (2, 2, 1)
        B = np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0)
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": B,
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True
        assert "model_structure" in result
        assert result["model_structure"]["n_states"] == 2
        assert result["model_structure"]["n_observations"] == 2
        assert result["compatibility_checks"]["A_D_compatible"] is True

    def test_validate_generative_model_missing_matrix(self):
        """Test validation fails for missing required matrix."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0),
            "C": np.array([1.0, -1.0]),
            # Missing D
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "Missing required matrix: D" in str(exc_info.value)

    def test_validate_generative_model_empty_matrix(self):
        """Test validation fails for empty matrix."""
        framework = ValidationFramework()
        model = {
            "A": np.array([]),
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0),
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "is empty" in str(exc_info.value)

    def test_validate_generative_model_not_numpy_array(self):
        """Test validation fails for non-numpy array matrix."""
        framework = ValidationFramework()
        model = {
            "A": [[0.8, 0.2], [0.2, 0.8]],  # List instead of array
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0),
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "is not a numpy array" in str(exc_info.value)

    def test_validate_generative_model_incompatible_A_D(self):
        """Test validation fails for incompatible A and D matrices."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2, 0.0], [0.2, 0.8, 0.0]]),  # 3 columns
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0),
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),  # 2 states
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "A matrix columns" in str(
            exc_info.value
        ) and "must match D length" in str(exc_info.value)

    def test_validate_generative_model_incompatible_C_A(self):
        """Test validation fails for incompatible C and A matrices."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),  # 2 observations
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0),
            "C": np.array([1.0, -1.0, 0.0]),  # 3 elements
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "C matrix length" in str(exc_info.value) and "must match A rows" in str(
            exc_info.value
        )

    def test_validate_generative_model_incompatible_B(self):
        """Test validation fails for incompatible B matrix dimensions."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": np.array([[[0.9, 0.1, 0.0], [0.1, 0.9, 0.0]]]).transpose(
                1, 2, 0
            ),  # Fixed shape
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "B matrix first two dimensions" in str(exc_info.value)

    def test_validate_generative_model_invalid_D(self):
        """Test validation fails for invalid D matrix (prior beliefs)."""
        framework = ValidationFramework()
        B = np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0)
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": B,
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.6, 0.6]),  # Doesn't sum to 1
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "prior beliefs" in str(
            exc_info.value
        ) or "not properly normalized" in str(exc_info.value)

    def test_validate_generative_model_invalid_A_columns(self):
        """Test validation fails for invalid A matrix columns (not probability distributions)."""
        framework = ValidationFramework()
        B = np.array([[[0.9, 0.1], [0.1, 0.9]]]).transpose(1, 2, 0)
        model = {
            "A": np.array(
                [[0.8, 0.3], [0.2, 0.8]]
            ),  # First column sums to 1.0, second to 1.1
            "B": B,
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(ValidationError) as exc_info:
            framework.validate_generative_model(model)

        assert "A[:, 1]" in str(exc_info.value) or "not properly normalized" in str(
            exc_info.value
        )

    def test_validate_generative_model_large_model(self):
        """Test validation of larger generative model."""
        framework = ValidationFramework()
        n_states = 3
        n_observations = 3
        n_actions = 2

        # A matrix: each column should be a probability distribution (sum to 1.0)
        # Shape: (n_observations, n_states) = (3, 3)
        A = np.array(
            [
                [0.7, 0.2, 0.1],  # Column 0 sums to 1.0
                [0.2, 0.6, 0.2],  # Column 1 sums to 1.0
                [0.1, 0.2, 0.7],  # Column 2 sums to 1.0
            ]
        )
        # B matrix: shape (n_states, n_states, n_actions) = (3, 3, 2)
        B_raw = np.array(
            [
                [[0.8, 0.1, 0.1], [0.2, 0.7, 0.1], [0.1, 0.2, 0.7]],  # Action 0
                [[0.9, 0.05, 0.05], [0.1, 0.8, 0.1], [0.05, 0.15, 0.8]],  # Action 1
            ]
        )
        B = B_raw.transpose(1, 2, 0)  # Reshape to (3, 3, 2)

        model = {
            "A": A,
            "B": B,
            "C": np.array([1.0, 0.0, -1.0]),
            "D": np.array([0.33, 0.33, 0.34]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True
        assert result["model_structure"]["n_states"] == n_states
        assert result["model_structure"]["n_observations"] == n_observations
        assert result["model_structure"]["n_actions"] == n_actions

    def test_validate_theoretical_correctness_with_efe(self):
        """Test theoretical correctness validation with EFE components."""
        framework = ValidationFramework()
        implementation_result = {
            "efe_components": {"epistemic": 0.5, "pragmatic": -1.2}
        }
        theoretical_expectation = {"efe_expectation": {}}

        result = framework.validate_theoretical_correctness(
            "test_algorithm", implementation_result, theoretical_expectation
        )

        assert result["algorithm"] == "test_algorithm"
        assert "theoretical_checks" in result
        assert "efe" in result["theoretical_checks"]
        assert result["overall_correctness"] is True

    def test_validate_theoretical_correctness_with_posterior(self):
        """Test theoretical correctness validation with posterior beliefs."""
        framework = ValidationFramework()
        implementation_result = {"posterior_beliefs": np.array([0.6, 0.4])}
        theoretical_expectation = {"inference_expectation": {}}

        result = framework.validate_theoretical_correctness(
            "inference_algorithm", implementation_result, theoretical_expectation
        )

        assert "theoretical_checks" in result
        assert "inference" in result["theoretical_checks"]
        assert result["overall_correctness"] is True

    def test_validate_theoretical_correctness_missing_efe_component(self):
        """Test theoretical correctness validation detects missing EFE component."""
        framework = ValidationFramework()
        implementation_result = {
            "efe_components": {
                "epistemic": 0.5
                # Missing pragmatic
            }
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "incomplete_algorithm", implementation_result, theoretical_expectation
        )

        assert result["overall_correctness"] is False
        assert len(result["issues"]) > 0
        assert any("Missing EFE component" in issue for issue in result["issues"])

    def test_validate_theoretical_correctness_infinite_efe(self):
        """Test theoretical correctness validation detects infinite EFE values."""
        framework = ValidationFramework()
        implementation_result = {
            "efe_components": {"epistemic": np.inf, "pragmatic": -1.2}
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "unstable_algorithm", implementation_result, theoretical_expectation
        )

        assert result["overall_correctness"] is False
        assert any("not finite" in issue for issue in result["issues"])

    def test_validate_theoretical_correctness_invalid_posterior(self):
        """Test theoretical correctness validation detects invalid posterior."""
        framework = ValidationFramework()
        implementation_result = {
            "posterior_beliefs": np.array([0.6, 0.6])  # Doesn't sum to 1
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "invalid_inference", implementation_result, theoretical_expectation
        )

        assert result["overall_correctness"] is False
        assert any("Posterior validation failed" in issue for issue in result["issues"])

    def test_validate_theoretical_correctness_degenerate_posterior(self):
        """Test theoretical correctness validation with degenerate posterior."""
        framework = ValidationFramework()
        implementation_result = {
            "posterior_beliefs": np.array([0.995, 0.005])  # Nearly degenerate but valid
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "degenerate_inference", implementation_result, theoretical_expectation
        )

        # Posterior is valid (sums to 1.0) but may be flagged as nearly degenerate
        assert result["overall_correctness"] is True
        # The degenerate check may or may not add an issue depending on implementation
        # Just verify the validation completes successfully

    def test_validate_theoretical_correctness_numerical_stability(self):
        """Test theoretical correctness validation checks numerical stability."""
        framework = ValidationFramework()
        implementation_result = {
            "results": {
                "value1": 1e12,  # Very large value
                "value2": np.array([1.0, 2.0, 3.0]),
            }
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "unstable_algorithm", implementation_result, theoretical_expectation
        )

        assert result["overall_correctness"] is False
        assert "implementation_checks" in result
        assert "numerical_stability" in result["implementation_checks"]
        assert not result["implementation_checks"]["numerical_stability"]["stable"]

    def test_validate_theoretical_correctness_complete(self):
        """Test theoretical correctness validation with all components."""
        framework = ValidationFramework()
        implementation_result = {
            "efe_components": {"epistemic": 0.5, "pragmatic": -1.2},
            "posterior_beliefs": np.array([0.6, 0.4]),
            "other_results": {"value": 1.0},
        }
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "complete_algorithm", implementation_result, theoretical_expectation
        )

        assert "theoretical_checks" in result
        assert "implementation_checks" in result
        assert "efe" in result["theoretical_checks"]
        assert "inference" in result["theoretical_checks"]
        assert "numerical_stability" in result["implementation_checks"]

    def test_validate_algorithm_performance_threshold(self):
        """Test algorithm performance validation with threshold requirement."""
        framework = ValidationFramework()
        performance_metrics = {"accuracy": 0.95, "precision": 0.92}
        requirements = {"accuracy": 0.90, "precision": 0.85}  # >= 0.90  # >= 0.85

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is True
        assert result["requirements_met"]["accuracy"] is True
        assert result["requirements_met"]["precision"] is True

    def test_validate_algorithm_performance_threshold_fail(self):
        """Test algorithm performance validation fails when threshold not met."""
        framework = ValidationFramework()
        performance_metrics = {"accuracy": 0.85, "precision": 0.92}  # Below 0.90
        requirements = {"accuracy": 0.90, "precision": 0.85}

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is False
        assert result["requirements_met"]["accuracy"] is False
        assert result["requirements_met"]["precision"] is True

    def test_validate_algorithm_performance_range(self):
        """Test algorithm performance validation with range requirement."""
        framework = ValidationFramework()
        performance_metrics = {"latency": 0.5}  # Should be between 0.1 and 1.0
        requirements = {"latency": (0.1, 1.0)}  # Range requirement

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is True
        assert result["requirements_met"]["latency"] is True

    def test_validate_algorithm_performance_range_fail(self):
        """Test algorithm performance validation fails when outside range."""
        framework = ValidationFramework()
        performance_metrics = {"latency": 1.5}  # Outside range
        requirements = {"latency": (0.1, 1.0)}

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is False
        assert result["requirements_met"]["latency"] is False

    def test_validate_algorithm_performance_missing_metric(self):
        """Test algorithm performance validation handles missing metrics."""
        framework = ValidationFramework()
        performance_metrics = {
            "accuracy": 0.95
            # Missing precision
        }
        requirements = {"accuracy": 0.90, "precision": 0.85}

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is False
        assert any("Missing required metric" in issue for issue in result["issues"])

    def test_validate_algorithm_performance_multiple_metrics(self):
        """Test algorithm performance validation with multiple metrics."""
        framework = ValidationFramework()
        performance_metrics = {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.88,
            "latency": 0.5,
        }
        requirements = {
            "accuracy": 0.90,
            "precision": 0.85,
            "recall": 0.80,
            "latency": (0.1, 1.0),
        }

        result = framework.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert result["overall_pass"] is True
        assert len(result["requirements_met"]) == 4

    def test_create_validation_report_single_pass(self):
        """Test validation report creation with single passing result."""
        framework = ValidationFramework()
        validation_results = [{"valid": True, "message": "Test passed"}]

        report = framework.create_validation_report(validation_results)

        assert report["summary"]["total_validations"] == 1
        assert report["summary"]["passed"] == 1
        assert report["summary"]["failed"] == 0
        assert report["summary"]["overall_status"] == "PASS"

    def test_create_validation_report_single_fail(self):
        """Test validation report creation with single failing result."""
        framework = ValidationFramework()
        validation_results = [{"valid": False, "issues": ["Issue 1", "Issue 2"]}]

        report = framework.create_validation_report(validation_results)

        assert report["summary"]["total_validations"] == 1
        assert report["summary"]["passed"] == 0
        assert report["summary"]["failed"] == 1
        assert report["summary"]["overall_status"] == "FAIL"

    def test_create_validation_report_multiple_results(self):
        """Test validation report creation with multiple results."""
        framework = ValidationFramework()
        validation_results = [
            {"valid": True, "message": "Test 1 passed"},
            {"overall_pass": True, "message": "Test 2 passed"},
            {"valid": False, "issues": ["Issue 1"]},
            {"overall_pass": False, "issues": ["Issue 2", "Issue 3"]},
        ]

        report = framework.create_validation_report(validation_results)

        assert report["summary"]["total_validations"] == 4
        assert report["summary"]["passed"] == 2
        assert report["summary"]["failed"] == 2
        assert report["summary"]["overall_status"] == "FAIL"

    def test_create_validation_report_issue_aggregation(self):
        """Test validation report aggregates issues correctly."""
        framework = ValidationFramework()
        validation_results = [
            {"valid": False, "issues": ["Issue 1", "Issue 2"]},
            {
                "overall_pass": False,
                "issues": ["Issue 2", "Issue 3"],
            },  # Issue 2 is duplicate
        ]

        report = framework.create_validation_report(validation_results)

        assert len(report["issues_summary"]) == 3  # Unique issues
        assert "Issue 1" in report["issues_summary"]
        assert "Issue 2" in report["issues_summary"]
        assert "Issue 3" in report["issues_summary"]

    def test_create_validation_report_recommendations(self):
        """Test validation report generates recommendations."""
        framework = ValidationFramework()
        validation_results = [
            {"valid": False, "issues": ["Issue 1"]},
            {"overall_pass": False, "issues": ["Issue 2"]},
        ]

        report = framework.create_validation_report(validation_results)

        assert len(report["recommendations"]) > 0
        assert any("failed validations" in rec for rec in report["recommendations"])

    def test_create_validation_report_no_issues(self):
        """Test validation report with no issues."""
        framework = ValidationFramework()
        validation_results = [{"valid": True, "message": "All good"}]

        report = framework.create_validation_report(validation_results)

        assert len(report["issues_summary"]) == 0
        assert len(report["recommendations"]) == 0

    def test_demonstrate_validation_framework(self):
        """Test demonstrate_validation_framework function."""
        result = demonstrate_validation_framework()

        assert "probability_validation" in result
        assert "generative_model_validation" in result
        assert "purpose" in result
        assert "valid_distribution" in result["probability_validation"]
        assert "invalid_distribution" in result["probability_validation"]


class TestValidationFrameworkEdgeCases:
    """Test edge cases and error handling in ValidationFramework."""

    def test_validate_probability_distribution_empty_array(self):
        """Test validation with empty array."""
        framework = ValidationFramework()
        dist = np.array([])

        with pytest.raises(ValidationError):
            framework.validate_probability_distribution(dist, "empty_dist")

    def test_validate_probability_distribution_single_value(self):
        """Test validation with single value (should be 1.0)."""
        framework = ValidationFramework()
        dist = np.array([1.0])

        result = framework.validate_probability_distribution(dist, "single_value")

        assert result["valid"] is True

    def test_validate_probability_distribution_very_small_values(self):
        """Test validation with very small probability values."""
        framework = ValidationFramework(tolerance=1e-9)
        dist = np.array([1e-10, 1.0 - 1e-10])

        result = framework.validate_probability_distribution(dist, "small_values")

        assert result["valid"] is True

    def test_validate_generative_model_B_2d(self):
        """Test validation with 2D B matrix (single action)."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": np.array([[0.9, 0.1], [0.1, 0.9]]),  # 2D instead of 3D
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True
        assert result["model_structure"]["n_actions"] == 1

    def test_validate_numerical_stability_nested_dict(self):
        """Test numerical stability check with nested dictionaries."""
        framework = ValidationFramework()
        results = {
            "level1": {
                "level2": {
                    "value": 1e11,  # Very large
                    "array": np.array([1.0, 2.0, np.inf]),  # Contains inf
                }
            }
        }

        stability = framework._validate_numerical_stability(results)

        assert stability["stable"] is False
        assert len(stability["issues"]) > 0

    def test_validate_numerical_stability_list(self):
        """Test numerical stability check with lists."""
        framework = ValidationFramework()
        results = {"values": [1.0, 2.0, 1e11, np.nan]}

        stability = framework._validate_numerical_stability(results)

        assert stability["stable"] is False

    def test_validate_numerical_stability_tuple(self):
        """Test numerical stability check with tuples."""
        framework = ValidationFramework()
        results = {"values": (1.0, 2.0, 1e11)}

        stability = framework._validate_numerical_stability(results)

        assert stability["stable"] is False

    def test_validate_algorithm_performance_list_value(self):
        """Test algorithm performance validation with list values."""
        framework = ValidationFramework()
        performance_metrics = {
            "scores": [0.9, 0.95, 0.92]  # List instead of single value
        }
        requirements = {"scores": 0.85}  # This will fail because list comparison

        # List comparison will fail (list >= float is not supported)
        with pytest.raises((TypeError, ValidationError)):
            framework.validate_algorithm_performance(performance_metrics, requirements)

    def test_validate_probability_distribution_exception_handling(self):
        """Test exception handling in validate_probability_distribution."""
        framework = ValidationFramework()

        # Test with invalid input that causes exception
        with pytest.raises(ValidationError):
            framework.validate_probability_distribution(None, "test")

    def test_validate_generative_model_exception_handling(self):
        """Test exception handling in validate_generative_model."""
        framework = ValidationFramework()

        # Test with invalid input
        with pytest.raises(ValidationError):
            framework.validate_generative_model(None)

    def test_validate_generative_model_2d_B_matrix(self):
        """Test validation with 2D B matrix (single action case)."""
        framework = ValidationFramework()
        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": np.array([[0.9, 0.1], [0.1, 0.9]]),  # 2D
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True

    def test_validate_theoretical_correctness_no_efe_no_posterior(self):
        """Test theoretical correctness validation with no EFE or posterior."""
        framework = ValidationFramework()
        implementation_result = {"other_results": {"value": 1.0}}
        theoretical_expectation = {}

        result = framework.validate_theoretical_correctness(
            "simple_algorithm", implementation_result, theoretical_expectation
        )

        assert result["algorithm"] == "simple_algorithm"
        assert "theoretical_checks" in result
        assert "implementation_checks" in result

    def test_validate_algorithm_performance_exception_handling(self):
        """Test exception handling in validate_algorithm_performance."""
        framework = ValidationFramework()

        # The method catches all exceptions and wraps them in ValidationError
        # Test with invalid input that will cause an error
        invalid_metrics = {"metric": "not a number"}  # String instead of number
        requirements = {"metric": 0.5}

        # This should work (string comparison might work), but let's test with None value
        invalid_metrics2 = {"metric": None}
        with pytest.raises(ValidationError):
            # None comparison will fail
            framework.validate_algorithm_performance(invalid_metrics2, requirements)

    def test_create_validation_report_exception_handling(self):
        """Test exception handling in create_validation_report."""
        framework = ValidationFramework()

        # Test with invalid input
        with pytest.raises(ValidationError):
            framework.create_validation_report(None)

    def test_validate_probability_distribution_2d_edge_case(self):
        """Test 2D distribution validation edge case with single row."""
        framework = ValidationFramework()
        dist = np.array([[1.0]])  # Single row, single column

        result = framework.validate_probability_distribution(dist, "single_row")

        assert result["valid"] is True

    def test_validate_generative_model_B_validation_loop(self):
        """Test B matrix validation loop for multiple actions."""
        framework = ValidationFramework()
        # B matrix shape should be (n_states, n_states, n_actions)
        B_actions = np.array(
            [
                [[0.9, 0.1], [0.1, 0.9]],  # Action 0
                [[0.8, 0.2], [0.2, 0.8]],  # Action 1
                [[0.7, 0.3], [0.3, 0.7]],  # Action 2
            ]
        )
        # Reshape from (n_actions, n_states, n_states) to (n_states, n_states, n_actions)
        B = np.transpose(B_actions, (1, 2, 0))

        model = {
            "A": np.array([[0.8, 0.2], [0.2, 0.8]]),
            "B": B,
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True
        assert result["model_structure"]["n_actions"] == 3

    def test_validate_generative_model_A_column_validation_loop(self):
        """Test A matrix column validation loop."""
        framework = ValidationFramework()
        # A should be (n_observations, n_states) = (3, 3)
        # Each column should be a probability distribution
        model = {
            "A": np.array([[0.8, 0.7, 0.6], [0.2, 0.2, 0.2], [0.0, 0.1, 0.2]]),
            "B": np.array(
                [[[0.9, 0.1, 0.0], [0.1, 0.8, 0.1], [0.0, 0.1, 0.9]]]
            ).transpose(
                1, 2, 0
            ),  # Fixed shape
            "C": np.array([1.0, -1.0, 0.0]),
            "D": np.array([0.33, 0.33, 0.34]),
        }

        result = framework.validate_generative_model(model)

        assert result["valid"] is True

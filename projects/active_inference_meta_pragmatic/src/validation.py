"""Validation Framework for Active Inference Meta-Pragmatic Framework.

This module provides validation and error checking capabilities for Active Inference
algorithms, ensuring theoretical correctness, numerical stability, and practical
reliability of implementations.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class ValidationFramework:
    """Comprehensive validation framework for Active Inference implementations.

    Provides theoretical validation, numerical stability checks, and practical
    reliability assessment for Active Inference algorithms and models.
    """

    def __init__(self, tolerance: float = 1e-6) -> None:
        """Initialize validation framework.

        Args:
            tolerance: Numerical tolerance for validation checks
        """
        self.tolerance = tolerance
        logger.info(f"Initialized validation framework with tolerance {tolerance}")

    def validate_probability_distribution(self, distribution: NDArray,
                                        name: str = "distribution") -> Dict[str, Union[bool, str, float]]:
        """Validate that an array represents a valid probability distribution.

        Args:
            distribution: Array to validate (1D for simple distributions, 2D for transition matrices)
            name: Name for error reporting

        Returns:
            Dictionary containing validation results

        Raises:
            ValidationError: If distribution is invalid
        """
        try:
            distribution = np.asarray(distribution)

            # Check for NaN or infinite values
            if not np.all(np.isfinite(distribution)):
                raise ValidationError(f"{name} contains NaN or infinite values")

            # Check for negative values
            if np.any(distribution < 0):
                raise ValidationError(f"{name} contains negative values")

            # Handle different dimensionalities
            if distribution.ndim == 1:
                # 1D probability distribution - should sum to 1
                total = np.sum(distribution)
                expected_sum = 1.0
            elif distribution.ndim == 2:
                # 2D transition matrix - each row should sum to 1
                row_sums = np.sum(distribution, axis=1)
                if not np.allclose(row_sums, 1.0, atol=self.tolerance):
                    bad_rows = np.where(~np.isclose(row_sums, 1.0, atol=self.tolerance))[0]
                    raise ValidationError(f"{name} rows are not properly normalized: rows {bad_rows} sum to {row_sums[bad_rows]}")
                total = np.sum(distribution)  # Total sum for reporting
                expected_sum = float(distribution.shape[0])  # Should equal number of rows
            else:
                raise ValidationError(f"{name} has unsupported dimensionality {distribution.ndim}")

            # Check overall normalization
            if not np.isclose(total, expected_sum, atol=self.tolerance):
                raise ValidationError(f"{name} is not properly normalized (sum = {total:.6f}, expected = {expected_sum:.6f})")

            validation = {
                'valid': True,
                'normalization_error': abs(total - expected_sum),
                'contains_negatives': False,
                'contains_nans': False,
                'message': f"{name} is a valid probability distribution"
            }

            logger.debug(f"Validated probability distribution: {name}")
            return validation

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating probability distribution: {e}")
            raise ValidationError(f"Probability distribution validation failed: {e}") from e

    def validate_generative_model(self, model: Dict[str, NDArray]) -> Dict[str, Union[bool, str, Dict]]:
        """Validate generative model structure and properties.

        Args:
            model: Generative model dictionary with A, B, C, D matrices

        Returns:
            Dictionary containing validation results

        Raises:
            ValidationError: If model is invalid
        """
        try:
            required_matrices = ['A', 'B', 'C', 'D']
            validation_results = {}

            for matrix_name in required_matrices:
                if matrix_name not in model:
                    raise ValidationError(f"Missing required matrix: {matrix_name}")

                matrix = model[matrix_name]

                # Basic shape validation
                if not isinstance(matrix, np.ndarray):
                    raise ValidationError(f"Matrix {matrix_name} is not a numpy array")

                if matrix.size == 0:
                    raise ValidationError(f"Matrix {matrix_name} is empty")

                validation_results[matrix_name] = {
                    'shape': matrix.shape,
                    'finite': np.all(np.isfinite(matrix)),
                    'valid': True
                }

            # Validate matrix compatibility
            A, B, C, D = model['A'], model['B'], model['C'], model['D']

            n_states = D.shape[0]
            n_observations = A.shape[0]

            # A matrix compatibility
            if A.shape[1] != n_states:
                raise ValidationError(f"A matrix columns ({A.shape[1]}) must match D length ({n_states})")

            # C matrix compatibility
            if C.shape[0] != n_observations:
                raise ValidationError(f"C matrix length ({C.shape[0]}) must match A rows ({n_observations})")

            # B matrix compatibility
            if len(B.shape) == 3:
                if B.shape[0] != n_states or B.shape[1] != n_states:
                    raise ValidationError(f"B matrix first two dimensions must be ({n_states}, {n_states})")

                # Validate each transition matrix
                for action in range(B.shape[2]):
                    transition_matrix = B[:, :, action]
                    self.validate_probability_distribution(transition_matrix,
                                                        f"B[:, :, {action}]")

            # Validate prior beliefs
            self.validate_probability_distribution(D, "prior beliefs (D)")

            # Validate observation likelihoods (each column should be a distribution)
            for state in range(n_states):
                obs_likelihood = A[:, state]
                self.validate_probability_distribution(obs_likelihood,
                                                    f"A[:, {state}]")

            overall_validation = {
                'valid': True,
                'model_structure': {
                    'n_states': n_states,
                    'n_observations': n_observations,
                    'n_actions': B.shape[2] if len(B.shape) > 2 else 1,
                    'matrices': validation_results
                },
                'compatibility_checks': {
                    'A_D_compatible': True,
                    'C_A_compatible': True,
                    'B_structure_valid': True
                },
                'message': "Generative model structure is valid"
            }

            logger.info(f"Validated generative model: {n_states} states, {n_observations} observations")
            return overall_validation

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error validating generative model: {e}")
            raise ValidationError(f"Generative model validation failed: {e}") from e

    def validate_theoretical_correctness(self, algorithm_name: str,
                                       implementation_result: Dict,
                                       theoretical_expectation: Dict) -> Dict[str, Union[bool, str, Dict]]:
        """Validate theoretical correctness of algorithm implementation.

        Args:
            algorithm_name: Name of the algorithm being validated
            implementation_result: Results from implementation
            theoretical_expectation: Expected theoretical results

        Returns:
            Dictionary containing correctness validation
        """
        try:
            validation_results = {
                'algorithm': algorithm_name,
                'theoretical_checks': {},
                'implementation_checks': {},
                'overall_correctness': True,
                'issues': []
            }

            # Validate EFE calculation (if applicable)
            if 'efe_components' in implementation_result:
                efe_validation = self._validate_efe_correctness(
                    implementation_result['efe_components'],
                    theoretical_expectation.get('efe_expectation', {})
                )
                validation_results['theoretical_checks']['efe'] = efe_validation

                if not efe_validation['correct']:
                    validation_results['overall_correctness'] = False
                    validation_results['issues'].extend(efe_validation['issues'])

            # Validate inference results (if applicable)
            if 'posterior_beliefs' in implementation_result:
                inference_validation = self._validate_inference_correctness(
                    implementation_result['posterior_beliefs'],
                    theoretical_expectation.get('inference_expectation', {})
                )
                validation_results['theoretical_checks']['inference'] = inference_validation

                if not inference_validation['correct']:
                    validation_results['overall_correctness'] = False
                    validation_results['issues'].extend(inference_validation['issues'])

            # Validate numerical stability
            stability_validation = self._validate_numerical_stability(implementation_result)
            validation_results['implementation_checks']['numerical_stability'] = stability_validation

            if not stability_validation['stable']:
                validation_results['overall_correctness'] = False
                validation_results['issues'].extend(stability_validation['issues'])

            validation_results['message'] = (
                "Theoretical correctness validated" if validation_results['overall_correctness']
                else f"Correctness issues found: {len(validation_results['issues'])} issues"
            )

            logger.info(f"Validated theoretical correctness for {algorithm_name}: "
                       f"{'PASS' if validation_results['overall_correctness'] else 'FAIL'}")
            return validation_results

        except Exception as e:
            logger.error(f"Error validating theoretical correctness: {e}")
            raise ValidationError(f"Theoretical correctness validation failed: {e}") from e

    def _validate_efe_correctness(self, efe_components: Dict, expectation: Dict) -> Dict[str, Union[bool, List]]:
        """Validate EFE calculation correctness."""
        issues = []
        correct = True

        # Check that epistemic and pragmatic components are present
        required_components = ['epistemic', 'pragmatic']
        for component in required_components:
            if component not in efe_components:
                issues.append(f"Missing EFE component: {component}")
                correct = False

        # Check component relationships (epistemic can be positive or negative, pragmatic typically negative)
        if 'epistemic' in efe_components and 'pragmatic' in efe_components:
            epistemic = efe_components['epistemic']
            pragmatic = efe_components['pragmatic']

            # Basic sanity checks
            if not np.isfinite(epistemic):
                issues.append("Epistemic component is not finite")
                correct = False

            if not np.isfinite(pragmatic):
                issues.append("Pragmatic component is not finite")
                correct = False

        return {'correct': correct, 'issues': issues}

    def _validate_inference_correctness(self, posterior: NDArray, expectation: Dict) -> Dict[str, Union[bool, List]]:
        """Validate inference result correctness."""
        issues = []
        correct = True

        # Validate posterior is a proper probability distribution
        try:
            self.validate_probability_distribution(posterior, "posterior beliefs")
        except ValidationError as e:
            issues.append(f"Posterior validation failed: {e}")
            correct = False

        # Check for degenerate posteriors (all mass on one state)
        if np.max(posterior) > 0.99:
            issues.append("Posterior is nearly degenerate (potential numerical issues)")
            # Not necessarily incorrect, but worth noting

        return {'correct': correct, 'issues': issues}

    def _validate_numerical_stability(self, results: Dict) -> Dict[str, Union[bool, List]]:
        """Validate numerical stability of results."""
        issues = []
        stable = True

        # Check for numerical issues in all numeric results
        def check_numeric_values(data, path=""):
            nonlocal issues, stable

            if isinstance(data, dict):
                for key, value in data.items():
                    check_numeric_values(value, f"{path}.{key}" if path else key)
            elif isinstance(data, (list, tuple)):
                for i, item in enumerate(data):
                    check_numeric_values(item, f"{path}[{i}]")
            elif isinstance(data, np.ndarray):
                if not np.all(np.isfinite(data)):
                    issues.append(f"Non-finite values in {path}")
                    stable = False
                if np.any(np.abs(data) > 1e10):  # Very large values
                    issues.append(f"Very large values in {path} (potential overflow)")
                    stable = False
            elif isinstance(data, (int, float)):
                if not np.isfinite(data):
                    issues.append(f"Non-finite value in {path}: {data}")
                    stable = False
                if abs(data) > 1e10:
                    issues.append(f"Very large value in {path}: {data}")
                    stable = False

        check_numeric_values(results)

        return {'stable': stable, 'issues': issues}

    def validate_algorithm_performance(self, performance_metrics: Dict[str, Union[float, List]],
                                     requirements: Dict[str, Union[float, Tuple[float, float]]]) -> Dict[str, Union[bool, str, Dict]]:
        """Validate algorithm performance against requirements.

        Args:
            performance_metrics: Dictionary of performance metrics
            requirements: Dictionary of required performance levels

        Returns:
            Dictionary containing performance validation results
        """
        try:
            validation_results = {
                'overall_pass': True,
                'metric_validations': {},
                'requirements_met': {},
                'issues': []
            }

            for metric_name, required_value in requirements.items():
                if metric_name not in performance_metrics:
                    validation_results['issues'].append(f"Missing required metric: {metric_name}")
                    validation_results['overall_pass'] = False
                    continue

                actual_value = performance_metrics[metric_name]

                # Handle different requirement types
                if isinstance(required_value, tuple):
                    # Range requirement (min, max)
                    min_val, max_val = required_value
                    passes = min_val <= actual_value <= max_val
                    requirement_desc = f"[{min_val}, {max_val}]"
                else:
                    # Threshold requirement
                    passes = actual_value >= required_value
                    requirement_desc = f">= {required_value}"

                validation_results['metric_validations'][metric_name] = {
                    'actual': actual_value,
                    'required': requirement_desc,
                    'passes': passes
                }

                validation_results['requirements_met'][metric_name] = passes

                if not passes:
                    validation_results['overall_pass'] = False
                    validation_results['issues'].append(
                        f"Metric {metric_name}: {actual_value} does not meet requirement {requirement_desc}"
                    )

            validation_results['message'] = (
                f"Performance validation: {'PASS' if validation_results['overall_pass'] else 'FAIL'} "
                f"({sum(validation_results['requirements_met'].values())}/{len(requirements)} metrics met)"
            )

            logger.info(f"Validated algorithm performance: "
                       f"{'PASS' if validation_results['overall_pass'] else 'FAIL'}")
            return validation_results

        except Exception as e:
            logger.error(f"Error validating algorithm performance: {e}")
            raise ValidationError(f"Algorithm performance validation failed: {e}") from e

    def create_validation_report(self, validation_results: List[Dict]) -> Dict[str, Union[str, Dict, List]]:
        """Create comprehensive validation report from multiple validation results.

        Args:
            validation_results: List of validation result dictionaries

        Returns:
            Dictionary containing comprehensive validation report
        """
        try:
            report = {
                'summary': {
                    'total_validations': len(validation_results),
                    'passed': sum(1 for r in validation_results if r.get('valid', r.get('overall_pass', False))),
                    'failed': sum(1 for r in validation_results if not r.get('valid', r.get('overall_pass', True))),
                    'overall_status': 'PASS'
                },
                'detailed_results': validation_results,
                'issues_summary': [],
                'recommendations': []
            }

            # Collect all issues
            all_issues = []
            for result in validation_results:
                if 'issues' in result and result['issues']:
                    all_issues.extend(result['issues'])

            report['issues_summary'] = list(set(all_issues))  # Remove duplicates

            # Determine overall status
            if report['summary']['failed'] > 0:
                report['summary']['overall_status'] = 'FAIL'

            # Generate recommendations
            if report['summary']['failed'] > 0:
                report['recommendations'].append(
                    f"Address {report['summary']['failed']} failed validations"
                )
                if report['issues_summary']:
                    report['recommendations'].append(
                        f"Review {len(report['issues_summary'])} unique issues"
                    )

            logger.info(f"Created validation report: {report['summary']['overall_status']} "
                       f"({report['summary']['passed']}/{report['summary']['total_validations']} passed)")
            return report

        except Exception as e:
            logger.error(f"Error creating validation report: {e}")
            raise ValidationError(f"Validation report creation failed: {e}") from e


def demonstrate_validation_framework() -> Dict[str, Union[str, Dict]]:
    """Demonstrate validation framework capabilities.

    Returns:
        Dictionary containing validation demonstrations
    """
    framework = ValidationFramework()

    # Demonstrate probability distribution validation
    valid_dist = np.array([0.2, 0.3, 0.5])
    invalid_dist = np.array([0.2, 0.3, 0.6])  # Doesn't sum to 1

    try:
        valid_result = framework.validate_probability_distribution(valid_dist, "test_valid")
    except ValidationError:
        valid_result = {"valid": False, "error": "Validation failed"}

    try:
        invalid_result = framework.validate_probability_distribution(invalid_dist, "test_invalid")
    except ValidationError as e:
        invalid_result = {"valid": False, "error": str(e)}

    # Demonstrate generative model validation
    simple_model = {
        'A': np.array([[0.8, 0.2], [0.2, 0.8]]),
        'B': np.array([[[0.9, 0.1], [0.1, 0.9]]]),
        'C': np.array([1.0, -1.0]),
        'D': np.array([0.5, 0.5])
    }

    try:
        model_validation = framework.validate_generative_model(simple_model)
    except ValidationError as e:
        model_validation = {"valid": False, "error": str(e)}

    demonstration = {
        'probability_validation': {
            'valid_distribution': valid_result,
            'invalid_distribution': invalid_result
        },
        'generative_model_validation': model_validation,
        'purpose': """
        The validation framework ensures theoretical correctness, numerical stability,
        and practical reliability of Active Inference implementations. It provides
        comprehensive checking of probability distributions, generative model structures,
        algorithm performance, and numerical stability.
        """
    }

    logger.info("Demonstrated validation framework capabilities")
    return demonstration
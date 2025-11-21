"""Validation framework for scientific computing.

This module provides result validation, reproducibility verification,
quality metrics calculation, anomaly detection, and validation reports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    check_name: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning, info
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "check_name": self.check_name,
            "message": self.message,
            "details": self.details,
            "severity": self.severity
        }


class ValidationFramework:
    """Framework for validating simulation and analysis results."""
    
    def __init__(self):
        """Initialize validation framework."""
        self.validation_results: List[ValidationResult] = []
    
    def validate_bounds(
        self,
        values: np.ndarray,
        name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        expected_range: Optional[Tuple[float, float]] = None
    ) -> ValidationResult:
        """Validate that values are within bounds.
        
        Args:
            values: Values to validate
            name: Name of the quantity being validated
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            expected_range: Expected (min, max) range
            
        Returns:
            ValidationResult
        """
        if expected_range is not None:
            min_value, max_value = expected_range
        
        violations = []
        if min_value is not None:
            below_min = np.sum(values < min_value)
            if below_min > 0:
                violations.append(f"{below_min} values below minimum {min_value}")
        
        if max_value is not None:
            above_max = np.sum(values > max_value)
            if above_max > 0:
                violations.append(f"{above_max} values above maximum {max_value}")
        
        is_valid = len(violations) == 0
        message = "All values within bounds" if is_valid else "; ".join(violations)
        
        result = ValidationResult(
            is_valid=is_valid,
            check_name="bounds_check",
            message=message,
            details={
                "name": name,
                "min_value": min_value,
                "max_value": max_value,
                "actual_min": float(np.min(values)),
                "actual_max": float(np.max(values))
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_sanity(
        self,
        value: float,
        name: str,
        expected_order_of_magnitude: Optional[float] = None,
        allow_zero: bool = True,
        allow_negative: bool = True
    ) -> ValidationResult:
        """Perform sanity checks on a value.
        
        Args:
            value: Value to check
            name: Name of the quantity
            expected_order_of_magnitude: Expected order of magnitude
            allow_zero: Whether zero is allowed
            allow_negative: Whether negative values are allowed
            
        Returns:
            ValidationResult
        """
        issues = []
        
        if not allow_zero and abs(value) < 1e-10:
            issues.append("Value is zero (not allowed)")
        
        if not allow_negative and value < 0:
            issues.append("Value is negative (not allowed)")
        
        if expected_order_of_magnitude is not None:
            actual_magnitude = np.log10(abs(value) + 1e-10)
            expected_magnitude = np.log10(expected_order_of_magnitude)
            if abs(actual_magnitude - expected_magnitude) > 2:
                issues.append(
                    f"Value order of magnitude ({actual_magnitude:.2f}) "
                    f"differs significantly from expected ({expected_magnitude:.2f})"
                )
        
        is_valid = len(issues) == 0
        message = "Value passes sanity checks" if is_valid else "; ".join(issues)
        
        result = ValidationResult(
            is_valid=is_valid,
            check_name="sanity_check",
            message=message,
            details={
                "name": name,
                "value": value,
                "expected_order_of_magnitude": expected_order_of_magnitude
            },
            severity="warning" if issues else "info"
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_reproducibility(
        self,
        run1_results: Dict[str, Any],
        run2_results: Dict[str, Any],
        tolerance: float = 1e-6
    ) -> ValidationResult:
        """Validate reproducibility between two runs.
        
        Args:
            run1_results: Results from first run
            run2_results: Results from second run
            tolerance: Tolerance for comparison
            
        Returns:
            ValidationResult
        """
        differences = []
        
        # Compare numeric values
        for key in set(run1_results.keys()) & set(run2_results.keys()):
            val1 = run1_results[key]
            val2 = run2_results[key]
            
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = abs(val1 - val2)
                if diff > tolerance:
                    differences.append(f"{key}: difference = {diff:.2e}")
        
        is_valid = len(differences) == 0
        message = "Runs are reproducible" if is_valid else f"Differences found: {', '.join(differences)}"
        
        result = ValidationResult(
            is_valid=is_valid,
            check_name="reproducibility_check",
            message=message,
            details={
                "tolerance": tolerance,
                "differences": differences
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def detect_anomalies(
        self,
        values: np.ndarray,
        method: str = "iqr",
        threshold: float = 3.0
    ) -> ValidationResult:
        """Detect anomalies in results.
        
        Args:
            values: Values to check
            method: Detection method (iqr, z_score)
            threshold: Threshold for anomaly detection
            
        Returns:
            ValidationResult
        """
        from data_processing import detect_outliers
        
        outlier_mask, info = detect_outliers(values, method, threshold)
        n_anomalies = np.sum(outlier_mask)
        anomaly_percentage = 100 * n_anomalies / len(values) if len(values) > 0 else 0
        
        # Consider > 5% anomalies as a problem
        is_valid = anomaly_percentage < 5.0
        message = (
            f"Found {n_anomalies} anomalies ({anomaly_percentage:.2f}%)"
            if n_anomalies > 0
            else "No anomalies detected"
        )
        
        result = ValidationResult(
            is_valid=is_valid,
            check_name="anomaly_detection",
            message=message,
            details={
                "method": method,
                "threshold": threshold,
                "n_anomalies": int(n_anomalies),
                "anomaly_percentage": float(anomaly_percentage),
                **info
            },
            severity="warning" if n_anomalies > 0 else "info"
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_quality_metrics(
        self,
        metrics: Dict[str, float],
        expected_ranges: Dict[str, Tuple[float, float]]
    ) -> List[ValidationResult]:
        """Validate quality metrics against expected ranges.
        
        Args:
            metrics: Dictionary of metric values
            expected_ranges: Dictionary mapping metric names to (min, max) ranges
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        
        for metric_name, value in metrics.items():
            if metric_name in expected_ranges:
                min_val, max_val = expected_ranges[metric_name]
                is_valid = min_val <= value <= max_val
                
                message = (
                    f"Metric '{metric_name}' within expected range [{min_val}, {max_val}]"
                    if is_valid
                    else f"Metric '{metric_name}' ({value:.4f}) outside expected range [{min_val}, {max_val}]"
                )
                
                result = ValidationResult(
                    is_valid=is_valid,
                    check_name="quality_metric_check",
                    message=message,
                    details={
                        "metric_name": metric_name,
                        "value": value,
                        "expected_range": expected_ranges[metric_name]
                    }
                )
                results.append(result)
                self.validation_results.append(result)
        
        return results
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate validation report.
        
        Returns:
            Dictionary with validation report
        """
        n_total = len(self.validation_results)
        n_passed = sum(1 for r in self.validation_results if r.is_valid)
        n_failed = n_total - n_passed
        
        errors = [r for r in self.validation_results if not r.is_valid and r.severity == "error"]
        warnings = [r for r in self.validation_results if not r.is_valid and r.severity == "warning"]
        
        return {
            "summary": {
                "total_checks": n_total,
                "passed": n_passed,
                "failed": n_failed,
                "errors": len(errors),
                "warnings": len(warnings)
            },
            "results": [r.to_dict() for r in self.validation_results],
            "errors": [r.to_dict() for r in errors],
            "warnings": [r.to_dict() for r in warnings],
            "all_passed": n_failed == 0
        }
    
    def clear_results(self) -> None:
        """Clear validation results."""
        self.validation_results = []


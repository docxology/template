"""Validation framework for tree grafting results.

This module provides result validation, biological constraint verification,
quality checks, and validation reports for grafting operations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class GraftValidationResult:
    """Result of a grafting validation check."""
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


class GraftValidationFramework:
    """Framework for validating grafting results."""
    
    def __init__(self):
        """Initialize validation framework."""
        self.validation_results: List[GraftValidationResult] = []
    
    def validate_compatibility(
        self,
        compatibility_scores: np.ndarray,
        min_compatibility: float = 0.3
    ) -> GraftValidationResult:
        """Validate compatibility scores are within acceptable range.
        
        Args:
            compatibility_scores: Compatibility scores (0-1)
            min_compatibility: Minimum acceptable compatibility
            
        Returns:
            GraftValidationResult
        """
        violations = np.sum(compatibility_scores < min_compatibility)
        is_valid = violations == 0
        
        message = "All compatibility scores acceptable" if is_valid else \
                  f"{violations} compatibility scores below minimum {min_compatibility}"
        
        result = GraftValidationResult(
            is_valid=is_valid,
            check_name="compatibility_check",
            message=message,
            details={
                "min_compatibility": min_compatibility,
                "violations": int(violations),
                "min_score": float(np.min(compatibility_scores)),
                "max_score": float(np.max(compatibility_scores))
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_environmental_conditions(
        self,
        temperature: np.ndarray,
        humidity: np.ndarray
    ) -> GraftValidationResult:
        """Validate environmental conditions are suitable for grafting.
        
        Args:
            temperature: Temperature values (°C)
            humidity: Humidity values (0-1)
            
        Returns:
            GraftValidationResult
        """
        # Optimal ranges
        temp_optimal = (temperature >= 15) & (temperature <= 30)
        humidity_optimal = (humidity >= 0.5) & (humidity <= 1.0)
        
        violations = np.sum(~(temp_optimal & humidity_optimal))
        is_valid = violations == 0
        
        message = "All environmental conditions suitable" if is_valid else \
                  f"{violations} conditions outside optimal range"
        
        result = GraftValidationResult(
            is_valid=is_valid,
            check_name="environmental_check",
            message=message,
            details={
                "violations": int(violations),
                "temp_range": (float(np.min(temperature)), float(np.max(temperature))),
                "humidity_range": (float(np.min(humidity)), float(np.max(humidity)))
            },
            severity="warning"  # Warning, not error
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_diameter_match(
        self,
        rootstock_diameter: np.ndarray,
        scion_diameter: np.ndarray,
        tolerance: float = 0.2
    ) -> GraftValidationResult:
        """Validate rootstock and scion diameters are compatible.
        
        Args:
            rootstock_diameter: Rootstock diameters (mm)
            scion_diameter: Scion diameters (mm)
            tolerance: Maximum relative difference allowed
            
        Returns:
            GraftValidationResult
        """
        ratios = scion_diameter / (rootstock_diameter + 1e-10)
        min_ratio = 1.0 - tolerance
        max_ratio = 1.0 + tolerance
        
        violations = np.sum((ratios < min_ratio) | (ratios > max_ratio))
        is_valid = violations == 0
        
        message = "All diameter matches acceptable" if is_valid else \
                  f"{violations} diameter mismatches outside tolerance"
        
        result = GraftValidationResult(
            is_valid=is_valid,
            check_name="diameter_match_check",
            message=message,
            details={
                "tolerance": tolerance,
                "violations": int(violations),
                "ratio_range": (float(np.min(ratios)), float(np.max(ratios)))
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def validate_biological_constraints(
        self,
        union_strength: np.ndarray,
        days_since_grafting: np.ndarray
    ) -> GraftValidationResult:
        """Validate biological constraints on union strength.
        
        Args:
            union_strength: Union strength values (0-1)
            days_since_grafting: Days since grafting
            
        Returns:
            GraftValidationResult
        """
        # Union strength should increase with time (generally)
        # Check for unrealistic values
        violations = []
        
        # Check for negative or >1 values
        if np.any(union_strength < 0) or np.any(union_strength > 1):
            violations.append("Union strength outside [0, 1] range")
        
        # Check for unrealistic early strength
        early_mask = days_since_grafting < 7
        if np.any(early_mask):
            early_strength = union_strength[early_mask]
            if np.any(early_strength > 0.8):
                violations.append("Unrealistic union strength in early days")
        
        is_valid = len(violations) == 0
        message = "All biological constraints satisfied" if is_valid else \
                  "; ".join(violations)
        
        result = GraftValidationResult(
            is_valid=is_valid,
            check_name="biological_constraints_check",
            message=message,
            details={
                "violations": violations,
                "union_strength_range": (float(np.min(union_strength)), 
                                        float(np.max(union_strength)))
            }
        )
        
        self.validation_results.append(result)
        return result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results.
        
        Returns:
            Dictionary with validation summary
        """
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r.is_valid)
        failed_checks = total_checks - passed_checks
        
        errors = [r for r in self.validation_results 
                 if not r.is_valid and r.severity == "error"]
        warnings = [r for r in self.validation_results 
                   if not r.is_valid and r.severity == "warning"]
        
        return {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "errors": len(errors),
            "warnings": len(warnings),
            "all_passed": failed_checks == 0,
            "results": [r.to_dict() for r in self.validation_results]
        }


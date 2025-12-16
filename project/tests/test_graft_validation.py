"""Comprehensive tests for graft_validation module."""
import pytest
import numpy as np
from graft_validation import GraftValidationFramework, GraftValidationResult


class TestValidationFramework:
    """Test validation framework."""
    
    def test_compatibility_validation(self):
        """Test compatibility validation."""
        framework = GraftValidationFramework()
        compatibility = np.array([0.8, 0.9, 0.2, 0.7])  # 0.2 is below threshold
        result = framework.validate_compatibility(compatibility, min_compatibility=0.3)
        # Convert numpy bool to Python bool for comparison
        assert bool(result.is_valid) is False
    
    def test_environmental_validation(self):
        """Test environmental validation."""
        framework = GraftValidationFramework()
        temperature = np.array([22.0, 25.0, 5.0])  # 5.0 is too cold
        humidity = np.array([0.8, 0.7, 0.9])
        result = framework.validate_environmental_conditions(temperature, humidity)
        assert result.severity == "warning"
    
    def test_diameter_match(self):
        """Test diameter match validation."""
        framework = GraftValidationFramework()
        rootstock = np.array([15.0, 15.0, 15.0])
        scion = np.array([15.0, 20.0, 10.0])  # Mismatches
        result = framework.validate_diameter_match(rootstock, scion, tolerance=0.2)
        # Convert numpy bool to Python bool for comparison
        assert bool(result.is_valid) is False
    
    def test_validation_summary(self):
        """Test validation summary."""
        framework = GraftValidationFramework()
        framework.validate_compatibility(np.array([0.8, 0.9]))
        summary = framework.get_validation_summary()
        assert "total_checks" in summary
        assert summary["total_checks"] == 1
    
    def test_biological_constraints_valid(self):
        """Test biological constraints validation with valid data."""
        framework = GraftValidationFramework()
        union_strength = np.array([0.3, 0.5, 0.7, 0.9])
        days_since_grafting = np.array([10, 20, 30, 40])
        result = framework.validate_biological_constraints(union_strength, days_since_grafting)
        assert bool(result.is_valid) is True
        assert result.check_name == "biological_constraints_check"
    
    def test_biological_constraints_out_of_range(self):
        """Test biological constraints with out-of-range union strength."""
        framework = GraftValidationFramework()
        union_strength = np.array([0.5, 1.5, 0.7])  # 1.5 is > 1
        days_since_grafting = np.array([10, 20, 30])
        result = framework.validate_biological_constraints(union_strength, days_since_grafting)
        assert bool(result.is_valid) is False
        assert "outside [0, 1] range" in result.message
    
    def test_biological_constraints_negative(self):
        """Test biological constraints with negative union strength."""
        framework = GraftValidationFramework()
        union_strength = np.array([0.5, -0.1, 0.7])  # -0.1 is < 0
        days_since_grafting = np.array([10, 20, 30])
        result = framework.validate_biological_constraints(union_strength, days_since_grafting)
        assert bool(result.is_valid) is False
    
    def test_biological_constraints_unrealistic_early(self):
        """Test biological constraints with unrealistic early strength."""
        framework = GraftValidationFramework()
        union_strength = np.array([0.9, 0.85, 0.7])  # High strength
        days_since_grafting = np.array([3, 5, 30])  # First two are early days
        result = framework.validate_biological_constraints(union_strength, days_since_grafting)
        assert bool(result.is_valid) is False
        assert "Unrealistic union strength in early days" in result.message
    
    def test_biological_constraints_early_acceptable(self):
        """Test biological constraints with acceptable early strength."""
        framework = GraftValidationFramework()
        union_strength = np.array([0.3, 0.4, 0.7])  # Acceptable early strength
        days_since_grafting = np.array([3, 5, 30])
        result = framework.validate_biological_constraints(union_strength, days_since_grafting)
        assert bool(result.is_valid) is True


if __name__ == "__main__":
    pytest.main([__file__])


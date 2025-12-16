"""Comprehensive tests for graft_parameters module."""
import json
import tempfile
from pathlib import Path

import pytest

from graft_parameters import (
    GraftParameterConstraint,
    GraftParameterSet,
    GraftParameterSweep,
    create_default_graft_parameters
)


class TestGraftParameterConstraint:
    """Test GraftParameterConstraint class."""
    
    def test_validate_numeric_range(self):
        """Test numeric range validation."""
        constraint = GraftParameterConstraint(min_value=0.0, max_value=1.0)
        is_valid, msg = constraint.validate(0.5)
        assert is_valid is True
        
        is_valid, msg = constraint.validate(-0.1)
        assert is_valid is False
        assert "below minimum" in msg
    
    def test_validate_allowed_values(self):
        """Test allowed values validation."""
        constraint = GraftParameterConstraint(allowed_values=["whip", "cleft", "bark"])
        is_valid, msg = constraint.validate("whip")
        assert is_valid is True
        
        is_valid, msg = constraint.validate("unknown")
        assert is_valid is False
    
    def test_validate_type_check(self):
        """Test type checking validation."""
        constraint = GraftParameterConstraint(param_type=float)
        is_valid, msg = constraint.validate(0.5)
        assert is_valid is True
        
        is_valid, msg = constraint.validate("0.5")  # String instead of float
        assert is_valid is False
        assert "type" in msg.lower()


class TestGraftParameterSet:
    """Test GraftParameterSet class."""
    
    def test_add_parameter(self):
        """Test adding parameters."""
        params = GraftParameterSet()
        params.add_parameter("temperature", 22.0)
        assert params.parameters["temperature"] == 22.0
    
    def test_get_parameter(self):
        """Test getting parameter values."""
        params = GraftParameterSet()
        params.add_parameter("compatibility", 0.8)
        assert params.get("compatibility") == 0.8
        assert params.get("unknown", 0.5) == 0.5
    
    def test_validate(self):
        """Test parameter validation."""
        params = GraftParameterSet()
        constraint = GraftParameterConstraint(min_value=0.0, max_value=1.0)
        params.add_parameter("compatibility", 0.8, constraint=constraint)
        is_valid, errors = params.validate()
        assert is_valid is True
        
        params.parameters["compatibility"] = 1.5
        is_valid, errors = params.validate()
        assert is_valid is False


class TestDefaultParameters:
    """Test default parameter creation."""
    
    def test_create_default(self):
        """Test creating default parameters."""
        params = create_default_graft_parameters()
        assert params.get("temperature") == 22.0
        assert params.get("compatibility") == 0.8
        assert params.get("technique") == "whip"


class TestParameterSweep:
    """Test parameter sweep functionality."""
    
    def test_generate_combinations(self):
        """Test generating parameter combinations."""
        base = GraftParameterSet()
        base.add_parameter("temperature", 22.0)
        base.add_parameter("humidity", 0.8)
        
        sweep = GraftParameterSweep(base)
        sweep.add_sweep("temperature", [20.0, 22.0, 24.0])
        sweep.add_sweep("humidity", [0.7, 0.8])
        
        combinations = sweep.generate_combinations()
        assert len(combinations) == 6
        assert sweep.get_sweep_size() == 6


if __name__ == "__main__":
    pytest.main([__file__])


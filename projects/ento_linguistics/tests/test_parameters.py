"""Comprehensive tests for src/parameters.py to ensure 100% coverage."""

import json
import tempfile
from pathlib import Path

import pytest
from core.parameters import ParameterConstraint, ParameterSet, ParameterSweep


class TestParameterConstraint:
    """Test ParameterConstraint class."""

    def test_validate_numeric_range(self):
        """Test numeric range validation."""
        constraint = ParameterConstraint(min_value=0.0, max_value=10.0)
        is_valid, msg = constraint.validate(5.0)
        assert is_valid is True

        is_valid, msg = constraint.validate(-1.0)
        assert is_valid is False
        assert "below minimum" in msg

        is_valid, msg = constraint.validate(11.0)
        assert is_valid is False
        assert "above maximum" in msg

    def test_validate_allowed_values(self):
        """Test allowed values validation."""
        constraint = ParameterConstraint(allowed_values=[1, 2, 3])
        is_valid, msg = constraint.validate(2)
        assert is_valid is True

        is_valid, msg = constraint.validate(4)
        assert is_valid is False
        assert "not in allowed values" in msg

    def test_validate_type(self):
        """Test type validation."""
        constraint = ParameterConstraint(param_type=int)
        is_valid, msg = constraint.validate(5)
        assert is_valid is True

        is_valid, msg = constraint.validate(5.0)
        assert is_valid is False
        assert "Expected type" in msg

    def test_validate_non_numeric(self):
        """Test validation with non-numeric value (branch 40->46)."""
        constraint = ParameterConstraint(min_value=0.0, max_value=10.0)
        # Test with string value (not numeric)
        is_valid, msg = constraint.validate("test")
        # Non-numeric values skip range checking, so should return True
        assert is_valid is True
        assert msg is None


class TestParameterSet:
    """Test ParameterSet class."""

    def test_add_parameter(self):
        """Test adding parameters."""
        params = ParameterSet()
        params.add_parameter("param1", 1.0)
        assert params.parameters["param1"] == 1.0

    def test_add_parameter_with_constraint(self):
        """Test adding parameter with constraint."""
        params = ParameterSet()
        constraint = ParameterConstraint(min_value=0.0, max_value=10.0)
        params.add_parameter("param1", 5.0, constraint=constraint)
        assert "param1" in params.constraints

    def test_add_parameter_with_default(self):
        """Test adding parameter with default value (line 78)."""
        params = ParameterSet()
        params.add_parameter("param1", 1.0, default=2.0)
        assert params.parameters["param1"] == 1.0
        assert params.defaults["param1"] == 2.0

    def test_add_parameter_with_description(self):
        """Test adding parameter with description (branch 80->82)."""
        params = ParameterSet()
        # Ensure metadata is empty (doesn't have "descriptions" key)
        # This triggers branch 80->82 when we add the first description
        params.add_parameter("param1", 1.0, description="First description")
        assert "descriptions" in params.metadata
        assert params.metadata["descriptions"]["param1"] == "First description"

        # Add another with description (should not trigger branch since "descriptions" already exists)
        params.add_parameter("param2", 2.0, description="Second description")
        assert params.metadata["descriptions"]["param2"] == "Second description"

    def test_get_parameter(self):
        """Test getting parameter values."""
        params = ParameterSet()
        params.add_parameter("param1", 1.0)
        params.defaults["param2"] = 2.0

        assert params.get("param1") == 1.0
        assert params.get("param2") == 2.0
        assert params.get("param3", 3.0) == 3.0
        assert params.get("param4") is None

    def test_validate_parameters(self):
        """Test parameter validation."""
        params = ParameterSet()
        constraint = ParameterConstraint(min_value=0.0, max_value=10.0)
        params.add_parameter("param1", 5.0, constraint=constraint)
        params.add_parameter("param2", 15.0, constraint=constraint)

        is_valid, errors = params.validate()
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_parameters_no_constraint(self):
        """Test parameter validation when parameter has no constraint (branch 109->108)."""
        params = ParameterSet()
        # Add parameter without constraint
        params.add_parameter("param1", 5.0)
        # Add another parameter with constraint
        constraint = ParameterConstraint(min_value=0.0, max_value=10.0)
        params.add_parameter("param2", 5.0, constraint=constraint)

        is_valid, errors = params.validate()
        # Should be valid since param1 has no constraint and param2 is valid
        assert is_valid is True
        assert len(errors) == 0

    def test_to_dict(self):
        """Test converting to dictionary."""
        params = ParameterSet()
        params.add_parameter("param1", 1.0)
        params.defaults["param2"] = 2.0

        data = params.to_dict()
        assert "parameters" in data
        assert "defaults" in data
        assert data["parameters"]["param1"] == 1.0

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "parameters": {"param1": 1.0},
            "defaults": {"param2": 2.0},
            "metadata": {},
        }
        params = ParameterSet.from_dict(data)
        assert params.parameters["param1"] == 1.0
        assert params.defaults["param2"] == 2.0

    def test_save_and_load(self, tmp_path):
        """Test saving and loading parameter set."""
        params = ParameterSet()
        params.add_parameter("param1", 1.0, description="Test parameter")

        filepath = tmp_path / "params.json"
        params.save(filepath)
        assert filepath.exists()

        loaded = ParameterSet.load(filepath)
        assert loaded.parameters["param1"] == 1.0


class TestParameterSweep:
    """Test ParameterSweep class."""

    def test_initialization(self):
        """Test parameter sweep initialization."""
        base_params = ParameterSet()
        base_params.add_parameter("param1", 1.0)
        sweep = ParameterSweep(base_params)
        assert sweep.base_parameters == base_params

    def test_add_sweep(self):
        """Test adding sweep parameter."""
        base_params = ParameterSet()
        base_params.add_parameter("param1", 1.0)
        sweep = ParameterSweep(base_params)
        sweep.add_sweep("param1", [1.0, 2.0, 3.0])
        assert "param1" in sweep.sweep_configs
        assert len(sweep.sweep_configs["param1"]) == 3

    def test_generate_combinations(self):
        """Test generating parameter combinations."""
        base_params = ParameterSet()
        base_params.add_parameter("param1", 1.0)
        base_params.add_parameter("param2", 2.0)

        sweep = ParameterSweep(base_params)
        sweep.add_sweep("param1", [1.0, 2.0])
        sweep.add_sweep("param2", [3.0, 4.0])

        combinations = sweep.generate_combinations()
        assert len(combinations) == 4
        assert {"param1": 1.0, "param2": 3.0} in combinations

    def test_get_sweep_size(self):
        """Test getting sweep size."""
        base_params = ParameterSet()
        sweep = ParameterSweep(base_params)
        sweep.add_sweep("param1", [1, 2, 3])
        sweep.add_sweep("param2", [4, 5])

        assert sweep.get_sweep_size() == 6

    def test_get_sweep_size_empty(self):
        """Test getting sweep size when no sweep configs (line 214)."""
        base_params = ParameterSet()
        sweep = ParameterSweep(base_params)
        # No sweep configs added
        assert sweep.get_sweep_size() == 1

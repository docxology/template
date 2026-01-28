"""Parameter management for scientific simulations.

This module provides parameter set management, validation, sweeps,
and serialization for reproducible simulations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class ParameterConstraint:
    """Constraint for parameter validation."""

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    param_type: Optional[type] = None

    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a parameter value.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Type checking
        if self.param_type is not None and not isinstance(value, self.param_type):
            return False, f"Expected type {self.param_type}, got {type(value)}"

        # Allowed values check
        if self.allowed_values is not None and value not in self.allowed_values:
            return False, f"Value {value} not in allowed values {self.allowed_values}"

        # Numeric range checking
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                return False, f"Value {value} below minimum {self.min_value}"
            if self.max_value is not None and value > self.max_value:
                return False, f"Value {value} above maximum {self.max_value}"

        return True, None


@dataclass
class ParameterSet:
    """A set of parameters with validation."""

    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, ParameterConstraint] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_parameter(
        self,
        name: str,
        value: Any,
        constraint: Optional[ParameterConstraint] = None,
        default: Optional[Any] = None,
        description: Optional[str] = None,
    ) -> None:
        """Add a parameter with optional constraint.

        Args:
            name: Parameter name
            value: Parameter value
            constraint: Optional validation constraint
            default: Default value
            description: Parameter description
        """
        self.parameters[name] = value
        if constraint is not None:
            self.constraints[name] = constraint
        if default is not None:
            self.defaults[name] = default
        if description is not None:
            if "descriptions" not in self.metadata:
                self.metadata["descriptions"] = {}
            self.metadata["descriptions"][name] = description

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        """Get parameter value.

        Args:
            name: Parameter name
            default: Default value if not found

        Returns:
            Parameter value or default
        """
        if name in self.parameters:
            return self.parameters[name]
        if name in self.defaults:
            return self.defaults[name]
        return default

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all parameters.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for name, value in self.parameters.items():
            if name in self.constraints:
                constraint = self.constraints[name]
                is_valid, error_msg = constraint.validate(value)
                if not is_valid:
                    errors.append(f"Parameter '{name}': {error_msg}")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "parameters": self.parameters,
            "defaults": self.defaults,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ParameterSet:
        """Create from dictionary."""
        return cls(
            parameters=data.get("parameters", {}),
            defaults=data.get("defaults", {}),
            metadata=data.get("metadata", {}),
        )

    def save(self, filepath: Union[str, Path]) -> None:
        """Save parameter set to file.

        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> ParameterSet:
        """Load parameter set from file.

        Args:
            filepath: Path to load file

        Returns:
            ParameterSet instance
        """
        filepath = Path(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


class ParameterSweep:
    """Configuration for parameter sweeps."""

    def __init__(self, base_parameters: ParameterSet):
        """Initialize parameter sweep.

        Args:
            base_parameters: Base parameter set
        """
        self.base_parameters = base_parameters
        self.sweep_configs: Dict[str, List[Any]] = {}

    def add_sweep(self, parameter_name: str, values: List[Any]) -> None:
        """Add parameter to sweep.

        Args:
            parameter_name: Name of parameter to sweep
            values: List of values to try
        """
        self.sweep_configs[parameter_name] = values

    def generate_combinations(self) -> List[Dict[str, Any]]:
        """Generate all parameter combinations.

        Returns:
            List of parameter dictionaries
        """
        import itertools

        # Get all parameter names to sweep
        sweep_params = list(self.sweep_configs.keys())
        sweep_values = [self.sweep_configs[p] for p in sweep_params]

        # Generate all combinations
        combinations = []
        for combo in itertools.product(*sweep_values):
            # Start with base parameters
            params = self.base_parameters.parameters.copy()

            # Override with sweep values
            for param_name, value in zip(sweep_params, combo):
                params[param_name] = value

            combinations.append(params)

        return combinations

    def get_sweep_size(self) -> int:
        """Get total number of combinations.

        Returns:
            Number of parameter combinations
        """
        if not self.sweep_configs:
            return 1

        total = 1
        for values in self.sweep_configs.values():
            total *= len(values)
        return total

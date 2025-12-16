"""Parameter management for tree grafting operations.

This module provides parameter set management, validation, and configuration
for grafting experiments including environmental factors, biological parameters,
and technique parameters.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class GraftParameterConstraint:
    """Constraint for grafting parameter validation."""
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
class GraftParameterSet:
    """A set of grafting parameters with validation."""
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, GraftParameterConstraint] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_parameter(
        self,
        name: str,
        value: Any,
        constraint: Optional[GraftParameterConstraint] = None,
        default: Optional[Any] = None,
        description: Optional[str] = None
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
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GraftParameterSet:
        """Create from dictionary."""
        return cls(
            parameters=data.get("parameters", {}),
            defaults=data.get("defaults", {}),
            metadata=data.get("metadata", {})
        )
    
    def save(self, filepath: Union[str, Path]) -> None:
        """Save parameter set to file.
        
        Args:
            filepath: Path to save file
        """
        filepath = Path(filepath)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, filepath: Union[str, Path]) -> GraftParameterSet:
        """Load parameter set from file.
        
        Args:
            filepath: Path to load file
            
        Returns:
            GraftParameterSet instance
        """
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_default_graft_parameters() -> GraftParameterSet:
    """Create default grafting parameter set with constraints.
    
    Returns:
        GraftParameterSet with standard grafting parameters
    """
    params = GraftParameterSet()
    
    # Environmental parameters
    params.add_parameter(
        "temperature",
        22.0,
        constraint=GraftParameterConstraint(min_value=10.0, max_value=35.0, param_type=float),
        default=22.0,
        description="Ambient temperature in Celsius"
    )
    
    params.add_parameter(
        "humidity",
        0.8,
        constraint=GraftParameterConstraint(min_value=0.0, max_value=1.0, param_type=float),
        default=0.8,
        description="Relative humidity (0-1)"
    )
    
    # Biological parameters
    params.add_parameter(
        "compatibility",
        0.8,
        constraint=GraftParameterConstraint(min_value=0.0, max_value=1.0, param_type=float),
        default=0.8,
        description="Species compatibility score (0-1)"
    )
    
    params.add_parameter(
        "rootstock_diameter",
        15.0,
        constraint=GraftParameterConstraint(min_value=5.0, max_value=50.0, param_type=float),
        default=15.0,
        description="Rootstock diameter in mm"
    )
    
    params.add_parameter(
        "scion_diameter",
        15.0,
        constraint=GraftParameterConstraint(min_value=5.0, max_value=50.0, param_type=float),
        default=15.0,
        description="Scion diameter in mm"
    )
    
    # Technique parameters
    params.add_parameter(
        "technique",
        "whip",
        constraint=GraftParameterConstraint(
            allowed_values=["whip", "whip_and_tongue", "cleft", "bark", "bud", "approach"],
            param_type=str
        ),
        default="whip",
        description="Grafting technique"
    )
    
    params.add_parameter(
        "technique_quality",
        0.8,
        constraint=GraftParameterConstraint(min_value=0.0, max_value=1.0, param_type=float),
        default=0.8,
        description="Quality of technique execution (0-1)"
    )
    
    # Seasonal parameters
    params.add_parameter(
        "month",
        3,
        constraint=GraftParameterConstraint(min_value=1, max_value=12, param_type=int),
        default=3,
        description="Grafting month (1-12)"
    )
    
    params.add_parameter(
        "species_type",
        "temperate",
        constraint=GraftParameterConstraint(
            allowed_values=["temperate", "tropical", "subtropical"],
            param_type=str
        ),
        default="temperate",
        description="Species type"
    )
    
    return params


class GraftParameterSweep:
    """Configuration for grafting parameter sweeps."""
    
    def __init__(self, base_parameters: GraftParameterSet):
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


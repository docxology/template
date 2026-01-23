# Infrastructure Module Prompt

## Purpose

Create generic, reusable infrastructure modules that provide domain-independent utilities for the Research Project Template, ensuring 60% test coverage and proper public API design.

## Context

This prompt enforces infrastructure module standards for reusable components:

- [`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md) - Infrastructure development standards
- [`../core/ARCHITECTURE.md`](../core/ARCHITECTURE.md) - Infrastructure layer architecture
- [`../architecture/TWO_LAYER_ARCHITECTURE.md`](../architecture/TWO_LAYER_ARCHITECTURE.md) - Two-layer architecture guide

## Prompt Template

```
You are creating an infrastructure module for the Research Project Template. Infrastructure modules must be generic, reusable across research projects, domain-independent, and meet strict quality standards.

MODULE PURPOSE: [Describe the generic functionality this module provides]
MODULE NAME: [Name for the infrastructure module]
REUSABILITY SCOPE: [Describe which types of projects/research can use this module]

INFRASTRUCTURE REQUIREMENTS:

## 1. Infrastructure Module Standards

### Generic Focus - CRITICAL REQUIREMENT

**Domain Independence:**
- No research-specific assumptions or hardcoded values
- Generic algorithms applicable to any research domain
- Configurable parameters for domain-specific adaptation
- Abstract interfaces for domain-specific implementations

**Reusability Requirements:**
- Usable by `project`, `code_project`, `prose_project`, and future projects
- Clear separation of generic logic from domain-specific logic
- Extensible design for domain-specific extensions
- Stable APIs that don't break between versions

### Module Structure
```
infrastructure/[module_name]/
├── __init__.py          # Public API exports (__all__ list)
├── core.py             # Main functionality implementation
├── exceptions.py       # Custom exception classes
├── validators.py       # Input validation functions
├── utils.py            # Generic utility functions
├── types.py            # Type definitions and protocols
├── AGENTS.md           # Technical documentation
├── README.md           # Quick reference
└── tests/
    ├── __init__.py
    ├── test_core.py
    ├── test_validators.py
    ├── test_utils.py
    └── test_integration.py
```

## 2. Public API Design

### Clean Public Interface
```python
# infrastructure/[module_name]/__init__.py
"""[Module description providing generic functionality.]

This module provides [generic functionality description] that can be
used across different research projects and domains.
"""

from .core import MainClass
from .exceptions import ModuleError, ValidationError
from .validators import validate_input
from .types import InputType, OutputType

__version__ = "1.0.0"
__all__ = [
    "MainClass",
    "ModuleError",
    "ValidationError",
    "validate_input",
    "InputType",
    "OutputType",
]
```

### Type-Safe Generic Interfaces
```python
# infrastructure/[module_name]/types.py
"""Type definitions for infrastructure module."""

from typing import Protocol, TypeVar, Generic, Any, Dict, List
from abc import ABC, abstractmethod

T = TypeVar('T')
InputData = TypeVar('InputData')
OutputData = TypeVar('OutputData')

class ProcessorProtocol(Protocol, Generic[InputData, OutputData]):
    """Generic processor interface."""

    def process(self, data: InputData) -> OutputData:
        """Process input data to output data."""
        ...

    def validate(self, data: InputData) -> bool:
        """Validate input data."""
        ...

class ConfigurableProcessor(ABC, Generic[T]):
    """Abstract base class for configurable processors."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        pass

    @abstractmethod
    def process(self, data: T) -> Any:
        """Process data according to configuration."""
        pass
```

### Exception Hierarchy
```python
# infrastructure/[module_name]/exceptions.py
"""Exception classes for infrastructure module."""

from infrastructure.core.exceptions import TemplateError

class ModuleError(TemplateError):
    """Base exception for module errors."""
    pass

class ValidationError(ModuleError):
    """Raised when input validation fails."""
    pass

class ConfigurationError(ModuleError):
    """Raised when configuration is invalid."""
    pass

class ProcessingError(ModuleError):
    """Raised when processing fails."""
    pass
```

## 3. Core Implementation

### Generic Algorithm Design
```python
# infrastructure/[module_name]/core.py
"""Core implementation of generic functionality."""

from typing import Any, Dict, List, Optional, Union
from .exceptions import ValidationError, ConfigurationError, ProcessingError
from .validators import validate_input
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

class GenericProcessor:
    """Generic processor with domain-independent logic.

    This class provides [generic functionality] that can be configured
    for different research domains and use cases.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize processor with configuration.

        Args:
            config: Configuration dictionary with generic parameters

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config.copy()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._validate_configuration()
        self._initialize_components()

    def _validate_configuration(self) -> None:
        """Validate configuration parameters."""
        required_keys = ['algorithm', 'parameters']
        for key in required_keys:
            if key not in self.config:
                raise ConfigurationError(f"Missing required config key: {key}")

        # Domain-independent validation
        if not isinstance(self.config['parameters'], dict):
            raise ConfigurationError("Parameters must be a dictionary")

    def _initialize_components(self) -> None:
        """Initialize internal components."""
        self.algorithm = self.config['algorithm']
        self.parameters = self.config['parameters']

    def process(self, data: Any) -> Any:
        """Process data using generic algorithm.

        Args:
            data: Input data to process

        Returns:
            Processed output data

        Raises:
            ValidationError: If input validation fails
            ProcessingError: If processing fails
        """
        self.logger.info(f"Starting processing with algorithm: {self.algorithm}")

        try:
            # Generic input validation
            if not self._validate_input_generic(data):
                raise ValidationError("Input validation failed")

            # Domain-independent processing
            result = self._process_generic(data)

            # Generic output validation
            if not self._validate_output_generic(result):
                raise ProcessingError("Output validation failed")

            self.logger.info("Processing completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            raise ProcessingError(f"Processing failed: {e}") from e

    def _validate_input_generic(self, data: Any) -> bool:
        """Generic input validation applicable to any domain."""
        # Domain-independent checks
        if data is None:
            return False

        # Type checking based on configuration
        expected_type = self.config.get('input_type')
        if expected_type and not isinstance(data, expected_type):
            return False

        return True

    def _process_generic(self, data: Any) -> Any:
        """Generic processing logic applicable to any domain."""
        # Domain-independent processing steps
        processed = self._apply_algorithm(data)
        validated = self._validate_processing_result(processed)
        formatted = self._format_output(validated)

        return formatted

    def _validate_output_generic(self, result: Any) -> bool:
        """Generic output validation applicable to any domain."""
        # Basic output validation
        if result is None:
            return False

        # Configuration-based validation
        output_requirements = self.config.get('output_requirements', {})
        for requirement, value in output_requirements.items():
            if not self._check_requirement(result, requirement, value):
                return False

        return True

    def _apply_algorithm(self, data: Any) -> Any:
        """Apply the configured algorithm to data."""
        # Generic algorithm dispatcher
        algorithm_map = {
            'transform': self._transform_algorithm,
            'analyze': self._analysis_algorithm,
            'validate': self._validation_algorithm,
        }

        algorithm_func = algorithm_map.get(self.algorithm)
        if not algorithm_func:
            raise ConfigurationError(f"Unknown algorithm: {self.algorithm}")

        return algorithm_func(data, self.parameters)

    def _transform_algorithm(self, data: Any, params: Dict[str, Any]) -> Any:
        """Generic transformation algorithm."""
        # Domain-independent transformation logic
        # Can be configured for different transformation types
        pass

    def _analysis_algorithm(self, data: Any, params: Dict[str, Any]) -> Any:
        """Generic analysis algorithm."""
        # Domain-independent analysis logic
        pass

    def _validation_algorithm(self, data: Any, params: Dict[str, Any]) -> Any:
        """Generic validation algorithm."""
        # Domain-independent validation logic
        pass

    def _validate_processing_result(self, result: Any) -> Any:
        """Validate intermediate processing results."""
        # Generic result validation
        return result

    def _format_output(self, result: Any) -> Any:
        """Format output according to configuration."""
        # Generic output formatting
        return result

    def _check_requirement(self, result: Any, requirement: str, value: Any) -> bool:
        """Check if result meets a specific requirement."""
        # Generic requirement checking
        if requirement == 'not_empty':
            return len(result) > 0 if hasattr(result, '__len__') else True
        elif requirement == 'type':
            return isinstance(result, value)
        # Add more generic requirements as needed

        return True
```

## 4. Validation and Testing

### Input Validation Module
```python
# infrastructure/[module_name]/validators.py
"""Input validation functions for infrastructure module."""

from typing import Any, Dict, List, Union
from .exceptions import ValidationError

def validate_generic_input(data: Any, constraints: Dict[str, Any]) -> None:
    """Validate input data against generic constraints.

    Args:
        data: Input data to validate
        constraints: Validation constraints dictionary

    Raises:
        ValidationError: If validation fails
    """
    # Generic validation logic applicable to any domain
    if 'required' in constraints and constraints['required'] and data is None:
        raise ValidationError("Data is required but None provided")

    if 'type' in constraints:
        expected_type = constraints['type']
        if not isinstance(data, expected_type):
            raise ValidationError(f"Data must be of type {expected_type}, got {type(data)}")

    if 'min_length' in constraints and hasattr(data, '__len__'):
        if len(data) < constraints['min_length']:
            raise ValidationError(f"Data length {len(data)} is less than minimum {constraints['min_length']}")

    # Add more generic validations as needed

def validate_configuration(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate configuration against schema.

    Args:
        config: Configuration to validate
        schema: Validation schema

    Raises:
        ValidationError: If configuration is invalid
    """
    # Generic configuration validation
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Required configuration field missing: {field}")

    field_validations = schema.get('fields', {})
    for field, field_schema in field_validations.items():
        if field in config:
            validate_generic_input(config[field], field_schema)
```

### Testing (60% Coverage)
```python
# tests/test_core.py
"""Tests for infrastructure module core functionality."""
import pytest
import numpy as np
from unittest.mock import MagicMock

from infrastructure.[module_name] import GenericProcessor, ModuleError
from infrastructure.[module_name].exceptions import ValidationError, ConfigurationError

class TestGenericProcessor:
    """Test suite for GenericProcessor class."""

    @pytest.fixture
    def valid_config(self):
        """Provide valid configuration for testing."""
        return {
            'algorithm': 'transform',
            'parameters': {'scale': 2.0},
            'input_type': list,
            'output_requirements': {'not_empty': True}
        }

    @pytest.fixture
    def processor(self, valid_config):
        """Provide configured processor instance."""
        return GenericProcessor(valid_config)

    def test_initialization_valid_config(self, valid_config):
        """Test processor initialization with valid configuration."""
        processor = GenericProcessor(valid_config)

        assert processor.algorithm == 'transform'
        assert processor.parameters['scale'] == 2.0

    def test_initialization_invalid_config(self):
        """Test processor initialization with invalid configuration."""
        invalid_configs = [
            {},  # Missing required keys
            {'algorithm': 'invalid'},  # Missing parameters
            {'algorithm': 'transform', 'parameters': 'not_dict'},  # Wrong parameter type
        ]

        for invalid_config in invalid_configs:
            with pytest.raises(ConfigurationError):
                GenericProcessor(invalid_config)

    def test_process_valid_data(self, processor):
        """Test processing with valid data."""
        # Create test data that should pass validation
        test_data = [1, 2, 3, 4, 5]

        # Mock the internal methods to return predictable results
        processor._apply_algorithm = MagicMock(return_value=[2, 4, 6, 8, 10])
        processor._validate_processing_result = MagicMock(return_value=[2, 4, 6, 8, 10])
        processor._format_output = MagicMock(return_value=[2, 4, 6, 8, 10])

        result = processor.process(test_data)

        assert result == [2, 4, 6, 8, 10]
        processor._apply_algorithm.assert_called_once_with(test_data, processor.parameters)

    def test_process_invalid_input(self, processor):
        """Test processing with invalid input."""
        invalid_inputs = [
            None,  # None input
            "not_list",  # Wrong type
            [],  # Empty list
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises((ValidationError, ModuleError)):
                processor.process(invalid_input)

    @pytest.mark.parametrize("algorithm,parameters,expected_error", [
        ('unknown_algorithm', {}, "Unknown algorithm"),
        ('transform', {'invalid_param': 'value'}, "Configuration error"),
    ])
    def test_algorithm_errors(self, algorithm, parameters, expected_error):
        """Test algorithm-related error conditions."""
        config = {
            'algorithm': algorithm,
            'parameters': parameters,
        }

        processor = GenericProcessor(config)

        # This should trigger algorithm validation
        test_data = [1, 2, 3]
        with pytest.raises(ModuleError) as exc_info:
            processor.process(test_data)

        assert expected_error.lower() in str(exc_info.value).lower()

    def test_configuration_validation(self, valid_config):
        """Test configuration validation."""
        # Valid configuration should not raise
        GenericProcessor(valid_config)

        # Test various invalid configurations
        invalid_configs = [
            {'algorithm': 'transform'},  # Missing parameters
            {'parameters': {}},  # Missing algorithm
            {'algorithm': 'transform', 'parameters': None},  # None parameters
        ]

        for invalid_config in invalid_configs:
            with pytest.raises(ConfigurationError):
                GenericProcessor(invalid_config)

# Additional test files would cover validators, utilities, and integration
```

## 5. Documentation Standards

### AGENTS.md Technical Documentation
```markdown
# [Module Name] Infrastructure Module

> **Generic [functionality] infrastructure** - Reusable across research projects

**Quick Reference:** [README.md](README.md) | [API Reference](#api-reference)

## Overview

The `[module_name]` infrastructure module provides generic [functionality description] that can be configured and used across different research domains and project types.

## Architecture

### Generic Design Principles

- **Domain Independence**: No hardcoded research-specific assumptions
- **Configuration-Driven**: All domain-specific behavior configured externally
- **Extensible Interface**: Clear protocols for domain-specific extensions
- **Stable API**: Backward-compatible across versions

### Module Structure

```
infrastructure/[module_name]/
├── __init__.py          # Public API exports
├── core.py             # Main GenericProcessor implementation
├── exceptions.py       # Custom exception hierarchy
├── validators.py       # Generic validation functions
├── types.py            # Type definitions and protocols
└── tests/              # test suite (60%+ coverage)
```

## API Reference

### Classes

#### `GenericProcessor`

Main class providing generic [functionality] processing capabilities.

**Configuration Parameters:**
- `algorithm` (str): Algorithm to use ('transform', 'analyze', 'validate')
- `parameters` (dict): Algorithm-specific parameters
- `input_type` (type): Expected input data type
- `output_requirements` (dict): Output validation requirements

**Methods:**
- `process(data) -> result`: Process input data
- `validate_input(data) -> bool`: Validate input data

### Exceptions

#### `ModuleError`
Base exception for module-specific errors.

#### `ValidationError`
Raised when input/output validation fails.

#### `ConfigurationError`
Raised when configuration is invalid.

#### `ProcessingError`
Raised when processing operations fail.

## Usage Examples

### Basic Configuration

```python
from infrastructure.[module_name] import GenericProcessor

config = {
    'algorithm': 'transform',
    'parameters': {'scale': 2.0},
    'input_type': list
}

processor = GenericProcessor(config)
result = processor.process([1, 2, 3])
# Result: [2, 4, 6]
```

### Advanced Configuration

```python
config = {
    'algorithm': 'analyze',
    'parameters': {
        'method': 'statistical',
        'confidence': 0.95
    },
    'output_requirements': {
        'not_empty': True,
        'type': dict
    }
}

processor = GenericProcessor(config)
result = processor.process(dataset)
```

## Configuration Schema

```yaml
[module_name]:
  algorithm: "transform"  # or "analyze", "validate"
  parameters:
    key1: value1
    key2: value2
  input_type: "list"      # Python type name
  output_requirements:
    not_empty: true
    type: "dict"
```

## Integration Patterns

### With Research Projects

```python
# In projects/my_research/src/analysis.py
from infrastructure.[module_name] import GenericProcessor

class ResearchAnalyzer:
    """Domain-specific analyzer using generic infrastructure."""

    def __init__(self):
        self.generic_processor = GenericProcessor({
            'algorithm': 'analyze',
            'parameters': {'domain': 'research'},
        })

    def analyze_data(self, research_data):
        """Analyze research data using generic processor."""
        # Domain-specific preprocessing
        prepared_data = self._prepare_research_data(research_data)

        # Generic processing
        result = self.generic_processor.process(prepared_data)

        # Domain-specific postprocessing
        return self._interpret_results(result)
```

## Testing

### Coverage Requirements
- **60% minimum coverage** for infrastructure modules
- **data testing** (no mocks)
- **Integration testing** across module components

### Test Categories
- Unit tests for individual functions
- Integration tests for component interaction
- Performance tests for scalability
- Error handling tests for robustness

## Performance Characteristics

### Time Complexity
- **Generic algorithms**: O(n) to O(n log n) depending on configuration
- **Validation**: O(1) for simple checks, O(n) for complex validation
- **Configuration**: O(1) initialization, O(1) parameter access

### Space Complexity
- **Memory usage**: O(1) base + O(n) for data processing
- **Configuration**: O(c) where c is configuration size
- **Caching**: Optional O(cache_size) for performance optimization

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../../core/ARCHITECTURE.md`](../../docs/core/ARCHITECTURE.md) - Infrastructure layer architecture
- [`../../../.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md) - Infrastructure development standards
- [`../validation/AGENTS.md`](../validation/AGENTS.md) - Validation infrastructure
```

## Key Requirements

- [ ] Generic, domain-independent design
- [ ] Reusable across different research projects
- [ ] 60% minimum test coverage
- [ ] Clean public API with `__all__` exports
- [ ] Type hints on all public interfaces
- [ ] Custom exception hierarchy
- [ ] AGENTS.md documentation
- [ ] Configuration-driven behavior
- [ ] data testing (no mocks)

## Standards Compliance Checklist

### Infrastructure Standards ([`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md))
- [ ] Generic focus (domain-independent)
- [ ] 60% minimum test coverage achieved
- [ ] Public API with clear `__all__` exports
- [ ] AGENTS.md documentation
- [ ] Error handling with custom exceptions
- [ ] Type hints on all public APIs

### Code Quality Standards ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] Black formatting and isort compliance
- [ ] Google-style docstrings
- [ ] Unified logging system
- [ ] Consistent API design

### Testing Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] No mocks policy (data only)
- [ ] Coverage validation (pytest-cov)
- [ ] Test organization and structure
- [ ] Integration testing included

## Example Usage

**Input:**
```
MODULE PURPOSE: Generic data quality assessment applicable to any research dataset
MODULE NAME: data_quality
REUSABILITY SCOPE: All research projects needing data validation and quality metrics
```

**Expected Output:**
- `infrastructure/data_quality/` module with generic quality assessment
- 60%+ test coverage with data testing
- Clean public API for use across projects
- documentation and examples
- Integration with existing validation infrastructure

## Related Documentation

- [`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md) - Infrastructure development standards
- [`../core/ARCHITECTURE.md`](../core/ARCHITECTURE.md) - Infrastructure layer architecture
- [`../architecture/TWO_LAYER_ARCHITECTURE.md`](../architecture/TWO_LAYER_ARCHITECTURE.md) - Two-layer architecture guide
```

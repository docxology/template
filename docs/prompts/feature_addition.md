# Feature Addition Prompt

## Purpose

Add features to the Research Project Template while maintaining full architecture compliance, testing standards, and development workflow integrity.

## Context

This prompt ensures features integrate properly with the existing system:

- [`../core/WORKFLOW.md`](../core/WORKFLOW.md) - Development workflow
- [`../core/ARCHITECTURE.md`](../core/ARCHITECTURE.md) - Architecture principles
- [`../../.cursorrules/`](../../.cursorrules/) directory - All development standards

## Prompt Template

```
You are adding a feature to the Research Project Template. The feature must integrate seamlessly with the existing two-layer architecture and thin orchestrator pattern while meeting all quality and testing standards.

FEATURE DESCRIPTION: [Describe the feature to implement]
TARGET PROJECT: [Specify which project: "project", "code_project", "prose_project", or new project name]
LAYER: [Specify: "infrastructure" for generic/shared OR "project" for domain-specific]

FEATURE REQUIREMENTS:

## 1. Architecture Integration

### Two-Layer Architecture Compliance

**Infrastructure Layer Features:**
- Generic, reusable across research projects
- Domain-independent functionality
- Located in `infrastructure/` directory
- 60% minimum test coverage
- Stable, version-controlled APIs

**Project Layer Features:**
- Domain-specific research functionality
- Located in `projects/{name}/src/` directory
- 90% minimum test coverage
- Custom research implementations

### Thin Orchestrator Pattern Implementation

**Business Logic Placement:**
- All computational logic in `src/` modules (infrastructure or project)
- Pure functions and classes with clear responsibilities
- error handling with custom exceptions
- Logging using unified `get_logger(__name__)` system

**Orchestration Layer:**
- Thin coordination in `scripts/` directory
- Import and orchestrate module functions
- Handle I/O, configuration, and user interaction
- Minimal business logic (prefer module delegation)

## 2. Development Workflow

### Phase 1: Planning and Design

**Requirements Analysis:**
```python
# Feature requirements specification
class FeatureRequirements:
    """Specification for feature requirements."""

    def __init__(self, feature_name: str):
        self.feature_name = feature_name
        self.functional_requirements = []
        self.non_functional_requirements = []
        self.architecture_constraints = []
        self.testing_requirements = []

    def add_functional_requirement(self, requirement: str):
        """Add functional requirement."""
        self.functional_requirements.append(requirement)

    def add_architecture_constraint(self, constraint: str):
        """Add architecture constraint."""
        self.architecture_constraints.append(constraint)

    def validate_architecture_compliance(self) -> bool:
        """Validate feature complies with architecture."""
        return all(
            self._check_layer_compatibility(),
            self._check_orchestrator_pattern(),
            self._check_testing_requirements()
        )
```

**API Design:**
```python
# BEFORE: Plan the API design first
from typing import Protocol, runtime_checkable

@runtime_checkable
class FeatureInterface(Protocol):
    """Protocol defining feature interface."""

    def execute(self, input_data: Any) -> Any:
        """Execute feature with input data."""
        ...

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data compatibility."""
        ...

    def get_configuration(self) -> Dict[str, Any]:
        """Get feature configuration."""
        ...

# AFTER: Implement according to planned interface
class NewFeature:
    """Implementation of new research feature."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

    def execute(self, input_data: Any) -> Any:
        """Execute feature with error handling."""
        try:
            self._validate_input(input_data)
            result = self._perform_feature_logic(input_data)
            self.logger.info(f"Feature executed successfully: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Feature execution failed: {e}")
            raise FeatureExecutionError(f"Feature failed: {e}") from e

    def validate_input(self, input_data: Any) -> bool:
        """Validate input data compatibility."""
        # Implementation
        return True

    def get_configuration(self) -> Dict[str, Any]:
        """Get current feature configuration."""
        return self.config.copy()
```

### Phase 2: Implementation

**Module Structure Creation:**
```python
# infrastructure/new_feature/ (for infrastructure features)
"""
feature module providing reusable functionality.

This module implements [feature description] with full compliance
to template architecture and quality standards.
"""

__version__ = "1.0.0"
__author__ = "Research Team"

from .core import NewFeature
from .exceptions import FeatureExecutionError, ValidationError
from .validators import FeatureValidator

__all__ = [
    "NewFeature",
    "FeatureExecutionError",
    "ValidationError",
    "FeatureValidator",
]
```

**Script Orchestration:**
```python
# scripts/run_new_feature.py (thin orchestrator)
"""
Orchestrate feature execution.

This script coordinates the execution of the feature
using the thin orchestrator pattern.
"""

from pathlib import Path
from infrastructure.core import get_logger, load_config
from infrastructure.new_feature import NewFeature

logger = get_logger(__name__)

def main():
    """Main orchestration function."""
    logger.info("Starting feature execution")

    # Load configuration
    config = load_config()

    # Initialize feature
    feature = NewFeature(config.get('new_feature', {}))

    # Load input data
    input_data = load_feature_data(config['input_path'])

    # Execute feature
    result = feature.execute(input_data)

    # Save results
    save_feature_results(result, config['output_path'])

    # Generate reports
    generate_feature_report(result, config['report_path'])

    logger.info("feature execution completed")

if __name__ == "__main__":
    main()
```

### Phase 3: Testing

**Test Suite Implementation:**
```python
# tests/test_new_feature.py (90%+ coverage for project features)
"""Tests for feature implementation."""
import pytest
import numpy as np
from pathlib import Path

from infrastructure.new_feature import NewFeature, FeatureExecutionError

class TestNewFeature:
    """test suite for feature."""

    @pytest.fixture
    def sample_config(self):
        """Provide sample configuration."""
        return {
            'parameter1': 1.0,
            'parameter2': 'test_value',
            'enable_validation': True
        }

    @pytest.fixture
    def feature_instance(self, sample_config):
        """Provide configured feature instance."""
        return NewFeature(sample_config)

    @pytest.fixture
    def real_test_data(self):
        """Generate test data."""
        np.random.seed(42)  # Reproducible
        return {
            'data': np.random.randn(100, 5),
            'labels': np.random.randint(0, 2, 100),
            'metadata': {'source': 'test', 'version': '1.0'}
        }

    def test_initialization(self, sample_config):
        """Test feature initialization with valid config."""
        feature = NewFeature(sample_config)

        assert feature.config == sample_config
        assert hasattr(feature, 'logger')

    def test_feature_execution(self, feature_instance, real_test_data):
        """Test feature execution with data."""
        result = feature_instance.execute(real_test_data)

        assert result is not None
        assert isinstance(result, dict)
        assert 'output' in result

    def test_input_validation(self, feature_instance):
        """Test input validation functionality."""
        valid_data = {'data': [1, 2, 3]}
        invalid_data = {'invalid': 'data'}

        assert feature_instance.validate_input(valid_data)
        assert not feature_instance.validate_input(invalid_data)

    def test_error_handling(self, feature_instance):
        """Test error handling with invalid inputs."""
        with pytest.raises(FeatureExecutionError):
            feature_instance.execute(None)

    @pytest.mark.parametrize("config_param,expected", [
        ({'parameter1': 0.5}, 'adjusted'),
        ({'parameter1': 2.0}, 'scaled'),
        ({'parameter1': 1.0, 'special_mode': True}, 'special'),
    ])
    def test_configuration_variants(self, config_param, expected):
        """Test feature with different configurations."""
        config = {'parameter1': 1.0, 'parameter2': 'default'}
        config.update(config_param)

        feature = NewFeature(config)
        result = feature.execute({'test': True})

        assert result['mode'] == expected

    def test_integration_with_existing_systems(self, feature_instance, real_test_data):
        """Test integration with existing template systems."""
        # Test with logging system
        result = feature_instance.execute(real_test_data)
        assert 'log_entries' in result

        # Test with configuration system
        config = feature_instance.get_configuration()
        assert isinstance(config, dict)
        assert len(config) > 0
```

### Phase 4: Documentation Creation

**AGENTS.md Documentation:**
```markdown
# Feature Module

## Overview

[description of the feature, its purpose, and integration with the research workflow.]

## Architecture

### Design Principles

- **Layer Placement**: [Infrastructure/Project] layer
- **Pattern Compliance**: Thin orchestrator pattern
- **Error Handling**: Custom exceptions with proper chaining
- **Logging Integration**: Unified logging system

### Module Structure

```
new_feature/
├── __init__.py          # Public API exports
├── core.py             # Main feature implementation
├── exceptions.py       # Custom exceptions
├── validators.py       # Input validation
├── AGENTS.md           # This documentation
├── README.md           # Quick reference
└── tests/
    ├── __init__.py
    ├── test_core.py
    └── test_validators.py
```

## API Reference

### Classes

#### `NewFeature`

Main class implementing the feature functionality.

**Parameters:**
- `config` (Dict[str, Any]): Feature configuration dictionary

**Methods:**

##### `execute(input_data: Any) -> Any`
Execute the feature with provided input data.

**Parameters:**
- `input_data`: Input data for feature execution

**Returns:**
Feature execution results

**Raises:**
- `FeatureExecutionError`: If execution fails
- `ValidationError`: If input validation fails

##### `validate_input(input_data: Any) -> bool`
Validate input data compatibility.

##### `get_configuration() -> Dict[str, Any]`
Get current feature configuration.

### Exceptions

#### `FeatureExecutionError`
Raised when feature execution fails.

#### `ValidationError`
Raised when input validation fails.

## Usage Examples

### Basic Usage

```python
from infrastructure.new_feature import NewFeature

# Configure feature
config = {
    'parameter1': 1.0,
    'enable_validation': True
}

# Create instance
feature = NewFeature(config)

# Execute feature
result = feature.execute(input_data)
```

### Advanced Configuration

```python
# Advanced configuration
config = {
    'parameter1': 2.5,
    'parameter2': 'advanced_mode',
    'custom_validators': ['validator1', 'validator2'],
    'output_format': 'detailed'
}

feature = NewFeature(config)
result = feature.execute(complex_data)
```

## Integration with Research Workflow

### Data Processing Pipeline

```python
# Integration with research data processing
from infrastructure.new_feature import NewFeature
from infrastructure.data_processing import DataProcessor

class ResearchPipeline:
    """research pipeline with feature."""

    def __init__(self, config):
        self.data_processor = DataProcessor(config['data'])
        self.new_feature = NewFeature(config['feature'])

    def run_pipeline(self, raw_data):
        """Run research pipeline."""
        # Process data
        processed_data = self.data_processor.process(raw_data)

        # Apply feature
        result = self.new_feature.execute(processed_data)

        return result
```

## Testing

### Coverage Requirements

- **Infrastructure Features**: 60% minimum coverage
- **Project Features**: 90% minimum coverage
- **No Mocks Policy**: data testing only

### Test Categories

- **Unit Tests**: Individual method/function testing
- **Integration Tests**: Feature interaction testing
- **Performance Tests**: Execution time and resource validation
- **Error Handling Tests**: Exception condition testing

## Configuration

### Configuration Schema

```yaml
new_feature:
  parameter1: 1.0
  parameter2: "default_value"
  enable_validation: true
  custom_validators: []
  output_format: "standard"
```

### Environment Variables

- `NEW_FEATURE_LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARN, ERROR)
- `NEW_FEATURE_TIMEOUT`: Execution timeout in seconds
- `NEW_FEATURE_CACHE_DIR`: Cache directory path

## Performance Characteristics

### Time Complexity
- **Best Case**: O(n) for linear processing
- **Average Case**: O(n log n) with sorting operations
- **Worst Case**: O(n²) for complex validation

### Space Complexity
- **Memory Usage**: O(n) for data processing
- **Cache Usage**: O(1) with LRU eviction
- **Temporary Files**: O(batch_size) during processing

## Error Handling

### Exception Hierarchy

```
FeatureError (base exception)
├── FeatureExecutionError
├── ValidationError
├── ConfigurationError
└── ResourceError
```

### Error Recovery

- **Transient Errors**: Automatic retry with exponential backoff
- **Configuration Errors**: Clear error messages with suggestions
- **Resource Errors**: Graceful degradation with warnings
- **Data Errors**: Validation with detailed error reports

## See Also

- [`README.md`](README.md) - Quick reference and usage examples
- [`../../core/ARCHITECTURE.md`](../../core/ARCHITECTURE.md) - Architecture integration details
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing requirements
- [`../../.cursorrules/api_design.md`](../../.cursorrules/api_design.md) - API design standards
```

**README.md Quick Reference:**
```markdown
# Feature

[Brief description of the feature and its purpose.]

## Quick Start

```python
from infrastructure.new_feature import NewFeature

feature = NewFeature()
result = feature.execute(data)
```

## Features

- [Feature 1]: [Description]
- [Feature 2]: [Description]

## Documentation

See [`AGENTS.md`](AGENTS.md) for technical documentation.
```

## 3. Quality Assurance and Validation

### Validation Integration
```python
# Integrate with template validation system
from infrastructure.validation import validate_module_implementation

def validate_new_feature():
    """Validate feature implementation."""
    validation_result = validate_module_implementation('infrastructure.new_feature')

    assert validation_result['coverage'] >= 60  # Infrastructure requirement
    assert validation_result['linting']['errors'] == 0
    assert validation_result['type_check']['errors'] == 0

    return validation_result
```

### Performance Benchmarking
```python
# Performance validation
import time

def benchmark_feature():
    """Benchmark feature performance."""
    test_data = generate_large_test_dataset()

    start_time = time.time()
    result = NewFeature().execute(test_data)
    execution_time = time.time() - start_time

    # Performance assertions
    assert execution_time < 30  # Must within 30 seconds
    assert result['memory_peak'] < 500 * 1024 * 1024  # Under 500MB

    return {
        'execution_time': execution_time,
        'memory_usage': result['memory_peak'],
        'throughput': len(test_data) / execution_time
    }
```

## Key Requirements

- [ ] Two-layer architecture compliance (correct layer placement)
- [ ] Thin orchestrator pattern implementation
- [ ] development workflow (planning → implementation → testing → documentation)
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] No mocks policy (data testing only)
- [ ] Type hints on all public APIs
- [ ] error handling
- [ ] Unified logging integration
- [ ] AGENTS.md and README.md documentation
- [ ] Integration with existing systems
- [ ] Performance and quality validation

## Standards Compliance Checklist

### Architecture Standards ([`../../docs/core/ARCHITECTURE.md`](../../docs/core/ARCHITECTURE.md))
- [ ] Two-layer architecture compliance
- [ ] Thin orchestrator pattern implementation
- [ ] Correct layer placement (infrastructure vs project)
- [ ] Module organization and structure

### Code Quality Standards ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] Type hints on all public APIs
- [ ] Black formatting and isort compliance
- [ ] Google-style docstrings
- [ ] Error handling with custom exceptions
- [ ] Unified logging system integration

### Testing Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] No mocks policy (data only)
- [ ] Coverage requirements achieved
- [ ] Test organization and structure
- [ ] Integration and performance testing

### Documentation Standards ([`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md))
- [ ] AGENTS.md with technical documentation
- [ ] README.md with Mermaid diagrams
- [ ] Cross-references between documents
- [ ] Examples over explanations

## Example Usage

**Input:**
```
FEATURE DESCRIPTION: Add automated data quality assessment feature for research datasets
TARGET PROJECT: project
LAYER: infrastructure
```

**Expected Output:**
- `infrastructure/data_quality/` module with assessment algorithms
- `scripts/assess_data_quality.py` thin orchestrator script
- test suite (60%+ coverage) with data
- AGENTS.md and README.md documentation
- Integration with existing data processing pipeline
- Quality validation and performance benchmarking

## Related Documentation

- [`../core/WORKFLOW.md`](../core/WORKFLOW.md) - Development workflow
- [`../core/ARCHITECTURE.md`](../core/ARCHITECTURE.md) - Architecture principles
- [`../../.cursorrules/`](../../.cursorrules/) - All development standards
```

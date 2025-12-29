# Code Style and Formatting Standards

## Overview

Consistent code formatting ensures readability, maintainability, and reduces merge conflicts. All Python code must follow these standards.

## Python Code Style (PEP 8)

### Core PEP 8 Rules

#### Line Length
```python
# ✅ GOOD: Under 88 characters (Black default)
result = some_function_with_long_name(argument_one, argument_two)

# ❌ BAD: Too long
result = some_function_with_a_very_long_name_that_exceeds_the_limit(argument_one, argument_two)
```

#### Indentation
```python
# ✅ GOOD: 4 spaces
def function():
    if condition:
        return True
    else:
        return False

# ❌ BAD: Mixed tabs/spaces
def function():
	if condition:  # Tab
	    return True  # Spaces
```

#### Imports
```python
# ✅ GOOD: Standard library first, then third-party, then local
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from infrastructure.core.logging_utils import get_logger
from project.src.data_processing import clean_data

# ❌ BAD: Not grouped or ordered
from project.src.data_processing import clean_data
import pytest
import os
import numpy as np
```

#### Blank Lines
```python
# ✅ GOOD: Logical grouping
import os

def function_one():
    pass

def function_two():
    pass

class MyClass:
    pass

# ❌ BAD: Too many or missing blank lines
import os
def function_one():
    pass
def function_two():
    pass

class MyClass:
    pass
```

#### Naming Conventions
```python
# ✅ GOOD: snake_case for functions/variables
def process_data():
    raw_data = load_data()
    processed_data = clean_data(raw_data)
    return processed_data

# ✅ GOOD: PascalCase for classes
class DataProcessor:
    pass

# ✅ GOOD: UPPER_CASE for constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# ❌ BAD: camelCase or inconsistent
def processData():
    rawData = load_data()
    processedData = cleanData(rawData)
```

#### String Quotes
```python
# ✅ GOOD: Double quotes for strings
message = "Hello, world!"

# ✅ GOOD: Single quotes for contractions or apostrophes
error_msg = "Don't do that"

# ❌ BAD: Inconsistent
message = "Hello, world!'
```

## Code Formatting with Black

### Black Configuration

Use Black with these settings:
- **Line length**: 88 characters
- **Target Python version**: 3.10+
- **String normalization**: Yes

### Running Black

```bash
# Format specific file
black infrastructure/core/config_loader.py

# Format directory
black infrastructure/core/

# Check formatting without changing files
black --check infrastructure/

# Format entire project
black .
```

### Black Integration

Add to `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
  | htmlcov
  | __pycache__
)/
'''
```

## Import Sorting with isort

### isort Configuration

```python
# ✅ GOOD: isort maintains import order
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger
```

### isort Settings

Add to `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["infrastructure", "project"]
known_third_party = ["numpy", "pandas", "pytest"]
```

### Running isort

```bash
# Sort imports in file
isort infrastructure/core/config_loader.py

# Sort imports in directory
isort infrastructure/core/

# Check without changing
isort --check-only infrastructure/
```

## Linting with flake8

### flake8 Configuration

```ini
# .flake8 or setup.cfg
[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    .tox,
    htmlcov
per-file-ignores =
    __init__.py:F401
    tests/*:S101
```

### Running flake8

```bash
# Lint specific file
flake8 infrastructure/core/config_loader.py

# Lint directory
flake8 infrastructure/core/

# Lint entire project
flake8 .
```

## Pre-commit Hooks

### pre-commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=88"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Installing pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## Docstring Standards

### Google Style Docstrings

```python
def process_data(data: List[Dict], threshold: float = 0.5) -> Dict[str, Any]:
    """Process input data and filter based on threshold.

    This function takes raw data, applies filtering criteria,
    and returns processed results with statistics.

    Args:
        data: List of dictionaries containing data points.
            Each dict should have 'value' and 'category' keys.
        threshold: Minimum value threshold for filtering.
            Values below this are excluded. Defaults to 0.5.

    Returns:
        Dictionary containing:
        - 'filtered_data': List of filtered data points
        - 'statistics': Dict with count, mean, std stats
        - 'excluded_count': Number of excluded items

    Raises:
        ValueError: If data is empty or threshold is invalid.
        TypeError: If data format is incorrect.

    Example:
        >>> data = [{'value': 0.8, 'category': 'A'}, {'value': 0.3, 'category': 'B'}]
        >>> result = process_data(data, threshold=0.5)
        >>> result['filtered_data']
        [{'value': 0.8, 'category': 'A'}]
    """
```

### NumPy Style Docstrings

```python
def process_data(data, threshold=0.5):
    """Process input data and filter based on threshold.

    Parameters
    ----------
    data : list of dict
        List of dictionaries containing data points.
        Each dict should have 'value' and 'category' keys.
    threshold : float, optional
        Minimum value threshold for filtering. Default is 0.5.

    Returns
    -------
    dict
        Dictionary containing:
        - 'filtered_data': List of filtered data points
        - 'statistics': Dict with count, mean, std stats
        - 'excluded_count': Number of excluded items

    Raises
    ------
    ValueError
        If data is empty or threshold is invalid.
    TypeError
        If data format is incorrect.

    Examples
    --------
    >>> data = [{'value': 0.8, 'category': 'A'}, {'value': 0.3, 'category': 'B'}]
    >>> result = process_data(data, threshold=0.5)
    >>> result['filtered_data']
    [{'value': 0.8, 'category': 'A'}]
    """
```

## File Organization Standards

### Module Structure

```python
# __init__.py - Public API exports
"""Data processing module."""

from .core import process_data, validate_input
from .config import DataConfig

__all__ = ["process_data", "validate_input", "DataConfig"]

# core.py - Main implementation
"""Core data processing functionality."""

from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def process_data(data):
    """Process data."""
    logger.debug(f"Processing {len(data)} items")
    # Implementation...

# config.py - Configuration (optional)
"""Configuration for data processing."""

from dataclasses import dataclass

@dataclass
class DataConfig:
    threshold: float = 0.5

# cli.py - CLI interface (optional)
"""Command-line interface."""

import argparse

def main():
    parser = argparse.ArgumentParser()
    # CLI implementation...
```

### Test File Organization

```python
# tests/test_module.py
"""Tests for module."""

import pytest
from module import function_to_test

def test_basic_functionality():
    """Test basic case."""
    result = function_to_test("input")
    assert result == "expected"

def test_edge_cases():
    """Test edge cases."""
    assert function_to_test("") is None
    assert function_to_test(None) is None

def test_error_conditions():
    """Test error handling."""
    with pytest.raises(ValueError):
        function_to_test("invalid")
```

## Best Practices

### Do's ✅

- ✅ **Use Black** for consistent formatting
- ✅ **Use isort** for import organization
- ✅ **Use flake8** for linting
- ✅ **Use pre-commit hooks** to automate checks
- ✅ **Follow PEP 8** guidelines
- ✅ **Use descriptive names** for variables and functions
- ✅ **Keep functions small** (under 50 lines)
- ✅ **Use consistent quotes** (double for strings)
- ✅ **Add docstrings** to all public functions
- ✅ **Use type hints** on all function signatures

### Don'ts ❌

- ❌ **Mix tabs and spaces** for indentation
- ❌ **Use lines longer than 88 characters**
- ❌ **Import with wildcards** (`from module import *`)
- ❌ **Use single-letter variable names** (except in comprehensions)
- ❌ **Skip blank lines** between logical sections
- ❌ **Use inconsistent naming** (mix camelCase and snake_case)
- ❌ **Hardcode magic numbers** without constants
- ❌ **Skip error handling** in user-facing functions
- ❌ **Use print()** instead of logging
- ❌ **Commit unformatted code**

## Tool Integration

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm Settings

- **Editor → Code Style → Python**: Set line length to 88
- **Tools → Black**: Enable with line length 88
- **Tools → External Tools**: Configure isort and flake8

## Enforcement

### CI/CD Checks

Add to GitHub Actions workflow:

```yaml
- name: Code Quality Checks
  run: |
    black --check .
    isort --check-only .
    flake8 .
    mypy .
```

### Development Workflow

1. **Write code** following style guidelines
2. **Run pre-commit** to format and lint
3. **Fix any issues** flagged by tools
4. **Run tests** to ensure functionality
5. **Commit** with confidence

## See Also

- [type_hints_standards.md](type_hints_standards.md) - Type annotation patterns
- [testing_standards.md](testing_standards.md) - Testing patterns and coverage
- [error_handling.md](error_handling.md) - Exception handling patterns
- [python_logging.md](python_logging.md) - Logging standards
- [infrastructure_modules.md](infrastructure_modules.md) - Module development standards
- [../docs/best-practices/BEST_PRACTICES.md](../docs/best-practices/BEST_PRACTICES.md) - Code quality best practices

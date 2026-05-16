# Code Style and Formatting Standards

## Overview

Consistent code formatting ensures readability, maintainability, and reduces merge conflicts. All Python code must follow these standards.

**Automation**: CI and local hooks enforce **Ruff** (lint, format, import sorting) and **mypy** on `infrastructure/` and `projects/*/src/`. Mirror commands live in root [`CLAUDE.md`](../../CLAUDE.md); hook IDs are declared in [`/.pre-commit-config.yaml`](../../.pre-commit-config.yaml).

## Python Code Style (PEP 8)

### Core PEP 8 Rules

#### Line Length
```python
# ✅ GOOD: Under 88 characters (Ruff default line length)
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

from infrastructure.core.logging.utils import get_logger
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

## Formatting and linting (Ruff)

Ruff subsumes the roles historically filled by separate formatters (Black), import sorters (isort), and many flake8 rules. Configuration lives under **`[tool.ruff]`** in the repository root **`pyproject.toml`**.

### Commands (CI parity)

```bash
uvx ruff check infrastructure/ projects/*/src/ --fix
uvx ruff format infrastructure/ projects/*/src/
uv run mypy infrastructure/ projects/*/src/
```

### Line length

Keep wrapping aligned with the **88**-character default unless `pyproject.toml` overrides Ruff.

#### Legacy tooling (optional locally)

Black, isort, and flake8 are **not** the CI source of truth for this repository; use them only if you intentionally duplicate checks outside Ruff.

## Pre-commit Hooks

### pre-commit Configuration

The repository ships **[`.pre-commit-config.yaml`](../../.pre-commit-config.yaml)** at the repo root. **Do not** paste alternate Black/isort/flake8-only configs here — extend the existing hooks instead.

Illustrative hook IDs (authoritative YAML lives at repo root):

```yaml
# See /.pre-commit-config.yaml — commit-stage hooks include:
#   ruff-ci  → uvx ruff check … && uvx ruff format …
#   mypy-ci  → uv run mypy …
```

### Installing pre-commit

```bash
# Install pre-commit
uv tool install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Run specific hook (see .pre-commit-config.yaml for ids)
pre-commit run ruff-ci --all-files
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

from infrastructure.core.logging.utils import get_logger

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

- ✅ **Use Ruff** (`uvx ruff check`, `uvx ruff format`) for lint/format/import sorting — CI parity
- ✅ **Use mypy** (`uv run mypy`) on `infrastructure/` and `projects/*/src/`
- ✅ **Use pre-commit hooks** (`ruff-ci`, `mypy-ci`) to automate checks
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
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "python.analysis.typeCheckingMode": "basic"
}
```

Use **`uv run mypy`** from the terminal for CI-parity typing; enable **mypy** or **basedpyright** in the IDE if you want inline diagnostics.

### PyCharm / IntelliJ

- **Editor → Code Style → Python**: Line length **88** to match Ruff.
- Enable **Ruff** plugin (or configure external tool `uvx ruff`) for format/on-save.
- Run **`uv run mypy`** as an external tool or use bundled typing support.

## Enforcement

### CI/CD Checks

Mirror **[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)** `lint` job locally:

```bash
uvx ruff check infrastructure/ projects/*/src/
uvx ruff format --check infrastructure/ projects/*/src/
uv run mypy infrastructure/ projects/*/src/
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
- [docs/best-practices/best-practices.md](../best-practices/best-practices.md) - Code quality best practices

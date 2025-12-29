# Development Workflow Guide

This guide provides a complete, step-by-step workflow for developing in the project, integrating all development standards and best practices.

## Overview

The development workflow follows a structured approach that ensures code quality, comprehensive testing, and proper documentation. All development must follow the standards outlined in the `.cursorrules/` directory.

## Development Standards Integration

This workflow integrates the following development standards:

**Core Standards:**
- [`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md) - Git workflow and commit standards
- [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing patterns and coverage standards
- [`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md) - Documentation writing guide
- [`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md) - Code formatting and style standards

**Supporting Standards:**
- [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) - Refactoring standards
- [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) - Error handling patterns
- [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) - Logging standards
- [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) - Type annotation patterns

## Workflow Phases

### Phase 1: Preparation

#### 1.1 Set Up Development Environment

```bash
# Ensure you're in the project directory
cd projects/project

# Activate virtual environment (if using one)
# source venv/bin/activate

# Verify environment
python3 --version
which python3
```

#### 1.2 Create Feature Branch

Follow [`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md) standards:

```bash
# Update main branch
git checkout develop
git pull origin develop

# Create feature branch with proper naming
git checkout -b feature/add-new-analysis-function

# Verify branch
git branch
```

### Phase 2: Development

#### 2.1 Plan Changes

**Before writing code:**
- [ ] Identify which layer (infrastructure vs project) the change belongs to
- [ ] Review relevant `.cursorrules/` standards
- [ ] Plan with thin orchestrator pattern
- [ ] Consider testing requirements (90% project, 60% infrastructure coverage)

#### 2.2 Write Code

**Code Standards** ([`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md)):

```python
# ✅ GOOD: Follow standards
from pathlib import Path
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def process_data(data: list[dict], output_path: Path) -> dict[str, Any]:
    """Process data according to project requirements.

    Args:
        data: Input data to process
        output_path: Path for output files

    Returns:
        Processing results dictionary

    Raises:
        ValueError: If data validation fails
    """
    logger.info(f"Processing {len(data)} items")

    # Implementation following standards
    pass
```

**Key Requirements:**
- [ ] Type hints on all public APIs
- [ ] Comprehensive docstrings
- [ ] Proper import organization
- [ ] Consistent naming (snake_case for functions/variables)
- [ ] Error handling with custom exceptions

#### 2.3 Write Tests First (TDD)

Follow [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md):

```python
# ✅ GOOD: Test-driven development
import pytest
from pathlib import Path
import tempfile

def test_process_data_basic():
    """Test basic data processing functionality."""
    # Arrange
    test_data = [{"id": 1, "value": 10}, {"id": 2, "value": 20}]

    # Act
    with tempfile.TemporaryDirectory() as tmpdir:
        result = process_data(test_data, Path(tmpdir))

    # Assert
    assert "processed_count" in result
    assert result["processed_count"] == 2
    assert result["success"] is True

def test_process_data_validation():
    """Test data validation."""
    invalid_data = []  # Empty data

    with pytest.raises(ValueError):
        process_data(invalid_data, Path("/tmp"))
```

**Testing Requirements:**
- [ ] Write tests before implementation (TDD)
- [ ] No mocks - use real data
- [ ] Cover edge cases and error conditions
- [ ] Achieve required coverage (90% project, 60% infrastructure)

#### 2.4 Format Code

Use automated formatting ([`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md)):

```bash
# Format with Black
black src/your_module.py tests/test_your_module.py

# Sort imports with isort
isort src/your_module.py tests/test_your_module.py

# Lint with flake8
flake8 src/your_module.py tests/test_your_module.py

# Type check with mypy
mypy src/your_module.py
```

### Phase 3: Validation

#### 3.1 Run Tests

```bash
# Run specific tests
pytest tests/test_your_module.py -v

# Run with coverage
pytest tests/test_your_module.py --cov=src.your_module --cov-report=html

# Run all project tests
pytest tests/ --cov=src --cov-fail-under=90

# Open coverage report
open htmlcov/index.html
```

#### 3.2 Validate Code Quality

```bash
# Check formatting
black --check src/your_module.py
isort --check-only src/your_module.py

# Lint code
flake8 src/your_module.py

# Type check
mypy src/your_module.py

# Verify no mocks in tests
python3 ../../scripts/verify_no_mocks.py tests/
```

#### 3.3 Integration Testing

```bash
# Test script integration
python3 scripts/your_script.py --dry-run

# Test with infrastructure
python3 -m infrastructure.validation.cli markdown manuscript/ --strict
```

### Phase 4: Documentation

#### 4.1 Update Documentation

Follow [`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md):

**Update AGENTS.md:**
```markdown
## New Feature: Data Processing

Added `process_data()` function to `src/data_processing.py`:

- Validates input data structure
- Processes items with error handling
- Generates output files in standard format
- Comprehensive test coverage (95%)

### Usage Example

```python
from data_processing import process_data

result = process_data(data, output_path)
print(f"Processed {result['processed_count']} items")
```
```

**Update README.md if needed:**
- Add new commands to common commands section
- Update quick start examples
- Add new feature highlights

#### 4.2 Validate Documentation

```bash
# Check markdown validation
python3 -m infrastructure.validation.cli markdown docs/ --strict

# Check cross-references
python3 scripts/manuscript_preflight.py --strict
```

### Phase 5: Commit and Push

#### 5.1 Commit Standards

Follow [`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md):

```bash
# Stage changes
git add src/your_module.py
git add tests/test_your_module.py
git add docs/AGENTS.md

# Commit with proper format
git commit -m "feat(data_processing): add process_data function

Add new process_data() function to src/data_processing.py
- Validates input data with comprehensive error handling
- Processes data items with logging
- Generates standardized output files
- Includes comprehensive tests (95% coverage)
- Updates documentation in AGENTS.md

Resolves #123"
```

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### 5.2 Push Changes

```bash
# Push feature branch
git push origin feature/add-new-analysis-function

# Create pull request
# Include description following PR template
```

## Common Development Tasks

### Adding a New Analysis Function

```bash
# 1. Create feature branch
git checkout -b feature/add-convergence-analysis

# 2. Write tests first
vim tests/test_analysis.py
# Implement test cases

# 3. Implement function
vim src/analysis.py
# Add function with type hints and docstring

# 4. Run tests
pytest tests/test_analysis.py --cov=src.analysis

# 5. Format and validate
black src/analysis.py tests/test_analysis.py
isort src/analysis.py tests/test_analysis.py
flake8 src/analysis.py tests/test_analysis.py

# 6. Update docs
vim docs/AGENTS.md
# Add function documentation

# 7. Commit
git add .
git commit -m "feat(analysis): add convergence analysis function

Add analyze_convergence() to src/analysis.py
- Computes convergence metrics for optimization runs
- Handles edge cases (constant sequences, etc.)
- Comprehensive test coverage
- Documentation updated"
```

### Modifying Existing Code

```bash
# 1. Create feature branch
git checkout -b refactor/improve-error-handling

# 2. Update tests first
vim tests/test_existing.py
# Add tests for new error conditions

# 3. Modify implementation
vim src/existing.py
# Improve error handling following standards

# 4. Run full test suite
pytest tests/ --cov=src

# 5. Update docs if API changed
vim docs/AGENTS.md

# 6. Commit
git commit -m "refactor(error_handling): improve validation error messages

BREAKING CHANGE: ValidationError now includes context field

- Add context information to validation errors
- Improve error messages with specific details
- Update all error handling code
- Tests updated for new error format"
```

### Infrastructure Development

```bash
# 1. Work in infrastructure directory
cd ../../infrastructure

# 2. Create feature branch
git checkout -b feature/add-validation-module

# 3. Follow infrastructure standards
# See .cursorrules/infrastructure_modules.md

# 4. Implement with 60% coverage requirement
pytest tests/infrastructure/test_new_module.py --cov=infrastructure.new_module --cov-fail-under=60

# 5. Update infrastructure docs
vim infrastructure/AGENTS.md
```

## Quality Gates

### Pre-Commit Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] Code formatted (`black --check . && isort --check-only .`)
- [ ] Linting passes (`flake8 .`)
- [ ] Type checking passes (`mypy .`)
- [ ] No mocks in tests (`verify_no_mocks.py`)
- [ ] Documentation updated and validates
- [ ] Commit message follows standards

### Pull Request Checklist

- [ ] Feature branch up-to-date with develop
- [ ] All CI checks pass
- [ ] Code review completed
- [ ] Documentation reviewed
- [ ] Tests reviewed
- [ ] Breaking changes documented
- [ ] Migration guide provided (if needed)

## Troubleshooting

### Test Failures

```bash
# Debug failing test
pytest tests/test_module.py::test_function -v -s

# Run with coverage to see uncovered lines
pytest tests/test_module.py --cov=src.module --cov-report=html
open htmlcov/index.html
```

### Import Issues

```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Test imports
python3 -c "from src.module import function; print('Import OK')"
```

### Documentation Issues

```bash
# Validate markdown
python3 -m infrastructure.validation.cli markdown docs/ --strict

# Check cross-references
python3 scripts/manuscript_preflight.py
```

## Integration with CI/CD

The workflow integrates with automated checks:

### GitHub Actions Workflow

```yaml
name: CI/CD
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e .[dev]

      - name: Format check
        run: |
          black --check .
          isort --check-only .

      - name: Lint
        run: flake8 .

      - name: Type check
        run: mypy .

      - name: Test
        run: pytest --cov=. --cov-fail-under=90

      - name: Validate docs
        run: python3 -m infrastructure.validation.cli markdown docs/
```

## Best Practices

### Development Habits

1. **Always write tests first** - TDD ensures testable code
2. **Run tests frequently** - Catch issues early
3. **Format code automatically** - Don't manually format
4. **Update docs immediately** - Don't let docs drift
5. **Commit small, focused changes** - Easier to review and revert
6. **Use feature branches** - Keep main branch stable
7. **Review your own code** - Self-review before PR

### Code Quality

1. **Follow the standards** - All `.cursorrules/` apply
2. **Write readable code** - Clear names, good structure
3. **Handle errors properly** - Use custom exceptions
4. **Log appropriately** - Use structured logging
5. **Document everything** - Public APIs need docs
6. **Type everything** - Type hints on all functions

### Testing Philosophy

1. **No mocks allowed** - Test real behavior
2. **Test behavior, not implementation** - Focus on what, not how
3. **Cover edge cases** - Error conditions, boundaries
4. **Keep tests fast** - Unit tests < 1 second
5. **Test integration points** - End-to-end workflows

## See Also

**Development Standards:**
- [`.cursorrules/git_workflow.md`](../../../.cursorrules/git_workflow.md) - Git workflow and commit standards
- [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing patterns and coverage standards
- [`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md) - Documentation writing guide
- [`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md) - Code formatting and style standards
- [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) - Refactoring standards
- [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) - Error handling patterns
- [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) - Logging standards
- [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) - Type annotation patterns

**Project Documentation:**
- [`AGENTS.md`](AGENTS.md) - Complete project documentation
- [`README.md`](README.md) - Quick reference
- [`infrastructure_usage.md`](infrastructure_usage.md) - Infrastructure integration guide
- [`refactor_playbook.md`](refactor_playbook.md) - Refactoring procedures
- [`testing_expansion_plan.md`](testing_expansion_plan.md) - Testing expansion roadmap

**Template Documentation:**
- [`../../docs/core/WORKFLOW.md`](../../docs/core/WORKFLOW.md) - General development workflow
- [`../../docs/best-practices/BEST_PRACTICES.md`](../../docs/best-practices/BEST_PRACTICES.md) - Code quality best practices
- [`../../AGENTS.md`](../../AGENTS.md) - Complete template documentation
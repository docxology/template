# Best Practices Compilation

> **Consolidated best practices** for the Research Project Template

**Quick Reference:** [Getting Started](GETTING_STARTED.md) | [Advanced Usage](ADVANCED_USAGE.md) | [Workflow](WORKFLOW.md)

This document consolidates best practices from across all documentation, providing a single reference for code organization, testing, documentation, build systems, collaboration, version control, and security.

## Code Organization

### Directory Structure

**Follow the established structure:**
```
project/
├── src/              # Business logic (comprehensively tested)
├── tests/            # Test suite (70% project, 49% infra minimum)
├── scripts/          # Thin orchestrators
├── manuscript/       # Research sections
├── docs/             # Documentation
├── repo_utilities/   # Build tools
└── output/           # Generated files (disposable)
```

**Best Practices:**
- Keep `src/` focused on business logic
- Use `scripts/` only for orchestration
- Maintain clear separation of concerns
- Follow the thin orchestrator pattern

### Module Organization

**Organize modules logically:**
- Group related functionality
- Use clear naming conventions
- Maintain single responsibility
- Keep modules focused and cohesive

**Example:**
```python
# Good: Clear module purpose
# src/statistics.py - Statistical functions
# src/visualization.py - Plotting functions
# src/data_processing.py - Data manipulation

# Bad: Mixed concerns
# src/utils.py - Everything mixed together
```

### Import Patterns

**Use consistent import patterns:**
```python
# Standard library
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
import numpy as np
import matplotlib.pyplot as plt

# Local (src/)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from example import add_numbers, calculate_average
```

**Best Practices:**
- Group imports: stdlib, third-party, local
- Use absolute imports when possible
- Avoid circular dependencies
- Document import requirements

## Testing

### Test Coverage

**Maintain comprehensive coverage:**
- **Project code**: 70% minimum (currently achieving 99.88%)
- **Infrastructure**: 49% minimum (currently achieving 55.89%)
- Test all critical code paths
- Include edge cases
- Test error handling

**Coverage Requirements:**
```bash
# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Verify coverage meets requirements
# Look for lines marked ">>>>>" (missing coverage)
```

### Test Organization

**Organize tests by module:**
```
tests/
├── test_example.py
├── test_quality_checker.py
├── test_reproducibility.py
└── ...
```

**Best Practices:**
- One test file per module
- Clear test names: `test_function_name_scenario`
- Use fixtures for setup
- Keep tests independent

### Test-Driven Development

**Follow TDD workflow:**
1. Write test first (RED)
2. Implement minimal code (GREEN)
3. Refactor (REFACTOR)
4. Repeat

**Benefits:**
- Ensures code works before writing
- Drives good design
- Provides documentation
- Prevents regressions

### Real Data Testing

**Use real data, not mocks:**
```python
# Good: Real data
def test_calculate_average():
    data = [1.0, 2.0, 3.0, 4.0]
    result = calculate_average(data)
    assert result == 2.5

# Bad: Mocked behavior
@patch('module.function')
def test_calculate_average(mock_func):
    mock_func.return_value = 2.5
    # Doesn't test actual behavior
```

**Best Practices:**
- Use deterministic test data
- Set fixed random seeds
- Create realistic test cases
- Test actual behavior, not mocks

## Documentation

### Code Documentation

**Document all public APIs:**
```python
def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """Calculate descriptive statistics for data.
    
    Args:
        data: List of numerical values
        
    Returns:
        Dictionary with statistics:
        - mean: Average value
        - std: Standard deviation
        - min: Minimum value
        - max: Maximum value
        
    Raises:
        ValueError: If data is empty
        
    Example:
        >>> calculate_statistics([1, 2, 3, 4])
        {'mean': 2.5, 'std': 1.29, 'min': 1.0, 'max': 4.0}
    """
    if not data:
        raise ValueError("Data cannot be empty")
    # Implementation...
```

**Best Practices:**
- Use docstrings for all functions
- Include parameter descriptions
- Document return values
- Provide usage examples
- Note exceptions

### Documentation Maintenance

**Keep documentation current:**
- Update docs when code changes
- Sync examples with implementation
- Review documentation regularly
- Remove outdated information

**Documentation Standards:**
- Clear and concise
- Accurate and current
- Comprehensive coverage
- Well-organized structure

## Build System

### Build Pipeline

**Follow the established pipeline:**
1. Clean outputs
2. Run tests (verify coverage requirements met)
3. Execute scripts
4. Validate markdown
5. Generate glossary
6. Build PDFs
7. Validate outputs

**Best Practices:**
- Run full pipeline before commits
- Fix issues immediately
- Keep build times reasonable
- Monitor build performance

### Build Optimization

**Optimize build performance:**
- Use parallel execution
- Enable caching
- Skip unnecessary steps
- Optimize slow stages

**See:** [Performance Optimization Guide](PERFORMANCE_OPTIMIZATION.md)

### Build Validation

**Validate builds:**
- Check test coverage
- Verify outputs
- Validate PDFs
- Check integrity

**Automation:**
```bash
# Automated validation
python3 scripts/run_all.py

# Or validate outputs directly
python3 scripts/04_validate_output.py
```

## Collaboration

### Code Review

**Review checklist:**
- [ ] Code follows style guidelines
- [ ] Tests pass with required coverage (70% project, 49% infra)
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Follows thin orchestrator pattern

### Communication

**Best Practices:**
- Clear commit messages
- Descriptive pull requests
- Respond to feedback
- Document decisions
- Share knowledge

### Contribution Process

**Follow contribution guidelines:**
1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

**See:** [Contributing Guide](CONTRIBUTING.md)

## Version Control

### Git Workflow

**Use consistent workflow:**
```bash
# Feature development
git checkout -b feature/new-feature
# Make changes
git commit -m "feat: add new feature"
git push origin feature/new-feature

# Bug fixes
git checkout -b fix/issue-description
# Fix bug
git commit -m "fix: resolve issue"
git push origin fix/issue-description
```

**Best Practices:**
- Use descriptive branch names
- Write clear commit messages
- Keep commits focused
- Review before pushing

### Commit Messages

**Follow conventional commits:**
```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
refactor: restructure code
style: format code
chore: maintenance tasks
```

**Best Practices:**
- Use present tense
- Be specific and clear
- Reference issues when applicable
- Keep messages concise

### Branching Strategy

**Use feature branches:**
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates

## Security

### Dependency Management

**Keep dependencies updated:**
```bash
# Regular updates
uv sync --upgrade

# Check for vulnerabilities
uv audit
```

**Best Practices:**
- Update regularly
- Review dependency changes
- Use version constraints
- Monitor security advisories

### Secrets Management

**Never commit secrets:**
- Use environment variables
- Store secrets securely
- Use `.gitignore` for sensitive files
- Rotate secrets regularly

**Configuration:**
```bash
# Use environment variables
export AUTHOR_EMAIL="user@example.com"
export AUTHOR_ORCID="0000-0000-0000-0000"

# Not in code
# AUTHOR_EMAIL = "user@example.com"  # BAD
```

### Access Control

**Limit access appropriately:**
- Use least privilege principle
- Review access regularly
- Use secure authentication
- Monitor access logs

## Thin Orchestrator Pattern

### Script Requirements

**Scripts MUST:**
- Import from `src/` modules
- Use `src/` methods for computation
- Handle only I/O, visualization, orchestration
- Include proper error handling
- Print output paths

**Scripts MUST NOT:**
- Implement mathematical algorithms
- Duplicate business logic
- Contain complex computations
- Define new data structures

**Example:**
```python
# Good: Thin orchestrator
from example import calculate_average
data = load_data()
avg = calculate_average(data)  # Uses src/ method
plot_results(data, avg)

# Bad: Business logic in script
def calculate_average(data):
    return sum(data) / len(data)  # Duplicates src/ logic
```

### Integration Patterns

**Proper integration:**
```python
# Ensure src/ on path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import from src/
from module import function

# Use src/ methods
result = function(input_data)

# Script handles I/O
save_output(result, output_path)
```

## Performance

### Code Performance

**Optimize critical paths:**
- Profile before optimizing
- Focus on bottlenecks
- Use appropriate data structures
- Consider algorithm complexity

### Build Performance

**Optimize build times:**
- Use parallel execution
- Enable caching
- Skip unnecessary steps
- Monitor performance

**See:** [Performance Optimization Guide](PERFORMANCE_OPTIMIZATION.md)

## Quality Assurance

### Code Quality

**Maintain high standards:**
- Follow PEP 8 style
- Use type hints
- Write clear code
- Review regularly

### Testing Quality

**Comprehensive testing:**
- Coverage requirements: 70% project, 49% infrastructure
- Test edge cases
- Test error paths
- Test integration

### Documentation Quality

**High-quality documentation:**
- Accurate and current
- Clear and concise
- Comprehensive coverage
- Well-organized

## Anti-Patterns to Avoid

### Code Organization

**Avoid:**
- Business logic in scripts
- Duplicated code
- Mixed concerns
- Circular dependencies

### Testing

**Avoid:**
- Mocking everything
- Missing edge cases
- Incomplete coverage
- Brittle tests

### Documentation

**Avoid:**
- Outdated information
- Unclear explanations
- Missing examples
- Poor organization

## Summary

Key best practices:

1. **Code Organization** - Clear structure, separation of concerns
2. **Testing** - Comprehensive coverage, real data, TDD
3. **Documentation** - Current, accurate, comprehensive
4. **Build System** - Automated, validated, optimized
5. **Collaboration** - Clear communication, code review
6. **Version Control** - Consistent workflow, clear commits
7. **Security** - Updated dependencies, secure secrets
8. **Thin Orchestrator** - Scripts use src/ methods
9. **Performance** - Optimized code and builds
10. **Quality** - High standards throughout

For detailed guidance, see:
- [Architecture](ARCHITECTURE.md) - System design
- [Workflow](WORKFLOW.md) - Development process
- [Thin Orchestrator Summary](THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

---

**Related Documentation:**
- [Getting Started](GETTING_STARTED.md) - Basic practices
- [Advanced Usage](ADVANCED_USAGE.md) - Advanced practices
- [Workflow](WORKFLOW.md) - Development workflow
- [Contributing](CONTRIBUTING.md) - Contribution practices



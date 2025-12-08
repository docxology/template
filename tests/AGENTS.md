# tests/ - Test Suite

## Purpose

The `tests/` directory ensures **comprehensive test coverage** for all modules (70% project minimum, 49% infrastructure minimum). Tests validate that core business logic works correctly using real data and real computations.

## Testing Philosophy

### Test-Driven Development (TDD)
1. Write tests first
2. Implement functionality in `project/src/` (project-specific) or `infrastructure/` (reusable)
3. Run tests until they pass
4. Refactor with confidence

### No Mocks Policy
- **Always use real data** and real computations
- **No mock methods** - test actual behavior
- Create temporary directories/files for testing
- Use deterministic seeds for reproducibility
- Test real integration between components

### Network-Dependent Modules
For modules requiring external services (LLM, Literature, Publishing):
- **Pure logic tests**: Test configuration, validation, context management without network
- **Integration tests**: Mark with `@pytest.mark.requires_ollama` (or similar)
- **Skip gracefully**: Tests auto-skip when service unavailable
- Run integration tests with: `pytest -m requires_ollama`
- Skip integration tests with: `pytest -m "not requires_ollama"`

### Coverage Requirements
- All project/src/ modules must meet 90% minimum coverage (currently 98.03%)
- Infrastructure modules must meet 60% minimum coverage (currently 66.76%)
- Tests must pass before PDF generation proceeds
- Coverage validated by `pyproject.toml` configuration (`[tool.coverage.*]` sections)
- No code ships without tests

## Test Organization

Tests are organized to mirror `infrastructure/` module structure:

```
tests/
├── conftest.py              # Test configuration (adds infrastructure to path)
├── infrastructure/          # Infrastructure module tests
│   ├── conftest.py
│   ├── build/               # Build module tests
│   │   ├── test_build_verifier.py
│   │   ├── test_quality_checker.py
│   │   └── test_reproducibility.py
│   ├── core/                # Core module tests
│   │   ├── test_config_loader.py
│   │   ├── test_exceptions.py
│   │   └── test_logging_utils.py
│   ├── documentation/       # Documentation module tests
│   │   ├── test_figure_manager.py
│   │   ├── test_image_manager.py
│   │   ├── test_glossary_gen.py
│   │   └── test_markdown_integration.py
│   ├── literature/          # Literature module tests
│   │   ├── test_core.py
│   │   ├── test_api.py
│   │   ├── test_config.py
│   │   ├── test_cli.py
│   │   └── test_integration.py
│   ├── llm/                 # LLM module tests
│   │   ├── test_core.py
│   │   ├── test_context.py
│   │   ├── test_templates.py
│   │   ├── test_config.py
│   │   └── test_validation.py
│   ├── publishing/          # Publishing module tests
│   │   ├── test_publishing.py
│   │   ├── test_api.py
│   │   └── test_cli.py
│   ├── rendering/           # Rendering module tests
│   │   ├── test_core.py
│   │   ├── test_latex_utils.py
│   │   ├── test_renderers.py
│   │   ├── test_config.py
│   │   ├── test_poster_renderer.py
│   │   └── test_cli.py
│   ├── scientific/          # Scientific module tests
│   │   └── test_scientific_dev.py
│   └── validation/          # Validation module tests
│       ├── test_markdown_validator.py
│       ├── test_pdf_validator.py
│       ├── test_integrity.py
│       ├── test_check_links.py
│       ├── test_doc_scanner.py
│       ├── test_repo_scanner.py
│       └── test_cli.py
└── integration/             # Integration tests
    ├── test_module_interoperability.py
    ├── test_figure_equation_citation.py
    ├── test_output_copying.py
    └── test_edge_cases_and_error_paths.py
```

## conftest.py

Configures test environment:
```python
"""Pytest configuration for template infrastructure tests."""
import os
import sys

# Force headless backend for matplotlib in tests
os.environ.setdefault("MPLBACKEND", "Agg")

# Add paths for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add ROOT to path so we can import infrastructure as a package
# Ensure ROOT is FIRST in path to avoid shadowing by tests/infrastructure
if ROOT in sys.path:
    sys.path.remove(ROOT)
sys.path.insert(0, ROOT)

# Remove tests/ directory from path if present to prevent shadowing
TESTS_DIR = os.path.join(ROOT, "tests")
if TESTS_DIR in sys.path:
    sys.path.remove(TESTS_DIR)

# Add src/ to path for scientific modules (if it exists)
SRC = os.path.join(ROOT, "src")
if os.path.exists(SRC) and SRC not in sys.path:
    sys.path.insert(0, SRC)

# Add project/src/ to path for project modules
PROJECT_SRC = os.path.join(ROOT, "project", "src")
if os.path.exists(PROJECT_SRC) and PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)
```

This allows tests to import directly:
```python
from infrastructure.core.config_loader import load_config  # Infrastructure imports
from project.src.example import add_numbers  # Project imports
```

## Test Categories

### Infrastructure Module Tests
Test individual infrastructure modules in `tests/infrastructure/`:
- **Build Module** (`tests/infrastructure/build/`)
  - `test_build_verifier.py` - Build verification and validation
  - `test_quality_checker.py` - Document quality analysis
  - `test_reproducibility.py` - Build reproducibility tracking
  
- **Core Module** (`tests/infrastructure/core/`)
  - `test_config_loader.py` - Configuration file handling
  - `test_exceptions.py` - Custom exception handling
  - `test_logging_utils.py` - Logging utilities
  - `test_checkpoint.py` - Checkpoint/resume functionality
  - `test_progress.py` - Progress tracking
  - `test_retry.py` - Retry mechanisms

- **Documentation Module** (`tests/infrastructure/documentation/`)
  - `test_figure_manager.py` - Figure management and registration
  - `test_image_manager.py` - Image handling in markdown
  - `test_glossary_gen.py` - API documentation generation
  - `test_markdown_integration.py` - Markdown processing integration

- **Validation Module** (`tests/infrastructure/validation/`)
  - `test_markdown_validator.py` - Markdown validation
  - `test_pdf_validator.py` - PDF validation
  - `test_integrity.py` - Integrity verification
  - `test_repo_scanner.py` - Repository scanning and validation

### Project Module Tests
Test project-specific code in `project/tests/`:
- Unit tests for `project/src/` modules (see `project/tests/AGENTS.md`)
- Integration tests in `project/tests/integration/`
  - `test_integration_pipeline.py` - Full analysis pipeline
  - `test_example_figure.py` - Figure generation integration
  - `test_generate_research_figures.py` - Research figure pipeline

### Integration Tests
Test cross-module interactions in `tests/integration/`:
- `test_edge_cases_and_error_paths.py` - Edge cases and error handling
- `test_figure_equation_citation.py` - Figure/equation/citation handling
- `test_module_interoperability.py` - Cross-module integration validation (no mocks policy)
- `test_output_copying.py` - Output file handling and copying

## Running Tests

### All Tests with Coverage
```bash
# Using pytest directly (both infrastructure and project)
pytest tests/ --cov=infrastructure --cov=project/src --cov-report=term-missing --cov-report=html

# Using uv
uv run pytest tests/ --cov=infrastructure --cov=project/src --cov-report=html

# Verify coverage requirements
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=60
pytest project/tests/ --cov=project/src --cov-fail-under=90
```

### Specific Tests
```bash
# Infrastructure tests
pytest tests/infrastructure/core/test_config_loader.py -v

# Project tests
pytest project/tests/test_example.py -v

# Integration tests
pytest tests/integration/test_module_interoperability.py -v

# By pattern
pytest tests/ -k "test_config" -v
```

### Coverage Reports
```bash
# Terminal report with missing lines
pytest tests/ --cov=infrastructure --cov=project/src --cov-report=term-missing

# HTML report (opens in browser)
pytest tests/ --cov=infrastructure --cov=project/src --cov-report=html
open htmlcov/index.html

# Separate reports
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html --cov-fail-under=49
pytest project/tests/ --cov=project/src --cov-report=html --cov-fail-under=70
```

### Coverage Snapshot (latest)
- Project: **99.88%** (target 70%+)
- Infrastructure: **61.48%** (target 49%+)
- Total tests: **2175** (1855 infrastructure, 320 project)

Skip Ollama-dependent suites when needed:
```bash
pytest tests/ -m "not requires_ollama"
```

### Common Markers

Tests use pytest markers to indicate dependencies:

- `requires_ollama`: tests that need a running Ollama service
- `requires_zenodo`: tests that need Zenodo API credentials
- `requires_github`: tests that need GitHub API credentials  
- `requires_arxiv`: tests that need arXiv API credentials (optional)
- `requires_latex`: tests that need LaTeX installed (pdflatex or xelatex)
- `requires_network`: tests that need internet access
- `requires_credentials`: general marker for any external service credentials

**Skip tests without credentials:**
```bash
pytest tests/ -m "not requires_credentials"
```

**Run only specific service tests:**
```bash
pytest tests/ -m requires_zenodo
pytest tests/ -m requires_github
```

**See [docs/TESTING_WITH_CREDENTIALS.md](../docs/TESTING_WITH_CREDENTIALS.md) for credential setup.**

## Writing Tests

### Test Structure
```python
"""Tests for infrastructure/module_name.py or project/src/module_name.py"""
import pytest
from infrastructure.module_name import function_to_test
# or
from project.src.module_name import function_to_test

class TestFunctionName:
    """Test suite for function_to_test."""
    
    def test_basic_functionality(self):
        """Test basic usage."""
        result = function_to_test("input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case."""
        result = function_to_test("")
        assert result is None
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Fixtures for Temporary Files
```python
def test_with_temp_file(tmp_path):
    """Use pytest's tmp_path fixture."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    # Test your function
    result = process_file(test_file)
    
    assert result == expected
    # tmp_path automatically cleaned up
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Test doubling with multiple inputs."""
    assert double(input) == expected
```

## Test Coverage Details

### Current Coverage Status

**Project Modules** (`project/src/`): **99.88%** (Target: 70%+)
- All project-specific modules exceed the 90% minimum requirement
- Comprehensive test coverage ensures research code reliability

**Infrastructure Modules** (`infrastructure/`): **70.09%** (Target: 49%+)
- Exceeds the 60% minimum requirement
- Core modules have higher coverage
- Some CLI and advanced features have lower coverage (see `docs/COVERAGE_GAPS.md`)

### Coverage Configuration
`pyproject.toml` enforces coverage rules via `[tool.coverage.*]` sections:
```toml
[tool.coverage.run]
branch = true
source = ["infrastructure", "project/src"]

[tool.coverage.report]
fail_under = 70
show_missing = true
precision = 2
```

## Debugging Test Failures

### Verbose Output
```bash
pytest tests/ -v  # Verbose test names
pytest tests/ -vv  # Very verbose with diffs
pytest tests/ -s  # Show print statements
```

### Stop on First Failure
```bash
pytest tests/ -x  # Stop on first failure
pytest tests/ --maxfail=3  # Stop after 3 failures
```

### Run Failed Tests Only
```bash
pytest tests/ --lf  # Run last failed
pytest tests/ --ff  # Run failed first, then others
```

### Debugging with PDB
```python
def test_something():
    """Test with debugging."""
    result = function()
    import pdb; pdb.set_trace()  # Breakpoint
    assert result == expected
```

## Best Practices

### Do's
- ✅ Test all public APIs
- ✅ Use real data and computations
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Test one thing per test function
- ✅ Use fixtures for setup/teardown
- ✅ Document what each test validates

### Don'ts
- ❌ Use mock methods (test real behavior)
- ❌ Use MagicMock, mocker.patch, or unittest.mock
- ❌ Skip tests to fix coverage
- ❌ Test implementation details
- ❌ Use hardcoded file paths
- ❌ Leave commented-out tests
- ❌ Write tests that depend on order
- ❌ Test multiple things in one function

## Integration with Build System

### Automatic Execution
`scripts/01_run_tests.py` (orchestrated by `scripts/run_all.py`) automatically:
1. **Runs infrastructure tests** with 49% coverage requirement
2. **Runs project tests** with 70% coverage requirement
3. **Fails build** if tests don't pass or coverage requirements not met
4. **Generates coverage reports** (htmlcov/)
5. **Validates integration** between components

### Pre-commit Checks
Before committing code:
```bash
# Run all tests with coverage
pytest tests/ --cov=infrastructure --cov=project/src --cov-report=html

# Verify infrastructure coverage (60% minimum)
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=49

# Verify project coverage (90% minimum)
pytest project/tests/ --cov=project/src --cov-fail-under=70

# Check coverage report
open htmlcov/index.html
```

## Adding New Tests

### Checklist
1. Determine if code is project-specific (`project/src/`) or infrastructure (`infrastructure/`)
2. Create test file in appropriate location (`project/tests/` or `tests/infrastructure/`)
3. Import functions to test from correct module path
4. Write comprehensive test cases using real data (no mocks)
5. Ensure coverage requirements met (70% project, 49% infrastructure)
6. Run full test suite to verify
7. Update this documentation if needed

### Template
```python
"""Tests for infrastructure/new_module.py or project/src/new_module.py"""
import pytest
from infrastructure.new_module import new_function
# or
from project.src.new_module import new_function


class TestNewFunction:
    """Test suite for new_function."""
    
    def test_basic_usage(self):
        """Test basic functionality."""
        result = new_function("input")
        assert result == "expected"
    
    def test_edge_cases(self):
        """Test edge case handling."""
        assert new_function("") is None
        assert new_function(None) is None
    
    def test_error_conditions(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            new_function("invalid")


def test_integration_with_other_modules():
    """Test integration between modules."""
    # Test how new_function works with other src/ modules
    pass
```

## Credential-Based Testing

### Setup

Tests that require external service credentials (Zenodo, GitHub, arXiv) will automatically skip if credentials are not configured. To run these tests:

1. Copy credential templates:
   ```bash
   cp .env.example .env
   cp test_credentials.yaml.example test_credentials.yaml
   ```

2. Add your credentials to `.env`:
   ```bash
   ZENODO_SANDBOX_TOKEN=your_token
   GITHUB_TOKEN=your_token
   GITHUB_REPO=username/test-repo
   ```

3. Run tests (credential-dependent tests will run if configured):
   ```bash
   pytest tests/
   ```

### Credential Fixtures

The test suite provides credential fixtures via `tests/conftest.py`:

- `credential_manager` - CredentialManager instance
- `zenodo_credentials` - Zenodo API credentials (sandbox)
- `github_credentials` - GitHub API credentials
- `arxiv_credentials` - arXiv API credentials (optional)
- `skip_if_no_latex` - Skip if LaTeX not installed

**Example usage:**
```python
@pytest.mark.requires_zenodo
@pytest.mark.requires_network
def test_publish_to_zenodo(zenodo_credentials, tmp_path):
    # Real API test with automatic skip if no credentials
    from infrastructure.publishing.api import ZenodoClient
    client = ZenodoClient(access_token=zenodo_credentials["token"])
    # ... test with real API calls ...
```

### Security

- Never commit `.env` or `test_credentials.yaml` (in `.gitignore`)
- Always use Zenodo *sandbox* for tests, not production
- Tests automatically clean up artifacts (depositions, releases)
- Tokens should have minimum required scopes

See **[docs/TESTING_WITH_CREDENTIALS.md](../docs/TESTING_WITH_CREDENTIALS.md)** for complete setup guide.

## See Also

- [`conftest.py`](conftest.py) - Test configuration and fixtures
- [`../infrastructure/AGENTS.md`](../infrastructure/AGENTS.md) - Infrastructure module documentation
- [`../project/src/AGENTS.md`](../project/src/AGENTS.md) - Project module documentation
- [`../AGENTS.md`](../AGENTS.md) - System documentation
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow
- [`../docs/TESTING_WITH_CREDENTIALS.md`](../docs/TESTING_WITH_CREDENTIALS.md) - Credential configuration guide





# tests/ - Test Suite

## Purpose

The `tests/` directory ensures **comprehensive test coverage** for all modules (90% project minimum, 60% infrastructure minimum). Tests validate that core business logic works correctly using real data and real computations.

## Testing Philosophy

### Test-Driven Development (TDD)
1. Write tests first
2. Implement functionality in `projects/{name}/src/` (project-specific) or `infrastructure/` (reusable)
3. Run tests until they pass
4. Refactor with confidence

### ABSOLUTE PROHIBITION: No Mocks Policy

**🔄 CURRENT STATUS: MAJOR PROGRESS** - Significant infrastructure test fixes completed, LLM tests partially migrated to real HTTP calls.

**✅ COMPLETED FIXES:**
- **Project Test Imports**: Fixed `test_reporting.py` and `test_validation.py` import errors by updating conftest.py to add repository root to Python path
- **Checkpoint Tests**: Fixed directory existence expectations and permission testing for macOS compatibility
- **CLI Tests**: Updated subprocess test assertions to match actual output format and handle PYTHONPATH requirements
- **Logging Tests**: Removed syntax error and mock usage, eliminated unused Mock/patch imports
- **Validation Tests**: Fixed CLI test to pass manuscript directory as argument instead of relying on automatic discovery
- **Integration Tests**: Corrected type assertions for `verify_file_integrity` return values (dict vs list)
- **Bash Logging Tests**: Added ANSI color code stripping for proper output comparison
- **Output Copying Tests**: Updated missing file handling assertions to match current implementation labels

**🔄 LLM TESTS (PARTIALLY COMPLETE):**
- **✅ Fallback Logic**: Successfully migrated `test_query_fallback_on_connection_error` to use real HTTP calls with test server
- **⏳ Remaining**: 32 additional LLM tests need server modifications for edge cases (structured JSON parsing, streaming, model discovery, etc.)

**⏳ REMAINING PHASES:**
- Complete LLM test migration (HTTP testing with pytest-httpserver)
- Publishing module tests (Zenodo/arXiv/GitHub integration)
- Validation & Rendering (CLI and file operations)
- Supporting Infrastructure & QA

**NON-NEGOTIABLE REQUIREMENT**: Under no circumstances use `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework. All tests must use **real data** and **real computations only**.

**See `MOCK_ELIMINATION_GUIDE.md`** for systematic elimination plan.

This is a fundamental testing principle that ensures:
- Tests validate actual behavior, not mocked behavior
- Integration points are truly tested
- Code is tested in realistic conditions
- No false confidence from mocked tests

**ABSOLUTELY FORBIDDEN:**
- `MagicMock()`, `mocker.patch()`, `unittest.mock`
- Any form of dependency injection for testing
- Mocking external services or APIs
- Creating fake test data instead of real data

**ALWAYS USE REAL OPERATIONS:**
- Real data and real computations
- Create temporary directories/files for testing
- Use deterministic seeds for reproducibility
- Test real integration between components

### Implementation Examples

**LLM Testing with pytest-httpserver:**
```python
@pytest.fixture(scope="session")
def ollama_test_server():
    """Local HTTP test server mimicking Ollama API."""
    server = HTTPServer()
    server.expect_request("/api/chat").respond_with_json({
        "message": {"content": "Test response"}
    })
    yield server
    server.stop()

def test_llm_query(ollama_test_server):
    config = LLMConfig(base_url=ollama_test_server.url_for("/"))
    client = LLMClient(config)
    response = client.query("test")  # Real HTTP request
    assert "Test response" in response
```

**CLI Testing with Real Subprocess:**
```python
def test_cli_validation(tmp_path):
    # Create real test file
    pdf_file = tmp_path / "test.pdf"
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(pdf_file))
    c.drawString(100, 750, "Test")
    c.save()

    # Execute real CLI command
    result = subprocess.run([
        'python', '-m', 'infrastructure.validation.cli',
        'pdf', str(pdf_file)
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

**PDF Processing with Real Files:**
```python
def test_pdf_extraction(tmp_path):
    # Create real PDF
    pdf_file = tmp_path / "test.pdf"
    c = canvas.Canvas(str(pdf_file))
    c.drawString(100, 750, "Extracted content")
    c.save()

    # Test real PDF extraction
    text = extract_manuscript_text(str(pdf_file))
    assert "Extracted content" in text
```

### Network-Dependent Modules
For modules requiring external services (LLM, Literature, Publishing):
- **Pure logic tests**: Test configuration, validation, context management without network
- **Integration tests**: Mark with `@pytest.mark.requires_ollama` (or similar)
- **Skip gracefully**: Tests auto-skip when service unavailable
- Run integration tests with: `pytest -m requires_ollama`
- Skip integration tests with: `pytest -m "not requires_ollama"`

### Coverage Requirements
- All projects/{name}/src/ modules must meet 90% minimum coverage (currently 100% - perfect coverage!)
- Infrastructure modules must meet 60% minimum coverage (currently 83.33% - exceeds stretch goal!)
- Tests must pass before PDF generation proceeds
- Coverage validated by `pyproject.toml` configuration (`[tool.coverage.*]` sections)
- No code ships without tests

## Test Organization

Tests are organized to mirror `infrastructure/` module structure. Note: Multiple test files with suffixes like `_coverage`, `_full`, `_comprehensive` exist to achieve comprehensive test coverage across different scenarios and edge cases. These files are intentionally split rather than consolidated to ensure thorough validation of complex functionality:

```
tests/
├── conftest.py                          # Root test configuration and fixtures
├── infrastructure/                      # Infrastructure module tests
│   ├── conftest.py                      # Infrastructure test configuration
│   ├── test_project_discovery.py        # Project discovery and validation (284 lines)
│   ├── build/                           # Build system tests
│   │   ├── test_build_verifier.py       # Build verification (400 lines)
│   │   ├── test_build_verifier_*.py     # Additional build verifier tests
│   │   ├── test_quality_checker.py      # Document quality analysis (463 lines)
│   │   └── test_quality_checker_*.py    # Additional quality checker tests
│   │   └── test_reproducibility.py      # Environment tracking (427 lines)
│   │   └── test_reproducibility_*.py    # Additional reproducibility tests
│   ├── core/                            # Core utilities tests
│   │   ├── test_checkpoint.py           # Checkpoint/resume functionality
│   │   ├── test_config_cli_coverage.py  # Config CLI coverage
│   │   ├── test_config_loader.py        # Configuration loading
│   │   ├── test_credentials.py          # Credential management
│   │   ├── test_environment.py          # Environment handling
│   │   ├── test_exceptions.py           # Exception handling
│   │   ├── test_file_operations.py      # File operations
│   │   ├── test_logging_*.py            # Logging system tests
│   │   ├── test_performance.py          # Performance monitoring
│   │   ├── test_progress.py             # Progress tracking
│   │   ├── test_retry.py                # Retry mechanisms
│   │   └── test_script_discovery.py     # Script discovery
│   ├── documentation/                   # Documentation tools tests
│   │   ├── test_figure_manager.py       # Figure management and registration
│   │   ├── test_generate_glossary_cli.py # Glossary generation CLI
│   │   ├── test_glossary_gen.py         # API documentation generation (189 lines)
│   │   ├── test_image_manager.py        # Image handling in markdown
│   │   └── test_markdown_integration.py # Markdown processing integration
│   ├── llm/                             # LLM integration tests
│   │   ├── conftest.py                  # LLM test configuration
│   │   ├── test_cli.py                  # CLI interface
│   │   ├── test_config.py               # Configuration management
│   │   ├── test_context.py              # Conversation context
│   │   ├── test_context_engineering.py  # Context engineering
│   │   ├── test_core.py                 # Core LLM functionality
│   │   ├── test_llm_core_*.py           # Additional core tests (coverage/full)
│   │   ├── test_llm_review.py           # LLM manuscript review
│   │   ├── test_logging.py              # LLM logging
│   │   ├── test_ollama_utils.py         # Ollama client utilities
│   │   ├── test_prompts_*.py            # Prompt management
│   │   ├── test_response_saving.py      # Response saving
│   │   ├── test_review_generators.py    # Review generation
│   │   ├── test_streaming.py            # Streaming responses
│   │   ├── test_templates.py            # Research prompt templates
│   │   └── test_validation.py           # Input validation
│   ├── publishing/                      # Publishing tools tests
│   │   ├── test_api.py                  # Platform API clients
│   │   ├── test_cli.py                  # CLI interface
│   │   ├── test_publish_cli.py          # Publishing CLI
│   │   ├── test_publishing.py           # Publishing metadata (427 lines)
│   │   └── test_publishing_*             # Additional publishing tests (coverage/full/edge_cases)
│   ├── rendering/                       # Rendering pipeline tests
│   │   ├── conftest.py                  # Rendering test configuration
│   │   ├── test_cli.py                  # CLI interface
│   │   ├── test_config.py               # Rendering configuration
│   │   ├── test_core.py                 # Core rendering functionality
│   │   ├── test_latex_*.py              # LaTeX utilities and validation
│   │   ├── test_manuscript_*.py         # Manuscript handling
│   │   ├── test_pdf_renderer_*.py       # PDF rendering (core/coverage/full/additional)
│   │   ├── test_poster_renderer.py      # Scientific poster rendering
│   │   ├── test_render_*.py             # Render CLI and utilities
│   │   ├── test_renderers.py            # General rendering tests
│   │   ├── test_rendering_cli*.py       # CLI functionality (core/full)
│   │   ├── test_slides_renderer_*.py    # Presentation slides (core/coverage)
│   │   └── test_web_renderer_*.py       # Web/HTML rendering
│   ├── reporting/                       # Reporting and dashboard tests
│   │   ├── test_dashboard_generator.py  # Dashboard generation
│   │   ├── test_error_aggregator.py     # Error aggregation
│   │   ├── test_executive_reporter.py   # Executive reporting
│   │   ├── test_html_templates.py       # HTML template rendering
│   │   ├── test_manuscript_overview.py  # Manuscript overview generation
│   │   ├── test_output_reporter.py      # Output reporting
│   │   ├── test_pipeline_reporter.py    # Pipeline reporting
│   │   └── test_test_reporter.py        # Test result reporting
│   ├── scientific/                      # Scientific tools tests
│   │   ├── test_scientific_dev.py       # Scientific development utilities
│   │   └── test_scientific_dev_edge_cases.py # Edge case handling
│   └── validation/                      # Validation system tests
│       ├── test_check_links*.py         # Link validation (core/coverage/full/edge_cases)
│       ├── test_cli.py                  # CLI interface
│       ├── test_doc_scanner*.py         # Document scanning (core/coverage/full/phases)
│       ├── test_figure_validator.py     # Figure validation
│       ├── test_integrity*.py           # Integrity verification (core/edge_cases)
│       ├── test_markdown_validator.py   # Markdown validation
│       ├── test_output_validator.py     # Output validation
│       ├── test_pdf_validator.py        # PDF validation (328 lines)
│       ├── test_repo_scanner*.py        # Repository scanning (core/coverage/full/comprehensive/additional)
│       ├── test_validate_markdown_cli*.py # Markdown CLI (core/coverage/full/comprehensive)
│       ├── test_validate_pdf_cli*.py    # PDF CLI (core/coverage/full/comprehensive)
│       └── test_validation_cli.py       # General validation CLI
└── integration/                         # Integration tests
    ├── conftest.py                      # Integration test configuration
    ├── test_07_generate_executive_report.py # Executive report generation
    ├── test_bash_utils.sh               # Bash utility function tests
    ├── test_edge_cases_and_error_paths.py # Edge cases and error handling
    ├── test_figure_equation_citation.py # Figure/equation/citation handling
    ├── test_logging.py                  # Bash logging integration tests
    ├── test_module_interoperability.py  # Cross-module interaction validation
    ├── test_output_copying.py           # Output file handling and copying
    └── test_run_sh.py                   # Script orchestration tests
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
- Unit tests for `projects/{name}/src/` modules (see `projects/{name}/tests/AGENTS.md`)
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
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html --cov-fail-under=60
pytest project/tests/ --cov=project/src --cov-report=html --cov-fail-under=90
```

### Coverage Snapshot (latest)
- Project: **100%** (exceeds 90% target!)
- Infrastructure: **83.33%** (exceeds 60% target by 39%!)
- Total tests: **2118** (1796 infrastructure [2 skipped], 320 project)

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

**See [docs/TESTING_WITH_CREDENTIALS.md](../docs/development/TESTING_WITH_CREDENTIALS.md) for credential setup.**

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

**Project Modules** (`project/src/`): **100%** (Target: 90%+)
- Perfect coverage achieved - all project-specific modules fully tested
- Comprehensive test coverage ensures research code reliability

**Infrastructure Modules** (`infrastructure/`): **83.33%** (Target: 60%+)
- Exceeds the 60% minimum requirement by 39%!
- Exceeded stretch goal of 75% by 8%
- Core modules have higher coverage
- Some CLI and advanced features have lower coverage (see test coverage reports)

### Coverage Configuration
`pyproject.toml` enforces coverage rules via `[tool.coverage.*]` sections:
```toml
[tool.coverage.run]
branch = true
source = ["infrastructure", "project/src"]

[tool.coverage.report]
fail_under = 70  # Global fallback; individual runs use 60% (infra) and 90% (project)
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
1. **Runs infrastructure tests** with 60% coverage requirement
2. **Runs project tests** with 90% coverage requirement
3. **Fails build** if tests don't pass or coverage requirements not met
4. **Generates coverage reports** (htmlcov/)
5. **Validates integration** between components

### Pre-commit Checks
Before committing code:
```bash
# Run all tests with coverage
pytest tests/ --cov=infrastructure --cov=project/src --cov-report=html

# Verify infrastructure coverage (60% minimum)
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=60

# Verify project coverage (90% minimum)
pytest project/tests/ --cov=project/src --cov-fail-under=90

# Check coverage report
open htmlcov/index.html
```

## Adding New Tests

### Checklist
1. Determine if code is project-specific (`project/src/`) or infrastructure (`infrastructure/`)
2. Create test file in appropriate location (`project/tests/` or `tests/infrastructure/`)
3. Import functions to test from correct module path
4. Write comprehensive test cases using real data (no mocks)
5. Ensure coverage requirements met (90% project, 60% infrastructure)
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

See **[docs/TESTING_WITH_CREDENTIALS.md](../docs/development/TESTING_WITH_CREDENTIALS.md)** for complete setup guide.

## See Also

- [`conftest.py`](conftest.py) - Test configuration and fixtures
- [`../infrastructure/AGENTS.md`](../infrastructure/AGENTS.md) - Infrastructure module documentation
- [`../project/src/AGENTS.md`](../project/src/AGENTS.md) - Project module documentation
- [`../AGENTS.md`](../AGENTS.md) - System documentation
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow
- [`../docs/development/TESTING_WITH_CREDENTIALS.md`](../docs/development/TESTING_WITH_CREDENTIALS.md) - Credential configuration guide





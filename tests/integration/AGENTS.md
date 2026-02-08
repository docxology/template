# tests/integration/ - Integration Test Suite

## Purpose

The `tests/integration/` directory contains integration tests that validate the interaction between multiple modules and components. These tests ensure that the system works together correctly, from data generation through analysis to output generation.

**Testing Philosophy:** Integration tests follow the "no mocks" policy - all tests use real implementations. Network-dependent tests are marked with `@pytest.mark.requires_ollama` (or similar) and skip gracefully when services are unavailable.

## Test Coverage

Integration tests complement unit tests by validating:

- **Cross-module interactions** - How different components work together
- **End-to-end workflows** - pipelines from input to output
- **File I/O coordination** - Proper handling of generated files and directories
- **Error propagation** - How errors are handled across module boundaries

## Directory Structure

```text
tests/integration/
├── conftest.py                          # Integration test configuration (expanded)
├── test_bash_utils.sh                   # Bash utility function tests
├── test_edge_cases_and_error_paths.py   # Edge cases and error handling
├── test_environment_setup.py            # Environment setup integration tests
├── test_execute_pipeline_cli.py         # Pipeline CLI surface tests
├── test_executive_report_generation.py  # Executive report generation tests
├── test_figure_equation_citation.py     # Figure/equation/citation handling
├── test_logging.py                      # Bash logging integration tests
├── test_module_interoperability.py      # Cross-module interaction validation
├── test_output_copying.py               # Output file handling and copying
└── test_run_sh.py                       # Script orchestration tests
```

## Test Categories

### Environment Setup (`test_environment_setup.py`)

**Purpose:** Validate environment setup workflow with real system operations

**Test Coverage:**
- uv package manager integration and fallback behavior
- Real dependency checking without mocks
- Directory structure creation and validation
- Build tool availability testing with `shutil.which()`
- Environment variable setting and isolation
- Subprocess execution patterns for external tools
- Filesystem operations integration
- Python version validation without version mocking

**Real Operations Testing:**
All tests use actual system calls and filesystem operations:
- Real `uv sync` subprocess execution
- Real `shutil.which()` for tool detection
- Real `importlib.import_module()` for dependency checking
- Real `os.environ` manipulation and restoration
- Real directory creation and validation
- subprocess execution with error handling

**Skip Patterns:**
Tests use `@pytest.mark.integration` and skip gracefully when dependencies unavailable:
```python
@pytest.mark.integration
def test_uv_sync_when_available(tmp_path):
    if not shutil.which('uv'):
        pytest.skip("uv not installed - skipping integration test")
    # Real uv sync execution...
```

**Example Test:**
```python
def test_complete_setup_with_uv(tmp_path):
    """Test setup when uv is available."""
    if not shutil.which('uv'):
        pytest.skip("uv not installed")

    # Create real pyproject.toml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname="test"\n')

    # subprocess call
    result = subprocess.run(['uv', 'sync'], cwd=str(tmp_path))

    # Validate real results
    assert result.returncode == 0
    assert (tmp_path / ".venv").exists()
```

### Module Interoperability (`test_module_interoperability.py`)

**Purpose:** Validate that different infrastructure modules work together correctly

**Test Coverage:**
- Configuration loading across modules
- Logging integration between components
- Exception handling across module boundaries
- Shared utility function compatibility
- Module interoperability without mocks (uses real implementations or skips when services unavailable)

**Example Test:**
```python
def test_config_logging_integration():
    """Test that configuration and logging modules work together."""
    from infrastructure.core import load_config, get_logger

    config = load_config()
    logger = get_logger(__name__)

    # Verify both modules can be used together
    assert config is not None
    assert logger is not None

    # Test integrated functionality
    logger.info("Config loaded successfully")
```

### Output Management (`test_output_copying.py`)

**Purpose:** Validate output file generation, copying, and cleanup

**Test Coverage:**
- File generation in correct directories
- Output copying between project and root directories
- File permission and ownership handling
- Cleanup of temporary and intermediate files

**Example Test:**
```python
def test_output_directory_structure(tmp_path):
    """Test that output directories are created correctly."""
    from infrastructure.core import ensure_output_dirs

    base_dir = tmp_path / "project"
    ensure_output_dirs(base_dir)

    # Verify expected directories exist
    assert (base_dir / "output" / "figures").exists()
    assert (base_dir / "output" / "data").exists()
    assert (base_dir / "output" / "pdf").exists()
```

### Executive Reporting (`test_executive_report_generation.py`)

**Purpose:** Test the executive report generation pipeline (Stage 10)

**Test Coverage:**
- Cross-project metrics collection and aggregation
- Executive dashboard generation with visual summaries
- Report validation and integrity checking
- Multi-project output organization

**Example Test:**
```python
def test_executive_report_generation():
    """Test executive report generation workflow."""
    from scripts.generate_executive_report import generate_executive_report

    # Generate report for all projects
    report_dir = generate_executive_report(["project1", "project2"])

    # Verify report components exist
    assert (report_dir / "executive_summary.pdf").exists()
    assert (report_dir / "manuscript_overview_project1.png").exists()
    assert (report_dir / "manuscript_overview_project2.png").exists()
```

### Script Orchestration (`test_run_sh.py`)

**Purpose:** Test bash script orchestration and command-line interface

**Test Coverage:**
- `run.sh` script argument parsing and validation
- Project discovery and selection logic
- Pipeline stage execution coordination
- Error handling and exit code management
- Interactive vs non-interactive modes

**Example Test:**
```python
def test_run_sh_project_selection():
    """Test project selection and validation in run.sh."""
    # Test with valid project
    result = run_script("./run.sh --project valid_project --dry-run")
    assert result.returncode == 0

    # Test with invalid project
    result = run_script("./run.sh --project invalid_project --dry-run")
    assert result.returncode != 0
    assert "Project not found" in result.stderr
```

### Bash Integration (`test_logging.py`, `test_bash_utils.sh`)

**Purpose:** Test bash script utilities and logging integration

**Test Coverage:**
- ANSI color output and formatting
- Log level filtering and display
- Bash utility function validation
- Cross-platform compatibility
- Error message formatting

**Example Test:**
```bash
# Test bash logging functions
test_log_success_format() {
    source scripts/bash_utils.sh
    local output=$(log_success "Test message")
    assert_contains "$output" "✓"
    assert_contains "$output" "Test message"
}

test_ansi_color_handling() {
    source scripts/bash_utils.sh
    local output=$(log_error "Error message")
    # Verify ANSI color codes are present/absent based on TTY
    assert_valid_ansi_handling "$output"
}
```

## Integration Test Principles

### Realistic Scenarios

Integration tests simulate real usage patterns:

```python
def test_complete_figure_generation_workflow():
    """Test figure generation from data to output."""
    # Generate test data
    data = generate_test_data()

    # Create figure
    fig_path = create_figure(data)

    # Verify figure exists and is valid
    assert fig_path.exists()
    assert is_valid_image_file(fig_path)

    # Verify figure registry updated
    registry = load_figure_registry()
    assert fig_path.name in registry
```

### End-to-End Validation

Tests validate workflows:

```python
def test_manuscript_compilation_pipeline():
    """Test manuscript compilation workflow."""
    # Setup test manuscript
    manuscript_dir = create_test_manuscript()

    # Run compilation
    result = compile_manuscript(manuscript_dir)

    # Verify outputs
    assert result.pdf_path.exists()
    assert result.html_path.exists()
    assert validate_pdf(result.pdf_path)
```

### File System Integration

Tests validate file system operations:

```python
def test_cross_module_file_handling(tmp_path):
    """Test file handling across multiple modules."""
    # Module A creates file
    file_path = module_a.create_output_file(tmp_path)

    # Module B processes file
    result = module_b.process_file(file_path)

    # Module C validates result
    assert module_c.validate_result(result)

    # Cleanup works correctly
    module_a.cleanup(tmp_path)
    assert not file_path.exists()
```

## Running Integration Tests

### All Integration Tests

```bash
# Run integration tests only
pytest tests/integration/ -v

# With coverage (includes integration)
pytest tests/ --cov=src --cov-report=html
```

### Specific Integration Tests

```bash
# Module interoperability
pytest tests/integration/test_module_interoperability.py -v

# Output management
pytest tests/integration/test_output_copying.py -v
```

## Test Configuration

### conftest.py

Integration test configuration provides fixtures:

```python
import pytest
from pathlib import Path

# Path fixtures - get repository locations
@pytest.fixture
def repo_root() -> Path:
    """Get the repository root directory."""
    ...

@pytest.fixture
def scripts_path(repo_root: Path) -> Path:
    """Get the scripts directory path."""
    ...

# Project structure fixtures - create test environments
@pytest.fixture
def temp_project_dir(tmp_path: Path):
    """Create temporary project with src/, tests/, manuscript/, output/."""
    ...

@pytest.fixture
def sample_project_structure(tmp_path: Path):
    """Create multi-project structure with sample content."""
    ...

@pytest.fixture
def sample_manuscript_files(temp_project_dir: Path):
    """Create sample markdown manuscript files with LaTeX content."""
    ...

# Subprocess helpers - run commands in tests
@pytest.fixture
def run_bash_command():
    """Helper to run bash commands and capture output."""
    ...

@pytest.fixture
def run_python_script(repo_root: Path):
    """Helper to run Python scripts with arguments."""
    ...

# Script path fixtures
@pytest.fixture
def bash_utils_path(repo_root: Path) -> Path:
    """Get path to scripts/bash_utils.sh."""
    ...

@pytest.fixture
def run_sh_path(repo_root: Path) -> Path:
    """Get path to run.sh."""
    ...

# Cleanup fixtures
@pytest.fixture
def cleanup_temp_files(tmp_path: Path):
    """Register paths for automatic cleanup on teardown."""
    ...
```


## Integration Test Development

### Environment Setup Testing Patterns

**Subprocess Testing:**
```python
def test_real_subprocess_execution():
    """Test subprocess execution with real commands."""
    result = subprocess.run(
        [sys.executable, '-c', 'print("test")'],
        capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "test"
```

**Real System Integration:**
```python
@pytest.mark.integration
def test_uv_sync_integration(tmp_path):
    """Test real uv sync subprocess execution."""
    if not shutil.which('uv'):
        pytest.skip("uv not installed")

    # Create real pyproject.toml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname="test"\n')

    # Execute subprocess
    result = subprocess.run(['uv', 'sync'], cwd=str(tmp_path))
    assert result.returncode == 0

    # Validate filesystem changes
    assert (tmp_path / ".venv").exists()
    assert (tmp_path / "uv.lock").exists()
```

**Filesystem Integration:**
```python
def test_filesystem_operations_integration(tmp_path):
    """Test integration of filesystem operations."""
    # Create complex directory structure
    test_structure = {
        'projects/test/src': ['module1.py', 'module2.py'],
        'output/test/figures': ['fig1.png', 'fig2.png'],
    }

    # Create directories and files
    for dir_path, files in test_structure.items():
        full_dir = tmp_path / dir_path
        full_dir.mkdir(parents=True)

        for filename in files:
            (full_dir / filename).write_text(f"# Test {filename}")

    # Verify structure exists
    for dir_path, files in test_structure.items():
        full_dir = tmp_path / dir_path
        assert full_dir.exists()

        for filename in files:
            file_path = full_dir / filename
            assert file_path.exists()
```

**Environment Isolation:**
```python
def test_environment_isolation(tmp_path):
    """Test that environment setup doesn't affect global state."""
    # Save original environment
    original_env = dict(os.environ)

    try:
        # Run environment setup
        result = set_environment_variables(tmp_path)
        assert result is True

        # Check that variables are set
        assert os.environ.get('MPLBACKEND') == 'Agg'

    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
```

### Test Structure

```python
"""Integration tests for cross-module functionality."""
import pytest
from pathlib import Path

def test_module_a_and_b_integration(temp_project_dir):
    """Test that module A and B work together correctly."""
    # Setup
    config = create_test_config(temp_project_dir)

    # Execute module A
    result_a = module_a.process(config)

    # Execute module B using A's output
    result_b = module_b.process(result_a)

    # Validate integrated result
    assert validate_integrated_result(result_b)

def test_error_propagation_across_modules():
    """Test that errors are properly propagated between modules."""
    # Setup scenario that will cause error
    config = create_error_config()

    # Execute workflow
    with pytest.raises(ExpectedException):
        run_complete_workflow(config)
```

### Test Data Management

Integration tests use realistic test data:

```python
@pytest.fixture
def sample_manuscript_files(temp_project_dir):
    """Create sample manuscript files for testing."""
    manuscript_dir = temp_project_dir / "manuscript"

    # Create sample markdown files
    abstract = manuscript_dir / "01_abstract.md"
    abstract.write_text("# Abstract\n\nTest abstract content.")

    introduction = manuscript_dir / "02_introduction.md"
    introduction.write_text("# Introduction\n\nTest introduction.")

    return manuscript_dir
```

## Common Integration Scenarios

### Build Pipeline Integration

```python
def test_build_pipeline_integration():
    """Test build pipeline from setup to output."""
    # 1. Environment setup
    setup_environment()

    # 2. Test execution
    run_tests()

    # 3. Analysis execution
    run_analysis()

    # 4. PDF rendering
    render_pdf()

    # 5. Validation
    validate_output()

    # 6. Output copying
    copy_outputs()
```

### Data Flow Validation

```python
def test_data_flow_from_generation_to_visualization():
    """Test data flows correctly from generation to visualization."""
    # Generate data
    data = generate_synthetic_data(n_samples=1000, seed=42)

    # Process data
    processed = preprocess_data(data)

    # Analyze data
    results = analyze_data(processed)

    # Create visualization
    fig_path = create_visualization(results)

    # Validate final output
    assert fig_path.exists()
    assert validate_figure_content(fig_path)
```

## Performance and Reliability

### Test Execution Time

Integration tests are designed to run efficiently:

- **Typical runtime:** 30-60 seconds for full suite
- **No external dependencies** required for core tests
- **Parallel execution** supported where possible

### Reliability Features

```python
def test_integration_with_retry_logic():
    """Test integration scenarios with retry logic."""
    # Simulate intermittent failures
    attempt_count = 0

    while attempt_count < 3:
        try:
            result = run_integration_workflow()
            assert result.success
            break
        except TemporaryFailure:
            attempt_count += 1
            time.sleep(1)  # Retry delay

    assert attempt_count < 3, "Integration workflow failed after retries"
```

## Debugging Integration Tests

### Logging and Diagnostics

```python
def test_integration_with_detailed_logging(caplog):
    """Test integration with detailed logging capture."""
    with caplog.at_level(logging.DEBUG):
        run_integration_workflow()

    # Verify expected log messages
    assert "Starting workflow" in caplog.text
    assert "Workflow completed" in caplog.text

    # Check for error messages
    error_logs = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_logs) == 0, f"Errors found: {error_logs}"
```

### State Inspection

```python
def test_integration_state_inspection(tmp_path):
    """Test integration with state inspection capabilities."""
    # Run workflow with state logging
    state_log = run_workflow_with_state_logging(tmp_path)

    # Verify intermediate states
    assert state_log["setup_completed"] is True
    assert state_log["analysis_completed"] is True
    assert state_log["rendering_completed"] is True

    # Verify final outputs
    assert (tmp_path / "output" / "final_result.pdf").exists()
```

## Integration with CI/CD

### Automated Testing

Integration tests run as part of the standard test suite:

```bash
# test execution (unit + integration)
python3 scripts/01_run_tests.py

# Integration tests only
pytest tests/integration/
```

### Failure Analysis

When integration tests fail:

1. **Check individual module tests** - Ensure unit tests pass
2. **Verify test environment** - Check temporary directories and file permissions
3. **Review error messages** - Look for specific failure points
4. **Run with verbose output** - Use `-v` and `-s` flags for detailed output

## Best Practices

### Do's ✅

- ✅ **Test realistic scenarios** - Simulate actual usage patterns
- ✅ **Use temporary directories** - Avoid conflicts with real project files
- ✅ **Validate end-to-end workflows** - Test user journeys
- ✅ **Check error propagation** - Ensure errors are handled gracefully
- ✅ **Document test purpose** - Clear docstrings explaining what is integrated

### Don'ts ❌

- ❌ **Test implementation details** - Focus on behavior, not internals
- ❌ **Create overly complex tests** - Keep tests focused and maintainable
- ❌ **Skip cleanup** - Always clean up temporary files and directories
- ❌ **Hardcode paths** - Use fixtures for dynamic path management
- ❌ **Ignore test performance** - Keep integration tests reasonably fast

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../../tests/AGENTS.md`](../../tests/AGENTS.md) - test suite documentation
- [`../../docs/development/TESTING_GUIDE.md`](../../docs/development/TESTING_GUIDE.md) - Testing best practices
- [`../../scripts/AGENTS.md`](../../scripts/AGENTS.md) - Build pipeline documentation


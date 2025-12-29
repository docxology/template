# tests/integration/ - Integration Test Suite

## Purpose

The `tests/integration/` directory contains integration tests that validate the interaction between multiple modules and components. These tests ensure that the complete system works together correctly, from data generation through analysis to output generation.

**Testing Philosophy:** Integration tests follow the "no mocks" policy - all tests use real implementations. Network-dependent tests are marked with `@pytest.mark.requires_ollama` (or similar) and skip gracefully when services are unavailable.

## Test Coverage

Integration tests complement unit tests by validating:

- **Cross-module interactions** - How different components work together
- **End-to-end workflows** - Complete pipelines from input to output
- **File I/O coordination** - Proper handling of generated files and directories
- **Error propagation** - How errors are handled across module boundaries

## Directory Structure

```
tests/integration/
├── conftest.py                          # Integration test configuration
├── test_07_generate_executive_report.py # Executive report generation tests
├── test_bash_utils.sh                   # Bash utility function tests
├── test_edge_cases_and_error_paths.py   # Edge cases and error handling
├── test_figure_equation_citation.py     # Figure/equation/citation handling
├── test_logging.py                      # Bash logging integration tests
├── test_module_interoperability.py      # Cross-module interaction validation
├── test_output_copying.py               # Output file handling and copying
└── test_run_sh.py                       # Script orchestration tests
```

## Test Categories

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

### Executive Reporting (`test_07_generate_executive_report.py`)

**Purpose:** Test the executive report generation pipeline (Stage 10)

**Test Coverage:**
- Cross-project metrics collection and aggregation
- Executive dashboard generation with visual summaries
- Report validation and integrity checking
- Multi-project output organization

**Example Test:**
```python
def test_executive_report_generation():
    """Test complete executive report generation workflow."""
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
    """Test complete figure generation from data to output."""
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

Tests validate complete workflows:

```python
def test_manuscript_compilation_pipeline():
    """Test complete manuscript compilation workflow."""
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

Integration test configuration provides:

```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_project_dir():
    """Create temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "project"
        project_dir.mkdir()

        # Create standard subdirectories
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "output").mkdir()

        yield project_dir

@pytest.fixture
def temp_project_dir():
    """Create temporary project directory structure."""
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp) / "project"
        project_dir.mkdir()

        # Create standard subdirectories
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "manuscript").mkdir()
        (project_dir / "output").mkdir()

        yield project_dir
```

## Integration Test Development

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
    """Test complete build pipeline from setup to output."""
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
# Complete test execution (unit + integration)
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
- ✅ **Validate end-to-end workflows** - Test complete user journeys
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
- [`../../tests/AGENTS.md`](../../tests/AGENTS.md) - Complete test suite documentation
- [`../../docs/TESTING_GUIDE.md`](../../docs/TESTING_GUIDE.md) - Testing best practices
- [`../../scripts/AGENTS.md`](../../scripts/AGENTS.md) - Build pipeline documentation


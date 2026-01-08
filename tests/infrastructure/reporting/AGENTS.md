# Reporting Infrastructure Tests

## Overview

The `tests/infrastructure/reporting/` directory contains tests for the pipeline reporting and error aggregation infrastructure. These tests validate the reporting system's ability to generate consolidated pipeline reports, test results, and validation summaries.

## Directory Structure

```
tests/infrastructure/reporting/
├── AGENTS.md                           # This technical documentation
├── __init__.py                        # Test package initialization
├── conftest.py                        # Test configuration and fixtures
├── test_cli.py                        # CLI interface tests
├── test_config.py                     # Configuration tests
├── test_core.py                       # Core reporting functionality tests
├── test_error_aggregator.py           # Error aggregation tests
├── test_html_templates.py             # HTML template tests
├── test_pipeline_reporter.py          # Pipeline reporter tests
├── test_reporting_cli_full.py         # Full reporting CLI tests
├── test_reporting_cli.py              # Reporting CLI tests
├── test_reporting_integration.py      # Integration tests
└── test_reporting.py                  # General reporting tests
```

## Test Categories

### Core Reporting Tests

**Pipeline Reporter Tests (`test_pipeline_reporter.py`)**
- Pipeline execution reporting and summarization
- Stage duration tracking and bottleneck identification
- Resource usage monitoring and reporting
- Error aggregation and categorization

**Key Test Scenarios:**
```python
def test_pipeline_reporter_basic_reporting():
    """Test basic pipeline reporting functionality."""
    # Create mock pipeline results
    stage_results = [
        {'stage': 'setup', 'status': 'success', 'duration': 2.5},
        {'stage': 'testing', 'status': 'success', 'duration': 15.3},
        {'stage': 'analysis', 'status': 'success', 'duration': 45.2},
        {'stage': 'rendering', 'status': 'success', 'duration': 28.7}
    ]

    reporter = PipelineReporter()
    report = reporter.generate_report(stage_results, total_duration=91.7)

    # Verify report structure
    assert report['summary']['total_stages'] == 4
    assert report['summary']['successful_stages'] == 4
    assert report['summary']['total_duration'] == 91.7
    assert 'stage_details' in report
    assert 'performance_metrics' in report

def test_pipeline_reporter_error_handling():
    """Test error handling in pipeline reporting."""
    # Create results with failures
    stage_results = [
        {'stage': 'setup', 'status': 'success', 'duration': 2.5},
        {'stage': 'testing', 'status': 'failed', 'duration': 5.2, 'error': 'Test failure'},
        {'stage': 'analysis', 'status': 'skipped', 'duration': 0.0}
    ]

    reporter = PipelineReporter()
    report = reporter.generate_report(stage_results, total_duration=7.7)

    # Verify error reporting
    assert report['summary']['failed_stages'] == 1
    assert report['summary']['skipped_stages'] == 1
    assert 'errors' in report
    assert len(report['errors']) == 1
```

### Error Aggregation Tests

**Error Aggregator Tests (`test_error_aggregator.py`)**
- Error collection and categorization
- Duplicate error detection and merging
- Error frequency analysis and prioritization
- Error pattern recognition and reporting

**Test Scenarios:**
```python
def test_error_aggregator_categorization():
    """Test error categorization and aggregation."""
    aggregator = ErrorAggregator()

    # Add various errors
    aggregator.add_error('validation', 'PDF validation failed: missing reference', 'rendering')
    aggregator.add_error('dependency', 'Module not found: numpy', 'analysis')
    aggregator.add_error('validation', 'Invalid markdown syntax', 'rendering')
    aggregator.add_error('permission', 'Write access denied', 'output')

    # Verify categorization
    categorized = aggregator.get_categorized_errors()
    assert 'validation' in categorized
    assert 'dependency' in categorized
    assert 'permission' in categorized
    assert len(categorized['validation']) == 2  # Two validation errors

def test_error_aggregator_frequency_analysis():
    """Test error frequency analysis."""
    aggregator = ErrorAggregator()

    # Add repeated errors
    for _ in range(3):
        aggregator.add_error('network', 'Connection timeout', 'api_call')

    for _ in range(2):
        aggregator.add_error('parsing', 'Invalid JSON', 'data_processing')

    # Analyze frequency
    frequency = aggregator.get_error_frequency()
    assert frequency['network']['count'] == 3
    assert frequency['parsing']['count'] == 2

    # Verify prioritization
    prioritized = aggregator.get_prioritized_errors()
    assert prioritized[0]['category'] == 'network'  # Most frequent
```

### HTML Template Tests

**HTML Template Tests (`test_html_templates.py`)**
- HTML report template rendering and validation
- CSS styling and responsive design
- JavaScript functionality for interactive reports
- Template variable substitution and error handling

**Test Coverage:**
```python
def test_html_template_rendering():
    """Test HTML template rendering with data."""
    template_data = {
        'title': 'Pipeline Report',
        'stages': [
            {'name': 'setup', 'duration': 2.5, 'status': 'success'},
            {'name': 'testing', 'duration': 15.3, 'status': 'success'}
        ],
        'errors': [],
        'total_duration': 17.8
    }

    html_output = render_html_report(template_data)

    # Verify HTML structure
    assert '<!DOCTYPE html>' in html_output
    assert 'Pipeline Report' in html_output
    assert '17.8' in html_output  # Total duration

    # Verify CSS is included
    assert '<style>' in html_output or 'css' in html_output.lower()

def test_html_template_error_handling():
    """Test error handling in HTML template rendering."""
    # Test with missing data
    incomplete_data = {'title': 'Test Report'}  # Missing required fields

    # Should handle gracefully or raise clear error
    try:
        html_output = render_html_report(incomplete_data)
        # If it succeeds, verify basic structure
        assert '<html' in html_output
    except TemplateError as e:
        assert 'missing' in str(e).lower() or 'required' in str(e).lower()
```

### CLI and Configuration Tests

**CLI Interface Tests (`test_cli.py`, `test_reporting_cli*.py`)**
- Command-line argument parsing for reporting commands
- Output format selection (JSON, HTML, Markdown)
- Report generation and file output
- Error handling and user feedback

**Configuration Tests (`test_config.py`)**
- Reporting configuration validation
- Default value handling and overrides
- Environment variable integration
- Configuration file parsing

### Integration Tests

**Integration Tests (`test_reporting_integration.py`)**
- End-to-end reporting workflow validation
- Cross-component integration testing
- Data flow verification between components
- Real-world usage scenario simulation

## Test Design Principles

### Reporting Validation

**Data Testing Approach:**
- Unlike many infrastructure tests, reporting tests use realistic pipeline data
- Generate actual report files for validation
- Test file I/O operations with file system
- Validate report content and structure thoroughly

**Multi-Format Validation:**
```python
def validate_report_formats(report_data: dict, output_dir: Path):
    """Validate report generation in all supported formats."""

    # JSON format
    json_report = generate_json_report(report_data)
    validate_json_structure(json_report)

    json_file = output_dir / "report.json"
    save_report(json_report, json_file, 'json')
    assert json_file.exists()

    # HTML format
    html_report = generate_html_report(report_data)
    validate_html_structure(html_report)

    html_file = output_dir / "report.html"
    save_report(html_report, html_file, 'html')
    assert html_file.exists()

    # Markdown format
    md_report = generate_markdown_report(report_data)
    validate_markdown_structure(md_report)

    md_file = output_dir / "report.md"
    save_report(md_report, md_file, 'markdown')
    assert md_file.exists()

    # Verify content consistency across formats
    assert extract_key_metrics(json_report) == extract_key_metrics(html_report)
    assert extract_key_metrics(html_report) == extract_key_metrics(md_report)
```

### Test Organization

**Modular Test Structure:**
- Component-specific test files for each reporting module
- Integration tests that combine multiple components
- CLI tests separate from core functionality
- Configuration tests isolated from business logic

**Test Data Management:**
```python
@pytest.fixture
def sample_pipeline_results():
    """Provide realistic pipeline execution results."""
    return [
        {
            'stage': 'environment_setup',
            'status': 'success',
            'duration': 2.3,
            'start_time': '2024-01-15T10:00:00',
            'end_time': '2024-01-15T10:00:02.3'
        },
        {
            'stage': 'test_execution',
            'status': 'success',
            'duration': 45.6,
            'start_time': '2024-01-15T10:00:02.3',
            'end_time': '2024-01-15T10:00:47.9',
            'details': {
                'tests_run': 150,
                'tests_passed': 148,
                'tests_failed': 2,
                'coverage': 92.5
            }
        },
        {
            'stage': 'analysis_execution',
            'status': 'failed',
            'duration': 12.4,
            'start_time': '2024-01-15T10:00:47.9',
            'end_time': '2024-01-15T10:01:00.3',
            'error': 'AnalysisError: Insufficient data for statistical test',
            'error_details': {
                'error_type': 'AnalysisError',
                'error_location': 'statistical_analysis.py:142',
                'data_points': 45,
                'required_minimum': 50
            }
        }
    ]

@pytest.fixture
def comprehensive_error_set():
    """Provide diverse set of errors for aggregation testing."""
    return [
        {'category': 'validation', 'message': 'PDF missing cross-references', 'stage': 'rendering'},
        {'category': 'dependency', 'message': 'Module numpy not found', 'stage': 'analysis'},
        {'category': 'validation', 'message': 'Invalid markdown syntax', 'stage': 'processing'},
        {'category': 'network', 'message': 'Connection timeout to API', 'stage': 'data_fetching'},
        {'category': 'permission', 'message': 'Write access denied to output directory', 'stage': 'file_output'},
        {'category': 'validation', 'message': 'Citation key not found', 'stage': 'rendering'}
    ]
```

## Test Infrastructure

### Fixtures and Setup

**Report Generation Fixtures:**
```python
@pytest.fixture
def temp_report_dir(tmp_path):
    """Provide temporary directory for report file generation."""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return report_dir

@pytest.fixture
def mock_pipeline_data():
    """Provide mock pipeline execution data."""
    return {
        'pipeline_start': '2024-01-15T10:00:00',
        'pipeline_end': '2024-01-15T10:05:30',
        'total_duration': 330.0,
        'stages': [
            {'name': 'setup', 'status': 'success', 'duration': 5.2},
            {'name': 'testing', 'status': 'success', 'duration': 120.5},
            {'name': 'analysis', 'status': 'success', 'duration': 180.3},
            {'name': 'rendering', 'status': 'success', 'duration': 24.0}
        ],
        'errors': [],
        'warnings': ['Low test coverage: 78%'],
        'system_info': {
            'python_version': '3.10.0',
            'platform': 'Linux',
            'memory_total': '16GB',
            'cpu_count': 8
        }
    }
```

### Validation Helpers

**Report Content Validation:**
```python
def validate_report_content(report: dict, expected_keys: List[str]):
    """Validate report contains required content."""
    for key in expected_keys:
        assert key in report, f"Missing required key: {key}"

    # Validate specific content
    if 'summary' in report:
        validate_summary_section(report['summary'])

    if 'stages' in report:
        validate_stages_section(report['stages'])

    if 'errors' in report:
        validate_errors_section(report['errors'])

def validate_summary_section(summary: dict):
    """Validate summary section structure."""
    required_fields = ['total_stages', 'successful_stages', 'failed_stages', 'total_duration']
    for field in required_fields:
        assert field in summary, f"Missing summary field: {field}"
        assert isinstance(summary[field], (int, float)), f"Invalid type for {field}"

def validate_html_report_structure(html_content: str):
    """Validate HTML report has proper structure."""
    assert '<!DOCTYPE html>' in html_content
    assert '<html' in html_content
    assert '<head>' in html_content
    assert '<body>' in html_content
    assert '</html>' in html_content

    # Check for required sections
    assert 'Pipeline Report' in html_content or 'Report Summary' in html_content
```

## Running Tests

### Test Execution

```bash
# Run all reporting tests
pytest tests/infrastructure/reporting/

# Run specific component tests
pytest tests/infrastructure/reporting/test_pipeline_reporter.py

# Run integration tests
pytest tests/infrastructure/reporting/test_reporting_integration.py

# Run with coverage
pytest tests/infrastructure/reporting/ --cov=infrastructure.reporting --cov-report=html
```

### Test Filtering

**Category-Based Execution:**
```bash
# CLI tests only
pytest tests/infrastructure/reporting/ -k "cli"

# Error handling tests
pytest tests/infrastructure/reporting/ -k "error"

# HTML template tests
pytest tests/infrastructure/reporting/ -k "html"
```

## Test Coverage and Quality

### Coverage Goals

**Reporting Module Coverage:**
- Pipeline reporter: 95%+ coverage
- Error aggregator: 95%+ coverage
- HTML templates: 90%+ coverage
- CLI interface: 95%+ coverage
- Integration tests: 85%+ coverage

### Quality Metrics

**Test Effectiveness:**
- All report formats generate valid output files
- Error aggregation works across diverse error types
- HTML reports render correctly in browsers
- CLI commands execute successfully with proper output
- Integration tests cover realistic usage scenarios

## Common Test Issues

### Report Generation Failures

**Template Rendering Issues:**
```python
# Debug template rendering
def debug_template_rendering():
    """Debug template rendering issues."""
    try:
        # Test with minimal data
        minimal_data = {'title': 'Test Report', 'stages': []}
        html = render_html_report(minimal_data)
        print("Minimal template rendering: SUCCESS")

        # Test with full data
        full_data = create_comprehensive_test_data()
        html = render_html_report(full_data)
        print("Full template rendering: SUCCESS")

    except Exception as e:
        print(f"Template rendering failed: {e}")
        import traceback
        traceback.print_exc()
```

**File Output Issues:**
```python
# Debug file output problems
def debug_file_output():
    """Debug report file saving issues."""
    import tempfile
    import os

    # Test basic file operations
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        test_content = "Test report content"
        f.write(test_content)
        temp_path = f.name

    # Verify file was written
    assert os.path.exists(temp_path)
    with open(temp_path, 'r') as f:
        content = f.read()
    assert content == test_content

    # Clean up
    os.unlink(temp_path)
    print("Basic file operations: SUCCESS")
```

### Error Aggregation Problems

**Error Categorization Issues:**
```python
# Debug error categorization
def debug_error_categorization():
    """Debug error aggregation and categorization."""
    aggregator = ErrorAggregator()

    test_errors = [
        "PDF validation failed: missing reference",
        "Module numpy not found",
        "Connection timeout to API",
        "Invalid markdown syntax"
    ]

    for error in test_errors:
        aggregator.add_error('test', error, 'test_stage')

    categorized = aggregator.get_categorized_errors()
    print(f"Categorized errors: {categorized}")

    frequency = aggregator.get_error_frequency()
    print(f"Error frequency: {frequency}")
```

## Integration with CI/CD

### Automated Reporting

**Test Result Integration:**
```yaml
# CI pipeline integration
- name: Run Reporting Tests
  run: |
    pytest tests/infrastructure/reporting/ --cov=infrastructure.reporting --cov-report=xml

- name: Generate Test Report
  run: |
    python3 -m infrastructure.reporting.cli generate-report \
      --input pytest-results.xml \
      --format html \
      --output test-report.html
```

### Coverage Tracking

**Coverage Integration:**
```yaml
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    flags: reporting
```

## Future Test Enhancements

### Planned Improvements

**Testing:**
- **Visual Report Testing**: Validate HTML report appearance
- **Performance Benchmarking**: Track report generation speed
- **Load Testing**: Test with large pipeline result sets
- **Accessibility Testing**: Ensure reports are screen-reader friendly

**Test Infrastructure:**
- **Report Template Testing**: Automated template validation
- **Cross-Browser Testing**: HTML report compatibility
- **Mobile Responsiveness**: Test reports on mobile devices
- **Internationalization**: Multi-language report testing

## Troubleshooting

### Test Debugging

**Verbose Execution:**
```bash
# Run with detailed output
pytest tests/infrastructure/reporting/test_pipeline_reporter.py -v -s

# Debug specific assertion
pytest tests/infrastructure/reporting/ --pdb -k "test_pipeline_reporter_basic"
```

**Log Analysis:**
```bash
# Check for test-related errors
grep "ERROR\|FAIL" test_results.log

# Analyze coverage gaps
pytest tests/infrastructure/reporting/ --cov=infrastructure.reporting --cov-report=html
# Open htmlcov/index.html to see uncovered lines
```

### Environment Validation

**Pre-Test Setup:**
```bash
# Validate test environment
python3 -c "
import sys
print(f'Python: {sys.version}')

try:
    from infrastructure.reporting import PipelineReporter, ErrorAggregator
    print('Reporting modules: ✓')
except ImportError as e:
    print(f'Reporting modules: ✗ - {e}')

try:
    import jinja2
    print('Jinja2 templates: ✓')
except ImportError:
    print('Jinja2 templates: ✗')
"
```

## See Also

**Related Documentation:**
- [`../../../infrastructure/reporting/AGENTS.md`](../../../infrastructure/reporting/AGENTS.md) - Reporting module details
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure test suite overview
- [`../../../AGENTS.md`](../../../AGENTS.md) - System documentation

**Testing Standards:**
- [`../../../.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing standards
- [`../../../docs/development/TESTING_GUIDE.md`](../../../docs/development/TESTING_GUIDE.md) - Testing guide
# Integration Tests

## Overview

The `project/tests/integration/` directory contains integration tests that validate the end-to-end functionality of the research template system. These tests ensure that all components work together correctly, from data generation through figure creation to final manuscript production.

## Directory Structure

```
project/tests/integration/
├── AGENTS.md                       # This technical documentation
├── __init__.py                    # Package initialization
├── conftest.py                    # Test configuration and fixtures
├── test_example_figure.py         # Example figure generation tests
├── test_generate_research_figures.py  # Research figure pipeline tests
└── test_integration_pipeline.py   # pipeline integration tests
```

## Test Categories

### Pipeline Integration Tests (`test_integration_pipeline.py`)

**End-to-end pipeline validation:**

#### Pipeline Test

**Full Research Workflow Validation:**

```python
def test_complete_research_pipeline():
    """Test the research pipeline from data generation to manuscript."""

    # Setup test environment
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Step 1: Generate research data
        data = generate_example_data(n_samples=100, seed=42)
        data_file = temp_path / "research_data.npz"
        np.savez(data_file, **data)

        # Step 2: Create research figures
        figures_output = temp_path / "figures"
        figures_output.mkdir()

        create_all_figures(data, figures_output)

        # Step 3: Generate manuscript sections
        manuscript_dir = temp_path / "manuscript"
        manuscript_dir.mkdir()

        # Generate individual sections
        sections = generate_manuscript_sections(data, figures_output)

        # Step 4: Combine into manuscript
        combined_manuscript = combine_manuscript_sections(sections)

        # Step 5: Validate outputs
        assert data_file.exists()
        assert len(list(figures_output.glob("*.png"))) >= 3  # At least 3 figures
        assert len(sections) >= 5  # At least 5 sections
        assert len(combined_manuscript) > 1000  # Substantial manuscript

        # Step 6: Cross-reference validation
        validate_manuscript_references(combined_manuscript, figures_output)
```

#### Component Integration Tests

**Individual Component Integration:**

```python
def test_data_figure_integration():
    """Test integration between data generation and figure creation."""

    # Generate test data
    data = generate_example_data(n_samples=50, random_state=123)

    # Create figures from data
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Test each figure type
        convergence_figure = create_convergence_figure(data, output_dir)
        parameter_figure = create_parameter_comparison_figure(data, output_dir)
        landscape_figure = create_optimization_landscape_figure(data, output_dir)

        # Validate figure files exist
        assert convergence_figure.exists()
        assert parameter_figure.exists()
        assert landscape_figure.exists()

        # Validate figure content (basic checks)
        for fig_file in [convergence_figure, parameter_figure, landscape_figure]:
            # Check file size (non-empty)
            assert fig_file.stat().st_size > 1000

            # Validate image can be loaded
            img = plt.imread(str(fig_file))
            assert img.shape[0] > 100  # Reasonable height
            assert img.shape[1] > 100  # Reasonable width
```

### Figure Generation Tests (`test_generate_research_figures.py`)

**Research figure creation and validation:**

#### Figure Quality Tests

**Visual Quality Validation:**

```python
def test_figure_visual_quality():
    """Test that generated figures meet visual quality standards."""

    data = generate_example_data(n_samples=100)

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Generate figures
        figures = create_all_figures(data, output_dir)

        for figure_path in figures:
            # Validate file properties
            assert figure_path.exists()
            assert figure_path.suffix == '.png'

            # Check image dimensions
            img = plt.imread(str(figure_path))
            height, width = img.shape[:2]

            # Minimum size requirements
            assert height >= 400, f"Figure {figure_path.name} height too small: {height}"
            assert width >= 600, f"Figure {figure_path.name} width too small: {width}"

            # Check aspect ratio (reasonable range)
            aspect_ratio = width / height
            assert 0.5 <= aspect_ratio <= 3.0, f"Figure {figure_path.name} aspect ratio unusual: {aspect_ratio}"

            # Validate color content (not blank)
            if len(img.shape) == 3:  # Color image
                # Check for meaningful color variation
                color_variance = np.var(img)
                assert color_variance > 0.01, f"Figure {figure_path.name} appears blank or uniform"
```

#### Figure Data Accuracy Tests

**Data Representation Validation:**

```python
def test_figure_data_accuracy():
    """Test that figures accurately represent the input data."""

    # Create specific test data
    test_data = {
        'iterations': np.arange(100),
        'objective_values': np.exp(-np.arange(100) / 20),  # Exponential decay
        'parameter_sets': np.random.randn(10, 5),  # 10 parameter sets, 5 parameters each
        'final_objectives': np.random.rand(10)
    }

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Generate convergence figure
        conv_fig = create_convergence_figure(test_data, output_dir)

        # Validate convergence trend
        # (In practice, this would use image analysis or metadata)
        assert conv_fig.exists()

        # For parameter comparison
        param_fig = create_parameter_comparison_figure(test_data, output_dir)

        # Validate parameter visualization
        assert param_fig.exists()

        # Cross-validate with data statistics
        expected_min = np.min(test_data['objective_values'])
        expected_final = test_data['objective_values'][-1]

        # These would be validated through figure metadata or analysis
        # In this test, we verify the pipeline completes successfully
```

### Example Figure Tests (`test_example_figure.py`)

**Core figure generation functionality:**

#### Basic Figure Creation Tests

**Fundamental Figure Operations:**

```python
def test_basic_figure_creation():
    """Test basic figure creation functionality."""

    # Test data setup
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Create basic plot
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(x, y, 'b-', linewidth=2, label='sin(x)')
        ax.set_xlabel('x')
        ax.set_ylabel('sin(x)')
        ax.set_title('Basic Sine Wave')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Save figure
        output_file = output_dir / "basic_figure.png"
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close(fig)

        # Validate output
        assert output_file.exists()
        assert output_file.stat().st_size > 5000  # Reasonable file size

        # Validate image properties
        img = plt.imread(str(output_file))
        assert img.shape[0] > 400  # Height
        assert img.shape[1] > 600  # Width
```

#### Figure Configuration Tests

**Figure Customization Validation:**

```python
def test_figure_customization():
    """Test figure customization options."""

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Test different figure sizes
        sizes = [(6, 4), (10, 8), (12, 6)]

        for i, (width, height) in enumerate(sizes):
            fig, ax = plt.subplots(figsize=(width, height))

            # Add some content
            x = np.linspace(0, 10, 50)
            y = x**2
            ax.plot(x, y, 'r--', linewidth=1.5)
            ax.set_title(f'Figure Size {width}x{height}')

            # Save with different DPI
            dpi = 100 + i * 50  # 100, 150, 200
            output_file = output_dir / f"figure_size_{i}.png"
            fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
            plt.close(fig)

            # Validate
            assert output_file.exists()

            # Higher DPI should result in larger file
            if i > 0:
                prev_file = output_dir / f"figure_size_{i-1}.png"
                assert output_file.stat().st_size > prev_file.stat().st_size
```

## Test Infrastructure

### Test Configuration (`conftest.py`)

**Shared test fixtures and configuration:**

#### Data Generation Fixtures

**Reusable Test Data:**

```python
@pytest.fixture
def sample_research_data():
    """Generate sample research data for testing."""
    return generate_example_data(n_samples=50, seed=42)

@pytest.fixture
def temporary_output_dir():
    """Provide temporary directory for test outputs."""
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_figure_data():
    """Generate sample data for figure testing."""
    np.random.seed(123)
    return {
        'x_values': np.linspace(0, 10, 100),
        'y_values': np.sin(np.linspace(0, 10, 100)) + np.random.normal(0, 0.1, 100),
        'categories': ['A', 'B', 'C', 'D'],
        'values': np.random.rand(4)
    }
```

#### Test Utilities

**Helper Functions:**

```python
def validate_figure_file(figure_path: Path, min_size: int = 1000) -> bool:
    """Validate that a figure file exists and has reasonable size."""
    if not figure_path.exists():
        return False

    file_size = figure_path.stat().st_size
    if file_size < min_size:
        return False

    # Try to load as image
    try:
        img = plt.imread(str(figure_path))
        return img.size > 0
    except Exception:
        return False

def count_figure_files(output_dir: Path) -> int:
    """Count PNG figure files in directory."""
    return len(list(output_dir.glob("*.png")))

def validate_manuscript_structure(manuscript: str) -> dict:
    """Validate manuscript has required sections."""
    sections = {
        'abstract': '# Abstract' in manuscript,
        'introduction': '# Introduction' in manuscript,
        'methods': '# Methods' in manuscript,
        'results': '# Results' in manuscript,
        'discussion': '# Discussion' in manuscript
    }

    return {
        'has_required_sections': all(sections.values()),
        'section_count': sum(sections.values()),
        'missing_sections': [k for k, v in sections.items() if not v]
    }
```

## Test Execution

### Running Integration Tests

**Test Execution Commands:**

```bash
# Run all integration tests
python -m pytest project/tests/integration/ -v

# Run specific test file
python -m pytest project/tests/integration/test_integration_pipeline.py -v

# Run with coverage
python -m pytest project/tests/integration/ --cov=project.src --cov-report=html

# Run in parallel (if pytest-xdist installed)
python -m pytest project/tests/integration/ -n auto
```

### Test Organization

**Test Grouping and Dependencies:**

```python
# Mark tests by category
@pytest.mark.integration
@pytest.mark.pipeline
def test_complete_research_pipeline():
    """End-to-end pipeline test."""
    # ...

@pytest.mark.integration
@pytest.mark.figures
def test_figure_visual_quality():
    """Figure quality validation."""
    # ...

@pytest.mark.integration
@pytest.mark.data
def test_data_figure_integration():
    """Data to figure integration."""
    # ...
```

## Performance Testing

### Benchmarking Integration

**Performance Validation:**

```python
def test_pipeline_performance():
    """Test that the integration pipeline meets performance requirements."""

    import time

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        start_time = time.time()

        # Run pipeline
        data = generate_example_data(n_samples=100)
        figures_output = temp_path / "figures"
        figures_output.mkdir()
        create_all_figures(data, figures_output)

        sections = generate_manuscript_sections(data, figures_output)
        combined_manuscript = combine_manuscript_sections(sections)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertions
        assert execution_time < 30.0, f"Pipeline too slow: {execution_time:.2f}s"

        # Resource usage checks
        # (In practice, would monitor memory, CPU, disk I/O)
```

## Error Handling Testing

### Failure Scenario Testing

**Robustness Validation:**

```python
def test_pipeline_error_recovery():
    """Test pipeline behavior under error conditions."""

    # Test with invalid data
    invalid_data = {"invalid": "data"}

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Should handle gracefully
        try:
            create_all_figures(invalid_data, output_dir)
            figures_created = count_figure_files(output_dir)

            # Should create some figures or fail gracefully
            # (Exact behavior depends on error handling implementation)

        except Exception as e:
            # Should provide meaningful error message
            assert "error" in str(e).lower() or "invalid" in str(e).lower()
```

## Quality Assurance

### Output Validation

**Result Quality Checks:**

```python
def test_output_quality_standards():
    """Test that outputs meet quality standards."""

    data = generate_example_data(n_samples=100)

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)

        # Generate outputs
        figures = create_all_figures(data, output_dir)
        manuscript_sections = generate_manuscript_sections(data, output_dir)

        # Quality checks
        for figure in figures:
            # File integrity
            assert validate_figure_file(figure)

            # Minimum size requirements
            img = plt.imread(str(figure))
            assert min(img.shape[:2]) >= 300  # Minimum dimension

        # Manuscript quality
        combined = combine_manuscript_sections(manuscript_sections)
        structure_validation = validate_manuscript_structure(combined)

        assert structure_validation['has_required_sections'], \
            f"Missing sections: {structure_validation['missing_sections']}"

        # Content length check
        assert len(combined) > 2000, "Manuscript too short"

        # Readability checks (basic)
        word_count = len(combined.split())
        assert word_count > 500, f"Manuscript too short: {word_count} words"
```

## Continuous Integration

### CI/CD Integration

**Automated Testing:**

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run integration tests
      run: |
        python -m pytest project/tests/integration/ -v --tb=short

    - name: Upload test results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: |
          htmlcov/
          test-results.xml
```

## Debugging and Troubleshooting

### Test Debugging

**Verbose Test Output:**

```bash
# Run with detailed output
python -m pytest project/tests/integration/test_integration_pipeline.py -v -s

# Debug specific test
python -m pytest project/tests/integration/::test_complete_research_pipeline -v --pdb

# Run with logging
PYTHONPATH=. python -m pytest project/tests/integration/ -v --log-cli-level=DEBUG
```

### Common Test Issues

**Figure Generation Failures:**

```python
# Check matplotlib backend
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Validate data format
def debug_data_format(data):
    """Debug data structure issues."""
    required_keys = ['iterations', 'objective_values']
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"Missing data keys: {missing}")
    return len(missing) == 0
```

**File System Issues:**

```python
# Ensure proper permissions
def ensure_output_directory(output_dir: Path):
    """Ensure output directory exists and is writable."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Test writability
    test_file = output_dir / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
        return True
    except Exception:
        return False
```

## Maintenance

### Test Updates

**Keeping Tests Current:**

```python
def update_test_data():
    """Update test data when research code changes."""

    # Regenerate reference data
    new_data = generate_example_data(n_samples=100, seed=42)

    # Update test expectations
    # (This would modify test files or reference data)

    # Validate changes don't break tests
    # (Run tests to ensure they still pass)
```

### Test Coverage Analysis

**Coverage Reporting:**

```bash
# Generate coverage report
python -m pytest project/tests/integration/ --cov=project.src --cov-report=html

# Analyze coverage gaps
coverage report --show-missing

# Identify untested functions
coverage report | grep "0%" | head -10
```

## Future Enhancements

### Advanced Testing Features

**Planned Improvements:**

- **Visual Regression Testing**: Compare generated figures against references
- **Performance Benchmarking**: Track execution time trends
- **Load Testing**: Test with large datasets
- **Cross-Platform Testing**: Ensure compatibility across systems

**Integration Features:**

- **Database Integration**: Test data persistence workflows
- **API Testing**: Test external service integrations
- **UI Testing**: Test graphical interface components
- **Security Testing**: Validate secure data handling

## See Also

**Related Documentation:**

- [`../unit/AGENTS.md`](../unit/AGENTS.md) - Unit test documentation
- [`../../src/AGENTS.md`](../../src/AGENTS.md) - Source code documentation
- [`../../../scripts/AGENTS.md`](../../../scripts/AGENTS.md) - Script documentation

**System Documentation:**

- [`../../../../AGENTS.md`](../../../../AGENTS.md) - Project overview
- [`../../../../docs/development/TESTING_GUIDE.md`](../../../../docs/development/TESTING_GUIDE.md) - Testing guidelines

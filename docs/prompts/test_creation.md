# Test Creation Prompt

## Purpose

Create test suites that validate code functionality using data only, ensuring full compliance with testing standards and coverage requirements.

## Context

This prompt enforces the strict no-mocks testing policy and leverages testing standards:

- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing standards and no-mocks policy
- [`../development/TESTING_GUIDE.md`](../development/TESTING_GUIDE.md) - Testing guide and expansion strategy
- [`../core/WORKFLOW.md`](../core/WORKFLOW.md) - Development workflow integration

## Prompt Template

```
You are creating tests for the Research Project Template. ALL TESTS MUST USE DATA ONLY - NO MOCKS, NO PATCHING, NO SIMULATIONS. Tests must validate actual functionality with real inputs and outputs.

CODE TO TEST: [Specify the module/function/class to test]
LAYER: [Specify: "infrastructure" (60% coverage) OR "project" (90% coverage)]

TESTING REQUIREMENTS:

## 1. No Mocks Policy - ABSOLUTE REQUIREMENT

**CRITICAL**: Under no circumstances use MagicMock, mocker.patch, unittest.mock, or any mocking framework. All tests must use data and computations only.

### Valid Testing Approaches
```python
# ✅ GOOD: HTTP testing with pytest-httpserver
def test_api_call(httpserver):
    """Test real API call with local test server."""
    httpserver.expect_request("/api/data").respond_with_json({"result": "ok"})

    client = APIClient(base_url=httpserver.url_for("/"))
    response = client.get_data()  # HTTP request

    assert response["result"] == "ok"

# ✅ GOOD: file system operations
def test_file_processing(tmp_path):
    """Test file processing with real temporary files."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    processor = FileProcessor()
    result = processor.process_file(test_file)  # file operations

    assert result is not None

# ✅ GOOD: database operations (with test database)
def test_database_operations(test_db):
    """Test database operations with test database."""
    repo = DataRepository(connection=test_db)

    # database operations
    repo.save_data({"key": "value"})
    retrieved = repo.get_data("key")

    assert retrieved["key"] == "value"
```

### Forbidden Mocking Approaches
```python
# ❌ BAD: Mocking prohibited
def test_with_mocks(mocker):
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"result": "ok"}

    mocker.patch('requests.get', return_value=mock_response)
    # This violates the no-mocks policy

# ❌ BAD: Patching prohibited
with patch('module.function') as mock_func:
    mock_func.return_value = "mocked"
    # This violates the no-mocks policy
```

## 2. Coverage Requirements

### Project Layer (90% Minimum)
- Test all critical code paths
- Cover edge cases and error conditions
- Validate all public APIs
- Test integration between modules

### Infrastructure Layer (60% Minimum)
- Test core functionality
- Cover common usage patterns
- Validate error handling
- Test module integration

### Coverage Validation
```bash
# Validate coverage requirements
pytest tests/ --cov=src --cov-fail-under=90  # Project layer
pytest tests/ --cov=infrastructure --cov-fail-under=60  # Infrastructure layer
```

## 3. Test Structure and Organization

### Test File Organization
```python
"""Tests for src/module_name.py"""
import pytest
from pathlib import Path
import numpy as np
from research_module import ResearchAlgorithm, ValidationError

class TestResearchAlgorithm:
    """Test suite for ResearchAlgorithm class."""

    @pytest.fixture
    def sample_data(self):
        """Provide test data."""
        return np.random.randn(100, 5)

    @pytest.fixture
    def algorithm_instance(self):
        """Provide configured algorithm instance."""
        return ResearchAlgorithm(config={"param": "value"})

    def test_initialization(self):
        """Test algorithm initialization with valid config."""
        config = {"learning_rate": 0.01, "max_iter": 100}
        algo = ResearchAlgorithm(config)

        assert algo.config["learning_rate"] == 0.01
        assert algo.max_iter == 100

    def test_algorithm_execution(self, sample_data, algorithm_instance):
        """Test algorithm execution with data."""
        result = algorithm_instance.run(sample_data)

        assert result is not None
        assert hasattr(result, 'converged')
        assert isinstance(result.converged, bool)

    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        algo = ResearchAlgorithm({})

        with pytest.raises(ValidationError):
            algo.run([])  # Invalid empty data

    @pytest.mark.parametrize("data_size", [10, 100, 1000])
    def test_scalability(self, data_size):
        """Test algorithm scalability with different data sizes."""
        data = np.random.randn(data_size, 3)
        algo = ResearchAlgorithm()

        result = algo.run(data)

        assert result.converged
        assert result.execution_time < 30  # Performance requirement
```

### Test Data Management
```python
class TestDataFixtures:
    """test data fixtures and generators."""

    @pytest.fixture
    def synthetic_dataset(self, tmp_path):
        """Generate synthetic research dataset."""
        data_file = tmp_path / "dataset.csv"

        # Generate real synthetic data
        np.random.seed(42)  # Reproducible
        data = np.random.normal(0, 1, (1000, 10))
        labels = np.random.randint(0, 2, 1000)

        df = pd.DataFrame(data, columns=[f'feature_{i}' for i in range(10)])
        df['label'] = labels
        df.to_csv(data_file, index=False)

        return data_file

    @pytest.fixture
    def real_algorithm_output(self, synthetic_dataset):
        """Generate real algorithm output for testing."""
        algo = ResearchAlgorithm()
        data = pd.read_csv(synthetic_dataset)

        return algo.train(data.drop('label', axis=1), data['label'])
```

## 4. Testing Patterns

### Unit Testing with Data
```python
def test_data_preprocessing():
    """Test data preprocessing with dataset."""
    # Load test dataset
    raw_data = load_test_dataset('raw_data.csv')

    # Apply preprocessing
    preprocessor = DataPreprocessor(config={"normalize": True})
    processed_data = preprocessor.process(raw_data)

    # Validate results
    assert processed_data.shape[0] == raw_data.shape[0]  # Same number of samples
    assert processed_data.mean().abs().max() < 0.1  # Properly normalized
    assert not processed_data.isnull().any().any()  # No missing values
```

### Integration Testing
```python
def test_complete_workflow(tmp_path):
    """Test research workflow integration."""
    # Setup data
    data_file = tmp_path / "experiment_data.csv"
    generate_experiment_data(data_file)

    # Execute workflow
    workflow = ResearchWorkflow(config={"output_dir": tmp_path})
    results = workflow.run(data_file)

    # Validate outputs exist and are correct
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "figures").exists()
    assert len(results["metrics"]) > 0

    # Validate result quality
    assert results["accuracy"] > 0.8
    assert results["convergence"] is True
```

### Performance Testing
```python
def test_algorithm_performance():
    """Test algorithm performance with data."""
    data = generate_large_dataset(size=10000)

    algo = ResearchAlgorithm()
    start_time = time.time()

    result = algo.run(data)

    execution_time = time.time() - start_time

    # Performance assertions
    assert execution_time < 60  # Must within 1 minute
    assert result.memory_usage < 500 * 1024 * 1024  # Under 500MB
    assert result.converged
```

### Edge Case Testing
```python
@pytest.mark.parametrize("edge_case,expected_error", [
    ([], "EmptyDatasetError"),
    (np.array([[np.nan] * 5] * 10), "NaNValuesError"),
    (np.array([[np.inf] * 5] * 10), "InfiniteValuesError"),
    (np.array([['text'] * 5] * 10), "InvalidDataTypeError"),
])
def test_edge_cases(edge_case, expected_error):
    """Test algorithm behavior with edge case inputs."""
    algo = ResearchAlgorithm()

    with pytest.raises(expected_error):
        algo.run(edge_case)
```

## 5. Test Quality Standards

### Test Naming and Documentation
```python
def test_gradient_descent_convergence_with_adaptive_learning_rate():
    """Test that gradient descent converges using adaptive learning rate scheduling.

    This test validates the convergence behavior of the gradient descent algorithm
    when using an adaptive learning rate schedule that reduces the learning rate
    over time. The test uses real optimization data and verifies that:

    1. The algorithm converges to a minimum
    2. The final loss is lower than the initial loss
    3. The learning rate decreases over iterations
    4. No numerical instabilities occur
    """
```

### Assertion Quality
```python
def test_optimization_results():
    """Test optimization algorithm produces valid results."""
    data = generate_optimization_test_data()
    optimizer = GradientDescentOptimizer()

    result = optimizer.optimize(data)

    # Meaningful assertions with real validation
    assert result.converged, "Algorithm must converge for valid optimization"
    assert result.final_loss < result.initial_loss * 0.1, "Must achieve significant loss reduction"
    assert np.all(np.isfinite(result.parameters)), "Parameters must be finite (no NaN/inf)"
    assert 0 < result.execution_time < 300, "Execution must in reasonable time"
```

## 6. Test Organization

### Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── test_algorithms.py            # Algorithm tests
├── test_data_processing.py       # Data processing tests
├── test_validation.py            # Validation function tests
├── test_integration.py           # End-to-end workflow tests
├── test_performance.py           # Performance regression tests
└── test_data/                    # test data files
    ├── small_dataset.csv
    ├── large_dataset.csv
    └── edge_cases.json
```

### Test Configuration
```python
# conftest.py - Shared test configuration
import pytest
import numpy as np
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def set_random_seed():
    """Ensure reproducible test results."""
    np.random.seed(42)

@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def real_dataset(test_data_dir):
    """Load test dataset."""
    import pandas as pd
    return pd.read_csv(test_data_dir / "real_dataset.csv")
```

## 7. Coverage Analysis and Improvement

### Coverage Validation
```bash
# Generate detailed coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Analyze uncovered lines
coverage report --show-missing

# Identify coverage gaps
coverage report | grep -E " [0-9]+%" | sort -k4 -n
```

### Coverage Improvement Strategy
```python
# Add tests for missed lines
def test_unhandled_edge_case():
    """Test previously untested edge case."""
    # This test targets specific uncovered lines
    data = create_specific_edge_case()

    with pytest.raises(ExpectedError):
        algorithm.process(data)
```

## Key Requirements

- [ ] **NO MOCKS**: data and computations only
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] test data generation and management
- [ ] error condition testing
- [ ] Integration testing for workflows
- [ ] Performance testing with time/memory limits
- [ ] Edge case validation
- [ ] Clear test naming and documentation
- [ ] Test organization and structure

## Standards Compliance Checklist

### Testing Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] No mocks policy strictly enforced
- [ ] Coverage requirements achieved (90% project, 60% infrastructure)
- [ ] Test organization with clear structure
- [ ] TDD approach (tests before/ alongside code)
- [ ] data testing patterns
- [ ] Integration testing included

### Code Quality Standards
- [ ] Type hints in test functions
- [ ] Clear test documentation
- [ ] Proper error handling in tests
- [ ] Performance considerations

## Example Usage

**Input:**
```
CODE TO TEST: src/optimization.py::GradientDescentOptimizer
LAYER: project
```

**Expected Output:**
- `tests/test_optimization.py` with 90%+ coverage
- data fixtures for all test cases
- Edge case testing with actual error conditions
- Integration tests for optimization workflows
- Performance validation tests
- No mocking or patching used anywhere

## Related Documentation

- [`../development/TESTING_GUIDE.md`](../development/TESTING_GUIDE.md) - Testing guide and expansion strategy
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing standards
- [`../core/WORKFLOW.md`](../core/WORKFLOW.md) - Development workflow integration
```

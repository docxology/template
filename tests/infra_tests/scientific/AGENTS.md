# Scientific Infrastructure Tests

## Overview

The `tests/infra_tests/scientific/` directory contains tests for the scientific computing infrastructure. These tests validate the scientific development tools, benchmarking capabilities, documentation generation, and validation features that support research workflows.

## Directory Structure

```
tests/infra_tests/scientific/
├── AGENTS.md                           # This technical documentation
├── __init__.py                        # Test package initialization
├── conftest.py                        # Test configuration and fixtures
├── test_benchmarking.py               # Performance benchmarking tests
├── test_documentation.py              # API documentation tests
├── test_scientific_dev.py             # Scientific development tests
├── test_stability.py                  # Numerical stability tests
├── test_templates.py                  # Research template tests
├── test_validation.py                 # Scientific validation tests
```

## Test Categories

### Scientific Development Tests

**Scientific Dev Tests (`test_scientific_dev.py`)**
- Scientific utility function validation
- Research workflow tool testing
- Best practices compliance checking
- Development environment validation

**Key Test Areas:**
```python
def test_scientific_utilities():
    """Test scientific utility functions."""
    from infrastructure.scientific.scientific_dev import (
        check_numerical_stability,
        validate_research_data,
        optimize_performance
    )

    # Test numerical stability checking
    stable_result = check_numerical_stability(lambda x: x**2 + 2*x + 1, [1, 2, 3])
    assert stable_result['stable'] is True

    # Test data validation
    valid_data = validate_research_data(test_dataset)
    assert valid_data['valid'] is True
    assert 'quality_score' in valid_data

    # Test performance optimization
    optimized_func = optimize_performance(slow_function)
    result = optimized_func(test_input)
    assert result == expected_output
```

### Benchmarking Tests

**Benchmarking Tests (`test_benchmarking.py`)**
- Performance measurement accuracy
- Benchmark result validation
- Statistical analysis of performance data
- Comparative benchmarking functionality

**Test Scenarios:**
```python
def test_performance_benchmarking():
    """Test performance benchmarking functionality."""
    from infrastructure.scientific.benchmarking import (
        benchmark_function,
        analyze_performance,
        compare_implementations
    )

    # Benchmark single function
    results = benchmark_function(target_function, test_inputs, iterations=100)
    assert 'mean_time' in results
    assert 'std_dev' in results
    assert 'min_time' in results
    assert 'max_time' in results

    # Analyze performance characteristics
    analysis = analyze_performance(results)
    assert 'performance_score' in analysis
    assert 'stability_rating' in analysis

    # Compare multiple implementations
    implementations = {
        'version1': func_v1,
        'version2': func_v2,
        'optimized': func_opt
    }

    comparison = compare_implementations(implementations, test_data)
    assert 'fastest' in comparison
    assert 'relative_performance' in comparison
    assert comparison['fastest'] == 'optimized'  # Expected result
```

### Documentation Tests

**Documentation Tests (`test_documentation.py`)**
- API documentation generation validation
- Documentation completeness checking
- Format and structure validation
- Cross-reference accuracy testing

**Test Coverage:**
```python
def test_api_documentation_generation():
    """Test API documentation generation."""
    from infrastructure.scientific.documentation import (
        generate_api_docs,
        validate_documentation,
        check_doc_completeness
    )

    # Generate documentation for test module
    docs = generate_api_docs(test_module_path)
    assert len(docs) > 0
    assert 'functions' in docs
    assert 'classes' in docs

    # Validate documentation structure
    validation = validate_documentation(docs)
    assert validation['valid'] is True
    assert len(validation['errors']) == 0

    # Check completeness
    completeness = check_doc_completeness(docs)
    assert completeness['score'] > 0.8  # At least 80% assert 'missing_docs' in completeness
```

### Stability Tests

**Stability Tests (`test_stability.py`)**
- Numerical stability analysis validation
- Algorithm robustness testing
- Edge case handling verification
- Convergence testing

**Test Implementation:**
```python
def test_numerical_stability():
    """Test numerical stability analysis."""
    from infrastructure.scientific.stability import (
        analyze_stability,
        test_edge_cases,
        check_convergence
    )

    # Analyze algorithm stability
    stability_report = analyze_stability(
        algorithm=unstable_algorithm,
        test_inputs=problematic_inputs,
        tolerance=1e-10
    )

    assert stability_report['stable'] is False
    assert 'condition_number' in stability_report
    assert stability_report['condition_number'] > 1e10  # Very ill-conditioned

    # Test edge cases
    edge_case_results = test_edge_cases(algorithm, edge_cases)
    assert len(edge_case_results['failures']) > 0

    # Check convergence behavior
    convergence = check_convergence(iterative_algorithm, initial_guess)
    assert convergence['converged'] is True
    assert convergence['iterations'] < 1000
```

### Template Tests

**Template Tests (`test_templates.py`)**
- Research workflow template validation
- Template variable substitution testing
- Template rendering accuracy
- Template customization verification

**Test Scenarios:**
```python
def test_research_templates():
    """Test research workflow templates."""
    from infrastructure.scientific.templates import (
        ResearchTemplate,
        ExperimentTemplate,
        AnalysisTemplate
    )

    # Test experiment template
    experiment = ExperimentTemplate()
    experiment.configure(
        hypothesis="New algorithm performs better",
        variables=['dataset_size', 'algorithm_version'],
        metrics=['accuracy', 'runtime', 'memory_usage']
    )

    # Render template
    rendered = experiment.render()
    assert "hypothesis" in rendered.lower()
    assert "dataset_size" in rendered.lower()
    assert "accuracy" in rendered.lower()

    # Test analysis template
    analysis = AnalysisTemplate()
    analysis.set_data_characteristics(
        data_type='tabular',
        size=10000,
        features=50,
        target_variable='outcome'
    )

    rendered = analysis.render()
    assert "tabular" in rendered
    assert "10000" in rendered
    assert "outcome" in rendered
```

### Validation Tests

**Validation Tests (`test_validation.py`)**
- Scientific validation rule testing
- Research data quality assessment
- Methodology validation checking
- Result reproducibility verification

**Test Coverage:**
```python
def test_scientific_validation():
    """Test scientific validation functionality."""
    from infrastructure.scientific.validation import (
        validate_research_data,
        check_methodology,
        verify_reproducibility
    )

    # Validate research data
    data_validation = validate_research_data(
        dataset=test_dataset,
        expected_format='tabular',
        required_columns=['feature1', 'feature2', 'target']
    )

    assert data_validation['valid'] is True
    assert data_validation['completeness'] > 0.95
    assert data_validation['quality_score'] > 0.8

    # Check methodology
    methodology_check = check_methodology(
        description=research_description,
        requirements=['statistical_analysis', 'validation_split', 'error_metrics']
    )

    assert methodology_check['complete'] is True
    assert 'statistical_analysis' in methodology_check['covered_requirements']

    # Verify reproducibility
    reproducibility = verify_reproducibility(
        code_version='v1.2.3',
        random_seed=42,
        environment_snapshot=env_snapshot
    )

    assert reproducibility['reproducible'] is True
    assert reproducibility['seed_set'] is True
    assert 'environment' in reproducibility
```

## Test Design Principles

### Research-Focused Testing

**Real Scientific Data Approach:**
- Tests use realistic scientific datasets and algorithms
- Validation against known research methodologies
- Performance benchmarks based on actual computational requirements
- Edge cases derived from real research scenarios

**Scientific Validation:**
```python
def validate_scientific_algorithm(algorithm, test_cases):
    """scientific validation of algorithms."""

    results = {
        'correctness': [],
        'performance': [],
        'stability': [],
        'scalability': []
    }

    for test_case in test_cases:
        # Test correctness
        result = algorithm(test_case['input'])
        correctness = validate_result(result, test_case['expected'])
        results['correctness'].append(correctness)

        # Test performance
        performance = benchmark_algorithm(algorithm, test_case['input'])
        results['performance'].append(performance)

        # Test stability
        stability = test_numerical_stability(algorithm, test_case['input'])
        results['stability'].append(stability)

        # Test scalability
        scalability = test_scalability(algorithm, test_case['input'])
        results['scalability'].append(scalability)

    # Aggregate results
    summary = {
        'overall_correctness': sum(results['correctness']) / len(results['correctness']),
        'average_performance': statistics.mean(results['performance']),
        'stability_score': min(results['stability']),  # Worst case
        'scalability_rating': assess_scalability(results['scalability'])
    }

    return summary
```

### Test Organization

**Domain-Specific Test Structure:**
- Algorithm-specific test modules
- Methodology validation test suites
- Performance benchmarking test collections
- Documentation quality test categories

**Scientific Test Data Management:**
```python
@pytest.fixture
def scientific_test_data():
    """Provide realistic scientific test datasets."""
    return {
        'tabular_data': load_research_dataset('clinical_trials.csv'),
        'time_series': generate_synthetic_time_series(length=1000, trend=0.1),
        'image_data': load_medical_images('mri_scans/', sample_size=50),
        'genomic_data': load_genomic_sequences('sequences.fasta', n_sequences=100),
        'network_data': generate_social_network(nodes=500, edges=2000),
        'spatial_data': load_geographic_data('environmental_samples.geojson')
    }

@pytest.fixture
def research_algorithms():
    """Provide research algorithms for testing."""
    return {
        'statistical_model': lambda data: run_linear_regression(data),
        'machine_learning': lambda data: train_neural_network(data),
        'optimization': lambda data: genetic_algorithm_optimization(data),
        'simulation': lambda params: monte_carlo_simulation(params),
        'clustering': lambda data: hierarchical_clustering(data),
        'dimensionality_reduction': lambda data: pca_reduction(data, n_components=10)
    }
```

## Test Infrastructure

### Scientific Fixtures

**Research Data Fixtures:**
```python
@pytest.fixture
def synthetic_research_dataset():
    """Generate synthetic research dataset."""
    np.random.seed(42)  # Reproducible

    n_samples, n_features = 1000, 20
    X = np.random.randn(n_samples, n_features)
    # Add some structure
    X[:, 0] = X[:, 1] + X[:, 2] * 0.5 + np.random.randn(n_samples) * 0.1
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    return pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)]), y

@pytest.fixture
def performance_test_cases():
    """Provide performance benchmarking test cases."""
    return [
        {'name': 'small_dataset', 'size': (100, 10), 'iterations': 100},
        {'name': 'medium_dataset', 'size': (1000, 50), 'iterations': 50},
        {'name': 'large_dataset', 'size': (10000, 100), 'iterations': 10},
        {'name': 'sparse_data', 'size': (5000, 200), 'sparsity': 0.1, 'iterations': 20}
    ]
```

### Validation Helpers

**Scientific Result Validation:**
```python
def validate_scientific_result(result, expected_properties):
    """Validate scientific computation results."""

    # Check result structure
    assert isinstance(result, dict), "Result must be a dictionary"
    assert 'converged' in result, "Must indicate convergence status"
    assert 'metrics' in result, "Must include evaluation metrics"

    # Validate convergence
    if expected_properties.get('should_converge', True):
        assert result['converged'] is True, "Algorithm should have converged"

    # Validate metrics
    metrics = result['metrics']
    for expected_metric in expected_properties.get('required_metrics', []):
        assert expected_metric in metrics, f"Missing required metric: {expected_metric}"

        metric_value = metrics[expected_metric]
        if 'metric_ranges' in expected_properties:
            min_val, max_val = expected_properties['metric_ranges'].get(expected_metric, (-float('inf'), float('inf')))
            assert min_val <= metric_value <= max_val, f"Metric {expected_metric} out of range: {metric_value}"

    # Validate computational properties
    if 'max_runtime' in expected_properties:
        assert result.get('runtime', 0) <= expected_properties['max_runtime'], "Exceeded maximum runtime"

    return True
```

## Running Tests

### Test Execution

```bash
# Run all scientific tests
pytest tests/infra_tests/scientific/

# Run specific scientific domain tests
pytest tests/infra_tests/scientific/test_stability.py

# Run performance benchmarking tests
pytest tests/infra_tests/scientific/test_benchmarking.py

# Run with performance profiling
pytest tests/infra_tests/scientific/ --durations=10
```

### Specialized Test Execution

**Performance-Focused Testing:**
```bash
# Run performance tests only
pytest tests/infra_tests/scientific/ -k "benchmark or performance"

# Run with memory profiling
pytest tests/infra_tests/scientific/ --memray

# Run scalability tests
pytest tests/infra_tests/scientific/ -k "scalability"
```

## Test Coverage and Quality

### Coverage Goals

**Scientific Module Coverage:**
- Scientific development tools: 95%+ coverage
- Benchmarking functionality: 90%+ coverage
- Documentation generation: 90%+ coverage
- Stability analysis: 95%+ coverage
- Template system: 85%+ coverage
- Validation tools: 90%+ coverage

### Quality Metrics

**Scientific Accuracy:**
- Algorithms produce mathematically correct results
- Statistical tests validate properly
- Performance benchmarks are reproducible
- Documentation examples execute correctly
- Validation rules match scientific standards

## Common Test Issues

### Numerical Precision Problems

**Floating Point Testing:**
```python
def test_numerical_precision():
    """Test numerical computations with appropriate precision."""

    # Use relative tolerance for floating point comparisons
    result = scientific_algorithm(test_input)
    expected = known_correct_result

    # Use numpy.testing for robust floating point comparison
    np.testing.assert_allclose(result, expected, rtol=1e-10, atol=1e-12)

    # Alternative: check relative error
    relative_error = abs(result - expected) / abs(expected)
    assert relative_error < 1e-10, f"Relative error too high: {relative_error}"
```

### Performance Benchmark Variability

**Stable Benchmarking:**
```python
def stable_performance_test():
    """Run performance tests with statistical stability."""

    # Run multiple times to account for variability
    runtimes = []
    for _ in range(10):  # Multiple runs
        start_time = time.perf_counter()
        result = algorithm(test_data)
        end_time = time.perf_counter()
        runtimes.append(end_time - start_time)

        # Verify correctness each time
        assert validate_result(result)

    # Statistical analysis of runtimes
    mean_runtime = statistics.mean(runtimes)
    std_runtime = statistics.stdev(runtimes)
    cv = std_runtime / mean_runtime  # Coefficient of variation

    # Accept results if low variability
    assert cv < 0.1, f"High runtime variability: CV = {cv}"

    return {
        'mean_runtime': mean_runtime,
        'std_runtime': std_runtime,
        'coefficient_of_variation': cv
    }
```

### Memory and Resource Issues

**Resource-Intensive Testing:**
```python
def test_large_scale_computation():
    """Test large-scale computations with resource management."""

    # Check available resources before testing
    available_memory = psutil.virtual_memory().available
    required_memory = estimate_memory_requirement(large_dataset)

    if available_memory < required_memory * 1.2:  # 20% buffer
        pytest.skip(f"Insufficient memory: {available_memory / 1e9:.1f}GB available, {required_memory / 1e9:.1f}GB required")

    # Run test with resource monitoring
    with memory_monitor() as mem_monitor:
        result = large_scale_algorithm(large_dataset)

    # Verify result correctness
    assert validate_large_result(result)

    # Check resource usage was reasonable
    peak_memory = mem_monitor.get_peak_memory()
    assert peak_memory < required_memory * 1.5  # Allow 50% overhead
```

## Integration with Research Workflow

### End-to-End Scientific Testing

**Research Pipeline Testing:**
```python
def test_research_pipeline():
    """Test research workflow with scientific tools."""

    # 1. Data validation
    data_validation = validate_research_data(raw_dataset)
    assert data_validation['valid']

    # 2. Algorithm selection and benchmarking
    algorithms = [algorithm1, algorithm2, algorithm3]
    benchmark_results = benchmark_algorithms(algorithms, validated_data)

    best_algorithm = select_best_algorithm(benchmark_results)
    assert best_algorithm is not None

    # 3. Stability analysis
    stability_report = analyze_stability(best_algorithm, validated_data)
    assert stability_report['stable']

    # 4. Documentation generation
    docs = generate_api_docs(best_algorithm)
    assert len(docs) > 0

    # 5. Result validation
    final_result = best_algorithm(validated_data)
    result_validation = validate_scientific_result(final_result, research_requirements)
    assert result_validation['valid']

    # 6. Reproducibility check
    reproducibility = verify_reproducibility(best_algorithm, validated_data, random_seed=42)
    assert reproducibility['reproducible']
```

## Future Test Enhancements

### Advanced Scientific Testing

**Planned Improvements:**
- **Statistical Power Analysis**: Test suite statistical validation
- **Algorithm Convergence Testing**: Advanced convergence analysis
- **Cross-Platform Scientific Testing**: Numerical consistency across platforms
- **GPU Acceleration Testing**: CUDA/OpenCL scientific computing validation

**Research Integration:**
- **Dataset Integration**: Tests with anonymized research datasets
- **Peer Review Simulation**: Automated scientific review process testing
- **Publication Readiness Validation**: Pre-publication checklist testing

## Troubleshooting

### Scientific Test Debugging

**Numerical Debugging:**
```python
def debug_numerical_issues():
    """Debug numerical computation issues."""

    # Test with simple inputs first
    simple_result = algorithm(simple_input)
    print(f"Simple input result: {simple_result}")

    # Gradually increase complexity
    for complexity_level in [1, 2, 3, 4, 5]:
        test_input = generate_complexity_level(complexity_level)
        try:
            result = algorithm(test_input)
            print(f"Complexity {complexity_level}: SUCCESS - {result}")
        except Exception as e:
            print(f"Complexity {complexity_level}: FAILED - {e}")
            break

    # Check numerical properties
    check_numerical_properties(algorithm, test_input)
```

**Performance Debugging:**
```bash
# Profile scientific computations
python3 -c "
import cProfile
from tests.infrastructure.scientific.test_benchmarking import benchmark_function

cProfile.run('benchmark_function(target_algorithm, test_data)', 'scientific_profile.prof')

# Analyze profile
import pstats
stats = pstats.Stats('scientific_profile.prof')
stats.sort_stats('cumulative').print_stats(20)
"
```

### Environment Validation

**Scientific Dependencies Check:**
```bash
# Validate scientific computing environment
python3 -c "
import sys
print(f'Python: {sys.version}')

# Core scientific libraries
libs = ['numpy', 'scipy', 'pandas', 'scikit-learn', 'matplotlib']
for lib in libs:
    try:
        __import__(lib)
        print(f'{lib}: ✓')
    except ImportError:
        print(f'{lib}: ✗')

# Check BLAS/LAPACK
try:
    import numpy as np
    print(f'BLAS/LAPACK: {\"✓\" if np.__config__.blas_opt_info else \"✗\"}')
except:
    print('BLAS/LAPACK: Unable to check')
"
```

## See Also

**Related Documentation:**
- [`../../../infrastructure/scientific/AGENTS.md`](../../../infrastructure/scientific/AGENTS.md) - Scientific module details
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure test suite overview
- [`../../../AGENTS.md`](../../../AGENTS.md) - System documentation

**Testing Standards:**
- [`../../../.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing standards
- [`../../../docs/development/testing-guide.md`](../../../docs/development/testing-guide.md) - Testing guide
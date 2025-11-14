# Scientific Simulation and Analysis System Guide

## Overview

This guide provides comprehensive documentation for the scientific simulation, analysis, reporting, validation, visualization, and image management system integrated into the research template.

## Architecture

The system follows the **thin orchestrator pattern**:

- **Business Logic**: All algorithms, simulations, and analysis in `src/` modules
- **Thin Orchestrators**: Scripts in `scripts/` import and use `src/` methods
- **100% Test Coverage**: All `src/` modules fully tested
- **Automated Integration**: Figures automatically inserted with captions and references

## Core Modules

### Simulation Framework (`src/simulation.py`)

Provides a robust simulation engine with reproducibility, checkpointing, and result serialization.

**Key Classes:**
- `SimulationBase`: Abstract base class for simulations
- `SimulationState`: Represents simulation state
- `SimpleSimulation`: Example implementation

**Usage:**
```python
from simulation import SimpleSimulation

# Create simulation
sim = SimpleSimulation(
    parameters={"max_iterations": 100, "target_value": 5.0},
    seed=42,
    output_dir="output/simulations"
)

# Run simulation
state = sim.run(max_iterations=100, verbose=True)

# Save results
saved_files = sim.save_results("simulation_results")
```

### Parameter Management (`src/parameters.py`)

Manages parameter sets with validation, sweeps, and serialization.

**Key Classes:**
- `ParameterSet`: Parameter set with validation
- `ParameterConstraint`: Validation constraints
- `ParameterSweep`: Parameter sweep configurations

**Usage:**
```python
from parameters import ParameterSet, ParameterSweep

# Create parameter set
params = ParameterSet()
params.add_parameter("learning_rate", 0.01)
params.add_parameter("batch_size", 32)

# Validate
is_valid, errors = params.validate()

# Create parameter sweep
sweep = ParameterSweep(params)
sweep.add_sweep("learning_rate", [0.001, 0.01, 0.1])
combinations = sweep.generate_combinations()
```

### Data Generation (`src/data_generator.py`)

Generates synthetic data with configurable distributions and noise injection.

**Key Functions:**
- `generate_synthetic_data()`: Generate data with specified distribution
- `generate_time_series()`: Generate time series data
- `generate_correlated_data()`: Generate correlated multivariate data
- `inject_noise()`: Inject noise into data
- `validate_data()`: Validate data quality

**Usage:**
```python
from data_generator import generate_synthetic_data, generate_time_series

# Generate normal distribution
data = generate_synthetic_data(100, distribution="normal", seed=42)

# Generate time series
time, values = generate_time_series(100, trend="sinusoidal", seed=42)
```

## Analysis Framework

### Statistical Analysis (`src/statistics.py`)

Provides descriptive statistics, hypothesis testing, correlation analysis, and distribution fitting.

**Key Functions:**
- `calculate_descriptive_stats()`: Calculate descriptive statistics
- `t_test()`: Perform t-test
- `calculate_correlation()`: Calculate correlation
- `anova_test()`: Perform ANOVA test
- `fit_distribution()`: Fit distribution to data

**Usage:**
```python
from statistics import calculate_descriptive_stats, calculate_correlation

# Calculate statistics
stats = calculate_descriptive_stats(data)
print(f"Mean: {stats.mean}, Std: {stats.std}")

# Calculate correlation
corr = calculate_correlation(x, y, method="pearson")
```

### Performance Analysis (`src/performance.py`)

Analyzes convergence, scalability, and efficiency.

**Key Functions:**
- `analyze_convergence()`: Analyze convergence of sequence
- `analyze_scalability()`: Analyze algorithm scalability
- `calculate_speedup()`: Calculate speedup
- `benchmark_comparison()`: Compare methods

**Usage:**
```python
from performance import analyze_convergence, analyze_scalability

# Analyze convergence
convergence = analyze_convergence(values, target=0.0)
print(f"Converged: {convergence.is_converged}")

# Analyze scalability
scalability = analyze_scalability(problem_sizes, execution_times)
print(f"Complexity: {scalability.time_complexity}")
```

### Data Processing (`src/data_processing.py`)

Provides data cleaning, preprocessing, normalization, and outlier detection.

**Key Functions:**
- `clean_data()`: Clean invalid values
- `normalize_data()`: Normalize data
- `detect_outliers()`: Detect outliers
- `remove_outliers()`: Remove outliers

**Usage:**
```python
from data_processing import clean_data, normalize_data, detect_outliers

# Clean data
cleaned = clean_data(data, remove_nan=True, fill_method="mean")

# Normalize
normalized, params = normalize_data(data, method="z_score")

# Detect outliers
outlier_mask, info = detect_outliers(data, method="iqr")
```

## Reporting and Validation

### Report Generation (`src/reporting.py`)

Generates automated reports from simulation results.

**Key Classes:**
- `ReportGenerator`: Generate reports in multiple formats

**Usage:**
```python
from reporting import ReportGenerator

report_gen = ReportGenerator(output_dir="output/reports")
results = {
    "summary": {"mean": 1.0, "std": 0.5},
    "findings": ["Finding 1", "Finding 2"]
}
report_path = report_gen.generate_markdown_report("Report Title", results)
```

### Validation Framework (`src/validation.py`)

Validates results, checks reproducibility, and detects anomalies.

**Key Classes:**
- `ValidationFramework`: Validation framework
- `ValidationResult`: Validation result

**Usage:**
```python
from validation import ValidationFramework

validator = ValidationFramework()
validator.validate_bounds(data, "test_data", min_value=0, max_value=10)
validator.detect_anomalies(data, method="iqr")
report = validator.generate_validation_report()
```

### Metrics Calculation (`src/metrics.py`)

Calculates performance, convergence, and quality metrics.

**Key Functions:**
- `calculate_accuracy()`: Calculate classification accuracy
- `calculate_precision_recall_f1()`: Calculate precision, recall, F1
- `calculate_convergence_metrics()`: Calculate convergence metrics
- `calculate_snr()`: Calculate signal-to-noise ratio

**Usage:**
```python
from metrics import calculate_accuracy, calculate_precision_recall_f1

accuracy = calculate_accuracy(predictions, targets)
prf = calculate_precision_recall_f1(predictions, targets)
```

## Visualization System

### Visualization Engine (`src/visualization.py`)

Provides publication-quality figure generation.

**Key Classes:**
- `VisualizationEngine`: Main visualization engine

**Usage:**
```python
from visualization import VisualizationEngine

engine = VisualizationEngine(output_dir="output/figures")
fig, ax = engine.create_figure()
# ... plot on ax ...
engine.save_figure(fig, "figure_name")
```

### Plot Types (`src/plots.py`)

Provides various plot types: line, scatter, bar, heatmap, contour, 3D.

**Key Functions:**
- `plot_line()`: Create line plot
- `plot_scatter()`: Create scatter plot
- `plot_bar()`: Create bar chart
- `plot_convergence()`: Plot convergence curve

**Usage:**
```python
from plots import plot_line, plot_convergence

ax = plot_line(x, y, label="Data")
ax = plot_convergence(iterations, values, target=0.0)
```

### Figure Management (`src/figure_manager.py`)

Manages figures with automatic numbering, captioning, and cross-referencing.

**Key Classes:**
- `FigureManager`: Manages figure registry
- `FigureMetadata`: Figure metadata

**Usage:**
```python
from figure_manager import FigureManager

manager = FigureManager()
fig_meta = manager.register_figure(
    filename="figure.png",
    caption="Figure caption",
    section="experimental_results"
)
latex_block = manager.generate_latex_figure_block(fig_meta.label)
```

## Image Management

### Image Manager (`src/image_manager.py`)

Automatically inserts figures into markdown files with captions and references.

**Key Classes:**
- `ImageManager`: Manages image insertion

**Usage:**
```python
from image_manager import ImageManager

manager = ImageManager()
manager.insert_figure(markdown_file, figure_label, section="Results")
manager.insert_reference(markdown_file, figure_label)
```

### Markdown Integration (`src/markdown_integration.py`)

Integrates figures and references into markdown files.

**Key Classes:**
- `MarkdownIntegration`: Markdown integration system

**Usage:**
```python
from markdown_integration import MarkdownIntegration

integration = MarkdownIntegration(manuscript_dir="manuscript")
integration.insert_figure_in_section(markdown_file, figure_label, "Results")
integration.validate_manuscript()
```

## Example Scripts

### Scientific Simulation (`scripts/scientific_simulation.py`)

Demonstrates complete simulation workflow:
1. Set up parameters
2. Run simulations
3. Generate results and figures
4. Create analysis reports

**Run:**
```bash
python3 scripts/scientific_simulation.py
```

### Analysis Pipeline (`scripts/analysis_pipeline.py`)

Demonstrates statistical analysis workflow:
1. Load simulation results
2. Perform statistical analysis
3. Generate comparison plots
4. Create summary reports

**Run:**
```bash
python3 scripts/analysis_pipeline.py
```

### Generate Scientific Figures (`scripts/generate_scientific_figures.py`)

Automated figure generation workflow:
1. Run simulations
2. Perform analysis
3. Generate visualizations
4. Insert figures with captions automatically
5. Update cross-references

**Run:**
```bash
python3 scripts/generate_scientific_figures.py
```

## Integration with Build System

The scientific simulation system integrates seamlessly with the existing build pipeline:

1. **Scripts are automatically executed** by `render_pdf.sh`
2. **Figures are generated** in `output/figures/`
3. **Figures are registered** in `output/figures/figure_registry.json`
4. **Figures can be automatically inserted** into markdown files
5. **Cross-references work** with LaTeX compilation

## Best Practices

1. **Use src/ modules for all business logic** - Scripts should only orchestrate
2. **Register all figures** - Use `FigureManager` to track figures
3. **Validate results** - Use `ValidationFramework` to check outputs
4. **Generate reports** - Use `ReportGenerator` for documentation
5. **Follow reproducibility** - Always use seeds for random operations
6. **Test thoroughly** - Ensure 100% test coverage for all `src/` modules

## See Also

- [`ANALYSIS_FRAMEWORK.md`](ANALYSIS_FRAMEWORK.md) - Detailed analysis framework guide
- [`VISUALIZATION_GUIDE.md`](VISUALIZATION_GUIDE.md) - Visualization best practices
- [`IMAGE_MANAGEMENT.md`](IMAGE_MANAGEMENT.md) - Image management guide


# src/ - Core Business Logic

## Purpose

The `src/` directory contains **all core business logic, algorithms, and mathematical implementations** for the project. This is the single source of truth for computational functionality.

## Architectural Role

### Thin Orchestrator Pattern

In this architecture:
- **`src/`** = Core business logic (100% tested)
- **`scripts/`** = Thin orchestrators (import and use `src/` methods)
- **`tests/`** = Validation (100% coverage required)

Scripts **never** implement algorithms - they import and use `src/` methods.

## Module Organization

### Core Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `example.py` | Basic mathematical operations (template example) | 95 | 100% |
| `glossary_gen.py` | API documentation generation from source code | 123 | 100% |
| `pdf_validator.py` | PDF rendering validation and issue detection | 186 | 88% |

### Data Processing Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `data_generator.py` | Synthetic data generation with configurable distributions | 107 | 84% |
| `data_processing.py` | Data cleaning, preprocessing, normalization, outlier detection | 137 | 78% |
| `statistics.py` | Descriptive statistics, hypothesis testing, correlation analysis | 79 | 92% |
| `metrics.py` | Performance metrics, convergence metrics, quality metrics | 96 | 79% |
| `validation.py` | Result validation, reproducibility verification, anomaly detection | 93 | 92% |

### Visualization & Figure Management Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `visualization.py` | Publication-quality figure generation with consistent styling | 68 | 84% |
| `plots.py` | Plot type implementations (line, scatter, bar, heatmap, contour) | 84 | 67% |
| `figure_manager.py` | Automatic figure numbering, caption generation, cross-referencing | 84 | 92% |
| `image_manager.py` | Automatic image insertion into markdown, caption management | 91 | 72% |
| `markdown_integration.py` | LaTeX figure block generation, section detection, reference insertion | 85 | 85% |

### Simulation & Analysis Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `simulation.py` | Core simulation framework with reproducibility and checkpointing | 141 | 78% |
| `parameters.py` | Parameter set management, validation, sweeps, serialization | 92 | 95% |
| `performance.py` | Convergence analysis, scalability metrics, benchmark comparisons | 108 | 79% |
| `reporting.py` | Automated report generation from simulation results | 149 | 78% |

### Advanced Modules

| Module | Purpose | Lines | Test Coverage |
|--------|---------|-------|---------------|
| `build_verifier.py` | Build artifact verification and validation | 1036 | 66% |
| `integrity.py` | Output integrity checking and cross-references | 753 | 79% |
| `quality_checker.py` | Document quality analysis and metrics | 624 | 87% |
| `reproducibility.py` | Environment tracking and build manifests | 758 | 74% |
| `publishing.py` | Academic publishing workflow assistance | 872 | 81% |
| `scientific_dev.py` | Scientific computing best practices | 978 | 86% |

## Directory Files

### .gitkeep File

The `.gitkeep` file in `src/` is a placeholder used by git to track empty directories. It serves a historical purpose:

- **Purpose**: Ensures `src/` directory is tracked in git even when initially empty
- **History**: Created during initial template setup before any modules existed
- **Current Status**: Directory now contains 23+ Python modules
- **Can be safely deleted**: No longer needed since directory has content

The `.gitkeep` file has no effect on the build system or code execution.

## Requirements

### Test Coverage
- **100% coverage required** for all modules
- No code ships without tests
- Real data testing (no mocks policy)
- Tests live in `tests/` directory

### Code Standards
- Type hints on all public APIs
- Comprehensive docstrings
- Pure functions preferred
- Clear error messages
- Follow PEP 8 style

## Import Patterns

### From Scripts
```python
# In scripts/example_figure.py
import sys
import os

def _ensure_src_on_path():
    """Ensure src/ is on Python path."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(repo_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

_ensure_src_on_path()

# Now import from src/
from example import add_numbers, calculate_average
```

### From Tests
```python
# Tests automatically have src/ on path via conftest.py
from example import add_numbers
from quality_checker import analyze_document_quality
from data_generator import generate_synthetic_data
from statistics import calculate_descriptive_stats
from visualization import VisualizationEngine
```

### From Repo Utilities
```python
# In repo_utilities/validate_pdf_output.py
sys.path.insert(0, str(repo_root / "src"))
from pdf_validator import validate_pdf_rendering
```

## Module Descriptions

### example.py
Template module demonstrating basic patterns:
- `add_numbers()`, `multiply_numbers()` - Basic operations
- `calculate_average()` - Statistical functions
- `find_maximum()`, `find_minimum()` - Data analysis
- `is_even()`, `is_odd()` - Validation helpers

### glossary_gen.py
Generates API documentation from source code:
- `build_api_index()` - Scans src/ and extracts public APIs
- `generate_markdown_table()` - Creates formatted tables
- `inject_between_markers()` - Updates documentation files

### pdf_validator.py
Validates PDF rendering quality:
- `extract_text_from_pdf()` - Text extraction
- `scan_for_issues()` - Detects unresolved references, warnings
- `validate_pdf_rendering()` - Comprehensive validation

### build_verifier.py
Comprehensive build verification:
- `run_build_command()` - Execute and monitor builds
- `verify_build_artifacts()` - Check expected outputs
- `verify_build_reproducibility()` - Multiple build consistency
- `verify_build_environment()` - Dependency validation

### integrity.py
Output integrity verification:
- `verify_file_integrity()` - Hash-based validation
- `verify_cross_references()` - Markdown cross-refs
- `verify_academic_standards()` - Research document compliance
- `verify_output_completeness()` - All expected files present

### quality_checker.py
Document quality analysis:
- `analyze_readability()` - Flesch score, Gunning Fog
- `analyze_academic_standards()` - Research writing compliance
- `analyze_structural_integrity()` - Document organization
- `calculate_overall_quality_score()` - Comprehensive metrics

### reproducibility.py
Build reproducibility tracking:
- `capture_environment_state()` - System snapshot
- `generate_reproducibility_report()` - Build manifest
- `verify_reproducibility()` - Compare builds
- `create_reproducible_environment()` - Environment setup

### publishing.py
Academic publishing assistance:
- `extract_publication_metadata()` - Parse manuscript data
- `generate_citation_bibtex()` - BibTeX format
- `validate_doi()` - DOI format validation
- `create_publication_package()` - Submission bundle

### scientific_dev.py
Scientific computing best practices:
- `check_numerical_stability()` - Algorithm stability
- `benchmark_function()` - Performance analysis
- `generate_scientific_documentation()` - API docs
- `validate_scientific_implementation()` - Correctness checks

### data_generator.py
Synthetic data generation:
- `generate_synthetic_data()` - Generate data with specified distribution
- `generate_time_series()` - Generate time series with trends
- `generate_correlated_data()` - Generate correlated multivariate data
- `inject_noise()` - Add noise to data
- `generate_classification_dataset()` - Generate classification datasets
- `validate_data()` - Validate data quality

### data_processing.py
Data preprocessing and cleaning:
- `clean_data()` - Remove or fill invalid values
- `normalize_data()` - Normalize using z-score, min-max, or unit vector
- `standardize_data()` - Standardize to zero mean and unit variance
- `detect_outliers()` - Detect outliers using IQR or z-score
- `remove_outliers()` - Remove outliers from data
- `extract_features()` - Extract statistical features
- `transform_data()` - Apply transformations (log, sqrt, etc.)
- `create_validation_pipeline()` - Create data validation pipeline

### statistics.py
Statistical analysis:
- `calculate_descriptive_stats()` - Calculate mean, std, quartiles, etc.
- `t_test()` - Perform t-test (one-sample or two-sample)
- `calculate_correlation()` - Calculate Pearson or Spearman correlation
- `calculate_confidence_interval()` - Calculate confidence intervals
- `fit_distribution()` - Fit distributions to data
- `anova_test()` - Perform one-way ANOVA

### metrics.py
Performance and quality metrics:
- `calculate_accuracy()` - Classification accuracy
- `calculate_precision_recall_f1()` - Precision, recall, F1 score
- `calculate_convergence_metrics()` - Convergence analysis metrics
- `calculate_snr()` - Signal-to-Noise Ratio
- `calculate_psnr()` - Peak Signal-to-Noise Ratio
- `calculate_ssim()` - Structural Similarity Index
- `calculate_effect_size()` - Cohen's d effect size
- `calculate_all_metrics()` - Calculate all applicable metrics

### validation.py
Result validation framework:
- `ValidationFramework` - Framework for validating results
- `validate_bounds()` - Validate values are within bounds
- `validate_sanity()` - Perform sanity checks on values
- `validate_reproducibility()` - Validate reproducibility between runs
- `detect_anomalies()` - Detect anomalies in results
- `validate_quality_metrics()` - Validate quality metrics
- `generate_validation_report()` - Generate validation report

### visualization.py
Publication-quality visualization:
- `VisualizationEngine` - Engine for generating publication-quality figures
- `create_figure()` - Create figure with subplots
- `save_figure()` - Save figure in multiple formats
- `apply_publication_style()` - Apply publication styling
- `create_multi_panel_figure()` - Create multi-panel figures

### plots.py
Plot type implementations:
- `plot_line()` - Create line plots
- `plot_scatter()` - Create scatter plots
- `plot_bar()` - Create bar charts
- `plot_heatmap()` - Create heatmaps
- `plot_contour()` - Create contour plots
- `plot_convergence()` - Create convergence plots
- `plot_comparison()` - Create comparison plots

### figure_manager.py
Figure management and cross-referencing:
- `FigureManager` - Manages figures with automatic numbering
- `register_figure()` - Register a new figure
- `get_figure()` - Get figure metadata by label
- `generate_latex_figure_block()` - Generate LaTeX figure block
- `generate_reference()` - Generate LaTeX reference
- `generate_figure_list()` - Generate list of all figures
- `generate_table_of_figures()` - Generate LaTeX table of figures

### image_manager.py
Image insertion and management:
- `ImageManager` - Manages image insertion into markdown files
- `insert_figure()` - Insert figure into markdown file
- `insert_reference()` - Insert figure reference
- `validate_figures()` - Validate all figures in markdown

### markdown_integration.py
Markdown integration:
- `MarkdownIntegration` - Integrates figures and references into markdown
- `detect_sections()` - Detect sections in markdown file
- `insert_figure_in_section()` - Insert figure in specific section
- `generate_table_of_figures()` - Generate table of figures markdown
- `update_all_references()` - Update all figure references
- `validate_manuscript()` - Validate all figures in manuscript
- `get_figure_statistics()` - Get statistics about figures

### simulation.py
Core simulation framework:
- `SimulationBase` - Base class for scientific simulations
- `SimpleSimulation` - Simple simulation implementation
- `SimulationState` - Represents simulation state
- Provides reproducibility, checkpointing, result serialization

### parameters.py
Parameter management:
- `ParameterSet` - Parameter set with validation
- `ParameterConstraint` - Constraint for parameter validation
- `ParameterSweep` - Configuration for parameter sweeps
- `add_parameter()` - Add parameter with constraint
- `validate()` - Validate all parameters
- `generate_combinations()` - Generate parameter combinations

### performance.py
Performance analysis:
- `analyze_convergence()` - Analyze convergence of sequences
- `analyze_scalability()` - Analyze scalability metrics
- `benchmark_comparison()` - Compare benchmark results
- `ConvergenceMetrics` - Metrics for convergence analysis

### reporting.py
Automated report generation:
- `ReportGenerator` - Generate reports from results
- `generate_markdown_report()` - Generate markdown report
- `generate_summary_table()` - Generate summary statistics table
- `extract_key_findings()` - Extract key findings from results

## Adding New Modules

### Checklist
1. Create module in `src/` with type hints and docstrings
2. Add comprehensive tests in `tests/test_<module>.py`
3. Ensure 100% test coverage
4. Update this documentation
5. Add to import examples if commonly used
6. Run full test suite to verify integration

### Template
```python
"""Module description.

This module provides functionality for [purpose].
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any


def public_function(arg: str) -> str:
    """Function description.
    
    Args:
        arg: Argument description
        
    Returns:
        Return value description
        
    Raises:
        ValueError: When input is invalid
    """
    if not arg:
        raise ValueError("arg cannot be empty")
    return f"processed: {arg}"
```

## Integration Points

- **Scripts**: Import and use src/ methods for all computation
- **Tests**: Validate src/ functionality with 100% coverage
- **Repo Utilities**: Use src/ for validation and analysis
- **Glossary**: Auto-generate API docs from src/ modules

## Best Practices

1. **Pure Functions**: Prefer stateless functions with no side effects
2. **Type Safety**: Use type hints extensively
3. **Documentation**: Every public API needs docstrings
4. **Error Handling**: Clear, actionable error messages
5. **Testing**: Write tests first (TDD)
6. **Modularity**: Single responsibility per function
7. **Performance**: Profile before optimizing
8. **Compatibility**: Support Python 3.10+

## See Also

- [`tests/AGENTS.md`](../tests/AGENTS.md) - Testing philosophy and organization
- [`scripts/AGENTS.md`](../scripts/AGENTS.md) - How scripts use src/ modules
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Pattern details





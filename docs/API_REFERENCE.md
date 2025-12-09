# API Reference

> **Complete API documentation** for all infrastructure modules

**Quick Reference:** [Advanced Modules Guide](ADVANCED_MODULES_GUIDE.md) | [Infrastructure Docs](../infrastructure/AGENTS.md) | [Getting Started](GETTING_STARTED.md)

This document provides comprehensive API reference for all public functions and classes in the `infrastructure/` modules. All modules follow the thin orchestrator pattern with comprehensive test coverage.

**Note**: These modules are part of the infrastructure layer. For project-specific code, see `project/src/`.

## Module Organization

This API reference covers modules from both the **infrastructure layer** (reusable, generic tools) and the **project layer** (project-specific scientific code).

### Infrastructure Modules (Layer 1 - Generic, Reusable)

These modules are located in `infrastructure/` and provide generic tools applicable to any research project:

#### Documentation & API Generation
- `infrastructure/documentation/glossary_gen.py` - API documentation generation from source code

#### Validation & Quality Assurance
- `infrastructure/validation/pdf_validator.py` - PDF rendering validation
- `infrastructure/validation/integrity.py` - Output integrity verification
- `infrastructure/build/quality_checker.py` - Document quality analysis

#### Build & Reproducibility
- `infrastructure/build/build_verifier.py` - Build process validation
- `infrastructure/build/reproducibility.py` - Environment tracking and reproducibility

#### Scientific Computing
- `infrastructure/scientific/scientific_dev.py` - Scientific computing best practices

#### Publishing & Research Tools
- `infrastructure/publishing/` - Academic publishing workflows (DOI, citations, metadata)
- `infrastructure/literature/` - Academic literature search and reference management
- `infrastructure/llm/` - Local LLM integration for research assistance
- `infrastructure/rendering/` - Multi-format output generation (PDF, slides, web, posters)
- `infrastructure/reporting/` - Pipeline reporting and error aggregation

### Project Modules (Layer 2 - Project-Specific)

These modules are located in `project/src/` and contain project-specific scientific code:

#### Core Operations
- `project/src/example.py` - Basic mathematical operations

#### Data Processing
- `project/src/data_generator.py` - Synthetic data generation with configurable distributions
- `project/src/data_processing.py` - Data cleaning, preprocessing, normalization, outlier detection
- `project/src/statistics.py` - Descriptive statistics, hypothesis testing, correlation analysis
- `project/src/metrics.py` - Performance metrics, convergence metrics, quality metrics
- `project/src/validation.py` - Result validation, reproducibility verification, anomaly detection

#### Visualization
- `project/src/visualization.py` - Publication-quality figure generation with consistent styling
- `project/src/plots.py` - Plot type implementations (line, scatter, bar, heatmap, contour)

#### Simulation & Analysis
- `project/src/simulation.py` - Core simulation framework with reproducibility and checkpointing
- `project/src/parameters.py` - Parameter set management, validation, sweeps, serialization
- `project/src/performance.py` - Convergence analysis, scalability metrics, benchmark comparisons
- `project/src/reporting.py` - Automated report generation from simulation results

---

## Module: example

### Functions

#### `add_numbers(a: float, b: float) -> float`

Add two numbers together.

**Parameters:**
- `a` (float): First number
- `b` (float): Second number

**Returns:**
- `float`: Sum of a and b

**Example:**
```python
from example import add_numbers
result = add_numbers(3.5, 2.5)  # Returns 6.0
```

---

#### `multiply_numbers(a: float, b: float) -> float`

Multiply two numbers together.

**Parameters:**
- `a` (float): First number
- `b` (float): Second number

**Returns:**
- `float`: Product of a and b

**Example:**
```python
from example import multiply_numbers
result = multiply_numbers(3.0, 4.0)  # Returns 12.0
```

---

#### `calculate_average(numbers: List[float]) -> Optional[float]`

Calculate the average of a list of numbers.

**Parameters:**
- `numbers` (List[float]): List of numbers to average

**Returns:**
- `Optional[float]`: Average of the numbers, or None if list is empty

**Example:**
```python
from example import calculate_average
result = calculate_average([1.0, 2.0, 3.0, 4.0])  # Returns 2.5
result = calculate_average([])  # Returns None
```

---

#### `find_maximum(numbers: List[float]) -> Optional[float]`

Find the maximum value in a list of numbers.

**Parameters:**
- `numbers` (List[float]): List of numbers to search

**Returns:**
- `Optional[float]`: Maximum value, or None if list is empty

**Example:**
```python
from example import find_maximum
result = find_maximum([1.0, 5.0, 3.0, 2.0])  # Returns 5.0
```

---

#### `find_minimum(numbers: List[float]) -> Optional[float]`

Find the minimum value in a list of numbers.

**Parameters:**
- `numbers` (List[float]): List of numbers to search

**Returns:**
- `Optional[float]`: Minimum value, or None if list is empty

**Example:**
```python
from example import find_minimum
result = find_minimum([1.0, 5.0, 3.0, 2.0])  # Returns 1.0
```

---

#### `is_even(number: int) -> bool`

Check if a number is even.

**Parameters:**
- `number` (int): Integer to check

**Returns:**
- `bool`: True if number is even, False otherwise

**Example:**
```python
from example import is_even
result = is_even(4)  # Returns True
result = is_even(5)  # Returns False
```

---

#### `is_odd(number: int) -> bool`

Check if a number is odd.

**Parameters:**
- `number` (int): Integer to check

**Returns:**
- `bool`: True if number is odd, False otherwise

**Example:**
```python
from example import is_odd
result = is_odd(5)  # Returns True
result = is_odd(4)  # Returns False
```

---

## Module: glossary_gen

### Classes

#### `ApiEntry`

Container for API entry information.

**Attributes:**
- `module` (str): Module name
- `name` (str): Function or class name
- `kind` (str): Type ("function" or "class")
- `summary` (str): First sentence of docstring

---

### Functions

#### `build_api_index(src_dir: str) -> List[ApiEntry]`

Scan `src_dir` and collect public functions/classes with summaries.

**Parameters:**
- `src_dir` (str): Source directory to scan

**Returns:**
- `List[ApiEntry]`: List of API entries sorted by module and name

**Example:**
```python
from glossary_gen import build_api_index
entries = build_api_index("src")
for entry in entries:
    print(f"{entry.module}.{entry.name} ({entry.kind})")
```

---

#### `generate_markdown_table(entries: List[ApiEntry]) -> str`

Generate a Markdown table from API entries.

**Parameters:**
- `entries` (List[ApiEntry]): List of API entries to format

**Returns:**
- `str`: Markdown table string with headers and data rows

**Example:**
```python
from glossary_gen import build_api_index, generate_markdown_table
entries = build_api_index("src")
table = generate_markdown_table(entries)
print(table)
```

---

#### `inject_between_markers(text: str, begin_marker: str, end_marker: str, content: str) -> str`

Replace content between begin_marker and end_marker (inclusive markers preserved).

**Parameters:**
- `text` (str): Original text
- `begin_marker` (str): Start marker
- `end_marker` (str): End marker
- `content` (str): Content to inject

**Returns:**
- `str`: Text with content replaced between markers

---

## Module: pdf_validator

### Classes

#### `PDFValidationError(Exception)`

Exception raised for PDF validation errors.

---

### Functions

#### `extract_text_from_pdf(pdf_path: Path) -> str`

Extract text content from PDF file.

**Parameters:**
- `pdf_path` (Path): Path to PDF file

**Returns:**
- `str`: Extracted text content

**Raises:**
- `PDFValidationError`: If PDF cannot be read

**Example:**
```python
from pathlib import Path
from infrastructure.validation import extract_text_from_pdf
text = extract_text_from_pdf(Path("output/pdf/document.pdf"))
```

---

#### `scan_for_issues(text: str) -> Dict[str, int]`

Scan extracted text for common rendering issues.

**Parameters:**
- `text` (str): Extracted text from PDF

**Returns:**
- `Dict[str, int]`: Dictionary with issue counts:
  - `unresolved_references`: Count of ?? patterns
  - `warnings`: Count of warning patterns
  - `errors`: Count of error patterns
  - `missing_citations`: Count of [?] patterns
  - `total_issues`: Sum of all issues

**Example:**
```python
from infrastructure.validation import extract_text_from_pdf, scan_for_issues
text = extract_text_from_pdf(pdf_path)
issues = scan_for_issues(text)
print(f"Found {issues['total_issues']} issues")
```

---

#### `extract_first_n_words(text: str, n: int = 200) -> str`

Extract the first N words from text, preserving punctuation.

**Parameters:**
- `text` (str): Input text
- `n` (int): Number of words to extract (default: 200)

**Returns:**
- `str`: String containing first N words

**Example:**
```python
from infrastructure.validation import extract_text_from_pdf, extract_first_n_words
text = extract_text_from_pdf(pdf_path)
preview = extract_first_n_words(text, n=100)
print(preview)
```

---

#### `validate_pdf_rendering(pdf_path: Path, n_words: int = 200) -> Dict[str, Any]`

Perform comprehensive validation of PDF rendering.

**Parameters:**
- `pdf_path` (Path): Path to PDF file to validate
- `n_words` (int): Number of words to extract for preview (default: 200)

**Returns:**
- `Dict[str, Any]`: Validation report dictionary with:
  - `pdf_path`: Path to PDF
  - `issues`: Dictionary of issue counts
  - `first_words`: First N words of document
  - `summary`: Summary dictionary with has_issues and word_count

**Raises:**
- `PDFValidationError`: If PDF cannot be read or validated

**Example:**
```python
from pathlib import Path
from infrastructure.validation import validate_pdf_rendering
report = validate_pdf_rendering(Path("output/pdf/document.pdf"))
if report['summary']['has_issues']:
    print("PDF has issues:", report['issues'])
```

---

## Module: quality_checker

### Classes

#### `QualityMetrics`

Container for document quality metrics.

**Attributes:**
- `readability_score` (float): Readability score (0-100)
- `academic_compliance` (float): Academic standards compliance (0-1)
- `structural_integrity` (float): Document structure quality (0-1)
- `formatting_quality` (float): Formatting consistency (0-1)
- `overall_score` (float): Composite quality score (0-1)
- `issues` (List[str]): List of detected issues
- `recommendations` (List[str]): Improvement suggestions

---

### Functions

#### `analyze_document_quality(pdf_path: Path, text: Optional[str] = None) -> QualityMetrics`

Analyze document quality and return comprehensive metrics.

**Parameters:**
- `pdf_path` (Path): Path to PDF file
- `text` (str, optional): Pre-extracted text (optional)

**Returns:**
- `QualityMetrics`: Quality metrics object

**Example:**
```python
from pathlib import Path
from infrastructure.build import analyze_document_quality
metrics = analyze_document_quality(Path("output/pdf/document.pdf"))
print(f"Overall Score: {metrics.overall_score:.2f}")
```

---

#### `analyze_readability(text: str) -> Dict[str, float]`

Analyze text readability using multiple metrics.

**Parameters:**
- `text` (str): Text content to analyze

**Returns:**
- `Dict[str, float]`: Dictionary with:
  - `flesch_score`: Flesch Reading Ease Score (0-100)
  - `gunning_fog`: Gunning Fog Index
  - `avg_sentence_length`: Average sentence length
  - `avg_syllables_per_word`: Average syllables per word

**Example:**
```python
from infrastructure.build import analyze_readability
metrics = analyze_readability("Your document text here...")
print(f"Flesch Score: {metrics['flesch_score']:.2f}")
```

---

#### `generate_quality_report(metrics: QualityMetrics) -> str`

Generate a formatted quality report.

**Parameters:**
- `metrics` (QualityMetrics): Quality metrics object

**Returns:**
- `str`: Formatted report string

**Example:**
```python
from infrastructure.build import analyze_document_quality, generate_quality_report
metrics = analyze_document_quality(pdf_path)
report = generate_quality_report(metrics)
print(report)
```

---

## Module: reproducibility

### Classes

#### `ReproducibilityReport`

Container for reproducibility analysis results.

**Attributes:**
- `environment_hash` (str): Hash of environment state
- `dependency_hash` (str): Hash of dependencies
- `code_hash` (str): Hash of source code
- `data_hash` (str): Hash of data files
- `overall_hash` (str): Combined hash
- `timestamp` (str): Report timestamp
- `platform_info` (Dict[str, str]): Platform information
- `dependency_info` (List[Dict[str, str]]): Dependency information
- `issues` (List[str]): Detected issues
- `recommendations` (List[str]): Recommendations

---

### Functions

#### `generate_reproducibility_report(output_dir: Path) -> ReproducibilityReport`

Generate a comprehensive reproducibility report.

**Parameters:**
- `output_dir` (Path): Output directory to analyze

**Returns:**
- `ReproducibilityReport`: Reproducibility report object

**Example:**
```python
from pathlib import Path
from infrastructure.build import generate_reproducibility_report
report = generate_reproducibility_report(Path("output"))
print(f"Environment Hash: {report.environment_hash}")
```

---

#### `capture_environment_state() -> Dict[str, Any]`

Capture the current environment state for reproducibility.

**Returns:**
- `Dict[str, Any]`: Dictionary with environment information

**Example:**
```python
from infrastructure.build import capture_environment_state
env = capture_environment_state()
print(f"Python: {env['platform']['python_version']}")
```

---

#### `verify_reproducibility(current_report: ReproducibilityReport, baseline_report: ReproducibilityReport) -> Dict[str, Any]`

Verify reproducibility by comparing reports.

**Parameters:**
- `current_report` (ReproducibilityReport): Current build report
- `baseline_report` (ReproducibilityReport): Baseline report

**Returns:**
- `Dict[str, Any]`: Dictionary with:
  - `reproducible` (bool): Whether builds are reproducible
  - `differences` (List[str]): List of differences found

**Example:**
```python
from infrastructure.build import verify_reproducibility
result = verify_reproducibility(current, baseline)
if result['reproducible']:
    print("✅ Builds are reproducible")
```

---

## Module: integrity

### Classes

#### `IntegrityReport`

Container for integrity verification results.

**Attributes:**
- `file_integrity` (Dict[str, bool]): File integrity status
- `cross_reference_integrity` (Dict[str, bool]): Cross-reference status
- `data_consistency` (Dict[str, bool]): Data consistency status
- `academic_standards` (Dict[str, bool]): Academic standards status
- `overall_integrity` (bool): Overall integrity status
- `issues` (List[str]): Detected issues
- `warnings` (List[str]): Warnings
- `recommendations` (List[str]): Recommendations

---

### Functions

#### `verify_output_integrity(output_dir: Path) -> IntegrityReport`

Perform comprehensive integrity verification.

**Parameters:**
- `output_dir` (Path): Output directory to verify

**Returns:**
- `IntegrityReport`: Integrity report object

**Example:**
```python
from pathlib import Path
from infrastructure.validation import verify_output_integrity
report = verify_output_integrity(Path("output"))
if report.overall_integrity:
    print("✅ All integrity checks passed")
```

---

#### `verify_cross_references(markdown_files: List[Path]) -> Dict[str, bool]`

Verify cross-reference integrity in markdown files.

**Parameters:**
- `markdown_files` (List[Path]): List of markdown files to check

**Returns:**
- `Dict[str, bool]`: Dictionary mapping reference types to validity status

**Example:**
```python
from pathlib import Path
from infrastructure.validation import verify_cross_references
files = list(Path("manuscript").glob("*.md"))
integrity = verify_cross_references(files)
```

---

## Module: publishing

### Classes

#### `PublicationMetadata`

Container for publication metadata.

**Attributes:**
- `title` (str): Publication title
- `authors` (List[str]): List of authors
- `abstract` (str): Abstract text
- `keywords` (List[str]): Keywords
- `doi` (Optional[str]): Digital Object Identifier
- `journal` (Optional[str]): Journal name
- `conference` (Optional[str]): Conference name
- `publication_date` (Optional[str]): Publication date
- `publisher` (Optional[str]): Publisher name
- `license` (str): License type
- `repository_url` (Optional[str]): Repository URL
- `citation_count` (int): Citation count
- `download_count` (int): Download count

---

### Functions

#### `extract_publication_metadata(markdown_files: List[Path]) -> PublicationMetadata`

Extract publication metadata from markdown files.

**Parameters:**
- `markdown_files` (List[Path]): List of markdown files to analyze

**Returns:**
- `PublicationMetadata`: Publication metadata object

**Example:**
```python
from pathlib import Path
from infrastructure.publishing import extract_publication_metadata
files = list(Path("manuscript").glob("*.md"))
metadata = extract_publication_metadata(files)
print(f"Title: {metadata.title}")
```

---

#### `generate_citation_bibtex(metadata: PublicationMetadata) -> str`

Generate BibTeX citation.

**Parameters:**
- `metadata` (PublicationMetadata): Publication metadata

**Returns:**
- `str`: BibTeX-formatted citation

**Example:**
```python
from infrastructure.publishing import generate_citation_bibtex
bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

---

#### `validate_doi(doi: str) -> bool`

Validate DOI format and checksum.

**Parameters:**
- `doi` (str): DOI string to validate

**Returns:**
- `bool`: True if DOI is valid, False otherwise

**Example:**
```python
from infrastructure.publishing import validate_doi
if validate_doi("10.5281/zenodo.12345678"):
    print("✅ Valid DOI")
```

---

## Module: scientific_dev

### Classes

#### `BenchmarkResult`

Container for benchmark results.

**Attributes:**
- `function_name` (str): Function name
- `execution_time` (float): Execution time in seconds
- `memory_usage` (Optional[float]): Memory usage (if available)
- `iterations` (int): Number of iterations
- `parameters` (Dict[str, Any]): Benchmark parameters
- `result_summary` (str): Summary of results
- `timestamp` (str): Benchmark timestamp

---

#### `StabilityTest`

Container for numerical stability test results.

**Attributes:**
- `function_name` (str): Function name
- `test_name` (str): Test name
- `input_range` (Tuple[float, float]): Input range tested
- `expected_behavior` (str): Expected behavior description
- `actual_behavior` (str): Actual behavior description
- `stability_score` (float): Stability score (0-1)
- `recommendations` (List[str]): Recommendations

---

### Functions

#### `check_numerical_stability(func: Callable, test_inputs: List[Any], tolerance: float = 1e-12) -> StabilityTest`

Check numerical stability of a function across a range of inputs.

**Parameters:**
- `func` (Callable): Function to test
- `test_inputs` (List[Any]): List of input values to test
- `tolerance` (float): Numerical tolerance (default: 1e-12)

**Returns:**
- `StabilityTest`: Stability test results

**Example:**
```python
from scientific_dev import check_numerical_stability
import numpy as np
stability = check_numerical_stability(my_func, np.linspace(-10, 10, 100))
print(f"Stability Score: {stability.stability_score:.2f}")
```

---

#### `benchmark_function(func: Callable, test_inputs: List[Any], iterations: int = 100) -> BenchmarkResult`

Benchmark function performance across multiple inputs.

**Parameters:**
- `func` (Callable): Function to benchmark
- `test_inputs` (List[Any]): List of input values
- `iterations` (int): Number of iterations per input (default: 100)

**Returns:**
- `BenchmarkResult`: Benchmark results

**Example:**
```python
from scientific_dev import benchmark_function
result = benchmark_function(my_func, test_inputs, iterations=50)
print(f"Execution Time: {result.execution_time:.4f}s")
```

---

## Module: build_verifier

### Classes

#### `BuildVerificationReport`

Container for build verification results.

**Attributes:**
- `build_timestamp` (str): Build timestamp
- `build_duration` (float): Build duration in seconds
- `exit_code` (int): Build exit code
- `output_files` (List[str]): List of output files
- `build_hash` (str): Build hash
- `dependency_hash` (str): Dependency hash
- `environment_hash` (str): Environment hash
- `verification_passed` (bool): Whether verification passed
- `issues` (List[str]): Detected issues
- `warnings` (List[str]): Warnings
- `recommendations` (List[str]): Recommendations

---

### Functions

#### `verify_build_artifacts(output_dir: Path, expected_files: Dict[str, List[str]]) -> Dict[str, Any]`

Verify that expected build artifacts are present.

**Parameters:**
- `output_dir` (Path): Output directory to verify
- `expected_files` (Dict[str, List[str]]): Dictionary mapping categories to expected file lists

**Returns:**
- `Dict[str, Any]`: Dictionary with verification results

**Example:**
```python
from pathlib import Path
from infrastructure.build import verify_build_artifacts
expected = {"pdf": ["document.pdf"], "figures": ["figure.png"]}
result = verify_build_artifacts(Path("output"), expected)
```

---

#### `verify_build_reproducibility(build_command: List[str], expected_outputs: Dict[str, str], iterations: int = 3) -> Dict[str, Any]`

Verify build reproducibility by running build multiple times.

**Parameters:**
- `build_command` (List[str]): Build command to run
- `expected_outputs` (Dict[str, str]): Dictionary mapping output files to expected content
- `iterations` (int): Number of times to run build (default: 3)

**Returns:**
- `Dict[str, Any]`: Dictionary with reproducibility verification results

**Example:**
```python
from infrastructure.build import verify_build_reproducibility
result = verify_build_reproducibility(["./build.sh"], {"output.pdf": "hash"})
```

---

## Module: data_generator

Synthetic data generation with configurable distributions.

### Functions

#### `generate_synthetic_data(n_samples: int, n_features: int = 1, distribution: str = "normal", seed: Optional[int] = None, **kwargs) -> np.ndarray`

Generate synthetic data with specified distribution.

**Parameters:**
- `n_samples` (int): Number of samples
- `n_features` (int): Number of features (default: 1)
- `distribution` (str): Distribution type (normal, uniform, exponential, poisson, beta)
- `seed` (Optional[int]): Random seed
- `**kwargs`: Distribution-specific parameters

**Returns:**
- `np.ndarray`: Array of generated data

**Example:**
```python
from data_generator import generate_synthetic_data
data = generate_synthetic_data(100, n_features=2, distribution="normal", mean=0.0, std=1.0)
```

---

## Module: statistics

Statistical analysis including descriptive statistics, hypothesis testing, and correlation analysis.

### Functions

#### `calculate_descriptive_stats(data: np.ndarray) -> DescriptiveStats`

Calculate descriptive statistics for a dataset.

**Returns:**
- `DescriptiveStats`: Object with mean, std, median, min, max, quartiles, count

**Example:**
```python
from statistics import calculate_descriptive_stats
stats = calculate_descriptive_stats(data)
print(f"Mean: {stats.mean}, Std: {stats.std}")
```

---

## Module: visualization

Publication-quality figure generation with consistent styling.

### Classes

#### `VisualizationEngine`

Engine for generating publication-quality figures.

**Methods:**
- `create_figure(nrows, ncols, figsize, **kwargs)` - Create figure with subplots
- `save_figure(figure, filename, formats, dpi)` - Save figure in multiple formats
- `apply_publication_style(ax, title, xlabel, ylabel, grid, legend)` - Apply styling

**Example:**
```python
from visualization import VisualizationEngine
engine = VisualizationEngine(style="publication", output_dir="output/figures")
fig, ax = engine.create_figure()
engine.save_figure(fig, "my_figure", formats=["png", "pdf"])
```

---

## Module: figure_manager

Automatic figure numbering, caption generation, and cross-referencing.

### Classes

#### `FigureManager`

Manages figures with automatic numbering and cross-referencing.

**Methods:**
- `register_figure(filename, caption, label, section, ...)` - Register a new figure
- `get_figure(label)` - Get figure metadata by label
- `generate_latex_figure_block(label)` - Generate LaTeX figure block
- `generate_reference(label)` - Generate LaTeX reference

**Example:**
```python
from infrastructure.documentation import FigureManager
manager = FigureManager()
fig_meta = manager.register_figure("convergence.png", "Convergence analysis", "fig:convergence")
latex_block = manager.generate_latex_figure_block("fig:convergence")
```

---

## Additional Modules

For complete API documentation of all modules, see:
- **[Infrastructure Documentation](../infrastructure/AGENTS.md)** - Complete infrastructure module descriptions
- **[Project Source Documentation](../project/src/AGENTS.md)** - Project-specific module descriptions
- **[Scientific Simulation Guide](SCIENTIFIC_SIMULATION_GUIDE.md)** - Simulation and analysis modules
- **[Visualization Guide](VISUALIZATION_GUIDE.md)** - Visualization and figure management
- **[Image Management Guide](IMAGE_MANAGEMENT.md)** - Image insertion and cross-referencing

**Key Project Modules (project/src/):**
- `data_processing.py` - Data cleaning, normalization, outlier detection
- `metrics.py` - Performance metrics, convergence metrics, quality metrics
- `validation.py` - Result validation framework
- `simulation.py` - Core simulation framework
- `parameters.py` - Parameter management and sweeps
- `performance.py` - Convergence and scalability analysis
- `reporting.py` - Automated report generation
- `plots.py` - Plot type implementations

**Key Infrastructure Modules (infrastructure/):**
- `documentation/image_manager.py` - Image insertion into markdown
- `documentation/markdown_integration.py` - Markdown integration utilities
- `documentation/figure_manager.py` - Automatic figure numbering and cross-referencing

---

## Summary

This API reference covers all public functions and classes in the `infrastructure/` and `project/src/` directories. All modules:

- Follow the thin orchestrator pattern
- Maintain required test coverage (90% project, 60% infra)
- Include comprehensive type hints
- Provide detailed docstrings

For usage examples, see [Advanced Modules Guide](ADVANCED_MODULES_GUIDE.md).

For implementation details, see [Infrastructure Documentation](../infrastructure/AGENTS.md) and [Project Source Documentation](../project/src/AGENTS.md).

---

**Related Documentation:**
- [Advanced Modules Guide](ADVANCED_MODULES_GUIDE.md) - Usage examples
- [Infrastructure Docs](../infrastructure/AGENTS.md) - Infrastructure module implementation
- [Project Source Docs](../project/src/AGENTS.md) - Project module implementation
- [Best Practices](BEST_PRACTICES.md) - Usage recommendations



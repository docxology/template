# API Reference

> **API documentation** for all infrastructure modules

**Quick Reference:** [Modules Guide](../modules/modules-guide.md) | [Infrastructure Docs](../../infrastructure/AGENTS.md) | [Getting Started](../guides/getting-started.md)

This document provides API reference for all public functions and classes in the `infrastructure/` modules. All modules follow the thin orchestrator pattern with test coverage.

**Note**: These modules are part of the infrastructure layer. For project-specific code, see `projects/{name}/src/`.

## Module Organization

This API reference covers modules from both the **infrastructure layer** (reusable, generic tools) and the **project layer** (project-specific scientific code).

### Infrastructure Modules (Layer 1 - Generic, Reusable)

These modules are located in `infrastructure/` and provide generic tools applicable to any research project:

#### Documentation & API Generation

- `infrastructure/documentation/glossary_gen.py` - API documentation generation from source code

#### Validation & Quality Assurance

- `infrastructure/validation/content/pdf_validator.py` - PDF rendering validation
- `infrastructure/validation/integrity/checks.py` - Output integrity verification

#### Scientific Computing

- `infrastructure/scientific/` - Scientific computing best practices (modular package)

#### Publishing & Research Tools

- `infrastructure/publishing/` - Academic publishing workflows (DOI, citations, metadata)
- `infrastructure/llm/` - Local LLM integration for research assistance
- `infrastructure/rendering/` - Multi-format output generation (PDF, slides, web, posters)
- `infrastructure/reporting/` - Pipeline reporting and error aggregation

### Project Modules (Layer 2 - Project-Specific)

Project modules live in `projects/{name}/src/` and contain project-specific scientific code.
Module names and contents vary by project; the list below is **illustrative**, not a required template.

#### Core Operations

- `projects/{name}/src/example.py` - Basic mathematical operations

#### Data Processing

- `projects/{name}/src/data_generator.py` - Synthetic data generation with configurable distributions
- `projects/{name}/src/data_processing.py` - Data cleaning, preprocessing, normalization, outlier detection
- `projects/{name}/src/statistics.py` - Descriptive statistics, hypothesis testing, correlation analysis
- `projects/{name}/src/metrics.py` - Performance metrics, convergence metrics, quality metrics
- `projects/{name}/src/validation.py` - Result validation, reproducibility verification, anomaly detection

#### Visualization

- `projects/{name}/src/visualization.py` - Publication-quality figure generation with consistent styling
- `projects/{name}/src/plots.py` - Plot type implementations (line, scatter, bar, heatmap, contour)

#### Simulation & Analysis

- Example modules (if your project needs them): `simulation.py`, `parameters.py`, `performance_analysis.py`, `reporting.py`

---

## Infrastructure Core Module Inventory

> Module inventory for `infrastructure/core/`.

| Module | Description |
|--------|-------------|
| `checkpoint` | Pipeline checkpoint system for resume capability |
| `cli` | CLI interface for core infrastructure modules |
| `config_cli` | Load manuscript configuration script (THIN ORCHESTRATOR) |
| `config_loader` | Configuration loader for manuscript metadata |
| `credentials` | Secure credential management for testing and operations |
| `environment` | Environment setup and validation utilities |
| `errors` | Typed error constants for consistent error messaging |
| `exceptions` | Custom exception hierarchy for the Research Project Template |
| `file_inventory` | File inventory and collection utilities |
| `file_operations` | File and directory operation utilities |
| `health_check` | System health monitoring and status checks |
| `logging_formatters` | Logging formatters for structured and template-based output |
| `logging_helpers` | Helper functions for logging utilities |
| `logging_progress` | Progress bars, spinners, and ETA calculations for logging |
| `logging_utils` | Unified Python logging module for the Research Project Template |
| `menu` | Interactive menu utilities (pure helpers) |
| `multi_project` | Multi-project orchestration system |
| `performance` | Performance monitoring and resource tracking utilities |
| `performance_monitor` | Performance monitoring and profiling utilities for research workflows |
| `pipeline` | Pipeline execution system for research projects |
| `pipeline_summary` | Pipeline summary generation and reporting |
| `progress` | Progress reporting utilities for pipeline operations |
| `retry` | Retry utilities for handling transient failures |
| `script_discovery` | Script discovery and execution utilities |
| `security` | Security utilities and input validation for the research template system |

For detailed class and function signatures for each core module, see [Infrastructure Documentation](../../infrastructure/AGENTS.md).

---

## Module: core

The core module provides foundational utilities used across all infrastructure modules. See [Core Module Guide](../modules/guides/core-module.md) for detailed usage.

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `get_logger` | Function | `infrastructure.core` |
| `log_operation` | Function | `infrastructure.core` |
| `log_stage` | Function | `infrastructure.core` |
| `log_success` | Function | `infrastructure.core` |
| `format_duration` | Function | `infrastructure.core` |
| `TemplateError` | Exception | `infrastructure.core` |
| `CheckpointManager` | Class | `infrastructure.core` |
| `SystemHealthChecker` | Class | `infrastructure.core` |
| `monitor_performance` | Decorator | `infrastructure.core` |
| `ProgressBar` | Class | `infrastructure.core` |

### Subpackages

| Subpackage | Purpose | Key Symbols |
|------------|---------|-------------|
| `core.config` | YAML config loading | `load_config`, `get_config_as_dict` |
| `core.exceptions` | Exception hierarchy | `TemplateError`, `BuildError`, `ValidationError` |
| `core.logging` | Structured logging | `get_logger`, `ProjectLogger` |
| `core.pipeline` | Pipeline execution | `PipelineConfig`, `PipelineExecutor` |
| `core.runtime` | Checkpoints, profiling | `CheckpointManager`, `CodeProfiler` |
| `core.telemetry` | Stage resource metrics | `TelemetryCollector`, `TelemetryConfig` |
| `core.files` | File operations | `clean_coverage_files`, `copy_final_deliverables` |

---

## Module: llm

Local LLM integration via Ollama for manuscript review and literature search. See [LLM Module Guide](../modules/guides/llm-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `LLMClient` | Class | `infrastructure.llm` |
| `OllamaClientConfig` | Dataclass | `infrastructure.llm` |
| `GenerationOptions` | Dataclass | `infrastructure.llm` |
| `generate_review` | Function | `infrastructure.llm` |
| `ReviewResult` | Dataclass | `infrastructure.llm` |
| `ReviewConfig` | Dataclass | `infrastructure.llm` |
| `ReviewMode` | Enum | `infrastructure.llm` |

---

## Module: rendering

Multi-format output generation. See [Rendering Module Guide](../modules/guides/rendering-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `RenderManager` | Class | `infrastructure.rendering` |
| `RenderingConfig` | Dataclass | `infrastructure.rendering` |
| `execute_render_pipeline` | Function | `infrastructure.rendering.pipeline` |

---

## Module: reporting

Pipeline reporting and executive summaries. See [Reporting Module Guide](../modules/guides/reporting-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `generate_pipeline_report` | Function | `infrastructure.reporting` |
| `ErrorAggregator` | Class | `infrastructure.reporting` |
| `OutputOrganizer` | Class | `infrastructure.reporting` |
| `execute_test_pipeline` | Function | `infrastructure.reporting` |

---

## Module: project

Multi-project discovery and management. See [Project Module Guide](../modules/guides/project-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `ProjectInfo` | Dataclass | `infrastructure.project` |
| `discover_projects` | Function | `infrastructure.project` |
| `get_project_metadata` | Function | `infrastructure.project` |
| `validate_project_structure` | Function | `infrastructure.project` |

---

## Module: skills

Agent skill discovery and manifest generation. See [Skills Module Guide](../modules/guides/skills-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `SkillDescriptor` | Dataclass | `infrastructure.skills` |
| `discover_skills` | Function | `infrastructure.skills` |
| `write_skill_manifest` | Function | `infrastructure.skills` |
| `manifest_matches_discovery` | Function | `infrastructure.skills` |

---

## Module: steganography

Cryptographic watermarking and provenance embedding. See [Steganography Module Guide](../modules/guides/steganography-module.md).

### Key Exports

| Symbol | Type | Import Path |
|--------|------|-------------|
| `SteganographyConfig` | Dataclass | `infrastructure.steganography` |
| `SteganographyProcessor` | Class | `infrastructure.steganography` |
| `embed_steganography` | Function | `infrastructure.steganography` |
| `process_pdf` | Function | `infrastructure.steganography` |

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
text = extract_text_from_pdf(Path("output/code_project/pdf/code_project_combined.pdf"))
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
from infrastructure.validation import extract_text_from_pdf
from infrastructure.validation.content.pdf_validator import extract_first_n_words

text = extract_text_from_pdf(pdf_path)
preview = extract_first_n_words(text, n=100)
print(preview)
```

---

#### `validate_pdf_rendering(pdf_path: Path, n_words: int = 200) -> Dict[str, Any]`

Perform validation of PDF rendering.

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
report = validate_pdf_rendering(Path("output/code_project/pdf/code_project_combined.pdf"))
if report['summary']['has_issues']:
    print("PDF has issues:", report['issues'])
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

Perform integrity verification.

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

## Module: scientific

**Location**: `infrastructure/scientific/` (modular package)

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
from infrastructure.scientific import check_numerical_stability
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
from infrastructure.scientific import benchmark_function
result = benchmark_function(my_func, test_inputs, iterations=50)
print(f"Execution Time: {result.execution_time:.4f}s")
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

For API documentation of all modules, see:

- **[Infrastructure Documentation](../../infrastructure/AGENTS.md)** - infrastructure module descriptions
- **[Project Source Documentation](../../projects/code_project/src/AGENTS.md)** - Project-specific module descriptions
- **[Scientific Simulation Guide](../modules/scientific-simulation-guide.md)** - Simulation and analysis modules
- **[Visualization Guide](../usage/visualization-guide.md)** - Visualization and figure management
- **[Image Management Guide](../usage/image-management.md)** - Image insertion and cross-referencing

**Key Project Modules (illustrative; `projects/{name}/src/` names vary by project):**

- `data_processing.py` - Data cleaning, normalization, outlier detection
- `metrics.py` - Performance metrics, convergence metrics, quality metrics
- `validation.py` - Result validation framework
- `simulation.py` - Core simulation framework
- `parameters.py` - Parameter management and sweeps
- `performance_analysis.py` - Convergence and scalability analysis (example module name)
- `reporting.py` - Automated report generation
- `plots.py` - Plot type implementations

**Key Infrastructure Modules (infrastructure/):**

- `documentation/image_manager.py` - Image insertion into markdown
- `documentation/markdown_integration.py` - Markdown integration utilities
- `documentation/figure_manager.py` - Automatic figure numbering and cross-referencing

---

## Summary

This API reference covers all public functions and classes in the `infrastructure/` and `projects/{name}/src/` directories. All modules:

- Follow the thin orchestrator pattern
- Maintain required test coverage (90% project, 60% infra)
- Include type hints
- Provide detailed docstrings

For usage examples, see [Modules Guide](../modules/modules-guide.md).

For implementation details, see [Infrastructure Documentation](../../infrastructure/AGENTS.md) and [Project Source Documentation](../../projects/code_project/src/AGENTS.md).

---

**Related Documentation:**

- [Modules Guide](../modules/modules-guide.md) - Usage examples
- [Infrastructure Docs](../../infrastructure/AGENTS.md) - Infrastructure module implementation
- [Project Source Docs](../../projects/code_project/src/AGENTS.md) - Project module implementation
- [Best Practices](../best-practices/best-practices.md) - Usage recommendations

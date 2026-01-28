# Infrastructure Layer - Modular Architecture

## Overview

The Infrastructure layer provides reusable, modular tools for building, validating, and managing research projects. Organized by functionality into submodules, each with clear responsibilities and testing.

## New Modular Architecture (v2.1)

The infrastructure has been reorganized into focused modules grouping related functionalities:

```
infrastructure/
├── core/           # Foundation utilities
│   ├── exceptions.py       # Exception hierarchy with context
│   ├── logging_utils.py    # Unified Python logging
│   └── config_loader.py    # Configuration management
├── validation/     # Quality & validation tools
│   ├── pdf_validator.py      # PDF rendering validation
│   ├── markdown_validator.py # Markdown structure validation
│   ├── integrity.py          # File integrity & cross-references
│   └── cli.py                # CLI for validation tools
├── documentation/  # Documentation & figure management
│   ├── figure_manager.py       # Automatic figure numbering
│   ├── image_manager.py        # Image file management
│   ├── markdown_integration.py # Figure/reference insertion
│   ├── glossary_gen.py         # API documentation generation
│   └── cli.py                  # CLI for documentation tools
├── scientific/     # Scientific development
│   ├── scientific_dev.py    # Scientific utilities & best practices
│   └── AGENTS.md, README.md  # Documentation
├── llm/            # LLM integration
│   ├── core.py              # LLM client
│   ├── templates.py         # Research prompt templates
│   └── AGENTS.md, README.md  # Documentation
├── rendering/      # Multi-format rendering
│   ├── core.py              # Render manager
│   ├── latex_utils.py       # LaTeX utilities
│   ├── cli.py               # CLI for rendering
│   └── AGENTS.md, README.md  # Documentation
├── publishing/     # Academic publishing & dissemination
│   ├── core.py              # Publishing workflows
│   ├── api.py               # Platform API clients
│   ├── cli.py               # CLI for publishing
│   └── AGENTS.md, README.md  # Documentation
└── reporting/      # Pipeline reporting & error aggregation
    ├── pipeline_reporter.py  # Pipeline report generation
    ├── error_aggregator.py   # Error collection & categorization
    ├── html_templates.py     # HTML report templates
    └── AGENTS.md, README.md   # Documentation
```

## Function Signatures

### Core Module

#### exceptions.py
- `class TemplateError(Exception):`
- `class LLMError(TemplateError):`
- `class RenderingError(TemplateError):`
- `class PublishingError(TemplateError):`
- `class ValidationError(TemplateError):`
- `class ConfigurationError(TemplateError):`
- `class EnvironmentError(TemplateError):`
- `def format_exception_chain(exc: Exception) -> str:`
- `def preserve_context(func: Callable) -> Callable:`

#### logging_utils.py
- `class ProjectLogger:`
- `def get_project_logger(name: str, level: Optional[int] = None) -> ProjectLogger:`
- `def setup_project_logging(name: str, level: Optional[int] = None, ...):`
- `def get_log_level_from_env() -> int:`
- `def setup_logger(name: str, level: Optional[int] = None, ...) -> logging.Logger:`
- `def get_logger(name: str) -> logging.Logger:`
- `def log_operation(func: Callable, logger: Optional[logging.Logger] = None) -> Callable:`
- `def log_operation_silent(func: Callable, logger: Optional[logging.Logger] = None) -> Callable:`
- `def log_timing(func: Callable, logger: Optional[logging.Logger] = None) -> Callable:`
- `def log_function_call(logger: Optional[logging.Logger] = None) -> Callable:`
- `def log_success(message: str, logger: Optional[logging.Logger] = None) -> None:`
- `def log_header(message: str, logger: Optional[logging.Logger] = None) -> None:`
- `def log_progress(current: int, total: int, message: str = "", ...) -> None:`
- `def log_stage(stage_name: str, stage_num: Optional[int] = None, ...) -> None:`
- `def log_substep(message: str, logger: Optional[logging.Logger] = None) -> None:`
- `def set_global_log_level(level: int) -> None:`
- `def log_stage_with_eta(stage_name: str, current: int, total: int, ...) -> None:`
- `def log_resource_usage(logger: Optional[logging.Logger] = None) -> None:`

#### config_loader.py
- `def load_config_from_yaml(yaml_path: Path) -> Dict[str, Any]:`
- `def load_config_from_env() -> Dict[str, Any]:`
- `def merge_configs(yaml_config: Dict, env_config: Dict) -> Dict[str, Any]:`
- `def load_project_config(project_dir: Path) -> Dict[str, Any]:`
- `def format_author_name(author_data: Dict[str, Any]) -> str:`
- `def format_author_affiliation(author_data: Dict[str, Any]) -> str:`
- `def get_formatted_authors(config: Dict[str, Any]) -> List[str]:`

#### checkpoint.py
- `class PipelineCheckpoint:`
- `class CheckpointManager:`
- `def create_checkpoint_dir(base_dir: Path) -> Path:`
- `def save_checkpoint(checkpoint: PipelineCheckpoint, checkpoint_dir: Path) -> None:`
- `def load_checkpoint(checkpoint_dir: Path) -> Optional[PipelineCheckpoint]:`
- `def validate_checkpoint(checkpoint: PipelineCheckpoint) -> bool:`

#### file_operations.py
- `def clean_output_directory(output_dir: Path, project_name: str) -> None:`
- `def copy_final_deliverables(output_dir: Path, final_dir: Path, project_name: str) -> None:`
- `def ensure_directory_exists(directory: Path) -> None:`
- `def get_file_size_mb(file_path: Path) -> float:`
- `def calculate_directory_size(directory: Path) -> int:`

#### performance.py
- `class PerformanceMonitor:`
- `def get_system_resources() -> Dict[str, Any]:`
- `def monitor_performance(func: Callable) -> Callable:`
- `def log_performance_stats(stats: Dict[str, Any], logger: Optional[logging.Logger] = None) -> None:`
- `def format_performance_report(stats: Dict[str, Any]) -> str:`

### Validation Module

#### pdf_validator.py
- `def validate_pdf_content(pdf_path: Path) -> ValidationReport:`
- `def extract_text_from_pdf(pdf_path: Path) -> str:`
- `def check_unresolved_references(text: str) -> List[str]:`
- `def check_latex_warnings(text: str) -> List[str]:`
- `def validate_document_structure(pdf_path: Path) -> bool:`

#### markdown_validator.py
- `def validate_markdown_file(file_path: Path) -> ValidationReport:`
- `def validate_image_references(content: str, base_dir: Path) -> List[str]:`
- `def validate_cross_references(content: str) -> List[str]:`
- `def validate_equation_labels(content: str) -> List[str]:`
- `def validate_link_formats(content: str) -> List[str]:`

#### integrity.py
- `def verify_output_integrity(output_dir: Path) -> IntegrityReport:`
- `def check_file_integrity(file_path: Path) -> bool:`
- `def validate_cross_references(content: str) -> List[str]:`
- `def generate_integrity_report(report: IntegrityReport) -> str:`

### Rendering Module

#### pdf_renderer.py
- `def render_pdf_manuscript(manuscript_dir: Path, output_dir: Path, ...) -> Path:`
- `def render_individual_sections(manuscript_dir: Path, output_dir: Path) -> List[Path]:`
- `def combine_sections_to_pdf(section_files: List[Path], output_file: Path) -> None:`
- `def render_ide_friendly_pdf(source_file: Path, output_file: Path) -> None:`

#### latex_utils.py
- `def compile_latex_to_pdf(tex_file: Path, output_dir: Path, ...) -> Path:`
- `def extract_latex_errors(log_content: str) -> List[str]:`
- `def clean_latex_auxiliary_files(output_dir: Path) -> None:`

#### core.py
- `class RenderManager:`
- `def render_pdf(self, manuscript_dir: Path, output_dir: Path, ...) -> Path:`
- `def render_html(self, manuscript_dir: Path, output_dir: Path) -> Path:`
- `def render_all(self, manuscript_dir: Path, output_dir: Path) -> Dict[str, Path]:`

### LLM Module

#### core.py
- `class LLMConfig:`
- `class LLMClient:`
- `def query(self, prompt: str, options: Optional[GenerationOptions] = None) -> str:`
- `def apply_template(self, template_name: str, **kwargs) -> str:`

#### templates.py
- `def get_template(template_name: str) -> str:`
- `def list_available_templates() -> List[str]:`
- `def apply_template_with_context(template_name: str, context: Dict[str, Any]) -> str:`

### Publishing Module

#### core.py
- `def extract_publication_metadata(markdown_files: List[Path]) -> Dict[str, Any]:`
- `def validate_metadata(metadata: Dict[str, Any]) -> List[str]:`
- `def format_publication_metadata(metadata: Dict[str, Any]) -> str:`

#### api.py
- `def publish_to_zenodo(metadata: Dict[str, Any], files: List[Path], ...) -> str:`
- `def create_github_release(metadata: Dict[str, Any], files: List[Path], ...) -> str:`
- `def prepare_arxiv_submission(metadata: Dict[str, Any], files: List[Path]) -> Path:`

#### citations.py
- `def generate_citation_bibtex(metadata: Dict[str, Any]) -> str:`
- `def generate_citation_apa(metadata: Dict[str, Any]) -> str:`
- `def validate_doi(doi: str) -> bool:`

### Scientific Module

#### benchmarking.py
- `def benchmark_function(func: Callable, test_inputs: List[Any], ...) -> BenchmarkReport:`
- `def compare_implementations(functions: Dict[str, Callable], ...) -> ComparisonReport:`

#### stability.py
- `def check_numerical_stability(func: Callable, test_inputs: List[Any], ...) -> StabilityReport:`
- `def assess_algorithm_stability(func: Callable, input_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:`

#### validation.py
- `def validate_scientific_code(file_path: Path) -> ValidationReport:`
- `def check_best_practices(code_content: str) -> List[str]:`

### Reporting Module

#### pipeline_reporter.py
- `def generate_pipeline_report(checkpoint_dir: Path, output_dir: Path) -> Path:`
- `def generate_stage_report(stage_name: str, duration: float, ...) -> str:`

#### error_aggregator.py
- `def aggregate_errors(log_files: List[Path]) -> ErrorSummary:`
- `def categorize_errors(error_messages: List[str]) -> Dict[str, List[str]]:`
- `def generate_error_report(errors: ErrorSummary, output_dir: Path) -> Path:`

#### executive_reporter.py
- `def generate_executive_report(project_dirs: List[Path], output_dir: Path) -> Path:`
- `def aggregate_project_metrics(project_dirs: List[Path]) -> Dict[str, Any]:`

### Documentation Module

#### figure_manager.py
- `class FigureManager:`
- `def register_figure(self, figure_path: Path, caption: str, label: str) -> str:`
- `def get_figure_reference(self, label: str) -> str:`
- `def validate_figure_references(self, content: str) -> List[str]:`

#### markdown_integration.py
- `def integrate_figures_into_markdown(content: str, figure_manager: FigureManager) -> str:`
- `def integrate_tables_into_markdown(content: str) -> str:`
- `def validate_markdown_integrity(content: str) -> List[str]:`

## Key Design Principles

### 1. Layered Architecture
- **Layer 1 (infrastructure/)**: Generic, reusable tools for any project
- All code is domain-independent
- 100% test coverage required
- Can be copied to other projects

### 2. Thin Orchestrator Pattern
- **Business logic**: Implemented in module core (e.g., `core.py`)
- **Orchestration**: Delegated to CLI wrappers and entry points
- **Scripts**: Only coordinate, never duplicate logic
- **Reusability**: Each module stands alone or integrates with others

### 3. Module Standardization
- Each module has:
  - `__init__.py` - Public API exports
  - `core.py` - Core business logic (100% tested)
  - `cli.py` - Command-line interface (optional)
  - `config.py` - Configuration management (optional)
  - `AGENTS.md` - Detailed documentation
  - `README.md` - Quick reference
- All public APIs have type hints and docstrings

## Module Organization

### Core Module (`core/`)

**Foundation utilities used by all other modules.**

- `exceptions.py` - Exception hierarchy with context preservation
  - `TemplateError` - Base exception
  - Module-specific exceptions (LLM, Rendering, Publishing)
  - Context utilities and exception chaining

- `logging_utils.py` - Unified Python logging system
  - Environment-based configuration (LOG_LEVEL 0-3)
  - Context managers for operation tracking
  - Decorators for function logging
  - TTY-aware color output

- `config_loader.py` - Configuration management
  - YAML configuration file loading
  - Environment variable integration
  - Author and metadata formatting

- `progress.py` - Progress tracking utilities
  - `ProgressBar` - Visual progress indicators
  - `SubStageProgress` - Nested progress tracking

- `checkpoint.py` - Pipeline checkpoint management
  - `CheckpointManager` - Save/restore pipeline state
  - `PipelineCheckpoint` - Checkpoint data structures

- `retry.py` - Retry logic with backoff
  - `retry_with_backoff` - Exponential backoff retries
  - `RetryableOperation` - Retryable operation wrapper

- `performance.py` - Performance monitoring
  - `PerformanceMonitor` - Resource usage tracking
  - `get_system_resources` - System resource queries

- `environment.py` - Environment setup and validation
  - Dependency checking and installation
  - Build tool verification
  - Directory structure setup

- `script_discovery.py` - Script discovery and execution
  - `discover_analysis_scripts` - Find project scripts
  - `discover_orchestrators` - Find orchestrator scripts

- `file_operations.py` - File management utilities
  - `clean_output_directory` - Cleanup operations
  - `copy_final_deliverables` - Output copying

**Usage:**
```python
from infrastructure.core import (
    get_logger, TemplateError, load_config,
    CheckpointManager, ProgressBar, PerformanceMonitor
)
```

### Validation Module (`validation/`)

**Quality assurance and validation tools.**

- `pdf_validator.py` - PDF rendering validation
  - Text extraction and analysis
  - Issue detection (unresolved references, warnings)
  - Document structure verification

- `markdown_validator.py` - Markdown structure validation
  - Image reference validation
  - Cross-reference verification
  - Mathematical equation validation
  - Link integrity checking

- `integrity.py` - File integrity & cross-reference validation
  - SHA-256 hash verification
  - Cross-reference validation
  - Data consistency checking
  - Academic standards compliance

**CLI:**
```bash
python3 -m infrastructure.validation.cli pdf output/pdf/manuscript.pdf
python3 -m infrastructure.validation.cli markdown project/manuscript/
python3 -m infrastructure.validation.cli integrity output/
```

### Documentation Module (`documentation/`)

**Figure management and documentation tools.**

- `figure_manager.py` - Automatic figure numbering
  - Registry management with JSON persistence
  - LaTeX figure block generation
  - Cross-reference generation

- `image_manager.py` - Image insertion
  - Markdown insertion
  - Reference creation
  - Validation

- `markdown_integration.py` - Figure/reference integration
  - Section detection
  - Figure insertion into sections
  - Table of figures generation

- `glossary_gen.py` - API documentation generation
  - AST-based API extraction
  - Markdown table generation
  - Marker-based content injection

**CLI:**
```bash
python3 -m infrastructure.documentation.cli generate-api src/
```

### Scientific Module (`scientific/`)

**Scientific computing utilities.**

- `scientific_dev.py` - Scientific development tools
  - Numerical stability checking
  - Performance benchmarking
  - Scientific documentation generation
  - Best practices validation

### LLM Module (`llm/`)

**Local LLM integration for research assistance.**

Features:
- Ollama integration for local models
- Research prompt templates
- Multi-turn conversation support
- Streaming responses

**Usage:**
```python
from infrastructure.llm import LLMClient

client = LLMClient()
summary = client.apply_template("summarize_abstract", text=abstract)
```

### Rendering Module (`rendering/`)

**Multi-format output generation.**

Supports:
- PDF generation (standard & IDE-friendly)
- HTML presentation (reveal.js)
- Slide decks (Beamer & reveal.js)
- Scientific posters
- Web output with MathJax

**CLI:**
```bash
python3 -m infrastructure.rendering.cli pdf manuscript.tex
python3 -m infrastructure.rendering.cli all manuscript.tex
python3 -m infrastructure.rendering.cli slides presentation.md --format revealjs
```

### Reporting Module (`reporting/`)

**Pipeline reporting and error aggregation.**

Features:
- Consolidated pipeline reports (JSON, HTML, Markdown)
- Test results reporting with coverage metrics
- validation reports with actionable recommendations
- Performance metrics and bottleneck analysis
- Error aggregation with categorized fixes
- HTML templates for visual reports
- Output statistics and summaries

**Key Functions:**
- `generate_pipeline_report` - Main pipeline report generation
- `generate_test_report` - Test results reporting
- `generate_validation_report` - Validation results reporting
- `get_error_aggregator` - Error collection and categorization
- `generate_output_summary` - Output file statistics

**Usage:**
```python
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
    generate_test_report,
    generate_validation_report,
    generate_multi_project_report
)

# Generate pipeline report
report = generate_pipeline_report(
    stage_results=[...],
    total_duration=60.5,
    repo_root=Path("."),
)
saved_files = save_pipeline_report(report, Path("output/reports"))

# Generate multi-project executive report
exec_report = generate_multi_project_report(
    repo_root=Path("."),
    project_names=["code_project"],
    output_dir=Path("output/executive_summary")
)

# Aggregate errors
aggregator = get_error_aggregator()
aggregator.add_error("test_failure", "Test failed", stage="tests")
aggregator.save_report(Path("output/reports"))
```

**Integration:**
- Automatically integrated into `scripts/execute_pipeline.py`
- Test reports generated by `scripts/01_run_tests.py`
- Validation reports generated by `scripts/04_validate_output.py`
- Reports saved to `project/output/reports/`

### Publishing Module (`publishing/`)

**Academic publishing and dissemination.**

Features:
- Publication metadata extraction
- Citation generation (BibTeX, APA, MLA)
- Zenodo integration with DOI minting
- arXiv submission preparation
- GitHub release automation

**CLI:**
```bash
python3 -m infrastructure.publishing.cli extract-metadata manuscript/
python3 -m infrastructure.publishing.cli generate-citation manuscript/ --format bibtex
python3 -m infrastructure.publishing.cli publish-zenodo output/ --title "My Research"
python3 -m infrastructure.publishing.cli create-release v1.0 output/ $GITHUB_TOKEN
```

## Design Principles

### 1. Modular Organization
- Each module has a single, clear responsibility
- Modules can be used independently or together
- Related functionality grouped logically
- Minimal cross-module dependencies

### 2. Documentation
- Each module includes:
  - `AGENTS.md` - Detailed architecture and API
  - `README.md` - Quick reference and examples
  - Inline docstrings for all public APIs
  - Usage examples in documentation

### 3. Unified Infrastructure
- All modules use:
  - Shared `core/` utilities (logging, config, exceptions)
  - Consistent error handling
  - Standard logging patterns
  - Common environment variable support

### 4. CLI Integration
- Each module with external functionality includes `cli.py`
- Thin orchestrators calling module business logic
- Consistent argument parsing
- Helpful error messages

### 5. Testing
- 100% test coverage for all modules
- data analysis, no mocks
- Integration tests for module interoperability
- CI/CD compatible

## Integration with Build Pipeline

### Automatic Execution

The rendering pipeline (`scripts/02_run_analysis.py`, `scripts/03_render_pdf.py`, `scripts/04_validate_output.py`) automatically uses infrastructure modules:

1. **Setup** - Load configuration via `core.config_loader`
2. **Testing** - Initialize logging via `core.logging_utils`
3. **Analysis** - Run project scripts with error handling via `core.exceptions`
4. **Rendering** - Generate PDFs via `rendering/`
5. **Validation** - Verify quality via `validation/`
6. **Documentation** - Generate glossary via `documentation.glossary_gen`

### Validation Gates

Before PDF generation:
- Markdown validation via `validation/`
- File integrity checks via `validation/integrity`

## Configuration

### Environment Variables

All modules respect standard environment variables:

```bash
# Logging
export LOG_LEVEL=0  # 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR

# Paper metadata
export AUTHOR_NAME="Dr. Jane Smith"
export AUTHOR_ORCID="0000-0000-0000-1234"
export PROJECT_TITLE="Novel Framework"
export DOI="10.5281/zenodo.12345678"

# API tokens (for publishing)
export ZENODO_TOKEN="..."
export GITHUB_TOKEN="..."

# LLM configuration
export OLLAMA_HOST="http://localhost:11434"

# Disable colorized output
export NO_COLOR=1
```

### Configuration File

For persistent configuration, use `project/manuscript/config.yaml`:

```yaml
paper:
  title: "Novel Optimization Framework"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane@example.edu"
    affiliation: "University of Example"

publication:
  doi: "10.5281/zenodo.12345678"
  license: "Apache-2.0"
```

## Usage Examples

### Example: Summarization → Publication

```python
# 1. Summarize with LLM
from infrastructure.llm import LLMClient
client = LLMClient()
for paper in papers:
    summary = client.apply_template("summarize_abstract", text=paper.abstract)
    print(summary)

# 3. Render manuscript
from infrastructure.rendering import RenderManager
renderer = RenderManager()
pdf = renderer.render_pdf(Path("manuscript.tex"))

# 4. Validate quality
from infrastructure.validation import validate_pdf_rendering
report = validate_pdf_rendering(pdf)
print(f"Quality issues: {report['issues']['total_issues']}")

# 5. Publish to Zenodo
from infrastructure.publishing import publish_to_zenodo
doi = publish_to_zenodo(metadata, [pdf], token)
print(f"Published with DOI: {doi}")
```

### CLI Example: Full Workflow

```bash
# Validate manuscript
python3 -m infrastructure.validation.cli markdown project/manuscript/
python3 -m infrastructure.validation.cli integrity output/

# Generate API documentation
python3 -m infrastructure.documentation.cli generate-api project/src/

# Render to multiple formats
python3 -m infrastructure.rendering.cli all manuscript.tex

# Publish release
python3 -m infrastructure.publishing.cli publish-zenodo output/ --title "My Research"
python3 -m infrastructure.publishing.cli create-release v1.0 output/ $GITHUB_TOKEN
```

## Testing

### Run All Tests

```bash
# All infrastructure tests
pytest tests/infrastructure/ -v

# Specific module
pytest tests/infrastructure/test_validation/ -v

# With coverage
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html
```

### Coverage Status

All modules have test coverage:
- core: 100%
- validation: 100%
- documentation: 100%
- build: 100%
- scientific: 100%
- llm: 91%+
- rendering: 91%+
- publishing: 100%
- reporting: 67% (tests added; continue improving pipeline reporting paths)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'infrastructure.xxx'`:

1. Verify you're using the correct modular import path:
   ```python
   from infrastructure.validation.pdf_validator import validate_pdf_rendering
   from infrastructure.documentation.figure_manager import FigureManager
   from infrastructure.core.config_loader import load_config
   from infrastructure.core.logging_utils import get_logger
   from infrastructure.core.exceptions import TemplateError
   ```

2. Verify the module `__init__.py` exists with proper exports

### Configuration Issues

If configuration isn't loading:
1. Check `project/manuscript/config.yaml` exists
2. Verify YAML is well-formed
3. Fall back to environment variables as needed

## Architecture Advantages

1. **Clarity** - Related functionality grouped logically
2. **Maintainability** - Each module has focused responsibility
3. **Reusability** - Modules can be used independently
4. **Scalability** - Easy to add modules without cluttering core
5. **Documentation** - Each module documented
6. **Testing** - testing with 100% coverage
7. **Flexibility** - Use individual modules or pipeline

## Future Enhancements

Planned additions:
- LLM template library
- Additional rendering formats (EPUB, docx)
- Extended publishing platform support
- Data visualization utilities
- Collaboration features

## See Also

**Module Documentation:**
- Each module has detailed docs: `infrastructure/[module]/AGENTS.md`
- Quick reference guides: `infrastructure/[module]/README.md`

**Cross-Module Reference:**
- [`README.md`](README.md) - Quick start guide for all modules
- [`../.cursorrules/AGENTS.md`](../.cursorrules/AGENTS.md) - Development standards
- [`../.cursorrules/infrastructure_modules.md`](../.cursorrules/infrastructure_modules.md) - Infrastructure standards

**System Documentation:**
- [`../AGENTS.md`](../AGENTS.md) - system documentation
- [`../docs/core/ARCHITECTURE.md`](../docs/core/ARCHITECTURE.md) - System architecture overview
- [`../docs/architecture/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/architecture/THIN_ORCHESTRATOR_SUMMARY.md) - Orchestrator pattern details

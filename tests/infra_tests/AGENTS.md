# tests/infra_tests/ - Infrastructure Module Tests

## Purpose

The `tests/infra_tests/` directory contains tests for the reusable infrastructure modules in `infrastructure/`. These tests validate the build tools, validation systems, documentation utilities, and integration components that support research projects.

## Coverage Requirements

**60% minimum coverage** required for infrastructure modules. This ensures critical infrastructure functionality is validated while allowing flexibility for rapidly evolving research tools.

## Directory Structure

```text
tests/infra_tests/
├── conftest.py                      # Shared test configuration and fixtures
├── _test_helpers.py                 # Test utility functions (underscore = not a test file)
├── core/                           # Core utilities tests (24 test files)
│   ├── test_checkpoint.py          # Checkpoint/resume functionality
│   ├── test_cli.py                 # Core CLI interface
│   ├── test_config_cli_coverage.py # Config CLI coverage
│   ├── test_config_loader.py       # Configuration loading
│   ├── test_credentials.py         # Credential management
│   ├── test_credentials_module.py  # Credential module coverage
│   ├── test_environment.py         # Environment detection & setup
│   ├── test_exceptions.py          # Exception hierarchy
│   ├── test_file_inventory.py      # File inventory tracking
│   ├── test_file_operations.py     # File I/O utilities
│   ├── test_logging_helpers.py     # Logging helper functions
│   ├── test_logging_progress.py    # Progress-aware logging
│   ├── test_logging_utils.py       # Logging system
│   ├── test_menu.py                # Interactive menu
│   ├── test_multi_project.py       # Multi-project orchestration
│   ├── test_performance.py         # Performance monitoring
│   ├── test_pipeline.py            # Pipeline execution
│   ├── test_pipeline_summary.py    # Pipeline summary generation
│   ├── test_progress.py            # Progress tracking
│   ├── test_project_discovery.py   # Project discovery & validation
│   ├── test_project_logger.py      # Project-specific logging
│   ├── test_retry.py               # Retry mechanisms
│   ├── test_script_discovery.py    # Script auto-discovery
│   └── test_security.py            # Security utilities
├── documentation/                  # Documentation tools tests (4 test files)
│   ├── test_figure_manager.py      # Figure registry and numbering
│   ├── test_glossary_gen.py        # API documentation generation
│   ├── test_image_manager.py       # Image handling in markdown
│   └── test_markdown_integration.py # Markdown processing integration
├── llm/                            # LLM integration tests (19 test files)
│   ├── conftest.py                 # LLM test configuration
│   ├── AGENTS.md                   # LLM test documentation
│   ├── test_cli.py                 # CLI interface
│   ├── test_config.py              # Configuration management
│   ├── test_context.py             # Conversation context
│   ├── test_context_engineering.py # Context engineering strategies
│   ├── test_core.py                # Core LLM functionality
│   ├── test_llm_core_additional.py # Additional core tests
│   ├── test_llm_core_coverage.py   # Coverage-focused tests
│   ├── test_llm_core_full.py       # Full core tests
│   ├── test_llm_review.py          # LLM manuscript review
│   ├── test_logging.py             # LLM logging
│   ├── test_ollama_utils.py        # Ollama client utilities
│   ├── test_prompts_composer.py    # Prompt composition
│   ├── test_prompts_loader.py      # Prompt loading
│   ├── test_response_saving.py     # Response persistence
│   ├── test_review_generators.py   # Review generation
│   ├── test_sanitization.py        # Input sanitization
│   ├── test_streaming.py           # Streaming responses
│   ├── test_templates.py           # Research prompt templates
│   └── test_validation.py          # Input validation
├── project/                        # Project discovery tests (1 test file)
│   └── test_discovery.py           # Project discovery & orchestration
├── publishing/                     # Publishing tools tests (9 test files)
│   ├── test_api.py                 # Platform API clients
│   ├── test_cli.py                 # CLI interface
│   ├── test_publish_cli.py         # Publishing CLI
│   ├── test_publishing.py          # Publishing metadata
│   ├── test_publishing_api_coverage.py # API coverage tests
│   ├── test_publishing_api_full.py # Full API tests
│   ├── test_publishing_cli.py      # CLI functionality
│   ├── test_publishing_cli_full.py # Full CLI tests
│   └── test_publishing_edge_cases.py # Edge case handling
├── rendering/                      # Rendering pipeline tests (21 test files)
│   ├── conftest.py                 # Rendering test configuration
│   ├── test_cli.py                 # CLI interface
│   ├── test_config.py              # Rendering configuration
│   ├── test_core.py                # Core rendering functionality
│   ├── test_latex_package_validator.py # LaTeX package validation
│   ├── test_latex_utils.py         # LaTeX compilation utilities
│   ├── test_manuscript_discovery.py # Manuscript auto-discovery
│   ├── test_manuscript_logging.py  # Manuscript logging
│   ├── test_pdf_renderer_additional.py # Additional PDF rendering
│   ├── test_pdf_renderer_combined.py # Combined PDF rendering
│   ├── test_pdf_renderer_coverage.py # Coverage-focused PDF tests
│   ├── test_pdf_renderer_fixes.py  # PDF rendering bug fixes
│   ├── test_pdf_renderer_full.py   # Full PDF rendering tests
│   ├── test_pdf_renderer_missing_coverage.py # Missing coverage tests
│   ├── test_poster_renderer.py     # Scientific poster rendering
│   ├── test_render_all_cli.py      # Render all CLI
│   ├── test_renderers.py           # General rendering tests
│   ├── test_rendering_cli.py       # CLI functionality
│   ├── test_rendering_cli_full.py  # Full CLI tests
│   ├── test_slides_renderer_comprehensive.py # Comprehensive slides
│   ├── test_slides_renderer_coverage.py # Slides coverage
│   └── test_web_renderer_coverage.py # Web rendering coverage
├── reporting/                      # Reporting tests (9 test files)
│   ├── AGENTS.md                   # Reporting test documentation
│   ├── README.md                   # Quick reference
│   ├── test_dashboard_generator.py # Dashboard generation
│   ├── test_error_aggregator.py    # Error aggregation
│   ├── test_executive_reporter.py  # Executive reporting
│   ├── test_html_templates.py      # HTML template rendering
│   ├── test_manuscript_overview.py # Manuscript overview reports
│   ├── test_output_organizer.py    # Output organization
│   ├── test_output_reporter.py     # Output reporting
│   ├── test_pipeline_reporter.py   # Pipeline reporting
│   └── test_test_reporter.py       # Test result reporting
├── scientific/                     # Scientific tools tests (7 test files)
│   ├── test_benchmarking.py        # Performance benchmarking
│   ├── test_documentation.py       # Scientific documentation
│   ├── test_scientific_dev.py      # Scientific dev utilities
│   ├── test_scientific_dev_edge_cases.py # Edge case handling
│   ├── test_stability.py           # Numerical stability
│   ├── test_templates.py           # Scientific templates
│   └── test_validation.py          # Scientific validation
└── validation/                     # Validation system tests (32 test files)
    ├── test_audit_orchestrator.py  # Audit orchestration
    ├── test_check_links.py         # Link validation
    ├── test_check_links_comprehensive.py # Comprehensive link tests
    ├── test_check_links_edge_cases.py # Edge case link tests
    ├── test_check_links_full.py    # Full link validation
    ├── test_cli.py                 # CLI interface
    ├── test_doc_scanner.py         # Document scanning
    ├── test_doc_scanner_coverage.py # Coverage-focused scanning
    ├── test_doc_scanner_full.py    # Full document scanning
    ├── test_doc_scanner_phases.py  # Scanning phases
    ├── test_figure_validator.py    # Figure validation
    ├── test_integrity.py           # Integrity verification
    ├── test_integrity_edge_cases.py # Edge case integrity tests
    ├── test_issue_categorizer.py   # Issue categorization
    ├── test_link_validator.py      # Link validation engine
    ├── test_markdown_validator.py  # Markdown validation
    ├── test_output_validator.py    # Output validation
    ├── test_pdf_validator.py       # PDF validation
    ├── test_repo_scanner.py        # Repository scanning
    ├── test_repo_scanner_additional.py # Additional repo scanning
    ├── test_repo_scanner_comprehensive.py # Comprehensive repo scanning
    ├── test_repo_scanner_coverage.py # Coverage repo scanning
    ├── test_repo_scanner_full.py   # Full repo scanning
    ├── test_validate_markdown_cli.py # Markdown CLI
    ├── test_validate_markdown_cli_comprehensive.py # Comprehensive CLI
    ├── test_validate_markdown_cli_full.py # Full CLI tests
    ├── test_validate_md_cli_coverage.py # Coverage CLI tests
    ├── test_validate_pdf_cli.py    # PDF CLI
    ├── test_validate_pdf_cli_comprehensive.py # Comprehensive PDF CLI
    ├── test_validate_pdf_cli_coverage.py # Coverage PDF CLI
    ├── test_validate_pdf_cli_full.py # Full PDF CLI
    └── test_validation_cli.py      # General validation CLI
```

## Shared Test Infrastructure

### Test Fixtures (`conftest.py`)

The `conftest.py` file provides shared pytest fixtures for common test setup patterns:

#### Project Configuration Fixtures

```python
@pytest.fixture
def project_config_structure(tmp_path):
    """Create standard project config structure: tmp_path/projects/project/manuscript/config.yaml"""

@pytest.fixture
def sample_project_config():
    """Return sample project configuration data with paper, authors, publication info"""

@pytest.fixture
def project_config_file(project_config_structure, sample_project_config):
    """Create config.yaml file with sample data"""
```

#### Output Structure Fixtures

```python
@pytest.fixture
def output_directory_structure(tmp_path):
    """Create standard output directory structure with all subdirectories"""

@pytest.fixture
def pdf_file_fixture(tmp_path):
    """Create PDF file using reportlab (or fallback if not available)"""

@pytest.fixture
def output_with_pdf(output_directory_structure, pdf_file_fixture):
    """Create output directory with PDF in correct pdf/ subdirectory location"""
```

### Test Utilities (`_test_helpers.py`)

The `_test_helpers.py` module provides helper functions for creating test data:

#### Configuration Helpers

```python
def create_project_config_structure(repo_root: Path, project_name: str = "project") -> Path:
    """Create projects/{project_name}/manuscript/config.yaml structure"""

def create_sample_config_data() -> Dict[str, Any]:
    """Return sample config data with realistic values"""

def write_config_file(config_file: Path, config_data: Dict[str, Any]) -> None:
    """Write config data to YAML file"""
```

#### Output Structure Helpers

```python
def create_output_directory_structure(output_dir: Path) -> None:
    """Create pdf/, web/, slides/, figures/, data/, etc. subdirectories"""

def create_pdf_file(pdf_path: Path, content: str = "Test PDF", size_kb: int = 100) -> None:
    """Create PDF file with specified content and size"""

def create_output_with_pdf(output_dir: Path, pdf_name: str = "project_combined.pdf") -> Path:
    """Create output structure with PDF in correct location"""
```

#### Content Creation Helpers

```python
def create_test_manuscript_files(manuscript_dir: Path) -> Dict[str, Path]:
    """Create sample 01_abstract.md, 02_introduction.md, etc."""

def create_test_figure_files(figures_dir: Path) -> Dict[str, Path]:
    """Create sample PNG figure files"""

def cleanup_test_directory(test_dir: Path) -> None:
    """Clean up test directory and contents"""
```

### Usage Examples

#### Testing Configuration Loading

```python
def test_config_loading(project_config_file):
    """Test config loading with file structure"""
    config = load_config(project_config_file)
    assert config['paper']['title'] == 'Test Research Paper'
```

#### Testing Output Validation

```python
def test_output_validation(output_with_pdf):
    """Test output validation with proper PDF location"""
    result = validate_copied_outputs(output_with_pdf)
    assert result is True
```

#### Testing with Custom Config

```python
def test_custom_config(tmp_path):
    """Test with custom configuration"""
    from tests.infrastructure.test_utils import create_project_config_structure, write_config_file

    config_file = create_project_config_structure(tmp_path, "myproject")
    custom_config = {
        'paper': {'title': 'My Custom Paper'},
        'llm': {'translations': {'enabled': True, 'languages': ['es']}}
    }
    write_config_file(config_file, custom_config)

    languages = get_translation_languages(tmp_path, "myproject")
    assert languages == ['es']
```

## Test Organization by Module

### Core Infrastructure (`core/`)

**Purpose:** Test fundamental utilities used by all other modules (24 test files)

- **`test_checkpoint.py`** - Checkpoint/resume functionality
  - Checkpoint creation and validation
  - Resume from checkpoint
  - Checkpoint state management

- **`test_cli.py`** - Core CLI interface
- **`test_config_cli_coverage.py`** - Configuration CLI coverage tests
- **`test_config_loader.py`** - YAML/JSON configuration loading
  - Environment variable integration
  - Author metadata formatting
  - Configuration validation

- **`test_credentials.py`** - Credential management
  - Credential storage and retrieval
  - Secure credential handling

- **`test_credentials_module.py`** - Credential module coverage
- **`test_environment.py`** - Environment detection and setup
  - Virtual environment detection
  - System dependency checking

- **`test_exceptions.py`** - Custom exception hierarchy
  - Exception context preservation
  - Module-specific exception types
  - Error chaining and messaging

- **`test_file_inventory.py`** - File inventory tracking
  - File discovery and cataloging
  - Inventory reporting

- **`test_file_operations.py`** - File I/O utilities
  - Safe file reading and writing
  - Directory operations

- **`test_logging_helpers.py`** - Logging helper functions
- **`test_logging_progress.py`** - Progress-aware logging
- **`test_logging_utils.py`** - Logging system validation
  - Environment-based log level configuration
  - Context managers for operation tracking
  - TTY-aware color output

- **`test_menu.py`** - Interactive menu system
- **`test_multi_project.py`** - Multi-project orchestration
  - Cross-project execution
  - Project ordering and dependencies

- **`test_performance.py`** - Performance monitoring
  - Timing and memory tracking
  - Performance threshold validation

- **`test_pipeline.py`** - Pipeline execution
  - Stage execution and sequencing
  - Pipeline state management

- **`test_pipeline_summary.py`** - Pipeline summary generation
  - Summary report formatting
  - Stage result aggregation

- **`test_progress.py`** - Progress tracking
  - Progress bar functionality
  - Progress state management
  - Progress reporting

- **`test_project_discovery.py`** - Project discovery and validation
  - Project structure validation (src/, tests/ directories)
  - Project metadata extraction and parsing
  - Multi-project discovery from projects/ directory
  - Project structure integrity checking

- **`test_project_logger.py`** - Project-specific logging
- **`test_retry.py`** - Retry mechanisms
  - Retry logic with backoff
  - Retry condition handling
  - Retry state tracking

- **`test_script_discovery.py`** - Script auto-discovery
  - Pipeline script detection
  - Script ordering and validation

- **`test_security.py`** - Security utilities
  - Input sanitization
  - Path traversal prevention

### Documentation Tools (`documentation/`)

**Purpose:** Test figure management and documentation generation (4 test files)

- **`test_figure_manager.py`** - Figure registry and numbering
  - Figure registration with metadata
  - LaTeX figure block generation
  - Cross-reference management

- **`test_glossary_gen.py`** - API documentation generation
  - AST-based function/class extraction
  - Markdown table generation
  - Auto-generated content injection

- **`test_image_manager.py`** - Image processing in markdown
  - Image insertion and path resolution
  - Format validation and conversion

- **`test_markdown_integration.py`** - Markdown processing integration
  - Figure insertion into sections
  - Reference resolution and validation

### Project Discovery (`project/`)

**Purpose:** Test project discovery and orchestration (1 test file)

- **`test_discovery.py`** - Project discovery and orchestration
  - Multi-project directory scanning
  - Project validation and metadata extraction
  - Discovery configuration

### LLM Integration (`llm/`)

**Purpose:** Test local LLM integration for research assistance (19 test files)

- **`test_cli.py`** - Command-line interface
  - CLI argument parsing for LLM operations

- **`test_config.py`** - LLM configuration management
  - Model selection and parameter tuning
  - Environment-based configuration

- **`test_context.py`** - Conversation context management
  - Multi-turn conversation tracking
  - Context window management

- **`test_context_engineering.py`** - Context engineering strategies
  - Context window optimization
  - Priority-based context selection

- **`test_core.py`** - Core LLM client functionality
  - Model loading and inference
  - Streaming response handling

- **`test_llm_core_additional.py`** - Additional core tests
- **`test_llm_core_coverage.py`** - Coverage-focused tests
- **`test_llm_core_full.py`** - Full core tests

- **`test_llm_review.py`** - LLM manuscript review tests
  - Review metrics and session tracking
  - Manuscript review generation
  - Quality validation

- **`test_logging.py`** - LLM logging
- **`test_ollama_utils.py`** - Ollama client utilities
  - Model management and switching
  - Connection handling and error recovery

- **`test_prompts_composer.py`** - Prompt composition utilities
  - Multi-part prompt assembly
  - Template variable substitution

- **`test_prompts_loader.py`** - Prompt loading and management
  - Template file loading
  - Prompt caching and validation

- **`test_response_saving.py`** - Response persistence
  - Response storage and retrieval
  - Format preservation

- **`test_review_generators.py`** - Review generation
  - Automated review creation
  - Review quality metrics

- **`test_sanitization.py`** - Input sanitization
  - Prompt cleaning and validation
  - Output sanitization

- **`test_streaming.py`** - Streaming responses
  - Streaming token handling
  - Stream interruption recovery

- **`test_templates.py`** - Research prompt templates
  - Template loading and validation
  - Research-specific prompt engineering

- **`test_validation.py`** - Input validation and safety
  - Prompt sanitization and filtering
  - Response validation and filtering

### Publishing Tools (`publishing/`)

**Purpose:** Test academic publishing workflows

- **`test_api.py`** - Platform API client validation
  - Zenodo, arXiv, GitHub API integrations
  - Authentication and error handling

- **`test_cli.py`** - Publishing CLI interface
  - Command-line publishing workflows

- **`test_publish_cli.py`** - Publishing CLI tests
- **`test_publishing_api_coverage.py`** - API coverage tests
- **`test_publishing_api_full.py`** - Full API tests
- **`test_publishing_cli_full.py`** - Full CLI tests
- **`test_publishing_cli.py`** - CLI functionality
- **`test_publishing_edge_cases.py`** - Edge case handling
- **`test_publishing.py`** (427 lines) - Publishing metadata handling
  - Citation generation (BibTeX, APA, MLA)
  - DOI validation and formatting
  - Author and affiliation management

### Rendering Pipeline (`rendering/`)

**Purpose:** Test multi-format output generation (21 test files)

- **`test_cli.py`** - Rendering CLI interface
  - Multi-format rendering command-line tools

- **`test_config.py`** - Rendering configuration
- **`test_core.py`** - Core rendering functionality
  - Render manager initialization and coordination

- **`test_latex_package_validator.py`** - LaTeX package validation
  - Package availability checking
  - Dependency resolution

- **`test_latex_utils.py`** - LaTeX compilation utilities
  - LaTeX syntax validation and processing

- **`test_manuscript_discovery.py`** - Manuscript auto-discovery
  - Manuscript file detection
  - Metadata extraction from manuscripts

- **`test_manuscript_logging.py`** - Manuscript logging

- **`test_pdf_renderer_*.py`** (6 files) - PDF generation validation
  - Individual and combined PDF rendering
  - LaTeX compilation and error handling
  - Coverage and regression tests

- **`test_poster_renderer.py`** - Scientific poster generation
  - Poster layout and content validation

- **`test_render_all_cli.py`** - Render all CLI
- **`test_renderers.py`** - General rendering tests
- **`test_rendering_cli.py`** - CLI functionality
- **`test_rendering_cli_full.py`** - Full CLI tests

- **`test_slides_renderer_*.py`** (2 files) - Presentation slide generation
  - Beamer LaTeX and reveal.js HTML slides

- **`test_web_renderer_coverage.py`** - HTML/web output generation
  - Interactive web content creation

### Scientific Tools (`scientific/`)

**Purpose:** Test scientific computing utilities (7 test files)

- **`test_benchmarking.py`** - Performance benchmarking
  - Benchmark suite execution
  - Performance regression detection

- **`test_documentation.py`** - Scientific documentation
  - Documentation generation and validation

- **`test_scientific_dev.py`** - Scientific development tools
  - Numerical stability checking
  - Best practices validation

- **`test_scientific_dev_edge_cases.py`** - Edge case handling

- **`test_stability.py`** - Numerical stability
  - Floating point stability validation
  - Convergence testing

- **`test_templates.py`** - Scientific templates
  - Template generation and validation

- **`test_validation.py`** - Scientific validation
  - Data validation and integrity checks

### Reporting (`reporting/`)

**Purpose:** Test pipeline reporting and error aggregation (9 test files)

- **`test_dashboard_generator.py`** - Dashboard generation
  - Health-scored visual dashboard creation
  - Multi-metric aggregation

- **`test_error_aggregator.py`** - Error aggregation
  - Error collection and categorization
  - Frequency analysis and prioritization

- **`test_executive_reporter.py`** - Executive reporting
  - High-level summary generation
  - Metric extraction and formatting

- **`test_html_templates.py`** - HTML template rendering
  - Template variable substitution
  - CSS styling validation

- **`test_manuscript_overview.py`** - Manuscript overview reports
  - Manuscript metrics collection
  - Overview formatting

- **`test_output_organizer.py`** - Output organization
  - File organization and categorization
  - Output directory structure

- **`test_output_reporter.py`** - Output reporting
  - Output summary generation
  - Multi-format report output

- **`test_pipeline_reporter.py`** - Pipeline reporting
  - Stage duration tracking
  - Bottleneck identification

- **`test_test_reporter.py`** - Test result reporting
  - Test summary formatting
  - Coverage reporting

### Validation System (`validation/`)

**Purpose:** Test quality assurance and validation tools (32 test files)

- **`test_check_links.py`** - Link validation
  - Internal and external link checking
  - Reference resolution validation

- **`test_check_links_comprehensive.py`** - link tests
- **`test_check_links_edge_cases.py`** - Edge case link tests
- **`test_check_links_full.py`** - Full link validation

- **`test_cli.py`** - Validation CLI interface
  - Command-line validation tools

- **`test_doc_scanner.py`** - Document scanning and analysis
  - Repository-wide document validation
  - Quality and completeness checking

- **`test_doc_scanner_coverage.py`** - Coverage-focused scanning
- **`test_doc_scanner_full.py`** - Full document scanning
- **`test_doc_scanner_phases.py`** - Scanning phases

- **`test_integrity.py`** (496 lines) - Integrity verification
  - File hash validation
  - Cross-reference checking
  - Data consistency validation

- **`test_integrity_edge_cases.py`** - Edge case integrity tests

- **`test_issue_categorizer.py`** - Issue categorization
  - Issue type detection
  - Priority assignment

- **`test_link_validator.py`** - Link validation engine
  - Link resolution and verification
  - Broken link detection

- **`test_markdown_validator.py`** - Markdown validation
  - Image reference verification
  - Cross-reference validation
  - Mathematical notation checking

- **`test_pdf_validator.py`** (328 lines) - PDF validation
  - Text extraction and analysis
  - Unresolved reference detection
  - Document structure validation

- **`test_repo_scanner.py`** - Repository scanning
  - File structure validation
  - Documentation completeness checking

- **`test_repo_scanner_additional.py`** - Additional repo scanning
- **`test_repo_scanner_comprehensive.py`** - repo scanning
- **`test_repo_scanner_coverage.py`** - Coverage repo scanning
- **`test_repo_scanner_full.py`** - Full repo scanning

- **`test_validate_markdown_cli.py`** - Markdown CLI
- **`test_validate_markdown_cli_comprehensive.py`** - CLI
- **`test_validate_markdown_cli_full.py`** - Full CLI tests
- **`test_validate_md_cli_coverage.py`** - Coverage CLI tests

- **`test_validate_pdf_cli.py`** - PDF CLI
- **`test_validate_pdf_cli_comprehensive.py`** - PDF CLI
- **`test_validate_pdf_cli_coverage.py`** - Coverage PDF CLI
- **`test_validate_pdf_cli_full.py`** - Full PDF CLI

- **`test_validation_cli.py`** - General validation CLI

## Testing Approach

### Data and Real Services

All infrastructure tests use **real implementations** without mocks:

- **Literature tests**: PDF downloads from arXiv/Semantic Scholar
- **Publishing tests**: Real API calls to Zenodo sandbox and GitHub
- **Rendering tests**: Real LaTeX/Pandoc compilation
- **LLM tests**: Real Ollama service connections

### Network-Dependent Tests

Tests requiring external services use pytest markers and automatic skipping:

```python
@pytest.mark.requires_zenodo
@pytest.mark.requires_network
def test_publish_to_zenodo(zenodo_credentials):
    # Real Zenodo API test
    # Automatically skipped if ZENODO_SANDBOX_TOKEN not configured
    pass
```

**Available markers:**

- `requires_zenodo` - Zenodo API credentials needed
- `requires_github` - GitHub API credentials needed
- `requires_arxiv` - arXiv API credentials needed (optional)
- `requires_latex` - LaTeX installation needed
- `requires_network` - Internet access needed
- `requires_ollama` - Ollama service needed

**Run tests selectively:**

```bash
# Skip all credential-dependent tests
pytest tests/infra_tests/ -m "not requires_credentials"

# Run only Zenodo tests
pytest tests/infra_tests/ -m requires_zenodo

# Skip LaTeX tests
pytest tests/infra_tests/ -m "not requires_latex"
```

### Credential Configuration

1. Create `.env` file from template:

   ```bash
   cp .env.example .env
   ```

2. Add credentials:

   ```bash
   ZENODO_SANDBOX_TOKEN=your_sandbox_token
   GITHUB_TOKEN=your_github_token
   GITHUB_REPO=username/test-repo
   ```

3. Run tests (credential tests auto-skip if not configured):

   ```bash
   pytest tests/infra_tests/
   ```

See [docs/testing-with-credentials.md](../../docs/development/testing-with-credentials.md) for detailed setup.

### Test Cleanup

Tests automatically clean up test artifacts:

- **Zenodo**: Depositions deleted after test
- **GitHub**: Releases and tags deleted after test  
- **Files**: Temporary files cleaned by pytest fixtures
- **PDFs**: Downloaded files in temp directories

### For modules requiring external services

```python
@pytest.mark.requires_ollama
def test_llm_integration():
    """Test requiring Ollama service."""
    # Actual LLM integration test
    pass

# Run with service available
pytest -m requires_ollama

# Skip network tests
pytest -m "not requires_ollama"
```

### Pure Logic Tests

Tests that validate logic without external dependencies:

```python
def test_config_parsing():
    """Test configuration parsing logic only."""
    # No network calls, pure logic validation
    config = LiteratureConfig.from_env()
    assert config.default_limit == 25
```

### Mock-Free Philosophy

Infrastructure tests use real implementations where possible:

- **file I/O** with temporary directories
- **Actual subprocess calls** for CLI validation
- **data structures** and processing
- **Integration testing** of actual workflows

### Error Condition Testing

error handling validation:

```python
def test_api_rate_limit_handling():
    """Test graceful handling of API rate limits."""
    # Simulate rate limit response
    # Verify retry logic and backoff
    # Check error messaging
```

## Coverage Status

Current coverage: **83.33%** (exceeds 60% requirement by 39%!)

| Module | Tests | Coverage | Status |
| --- | --- | --- | --- |
| `core/` | 24 | 100% | ✅ |
| `documentation/` | 4 | 100% | ✅ |
| `llm/` | 19 | 91% | ✅ |
| `project/` | 1 | 100% | ✅ |
| `publishing/` | 9 | 100% | ✅ |
| `rendering/` | 21 | 91% | ✅ |
| `reporting/` | 9 | 75% | ✅ |
| `scientific/` | 7 | 100% | ✅ |
| `validation/` | 32 | 100% | ✅ |

## Running Infrastructure Tests

### All Infrastructure Tests

```bash
# From repository root
pytest tests/infra_tests/ --cov=infrastructure --cov-report=html --cov-fail-under=60

# Skip network-dependent tests
pytest tests/infra_tests/ -m "not requires_ollama"
```

### Module-Specific Testing

```bash
# Core utilities
pytest tests/infra_tests/core/ -v

# LLM integration (requires Ollama)
pytest tests/infra_tests/llm/ -m requires_ollama -v

# Reporting
pytest tests/infra_tests/reporting/ -v

# Validation system
pytest tests/infra_tests/validation/ -v
```

### Coverage Analysis

```bash
# Show missing lines
pytest tests/infra_tests/ --cov=infrastructure --cov-report=term-missing

# Generate HTML report
pytest tests/infra_tests/ --cov=infrastructure --cov-report=html
open htmlcov/index.html
```

## Integration with Build Pipeline

### Automatic Execution

Infrastructure tests run as part of the test suite:

```bash
# Stage 1: Run all tests
python3 scripts/01_run_tests.py
```

This executes both infrastructure and project tests with coverage validation.

### Selective Testing

For development workflows:

```bash
# Test only changed modules
pytest tests/infra_tests/core/ tests/infra_tests/reporting/

# Test specific functionality
pytest tests/infra_tests/ -k "test_config" -v
```

## Test Development Guidelines

### Test File Organization

```python
"""Tests for infrastructure.module.submodule"""
import pytest
from infrastructure.module.submodule import ClassToTest


class TestClassToTest:
    """Test suite for ClassToTest."""

    def test_basic_functionality(self):
        """Test normal operation."""
        instance = ClassToTest()
        result = instance.method("input")
        assert result == "expected"

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(SpecificException):
            ClassToTest().method("invalid")

    @pytest.mark.integration
    def test_full_workflow(self):
        """Test workflow integration."""
        # Test end-to-end functionality
        pass
```

### Temporary File Handling

```python
def test_file_operations(tmp_path):
    """Test file I/O operations."""
    test_file = tmp_path / "test.json"
    test_file.write_text('{"key": "value"}')

    # Test file processing
    result = process_json_file(test_file)
    assert result["key"] == "value"
```

### Network Test Management

```python
@pytest.mark.requires_ollama
def test_llm_functionality():
    """Test requiring Ollama service."""
    client = LLMClient()
    response = client.query("test prompt")
    assert "response" in response.lower()

# Alternative: test logic without network
def test_llm_prompt_formatting():
    """Test prompt formatting logic only."""
    template = get_template("summarize")
    prompt = template.format(text="test text")
    assert "test text" in prompt
```

## Debugging and Troubleshooting

### Common Test Issues

**Import Errors:**

```bash
# Ensure infrastructure is on path
cd /path/to/repo
PYTHONPATH=. pytest tests/infra_tests/test_core.py
```

**Network Test Failures:**

```bash
# Check service availability
curl http://localhost:11434/api/tags  # Ollama

# Skip network tests
pytest tests/infra_tests/ -m "not requires_ollama"
```

**Coverage Issues:**

```bash
# Show uncovered lines
pytest tests/infra_tests/ --cov=infrastructure --cov-report=term-missing

# Focus on specific module
pytest tests/infra_tests/core/ --cov=infrastructure.core --cov-report=html
```

### Performance Testing

```bash
# Time test execution
time pytest tests/infra_tests/ -x

# Profile slow tests
pytest tests/infra_tests/ --durations=10
```

## Module-Specific Testing Notes

### Reporting Module

**Dashboard and report generation** tests validate output formatting and metric aggregation.

**Error aggregation** tests verify error collection, categorization, and prioritization.

**HTML template** tests validate template rendering and styling.

### LLM Module

**Requires Ollama** running locally with at least one model.

**Context management** tests validate conversation state and token limits.

**Template system** tests ensure research prompts are well-formed.

### Rendering Module

**LaTeX compilation** tests require `xelatex` and related packages.

**File output validation** checks generated PDFs, HTML, and LaTeX files.

**Error handling** tests validate graceful failure on compilation errors.

### Validation Module

**Repository scanning** tests validate file structure and documentation completeness.

**PDF analysis** tests require sample PDF files for validation.

**Cross-reference checking** validates internal document links and citations.

## See Also

- [`README.md`](README.md) - Quick reference guide
- [`../AGENTS.md`](../AGENTS.md) - Test suite documentation
- [`../../docs/development/testing-guide.md`](../../docs/development/testing-guide.md) - Testing best practices
- [`../../infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md) - Infrastructure module overview

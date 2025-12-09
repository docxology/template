# tests/infrastructure/ - Infrastructure Module Tests

## Purpose

The `tests/infrastructure/` directory contains comprehensive tests for the reusable infrastructure modules in `infrastructure/`. These tests validate the build tools, validation systems, documentation utilities, and integration components that support research projects.

## Coverage Requirements

**60% minimum coverage** required for infrastructure modules. This ensures critical infrastructure functionality is validated while allowing flexibility for rapidly evolving research tools.

## Directory Structure

```
tests/infrastructure/
├── conftest.py                      # Shared test configuration
├── build/                          # Build system tests
│   ├── test_build_additional.py    # Additional build tests
│   ├── test_build_complete.py      # Comprehensive build tests
│   ├── test_build_verifier_complete_coverage.py # Complete build verifier coverage
│   ├── test_build_verifier_coverage.py # Build verifier coverage
│   ├── test_build_verifier.py      # Build verification (400 lines)
│   ├── test_quality_checker_complete_coverage.py # Complete quality checker coverage
│   ├── test_quality_checker_coverage.py # Quality checker coverage
│   ├── test_quality_checker.py     # Quality analysis (463 lines)
│   ├── test_reproducibility_complete_coverage.py # Complete reproducibility coverage
│   ├── test_reproducibility_coverage.py # Reproducibility coverage
│   └── test_reproducibility.py     # Reproducibility tracking (427 lines)
├── core/                           # Core utilities tests
│   ├── test_checkpoint.py          # Checkpoint/resume functionality
│   ├── test_config_cli_coverage.py # Config CLI coverage
│   ├── test_config_loader.py       # Configuration loading
│   ├── test_exceptions.py          # Exception handling
│   ├── test_logging_utils.py       # Logging system
│   ├── test_progress.py            # Progress tracking
│   └── test_retry.py               # Retry mechanisms
├── documentation/                  # Documentation tools tests
│   ├── test_figure_manager.py      # Figure management (registry, numbering)
│   ├── test_generate_glossary_cli.py # Glossary generation CLI
│   ├── test_glossary_gen.py        # API documentation generation (189 lines)
│   ├── test_image_manager.py       # Image handling in markdown
│   └── test_markdown_integration.py # Markdown processing integration
├── literature/                     # Literature search tests
│   ├── test_api.py                 # API client implementations
│   ├── test_config.py              # Literature configuration
│   ├── test_core.py                # Core literature functionality
│   ├── test_html_parsing.py        # HTML parsing utilities
│   ├── test_integration.py         # Full workflow integration
│   ├── test_library_index.py       # JSON library management
│   ├── test_literature_cli.py       # CLI interface (comprehensive)
│   ├── test_literature_cli_simple.py # CLI interface (simple)
│   ├── test_llm_operations.py      # LLM integration for literature
│   ├── test_logging.py             # Literature logging tests
│   ├── test_paper_selector.py     # Paper selection utilities
│   ├── test_pdf_handler_comprehensive.py # PDF downloading (robust)
│   ├── test_pdf_handler_fallbacks.py # PDF download fallback strategies
│   ├── test_pdf_handler_simple.py # PDF downloading (simple)
│   ├── test_progress.py            # Progress tracking for literature
│   ├── test_pure_logic.py          # Pure logic tests (no network)
│   ├── test_summarizer.py          # Paper summarization
│   ├── test_unpaywall.py           # Unpaywall integration
│   ├── test_workflow.py            # Literature workflow tests
│   └── test_workflow_skip_existing.py # Workflow with skip existing
├── llm/                            # LLM integration tests
│   ├── conftest.py                 # LLM test configuration
│   ├── AGENTS.md                   # LLM test documentation
│   ├── test_cli.py                 # CLI interface
│   ├── test_config.py              # Configuration management
│   ├── test_context.py             # Conversation context
│   ├── test_core.py                # Core LLM functionality
│   ├── test_llm_core_additional.py # Additional core tests
│   ├── test_llm_core_coverage.py   # Coverage-focused tests
│   ├── test_llm_core_full.py       # Comprehensive core tests
│   ├── test_llm_review.py          # LLM manuscript review tests
│   ├── test_ollama_utils.py        # Ollama client utilities
│   ├── test_prompts_composer.py    # Prompt composition utilities
│   ├── test_prompts_loader.py      # Prompt loading and management
│   ├── test_templates.py           # Research prompt templates
│   └── test_validation.py          # Input validation
├── publishing/                     # Publishing tools tests
│   ├── test_api.py                 # Platform API clients
│   ├── test_cli.py                 # CLI interface
│   ├── test_publish_cli.py         # Publishing CLI
│   ├── test_publishing_api_coverage.py # API coverage tests
│   ├── test_publishing_api_full.py # Full API tests
│   ├── test_publishing_cli_full.py # Full CLI tests
│   ├── test_publishing_cli.py      # CLI functionality
│   ├── test_publishing_edge_cases.py # Edge case handling
│   └── test_publishing.py          # Publishing metadata (427 lines)
├── test_cli/                        # Reserved for future CLI tests
├── rendering/                      # Rendering pipeline tests
│   ├── conftest.py                 # Rendering test configuration
│   ├── test_cli.py                 # CLI interface
│   ├── test_config.py              # Rendering configuration
│   ├── test_core.py                # Core rendering functionality
│   ├── test_latex_utils.py         # LaTeX compilation utilities
│   ├── test_pdf_renderer_additional.py # Additional PDF rendering
│   ├── test_pdf_renderer_combined.py # Combined PDF rendering
│   ├── test_pdf_renderer_coverage.py # Coverage-focused PDF tests
│   ├── test_pdf_renderer_fixes.py  # PDF rendering bug fixes
│   ├── test_pdf_renderer_full.py   # Full PDF rendering tests
│   ├── test_poster_renderer.py     # Scientific poster rendering
│   ├── test_render_all_cli.py      # Render all CLI
│   ├── test_renderers.py           # General rendering tests
│   ├── test_rendering_cli_full.py  # Full CLI tests
│   ├── test_rendering_cli.py       # CLI functionality
│   ├── test_slides_renderer_comprehensive.py # Comprehensive slides
│   ├── test_slides_renderer_coverage.py # Slides coverage
│   └── test_web_renderer_coverage.py # Web rendering coverage
├── scientific/                     # Scientific tools tests
│   ├── test_scientific_dev_edge_cases.py # Edge case handling
│   └── test_scientific_dev.py      # Scientific development utilities
├── validation/                     # Validation system tests
│   ├── test_check_links.py         # Link validation
│   ├── test_check_links_comprehensive.py # Comprehensive link tests
│   ├── test_check_links_edge_cases.py # Edge case link tests
│   ├── test_check_links_full.py    # Full link validation
│   ├── test_cli.py                 # CLI interface
│   ├── test_doc_scanner.py         # Document scanning
│   ├── test_doc_scanner_coverage.py # Coverage-focused scanning
│   ├── test_doc_scanner_full.py    # Full document scanning
│   ├── test_doc_scanner_phases.py  # Scanning phases
│   ├── test_integrity.py           # Integrity verification (496 lines)
│   ├── test_markdown_validator.py  # Markdown validation
│   ├── test_pdf_validator.py       # PDF validation (328 lines)
│   ├── test_repo_scanner.py        # Repository scanning
│   ├── test_repo_scanner_additional.py # Additional repo scanning
│   ├── test_repo_scanner_comprehensive.py # Comprehensive repo scanning
│   ├── test_repo_scanner_coverage.py # Coverage repo scanning
│   ├── test_repo_scanner_full.py   # Full repo scanning
│   ├── test_validate_markdown_cli.py # Markdown CLI
│   ├── test_validate_markdown_cli_comprehensive.py # Comprehensive CLI
│   ├── test_validate_markdown_cli_full.py # Full CLI tests
│   ├── test_validate_md_cli_coverage.py # Coverage CLI tests
│   ├── test_validate_pdf_cli.py    # PDF CLI
│   ├── test_validate_pdf_cli_comprehensive.py # Comprehensive PDF CLI
│   ├── test_validate_pdf_cli_coverage.py # Coverage PDF CLI
│   ├── test_validate_pdf_cli_full.py # Full PDF CLI
│   └── test_validation_cli.py      # General validation CLI
```

## Test Organization by Module

### Core Infrastructure (`core/`)

**Purpose:** Test fundamental utilities used by all other modules

- **`test_checkpoint.py`** - Checkpoint/resume functionality
  - Checkpoint creation and validation
  - Resume from checkpoint
  - Checkpoint state management

- **`test_config_cli_coverage.py`** - Configuration CLI coverage tests
- **`test_config_loader.py`** - YAML/JSON configuration loading
  - Environment variable integration
  - Author metadata formatting
  - Configuration validation

- **`test_exceptions.py`** - Custom exception hierarchy
  - Exception context preservation
  - Module-specific exception types
  - Error chaining and messaging

- **`test_logging_utils.py`** - Logging system validation
  - Environment-based log level configuration
  - Context managers for operation tracking
  - TTY-aware color output

- **`test_progress.py`** - Progress tracking
  - Progress bar functionality
  - Progress state management
  - Progress reporting

- **`test_retry.py`** - Retry mechanisms
  - Retry logic with backoff
  - Retry condition handling
  - Retry state tracking

### Build System (`build/`)

**Purpose:** Validate build verification and quality assurance

- **`test_build_additional.py`** - Additional build verification tests
- **`test_build_complete.py`** - Comprehensive build system tests
- **`test_build_verifier_complete_coverage.py`** - Complete coverage for build verifier
- **`test_build_verifier_coverage.py`** - Build verifier coverage tests
- **`test_build_verifier.py`** (400 lines) - Build process validation
  - Artifact verification and integrity
  - Build reproducibility testing
  - Environment consistency checking

- **`test_quality_checker_complete_coverage.py`** - Complete coverage for quality checker
- **`test_quality_checker_coverage.py`** - Quality checker coverage tests
- **`test_quality_checker.py`** (463 lines) - Document quality analysis
  - Readability metrics (Flesch score, Fog index)
  - Academic writing standards compliance
  - Quality scoring and reporting

- **`test_reproducibility_complete_coverage.py`** - Complete coverage for reproducibility
- **`test_reproducibility_coverage.py`** - Reproducibility coverage tests
- **`test_reproducibility.py`** (427 lines) - Environment tracking
  - Build manifest generation
  - Dependency snapshot capture
  - Reproducibility verification

### Documentation Tools (`documentation/`)

**Purpose:** Test figure management and documentation generation

- **`test_figure_manager.py`** - Figure registry and numbering
  - Figure registration with metadata
  - LaTeX figure block generation
  - Cross-reference management

- **`test_image_manager.py`** - Image processing in markdown
  - Image insertion and path resolution
  - Format validation and conversion

- **`test_generate_glossary_cli.py`** - Glossary generation CLI tests
- **`test_glossary_gen.py`** (189 lines) - API documentation generation
  - AST-based function/class extraction
  - Markdown table generation
  - Auto-generated content injection

- **`test_markdown_integration.py`** - Markdown processing integration
  - Figure insertion into sections
  - Reference resolution and validation

### Literature Search (`literature/`)

**Purpose:** Test academic literature discovery and management

- **`test_api.py`** - External API client validation
  - arXiv, Semantic Scholar, Unpaywall clients
  - Rate limiting and error handling

- **`test_config.py`** - Configuration management
  - Environment variable loading
  - Source configuration validation

- **`test_core.py`** - Core literature functionality
  - Search coordination across sources
  - Result normalization and deduplication

- **`test_html_parsing.py`** - HTML parsing utilities
  - HTML content extraction
  - Metadata parsing from HTML

- **`test_integration.py`** - Full workflow integration
  - Search → Download → Library → Citation workflow

- **`test_library_index.py`** - JSON library management
  - Entry addition and retrieval
  - Metadata validation and updating

- **`test_literature_cli.py`** - Command-line interface (comprehensive)
  - CLI argument parsing and validation
  - Output formatting and error reporting
  - Full CLI workflow testing

- **`test_literature_cli_simple.py`** - Command-line interface (simple)
  - Basic CLI functionality
  - Help output validation

- **`test_llm_operations.py`** - LLM integration for literature
  - Paper summarization with LLM
  - LLM-assisted search refinement

- **`test_logging.py`** - Literature logging tests
  - Logging configuration
  - Log message validation

- **`test_paper_selector.py`** - Paper selection utilities
  - Paper ranking and selection
  - Selection criteria validation

- **`test_pdf_handler_comprehensive.py`** - Robust PDF downloading
  - Multiple download strategies
  - Retry logic and fallback mechanisms

- **`test_pdf_handler_fallbacks.py`** - PDF download fallback strategies
  - Alternative download sources
  - Fallback mechanism testing

- **`test_pdf_handler_simple.py`** - PDF downloading (simple)
  - Basic PDF download functionality
  - Simple error handling

- **`test_progress.py`** - Progress tracking for literature
  - Progress bar functionality
  - Progress state management

- **`test_pure_logic.py`** - Logic-only tests (no network)
  - Configuration parsing, result processing
  - Citation key generation and validation

- **`test_summarizer.py`** - Paper summarization
  - Summary generation
  - Summary quality validation

- **`test_unpaywall.py`** - Open access PDF resolution
  - Unpaywall API integration
  - Legal PDF source discovery

- **`test_workflow.py`** - Literature workflow tests
  - Complete workflow validation
  - Workflow state management

- **`test_workflow_skip_existing.py`** - Workflow with skip existing
  - Skip existing files functionality
  - Incremental workflow processing

### LLM Integration (`llm/`)

**Purpose:** Test local LLM integration for research assistance

- **`test_core.py`** - Core LLM client functionality
  - Model loading and inference
  - Streaming response handling

- **`test_context.py`** - Conversation context management
  - Multi-turn conversation tracking
  - Context window management

- **`test_templates.py`** - Research prompt templates
  - Template loading and validation
  - Research-specific prompt engineering

- **`test_config.py`** - LLM configuration management
  - Model selection and parameter tuning
  - Environment-based configuration

- **`test_validation.py`** - Input validation and safety
  - Prompt sanitization and filtering
  - Response validation and filtering

- **`test_cli.py`** - Command-line interface
  - CLI argument parsing for LLM operations

- **`test_llm_review.py`** - LLM manuscript review tests
  - Review metrics and session tracking
  - Manuscript review generation
  - Quality validation

- **`test_ollama_utils.py`** - Ollama client utilities
  - Model management and switching
  - Connection handling and error recovery

- **`test_prompts_composer.py`** - Prompt composition utilities
  - Multi-part prompt assembly
  - Template variable substitution

- **`test_prompts_loader.py`** - Prompt loading and management
  - Template file loading
  - Prompt caching and validation

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

**Purpose:** Test multi-format output generation

- **`test_core.py`** - Core rendering functionality
  - Render manager initialization and coordination

- **`test_latex_utils.py`** - LaTeX compilation utilities
  - LaTeX syntax validation and processing

- **`test_pdf_renderer_*.py`** - PDF generation validation
  - Individual and combined PDF rendering
  - LaTeX compilation and error handling

- **`test_poster_renderer.py`** - Scientific poster generation
  - Poster layout and content validation

- **`test_slides_renderer_*.py`** - Presentation slide generation
  - Beamer LaTeX and reveal.js HTML slides

- **`test_web_renderer_coverage.py`** - HTML/web output generation
  - Interactive web content creation

- **`test_cli.py`** - Rendering CLI interface
  - Multi-format rendering command-line tools

### Scientific Tools (`scientific/`)

**Purpose:** Test scientific computing utilities

- **`test_scientific_dev_edge_cases.py`** - Edge case handling
- **`test_scientific_dev.py`** - Scientific development tools
  - Numerical stability checking
  - Performance benchmarking
  - Best practices validation

### Validation System (`validation/`)

**Purpose:** Test quality assurance and validation tools

- **`test_check_links.py`** - Link validation
  - Internal and external link checking
  - Reference resolution validation

- **`test_check_links_comprehensive.py`** - Comprehensive link tests
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
- **`test_repo_scanner_comprehensive.py`** - Comprehensive repo scanning
- **`test_repo_scanner_coverage.py`** - Coverage repo scanning
- **`test_repo_scanner_full.py`** - Full repo scanning

- **`test_validate_markdown_cli.py`** - Markdown CLI
- **`test_validate_markdown_cli_comprehensive.py`** - Comprehensive CLI
- **`test_validate_markdown_cli_full.py`** - Full CLI tests
- **`test_validate_md_cli_coverage.py`** - Coverage CLI tests

- **`test_validate_pdf_cli.py`** - PDF CLI
- **`test_validate_pdf_cli_comprehensive.py`** - Comprehensive PDF CLI
- **`test_validate_pdf_cli_coverage.py`** - Coverage PDF CLI
- **`test_validate_pdf_cli_full.py`** - Full PDF CLI

- **`test_validation_cli.py`** - General validation CLI

## Testing Approach

### Real Data and Real Services

All infrastructure tests use **real implementations** without mocks:

- **Literature tests**: Real PDF downloads from arXiv/Semantic Scholar
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
pytest tests/infrastructure/ -m "not requires_credentials"

# Run only Zenodo tests
pytest tests/infrastructure/ -m requires_zenodo

# Skip LaTeX tests
pytest tests/infrastructure/ -m "not requires_latex"
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
   pytest tests/infrastructure/
   ```

See [docs/TESTING_WITH_CREDENTIALS.md](../../docs/TESTING_WITH_CREDENTIALS.md) for detailed setup.

### Test Cleanup

Tests automatically clean up test artifacts:

- **Zenodo**: Depositions deleted after test
- **GitHub**: Releases and tags deleted after test  
- **Files**: Temporary files cleaned by pytest fixtures
- **PDFs**: Downloaded files in temp directories

### For modules requiring external services:

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

- **Real file I/O** with temporary directories
- **Actual subprocess calls** for CLI validation
- **Real data structures** and processing
- **Integration testing** of actual workflows

### Error Condition Testing

Comprehensive error handling validation:

```python
def test_api_rate_limit_handling():
    """Test graceful handling of API rate limits."""
    # Simulate rate limit response
    # Verify retry logic and backoff
    # Check error messaging
```

## Coverage Status

Current coverage: **61.48%** (exceeds 60% requirement)

| Module | Coverage | Status |
|--------|----------|--------|
| `core/` | 100% | ✅ |
| `build/` | 100% | ✅ |
| `documentation/` | 100% | ✅ |
| `literature/` | 91% | ✅ |
| `llm/` | 91% | ✅ |
| `publishing/` | 100% | ✅ |
| `rendering/` | 91% | ✅ |
| `scientific/` | 100% | ✅ |
| `validation/` | 100% | ✅ |

## Running Infrastructure Tests

### All Infrastructure Tests

```bash
# From repository root
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html --cov-fail-under=60

# Skip network-dependent tests
pytest tests/infrastructure/ -m "not requires_ollama"
```

### Module-Specific Testing

```bash
# Core utilities
pytest tests/infrastructure/core/ -v

# Literature search
pytest tests/infrastructure/literature/ -v

# LLM integration (requires Ollama)
pytest tests/infrastructure/llm/ -m requires_ollama -v

# Validation system
pytest tests/infrastructure/validation/ -v
```

### Coverage Analysis

```bash
# Show missing lines
pytest tests/infrastructure/ --cov=infrastructure --cov-report=term-missing

# Generate HTML report
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html
open htmlcov/index.html
```

## Integration with Build Pipeline

### Automatic Execution

Infrastructure tests run as part of the complete test suite:

```bash
# Stage 1: Run all tests
python3 scripts/01_run_tests.py
```

This executes both infrastructure and project tests with coverage validation.

### Selective Testing

For development workflows:

```bash
# Test only changed modules
pytest tests/infrastructure/core/ tests/infrastructure/build/

# Test specific functionality
pytest tests/infrastructure/ -k "test_config" -v
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
        """Test complete workflow integration."""
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
PYTHONPATH=. pytest tests/infrastructure/test_core.py
```

**Network Test Failures:**
```bash
# Check service availability
curl http://localhost:11434/api/tags  # Ollama

# Skip network tests
pytest tests/infrastructure/ -m "not requires_ollama"
```

**Coverage Issues:**
```bash
# Show uncovered lines
pytest tests/infrastructure/ --cov=infrastructure --cov-report=term-missing

# Focus on specific module
pytest tests/infrastructure/core/ --cov=infrastructure.core --cov-report=html
```

### Performance Testing

```bash
# Time test execution
time pytest tests/infrastructure/ -x

# Profile slow tests
pytest tests/infrastructure/ --durations=10
```

## Module-Specific Testing Notes

### Literature Module

**Network-dependent tests** require internet access for arXiv/Semantic Scholar APIs.

**Pure logic tests** validate configuration, result processing, and citation generation without network calls.

**Integration tests** validate complete search-download-cite workflows.

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
- [`../../project/tests/AGENTS.md`](../../project/tests/AGENTS.md) - Project test documentation
- [`../../docs/TESTING_GUIDE.md`](../../docs/TESTING_GUIDE.md) - Testing best practices
- [`../../infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md) - Infrastructure module overview


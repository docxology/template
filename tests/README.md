# tests/ - Test Suite

test suite ensuring coverage requirements for both infrastructure and project modules (60% infrastructure minimum, 90% project minimum). Current status: **100% project**, **83.33% infrastructure**, **2116 tests passing** (1796 infra [2 skipped] + 320 project).

## Quick Start

### Run All Tests
```bash
# With coverage report (both infrastructure and project)
pytest tests/ --cov=infrastructure --cov=projects/code_project/src --cov-report=html

# Using uv
uv run pytest tests/ --cov=infrastructure --cov=projects/code_project/src --cov-report=html

# Verify coverage requirements
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=60
pytest projects/code_project/tests/ --cov=projects/code_project/src --cov-fail-under=90
```

### Run Specific Tests
```bash
# Infrastructure tests
pytest tests/infrastructure/core/test_config_loader.py -v

# Project tests
pytest projects/code_project/tests/ -v

# Integration tests
pytest tests/integration/test_module_interoperability.py -v

# By pattern
pytest tests/ -k "test_config" -v

# Skip Ollama-dependent tests
pytest tests/ -m "not requires_ollama"
# Stop on first failure
pytest tests/ -x

### Common Markers
- `requires_ollama`: marks tests that need a running Ollama service. Skip with `-m "not requires_ollama"`.
```

## Recent Test Fixes

### ✅ Infrastructure Test Fixes Completed

**Project Test Imports:**
- Fixed `test_reporting.py` and `test_validation.py` collection errors
- Updated project test conftest.py files to add repository root to Python path
- Resolved infrastructure module import issues in project tests

**Core Infrastructure Tests:**
- **Checkpoint Tests**: Fixed directory existence expectations and macOS permission testing
- **CLI Tests**: Updated subprocess assertions to match actual output format
- **Logging Tests**: Removed syntax error and eliminated Mock/patch imports
- **Validation Tests**: Fixed CLI test manuscript directory argument handling
- **Integration Tests**: Corrected type assertions for integrity verification functions

**LLM Tests (Partial):**
- Migrated `test_query_fallback_on_connection_error` to HTTP calls
- `ollama_test_server` fixture for model-specific responses
- Established pattern for no-mocks LLM testing

**Output & Bash Tests:**
- Fixed ANSI color code handling in bash logging tests
- Updated output copying test assertions for current implementation

### Test Execution Commands

```bash
# Full test suite with coverage
python3 scripts/01_run_tests.py --project project

# Infrastructure tests only
python3 scripts/01_run_tests.py --infrastructure-only

# Project tests only
python3 scripts/01_run_tests.py --project-only --project project

# Check for mock usage (should return no violations)
python3 scripts/verify_no_mocks.py

# Run with verbose output
pytest tests/ -v --tb=short

# Run failing tests only
pytest tests/ --lf
```

## Coverage Requirements (pipeline enforced)

- **Projects** (`projects/{name}/src/`): 90% minimum (code_project: 94.1%, prose_project: 91.5%)
- **Infrastructure** (`infrastructure/`): 60% minimum (currently 83.33% - exceeds stretch goal!)
- Tests must pass before PDF generation
- data only (no mocks)
- Coverage report: `htmlcov/index.html`

## Test Organization

```mermaid
graph TD
    subgraph TestStructure["Test Suite Structure"]
        ROOT[tests/<br/>Root configuration<br/>conftest.py]

        INFRA[tests/infrastructure/<br/>Module-specific tests<br/>Mirrors infrastructure/]

        INTEGRATION[tests/integration/<br/>Cross-module tests<br/>End-to-end workflows]

        PROJECT[projects/{name}/tests/<br/>Project-specific tests<br/>90%+ coverage required]
    end

    subgraph InfrastructureTests["Infrastructure Module Tests"]
        CORE[core/<br/>Config, logging, exceptions<br/>+ project discovery]
        BUILD[build/<br/>Build verification & quality]
        VALIDATION[validation/<br/>Quality assurance]
        RENDERING[rendering/<br/>PDF & HTML generation]
        LLM[llm/<br/>AI integration]
        PUBLISHING[publishing/<br/>Academic dissemination]
        REPORTING[reporting/<br/>Dashboard & reporting]
        DOCS[documentation/<br/>Figure management]
        SCIENTIFIC[scientific/<br/>Research utilities]
    end

    subgraph IntegrationTests["Integration Tests"]
        INTEROP[test_module_interoperability.py<br/>Cross-module integration]
        FIGURES[test_figure_equation_citation.py<br/>Figure/equation handling]
        OUTPUT[test_output_copying.py<br/>File operations]
        EDGES[test_edge_cases_and_error_paths.py<br/>Error conditions]
        SCRIPTS[test_run_sh.py<br/>Script orchestration]
        EXEC[test_executive_report_generation.py<br/>Executive reporting]
        LOGGING[test_logging.py<br/>Bash logging]
        BASH[test_bash_utils.sh<br/>Bash utilities]
    end

    ROOT --> INFRA
    ROOT --> INTEGRATION
    ROOT --> PROJECT

    INFRA --> CORE
    INFRA --> BUILD
    INFRA --> VALIDATION
    INFRA --> RENDERING
    INFRA --> LLM
    INFRA --> PUBLISHING
    INFRA --> REPORTING
    INFRA --> DOCS
    INFRA --> SCIENTIFIC

    INTEGRATION --> INTEROP
    INTEGRATION --> FIGURES
    INTEGRATION --> OUTPUT
    INTEGRATION --> EDGES
    INTEGRATION --> SCRIPTS
    INTEGRATION --> EXEC
    INTEGRATION --> LOGGING
    INTEGRATION --> BASH

    classDef root fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef integration fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef project fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class ROOT root
    class INFRA,CORE,BUILD,VALIDATION,RENDERING,LLM,PUBLISHING,REPORTING,DOCS,SCIENTIFIC infra
    class INTEGRATION,INTEROP,FIGURES,OUTPUT,EDGES,SCRIPTS,EXEC,LOGGING,BASH integration
    class PROJECT project
```

```
tests/
├── conftest.py                          # Root test configuration
│
│ # Note: Multiple test files with suffixes (_coverage, _full, _comprehensive)
│ # exist to achieve coverage across scenarios and edge cases
├── infrastructure/                      # Infrastructure module tests
│   ├── conftest.py                      # Infrastructure test configuration
│   ├── core/                            # Core utilities tests
│   │   ├── test_project_discovery.py    # Project discovery and validation
│   ├── documentation/                   # Documentation handling tests
│   ├── llm/                             # LLM integration tests
│   ├── publishing/                      # Publishing tools tests
│   ├── rendering/                       # Rendering pipeline tests
│   ├── reporting/                       # Reporting and dashboard tests
│   ├── scientific/                      # Scientific tools tests
│   └── validation/                      # Validation tests
└── integration/                         # Integration tests
    ├── conftest.py                      # Integration test configuration
    ├── test_executive_report_generation.py  # Executive report generation
    ├── test_bash_utils.sh               # Bash utility tests
    ├── test_edge_cases_and_error_paths.py # Edge cases and error handling
    ├── test_figure_equation_citation.py # Fig/Eq/Citation tests
    ├── test_logging.py                  # Bash logging integration
    ├── test_module_interoperability.py  # Cross-module integration
    ├── test_output_copying.py           # Output file handling
    └── test_run_sh.py                   # Script orchestration tests
```

## Test Categories

### Infrastructure Module Tests

**Core Module** (`infrastructure/core/`)
- `test_checkpoint.py` - Checkpoint/resume functionality
- `test_config_loader.py` - Configuration file handling
- `test_exceptions.py` - Custom exception handling
- `test_logging_utils.py` - Logging utilities
- `test_progress.py` - Progress tracking
- `test_retry.py` - Retry mechanisms
- `test_project_discovery.py` - Project discovery and validation

**Build Module** (`infrastructure/build/`)
- `test_build_verifier.py` - Build verification and integrity
- `test_quality_checker.py` - Document quality analysis
- `test_reproducibility.py` - Environment tracking

**Documentation Module** (`infrastructure/documentation/`)
- `test_figure_manager.py` - Figure management and registration
- `test_image_manager.py` - Image handling in markdown
- `test_glossary_gen.py` - API documentation generation
- `test_markdown_integration.py` - Markdown processing integration

**LLM Module** (`infrastructure/llm/`)
- `test_core.py` - LLM client core functionality
- `test_context.py` - Conversation context management
- `test_templates.py` - Template system for common tasks
- `test_config.py` - LLM configuration
- `test_validation.py` - Input validation
- `test_llm_review.py` - LLM manuscript review

**Publishing Module** (`infrastructure/publishing/`)
- `test_publishing.py` - Publishing metadata and citations
- `test_api.py` - Platform API clients (Zenodo, arXiv, GitHub)
- `test_cli.py` - CLI wrapper for publishing

**Rendering Module** (`infrastructure/rendering/`)
- `test_core.py` - Render manager core
- `test_latex_utils.py` - LaTeX compilation utilities
- `test_renderers.py` - PDF, HTML, and slides renderers
- `test_pdf_renderer_*.py` - PDF generation tests
- `test_poster_renderer.py` - Scientific poster rendering

**Reporting Module** (`infrastructure/reporting/`)
- `test_executive_reporter.py` - Executive report generation
- `test_dashboard_generator.py` - Dashboard creation
- `test_pipeline_reporter.py` - Pipeline reporting

**Scientific Module** (`infrastructure/scientific/`)
- `test_scientific_dev.py` - Scientific development utilities

**Validation Module** (`infrastructure/validation/`)
- `test_markdown_validator.py` - Markdown validation
- `test_pdf_validator.py` - PDF validation
- `test_integrity.py` - Integrity verification
- `test_check_links.py` - Link validation
- `test_doc_scanner.py` - Document scanning
- `test_config.py` - Rendering configuration
- `test_poster_renderer.py` - Scientific poster generation
- `test_cli.py` - CLI wrapper for rendering

**Scientific Module** (`infrastructure/scientific/`)
- `test_scientific_dev.py` - Scientific computing best practices

**Validation Module** (`infrastructure/validation/`)
- `test_markdown_validator.py` - Markdown validation
- `test_pdf_validator.py` - PDF validation
- `test_integrity.py` - Integrity verification
- `test_check_links.py` - Documentation link checking
- `test_doc_scanner.py` - documentation scanning
- `test_repo_scanner.py` - Repository accuracy/completeness
- `test_cli.py` - CLI wrapper for validation

### Integration Tests (`tests/integration/`)
- `test_module_interoperability.py` - Cross-module integration validation
- `test_figure_equation_citation.py` - Figure/equation/citation handling
- `test_output_copying.py` - Output file handling and copying
- `test_edge_cases_and_error_paths.py` - Edge cases and error handling
- `test_run_sh.py` - Script orchestration and CLI testing
- `test_executive_report_generation.py` - Executive report generation
- `test_logging.py` - Bash logging integration tests
- `test_bash_utils.sh` - Bash utility function validation

### Project Tests (`projects/{name}/tests/`)
- Unit tests for `projects/{name}/src/` modules (see `projects/{name}/tests/AGENTS.md`)
- Each project has independent test suite with 90%+ coverage requirement
- code_project: 28 tests, 94.1% coverage
- prose_project: 47 tests, 91.5% coverage
  - `test_generate_research_figures.py` - Research figure pipeline

## Debugging

```bash
# Verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Run last failed tests
pytest tests/ --lf
```

## Writing Tests

```python
"""Tests for infrastructure/module.py or project/src/module.py"""
import pytest
from infrastructure.module import function
# or
from project.src.module import function

def test_basic_usage():
    """Test basic functionality."""
    result = function("input")
    assert result == "expected"

def test_error_handling():
    """Test error conditions."""
    with pytest.raises(ValueError):
        function("invalid")
```

## Figure, Equation, and Citation Tests

The test suite includes validation for:

### Figure Handling
- Figure generation with proper paths
- Figure referencing in markdown
- LaTeX figure environments and captioning
- Multiple figures with unique labels

### Equation Handling
- Equation labeling and cross-referencing
- Multiple equations with unique labels
- Detection of unlabeled equations
- Equation reference resolution

### Citation Handling
- Citation formatting in markdown
- Bibliography file structure
- Multiple citations in sentences
- Citation extraction and validation

### Integrated Workflows
- manuscript sections with all elements
- Cross-section references
- Validation integration
- PDF generation integration

## Test Coverage Statistics

### Overall Coverage (latest)
- **code_project** (`projects/code_project/src/`): **100%** (Target: 90%+) ✅ Exceeds requirement!
- **Infrastructure** (`infrastructure/`): **83.33%** (Target: 60%+) ✅ Exceeds stretch goal!

### Coverage Details
Both test suites exceed their minimum requirements. For detailed coverage information, see the test coverage reports generated by pytest.

## See Also

- [`AGENTS.md`](AGENTS.md) - Detailed testing guide
- [`conftest.py`](conftest.py) - Test configuration
- [`../infrastructure/README.md`](../infrastructure/README.md) - Infrastructure modules being tested
- [`../projects/code_project/src/README.md`](../projects/code_project/src/README.md) - code_project modules
- [`../docs/WORKFLOW.md`](../docs/WORKFLOW.md) - Development workflow

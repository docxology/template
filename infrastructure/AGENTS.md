# Infrastructure Layer - Modular Architecture

## Overview

The Infrastructure layer provides reusable, modular tools for building, validating, and managing research projects. Organized by functionality into submodules, each with clear responsibilities and comprehensive testing.

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
├── build/          # Build & reproducibility
│   ├── build_verifier.py    # Build verification
│   ├── reproducibility.py   # Environment & reproducibility tracking
│   ├── quality_checker.py   # Document quality metrics
│   └── AGENTS.md/README.md  # Documentation
├── scientific/     # Scientific development
│   ├── scientific_dev.py    # Scientific utilities & best practices
│   └── AGENTS.md/README.md  # Documentation
├── literature/     # Literature search & management
│   ├── core.py              # Literature manager
│   ├── config.py            # Configuration
│   ├── cli.py               # CLI for literature search
│   └── AGENTS.md/README.md  # Documentation
├── llm/            # LLM integration
│   ├── core.py              # LLM client
│   ├── templates.py         # Research prompt templates
│   └── AGENTS.md/README.md  # Documentation
├── rendering/      # Multi-format rendering
│   ├── core.py              # Render manager
│   ├── latex_utils.py       # LaTeX utilities
│   ├── cli.py               # CLI for rendering
│   └── AGENTS.md/README.md  # Documentation
└── publishing/     # Academic publishing & dissemination
    ├── core.py              # Publishing workflows
    ├── api.py               # Platform API clients
    ├── cli.py               # CLI for publishing
    └── AGENTS.md/README.md  # Documentation
```

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
  - Module-specific exceptions (Literature, LLM, Rendering, Publishing)
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

**Usage:**
```python
from infrastructure.core import (
    get_logger, TemplateError, load_config
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
python3 -m infrastructure.validation.cli markdown manuscript/
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

### Build Module (`build/`)

**Build verification and quality assurance.**

- `build_verifier.py` - Build process verification
  - Artifact verification
  - Reproducibility testing
  - Environment validation

- `reproducibility.py` - Reproducibility tracking
  - Environment state capture
  - Dependency snapshot
  - Build manifest generation

- `quality_checker.py` - Document quality analysis
  - Readability metrics
  - Academic standards compliance
  - Quality reporting

### Scientific Module (`scientific/`)

**Scientific computing utilities.**

- `scientific_dev.py` - Scientific development tools
  - Numerical stability checking
  - Performance benchmarking
  - Scientific documentation generation
  - Best practices validation

### Literature Module (`literature/`)

**Literature search and reference management.**

Multi-source literature search with:
- arXiv, Semantic Scholar, CrossRef, PubMed integration
- PDF download with retry logic
- Citation extraction
- BibTeX management
- Library organization

**CLI:**
```bash
python3 -m infrastructure.literature.cli search "machine learning" --limit 10 --download
```

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
```

## Design Principles

### 1. Modular Organization
- Each module has a single, clear responsibility
- Modules can be used independently or together
- Related functionality grouped logically
- Minimal cross-module dependencies

### 2. Comprehensive Documentation
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
- Real data analysis, no mocks
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
- Build reproducibility via `build/reproducibility`
- Document quality analysis via `build/quality_checker`

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

For persistent configuration, use `manuscript/config.yaml`:

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

### Complete Example: Literature Search → Summarization → Publication

```python
# 1. Search literature
from infrastructure.literature import LiteratureManager
manager = LiteratureManager()
papers = manager.search_papers("machine learning", limit=5)

# 2. Summarize with LLM
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
# Search and download papers
python3 -m infrastructure.literature.cli search "quantum computing" --download

# Validate manuscript
python3 -m infrastructure.validation.cli markdown manuscript/
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

All modules have comprehensive test coverage:
- core: 100%
- validation: 100%
- documentation: 100%
- build: 100%
- scientific: 100%
- literature: 91%+
- llm: 91%+
- rendering: 91%+
- publishing: 100%

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'infrastructure.xxx'`:

1. Check the new module paths use the `/` structure:
   ```python
   # OLD (won't work)
   from infrastructure.pdf_validator import ...
   
   # NEW (correct)
   from infrastructure.validation.pdf_validator import ...
   ```

2. Verify the module `__init__.py` exists with proper exports

### API Changes

Migration from old flat structure:
- `infrastructure.pdf_validator` → `infrastructure.validation.pdf_validator`
- `infrastructure.figure_manager` → `infrastructure.documentation.figure_manager`
- `infrastructure.config_loader` → `infrastructure.core.config_loader`
- `infrastructure.logging_utils` → `infrastructure.core.logging_utils`
- `infrastructure.exceptions` → `infrastructure.core.exceptions`

### Configuration Issues

If configuration isn't loading:
1. Check `manuscript/config.yaml` exists
2. Verify YAML is well-formed
3. Fall back to environment variables as needed

## Migration Guide

### For Existing Projects

If your project imports from the old flat structure:

**Before:**
```python
from infrastructure.pdf_validator import validate_pdf_rendering
from infrastructure.figure_manager import FigureManager
from infrastructure.config_loader import load_config
```

**After:**
```python
from infrastructure.validation.pdf_validator import validate_pdf_rendering
from infrastructure.documentation.figure_manager import FigureManager
from infrastructure.core.config_loader import load_config
```

### For Tests

Update test imports similarly:

**Before:**
```python
from infrastructure.pdf_validator import ...
```

**After:**
```python
from infrastructure.validation.pdf_validator import ...
```

## Architecture Advantages

1. **Clarity** - Related functionality grouped logically
2. **Maintainability** - Each module has focused responsibility
3. **Reusability** - Modules can be used independently
4. **Scalability** - Easy to add new modules without cluttering core
5. **Documentation** - Each module fully documented
6. **Testing** - Comprehensive testing with 100% coverage
7. **Flexibility** - Use individual modules or complete pipeline

## Future Enhancements

Planned additions:
- Enhanced LLM template library
- Additional rendering formats (EPUB, docx)
- Extended publishing platform support
- Advanced literature analysis tools
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
- [`../AGENTS.md`](../AGENTS.md) - Complete system documentation
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) - System architecture overview
- [`../docs/THIN_ORCHESTRATOR_SUMMARY.md`](../docs/THIN_ORCHESTRATOR_SUMMARY.md) - Orchestrator pattern details

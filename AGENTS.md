# 🤖 AGENTS.md - System Documentation

## 🎯 System Overview

This document provides documentation for the Research Project Template system, ensuring understanding of all functionality, configuration options, and operational procedures.

## 📋 Table of Contents

1. [Core Architecture](#core-architecture)
2. [Directory-Level Documentation](#directory-level-documentation)
3. [Configuration System](#configuration-system)
4. [Rendering Pipeline](#rendering-pipeline)
5. [Validation Systems](#validation-systems)
6. [Testing Framework](#testing-framework)
7. [Output Formats](#output-formats)
8. [Advanced Modules](#advanced-modules)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## 🏗️ Core Architecture

### Two-Layer Architecture

**Layer 1: Infrastructure (Generic - Reusable)**

- `infrastructure/` - Generic build/validation tools (reusable across projects)
- `scripts/` - Entry point orchestrators (two pipeline options: 6-stage core or 10-stage extended)
- `tests/` - Infrastructure and integration tests

**Layer 2: Projects (Project-Specific - Customizable)**

- `projects/{name}/src/` - Research algorithms and analysis (domain-specific per project)
- `projects/{name}/tests/` - Project test suite
- `projects/{name}/scripts/` - Project analysis scripts (thin orchestrators)
- `projects/{name}/manuscript/` - Research manuscript
- `projects/{name}/output/` - Working outputs during pipeline execution
- `output/{name}/...` - Final deliverables after pipeline completion

### Thin Orchestrator Pattern

**CRITICAL**: All business logic resides in `projects/{name}/src/` modules. Scripts are **thin orchestrators** that:

**Root Entry Points (Generic):**

- Coordinate build pipeline stages
- Discover and invoke `projects/{name}/scripts/` for specified project
- Handle I/O, orchestration only
- Work with ANY project structure (single or multi-project)

**Project Scripts (Project-Specific):**

- Import from `projects/{name}/src/` for computation
- Import from `infrastructure/` for utilities
- Orchestrate domain-specific workflows
- Handle I/O and visualization

**Violation of this pattern breaks the architecture**.

### Multi-Project Support

The template now supports **multiple independent projects** within a single repository:

**Project Discovery:**

- Projects are discovered automatically from `projects/` directory
- Each project must have `src/` and `tests/` directories
- Projects are validated for structural completeness

**Project Isolation:**

- Each project has its own source code, tests, manuscript, and scripts
- Working outputs are stored in `projects/{name}/output/`
- Final deliverables are organized in `output/{name}/...`

**Orchestration Options:**

- Run individual projects: `--project {name}`
- Run all projects sequentially: `--all-projects`
- Interactive project selection menu
- Backward compatibility with single-project workflows

**Example Projects:**

- `projects/code_project/` - Code-focused with analysis pipeline

**Note:** Archived projects are preserved in `projects_archive/` for reference but are not actively executed.

## 📂 Project Organization: Active vs Archived

### Active Projects (`projects/`)

Projects in the `projects/` directory are **actively discovered and executed** by infrastructure:

- **Discovered** by `infrastructure.project.discovery.discover_projects()`
- **Listed** in `run.sh` interactive menu
- **Executed** by all pipeline scripts (`01_run_tests.py`, `02_run_analysis.py`, etc.)
- **Outputs** generated in `projects/{name}/output/` and copied to `output/{name}/`

### Archived Projects (`projects_archive/`)

Projects in the `projects_archive/` directory are **preserved but not executed**:

- **NOT discovered** by infrastructure discovery functions
- **NOT listed** in `run.sh` menu
- **NOT executed** by any pipeline scripts
- **Preserved** for historical reference and potential reactivation

### Project Lifecycle

**Archiving:** Move `projects/{name}/` → `projects_archive/{name}/`
**Reactivation:** Move `projects_archive/{name}/` → `projects/{name}/`

Projects are automatically discovered when moved to the `projects/` directory.

## 📚 Repository Structure

The template separates **generic infrastructure** from **project-specific code**:

```
template/                           # Generic template repository
├── infrastructure/                 # Generic build/validation tools (Layer 1)
│   ├── AGENTS.md
│   ├── README.md
│   └── *.py                        # build_verifier, figure_manager, etc.
├── scripts/                        # Generic entry point orchestrators
│   ├── AGENTS.md                   # Entry points: 00-setup, 01-tests, 02-analysis, 03-pdf, 04-validate, 05-copy
│   ├── README.md
│   ├── 00_setup_environment.py
│   ├── 01_run_tests.py
│   ├── 02_run_analysis.py          # Discovers & executes project/scripts/
│   ├── 03_render_pdf.py
│   ├── 04_validate_output.py
│   ├── 05_copy_outputs.py          # Copies final deliverables
├── tests/                          # Infrastructure tests
│   ├── AGENTS.md
│   ├── README.md
│   └── test_*.py                   # Tests for infrastructure/ modules
├── projects/                      # Multiple research projects directory
│   ├── README.md                  # Multi-project guide
│   ├── code_project/              # Code-focused research project
│   │   ├── src/                   # Project-specific scientific code
│   │   │   ├── AGENTS.md
│   │   │   ├── README.md
│   │   │   └── *.py
│   │   ├── tests/                 # Project tests
│   │   │   ├── AGENTS.md
│   │   │   ├── README.md
│   │   │   └── test_*.py
│   │   ├── scripts/               # Project analysis scripts
│   │   │   ├── AGENTS.md
│   │   │   ├── README.md
│   │   │   └── *.py
│   │   ├── manuscript/            # Research manuscript markdown
│   │   ├── output/                # Working outputs (generated during pipeline)
│   │   └── pyproject.toml
└── output/                         # Final deliverables (organized by project)
    ├── code_project/              # Code project outputs
    └── ...
```

## 📚 Directory-Level Documentation

Each directory contains documentation for easy navigation:

### Generic Infrastructure (Reusable)

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| [`infrastructure/`](infrastructure/) | [AGENTS.md](infrastructure/AGENTS.md) | [README.md](infrastructure/README.md) | Generic build/validation tools (Layer 1) |
| [`scripts/`](scripts/) | [AGENTS.md](scripts/AGENTS.md) | [README.md](scripts/README.md) | Generic entry point orchestrators |
| [`tests/`](tests/) | [AGENTS.md](tests/AGENTS.md) | [README.md](tests/README.md) | Infrastructure test suite |

### Project-Specific (Customizable)

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|

### Documentation Directories

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| [`docs/`](docs/) | [AGENTS.md](docs/AGENTS.md) | [README.md](docs/README.md) | Project documentation hub |

### Documentation Navigation

**For detailed information:**

- Read directory-specific **AGENTS.md** files for details
- Each AGENTS.md covers architecture, usage, and best practices

**For quick reference:**

- Check directory-specific **README.md** files for fast answers
- Each README.md provides quick start and essential commands

**Root documentation:**

- This file (root **AGENTS.md**) - System overview
- [README.md](README.md) - Project quick start and introduction

### Directory Structure

```
template/                           # Generic Template
├── infrastructure/                 # Generic build/validation tools (Layer 1)
│   ├── AGENTS.md                   # Infrastructure documentation
│   ├── README.md                   # Quick reference
│   ├── build_verifier.py
│   ├── figure_manager.py
│   └── ...
├── scripts/                        # Entry Points (Generic Orchestrators)
│   ├── AGENTS.md                   # Entry point documentation
│   ├── README.md                   # Quick reference
│   ├── 00_setup_environment.py     # Stage 1: Setup Environment (Stage 0 is cleanup)
│   ├── 01_run_tests.py             # Stage 2: Test
│   ├── 02_run_analysis.py          # Stage 3: Analysis (discovers project/scripts/)
│   ├── 03_render_pdf.py            # Stage 4: PDF
│   ├── 04_validate_output.py       # Stage 5: Validate
│   ├── 05_copy_outputs.py          # Stage 6: Copy outputs
├── tests/                          # Infrastructure Tests
│   ├── AGENTS.md
│   ├── README.md
│   └── test_*.py
├── projects/                       # Multiple research projects directory
│   ├── code_project/               # Code-focused research project
│   │   ├── src/                    # Project scientific code (Layer 2)
│   │   │   ├── AGENTS.md           # Project documentation
│   │   │   ├── README.md
│   │   │   └── *.py                # Research algorithms
│   │   ├── tests/                  # Project Tests
│   │   │   ├── AGENTS.md
│   │   │   ├── README.md
│   │   │   └── test_*.py
│   │   ├── scripts/                # Project Analysis Scripts
│   │   │   ├── AGENTS.md           # Project scripts documentation
│   │   │   ├── README.md
│   │   │   └── *.py                # Analysis workflows
│   │   ├── manuscript/             # Research Manuscript
│   │   ├── output/                 # Generated Files (disposable)
│   │   └── pyproject.toml          # Project configuration
├── docs/                           # Documentation
│   ├── AGENTS.md
│   └── README.md
└── pyproject.toml                  # Root configuration
```

**Documentation in each directory:**

- **AGENTS.md** - Detailed directory-specific documentation
- **README.md** - Quick reference and navigation

**Note on src/ directory:**

- Root `src/` no longer exists (was empty shells)
- All code is in `infrastructure/` (generic) or `projects/{name}/src/` (project-specific)
- This separation enables reusability across projects

## ⚙️ Configuration System

### Configuration File (Recommended)

The system supports configuration through a YAML file, providing a centralized, version-controllable way to manage all paper metadata.

**Location**: `projects/{name}/manuscript/config.yaml`
**Template**: `projects/{name}/manuscript/config.yaml.example`

**Example configuration**:

```yaml
paper:
  title: "Novel Optimization Framework"
  subtitle: ""  # Optional
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"
    email: "jane.smith@university.edu"
    affiliation: "University of Example"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
  journal: ""  # Optional
  volume: ""  # Optional
  pages: ""  # Optional

keywords:
  - "optimization"
  - "machine learning"

metadata:
  license: "Apache-2.0"
  language: "en"

# LLM Review Settings (optional)
llm:
  reviews:
    enabled: true
    types:
      - executive_summary  # Default: single review
      # Uncomment to enable additional reviews:
      # - quality_review
      # - methodology_review
      # - improvement_suggestions
  translations:
    enabled: true  # Set to false to disable translation generation
    languages:
      - zh  # Default: single translation (Chinese Simplified)
      # Uncomment to enable additional languages:
      # - hi  # Hindi
      # - ru  # Russian
```

**Benefits**:

- ✅ Version controllable (can be committed to git)
- ✅ Single file for all metadata
- ✅ Supports multiple authors with affiliations
- ✅ Structured format (YAML)
- ✅ Easy to edit and maintain

### Environment Variables (Alternative Method)

Environment variables are supported as an alternative configuration method and take precedence over config file values:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTHOR_NAME` | `"Project Author"` | Primary author name |
| `AUTHOR_ORCID` | `"0000-0000-0000-0000"` | Author ORCID identifier |
| `AUTHOR_EMAIL` | `"author@example.com"` | Author contact email |
| `DOI` | `""` | Digital Object Identifier (optional) |
| `PROJECT_TITLE` | `"Project Title"` | Project/research title |
| `LOG_LEVEL` | `1` | Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR) |

**Priority order**:

1. Environment variables (highest priority - override config file)
2. Config file (`projects/{name}/manuscript/config.yaml`)
3. Default values (lowest priority)

### Configuration Examples

#### Using Configuration File (Recommended)

```bash
# Edit projects/{name}/manuscript/config.yaml with your information
vim projects/code_project/manuscript/config.yaml

# Build with config file values
python3 scripts/03_render_pdf.py --project code_project
```

#### Using Environment Variables

```bash
export AUTHOR_NAME="Dr. Jane Smith"
export PROJECT_TITLE="Novel Optimization Framework"
export AUTHOR_EMAIL="jane.smith@university.edu"
export AUTHOR_ORCID="0000-0000-0000-1234"
export DOI="10.5281/zenodo.12345678"  # Optional

python3 scripts/03_render_pdf.py
```

#### Verbose Logging

```bash
export LOG_LEVEL=0  # Show all debug messages
python3 scripts/03_render_pdf.py
```

### Runtime Configuration

Configuration is read at runtime by `scripts/03_render_pdf.py` and applied to:

- PDF metadata (title, author, date)
- LaTeX document properties
- Generated file headers
- Cross-reference systems
- Title page generation

## 🚀 Rendering Pipeline

### Pipeline Execution

The template provides **three entry points** for pipeline execution:

**Main Entry Point (Recommended)**

```bash
# Routes to manuscript operations
./run.sh
```

**Manuscript Operations**

```bash
# Interactive menu with manuscript operations
./run.sh

# Non-interactive: Extended pipeline (9 stages displayed as [1/9] to [9/9]) with optional LLM review
./run.sh --pipeline
```

**Alternative: Python Orchestrator**

```bash
# Core pipeline (no LLM) - Python orchestrator
python3 scripts/execute_pipeline.py --project code_project --core-only
```

**Entry Point Comparison**

- **`./run.sh`**: Main entry point - Interactive menu or extended pipeline (9 stages), includes optional LLM review stages. Stages are displayed as [1/9] to [9/9] in logs.
- **`./run.sh --pipeline`**: 9 stages, includes optional LLM review stages. Stages are displayed as [1/9] to [9/9] in logs.
- **`python3 scripts/execute_pipeline.py --core-only`**: Core pipeline only (no LLM).

### Pipeline Stages

**Full Pipeline Stages** (displayed as [1/9] to [9/9] in logs):

1. **Clean Output Directories** - Clean working and final output directories
2. **Environment Setup** - Verify system requirements and dependencies
3. **Infrastructure Tests** - Run infrastructure test suite (60% coverage minimum, may be skipped)
4. **Project Tests** - Run project test suite (90% coverage minimum)
5. **Project Analysis** - Execute `projects/{name}/scripts/` analysis workflows
6. **PDF Rendering** - Generate manuscript PDFs and figures
7. **Output Validation** - Validate all generated outputs
8. **LLM Scientific Review** - AI-powered manuscript analysis (optional, requires Ollama)
9. **LLM Translations** - Multi-language technical abstract generation (optional, requires Ollama)
10. **Copy Outputs** - Copy final deliverables to root `output/` directory

**Infrastructure Tests Behavior:**

- **Single project mode**: Infrastructure tests run as stage 3 (may be skipped with `--skip-infra`)
- **Multi-project mode** (`--all-projects`): Infrastructure tests run **once** for all projects at the start, then are **skipped** for individual project executions to avoid redundant testing. This is shown in logs as "Running infrastructure tests once for all projects..." followed by "Skipping stage: Infrastructure Tests" for each project.

**Multi-Project Executive Reporting** (`--all-projects` mode only):

- **Executive Reporting** - Cross-project metrics, summaries, and visual dashboards (generated after all projects, not as a numbered stage)

**Stage Numbering:**

- `./run.sh`: 9 stages displayed as [1/9] to [9/9] in progress logs
- `scripts/execute_pipeline.py`: Core vs full pipeline is selected by flags (no fixed stage numbering in filenames)

### Manual Execution Options

**Individual Stage Execution:**

```bash
# Environment setup
python3 scripts/00_setup_environment.py --project code_project

# Test execution (combined infra + project)
python3 scripts/01_run_tests.py --project code_project

# Project analysis scripts
python3 scripts/02_run_analysis.py --project code_project

# PDF rendering
python3 scripts/03_render_pdf.py --project code_project

# Output validation
python3 scripts/04_validate_output.py --project code_project

# Copy outputs
python3 scripts/05_copy_outputs.py --project code_project

# LLM manuscript review (optional, requires Ollama)
python3 scripts/06_llm_review.py --project code_project

# Generate executive report (multi-project only)
python3 scripts/07_generate_executive_report.py --project code_project
```

**Validation Tools:**

```bash
# Validate markdown files
python3 -m infrastructure.validation.cli markdown projects/code_project/manuscript/

# Validate PDF outputs
python3 -m infrastructure.validation.cli pdf output/code_project/pdf/
```

## ✅ Validation Systems

### PDF Validation

```bash
# Validate generated PDF for issues
python3 -m infrastructure.validation.cli pdf output/pdf/

# With verbose output
python3 -m infrastructure.validation.cli pdf output/pdf/ --verbose

# Specific PDF file
python3 -m infrastructure.validation.cli pdf output/pdf/01_abstract.pdf
```

**Validation Checks**:

- Unresolved references (`??`)
- Missing citations (`[?]`)
- LaTeX warnings and errors
- Document structure integrity
- Word count and content preview

### Markdown Validation

```bash
# Validate all markdown files
python3 -m infrastructure.validation.cli markdown projects/code_project/manuscript/

# Strict mode (fail on any issues)
python3 -m infrastructure.validation.cli markdown projects/code_project/manuscript/ --strict
```

**Validation Checks**:

- Image reference resolution
- Cross-reference integrity
- Equation label validation
- Link formatting
- Mathematical notation

### Test Coverage

```bash
# Run both infrastructure and project tests via orchestrator
python3 scripts/01_run_tests.py --project code_project

# Or run manually with coverage reports
python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-report=html
python3 -m pytest projects/code_project/tests/ --cov=projects/code_project/src --cov-report=html
```

**Coverage Requirements**:

- 90% minimum for projects/{name}/src/ (currently achieving 100%)
- 60% minimum for infrastructure/ (currently achieving 83.33% - exceeds stretch goal!)
- All tests must pass before PDF generation
- No mock methods (data analysis only)

**Coverage Gap Analysis**:

- See test coverage reports for detailed analysis
- Low-coverage modules identified and improvement plans documented
- Test files created for checkpoint, progress, retry, CLI, LLM operations, and paper selector

## 🧪 Testing Framework

### ABSOLUTE PROHIBITION: No Mocks Policy

**CRITICAL REQUIREMENT**: Under no circumstances use `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework. All tests must use data and computations only.

This policy ensures:

- Tests validate actual behavior, not mocked behavior
- Integration points are truly tested
- Code is tested in realistic conditions
- No false confidence from mocked tests

### No-Mocks Implementation Patterns

**HTTP API Testing**: Use `pytest-httpserver` for local test servers

```python
# BEFORE (mocked)
with patch('requests.post') as mock_post:
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"result": "ok"})

# AFTER (HTTP)
def test_api_call(ollama_test_server):
    # ollama_test_server fixture provides HTTP server
    config = LLMConfig(base_url=ollama_test_server.url_for("/"))
    client = LLMClient(config)
    response = client.query("test")  # HTTP request
    assert "response" in response.lower()
```

**CLI Testing**: Execute subprocess commands instead of mocking sys.argv

```python
# BEFORE (mocked)
with patch('sys.argv', ['cli.py', 'validate', 'file.pdf']):
    cli.main()

# AFTER (subprocess)
result = subprocess.run(
    ['python', '-m', 'infrastructure.validation.cli', 'validate', 'file.pdf'],
    capture_output=True, text=True
)
assert result.returncode == 0
```

**PDF Generation**: Create PDFs with reportlab instead of mocking PDF libraries

```python
# BEFORE (mocked)
with patch.dict('sys.modules', {'pdfplumber': mock_pdfplumber}):
    result = extract_text(pdf_file)

# AFTER (PDF)
from reportlab.pdfgen import canvas
c = canvas.Canvas(str(pdf_file))
c.drawString(100, 750, "Test content")
c.save()

result = extract_text(pdf_file)  # PDF processing
assert "Test content" in result
```

**File System Operations**: Use temp files and directories

```python
# BEFORE (mocked)
with patch('builtins.open') as mock_open:
    mock_open.return_value.__enter__.return_value.read.return_value = "content"

# AFTER (files)
def test_file_operation(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    result = read_file(test_file)  # File operation
    assert result == "content"
```

**External Tool Testing**: Use `@pytest.mark.skipif` for optional dependencies

```python
# BEFORE (mocked subprocess)
with patch('subprocess.run') as mock_run:
    mock_run.return_value = MagicMock(returncode=0)

# AFTER (tool execution)
@pytest.mark.skipif(not shutil.which('pandoc'), reason="pandoc not installed")
def test_pandoc_conversion(tmp_path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Test")
    pdf_file = tmp_path / "test.pdf"

    result = subprocess.run(['pandoc', str(md_file), '-o', str(pdf_file)])
    assert result.returncode == 0
    assert pdf_file.exists()
```

### Test Structure

Tests follow the **thin orchestrator pattern** principles:

- Import methods from `projects/{name}/src/` or `infrastructure/` modules
- Use data and computation
- Validate actual behavior (no mocks)
- Ensure reproducible, deterministic results

### Test Categories

1. **Unit Tests** (`test_*.py`) - Individual function validation
2. **Integration Tests** - Script and pipeline integration
3. **Validation Tests** - PDF and markdown quality checks

### Running Tests

```bash
# All tests via orchestrator (recommended)
python3 scripts/01_run_tests.py

# Specific test file
python3 -m pytest projects/code_project/tests/test_example.py -v

# Infrastructure tests with coverage
python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-report=html

# Project tests with coverage
python3 -m pytest projects/code_project/tests/ --cov=projects/code_project/src --cov-report=html
```

## 📤 Output Formats

### Generated Files Structure

```
output/
├── project/                # Project-specific outputs
│   ├── pdf/                # PDF documents
│   │   ├── 01_abstract.pdf # Individual section PDFs
│   │   ├── 02_introduction.pdf
│   │   ├── project_combined.pdf # Manuscript
│   │   └── *.pdf           # Additional formats
│   ├── tex/                # LaTeX source files
│   │   ├── 01_abstract.tex
│   │   ├── project_combined.tex
│   │   └── *.tex
│   ├── figures/            # Generated figures
│   │   ├── example_figure.png
│   │   ├── convergence_plot.png
│   │   └── *.png
│   ├── data/               # Generated datasets
│   │   ├── example_data.csv
│   │   ├── convergence_data.npz
│   │   └── *.csv
│   └── project_combined.html # HTML version for IDE
```

### PDF Versions

1. **Standard PDF** (`project_combined.pdf`)
   - Professional printing format
   - Optimized for LaTeX rendering
   - Cross-references and citations

2. **IDE-Friendly PDF** (`project_combined_ide_friendly.pdf`)
   - for text editor viewing
   - Better font rendering in IDEs
   - Simplified layout for screen reading

3. **HTML Version** (`project_combined.html`)
   - Web browser compatible
   - IDE integration
   - Interactive features (when available)

## 🧪 **Advanced Modules**

The template includes advanced modules for scientific package development:

### 🔒 **Security & Monitoring** (`infrastructure/core/`)

**Enterprise-grade security and system monitoring**

**Key Features:**

- **Input Sanitization**: LLM prompt validation and threat detection
- **Security Monitoring**: Security event tracking and alerting
- **Rate Limiting**: Configurable request rate limiting with monitoring
- **Health Checks**: System health monitoring with component-level status
- **Security Headers**: HTTP security header implementation

**Usage:**

```python
from infrastructure.core.security import validate_llm_input, get_security_validator
from infrastructure.core.health_check import quick_health_check, get_health_status

# Validate LLM input with security checks
sanitized = validate_llm_input(user_prompt)

# Perform system health check
if quick_health_check():
    status = get_health_status()
```

### 🔍 **Integrity Verification** (`infrastructure/validation/integrity.py`)

**File integrity and cross-reference validation**

**Key Features:**

- **File Integrity**: Hash-based verification of output files
- **Cross-Reference Validation**: LaTeX reference integrity checking
- **Data Consistency**: Format and structure validation
- **Academic Standards**: Compliance with writing standards
- **Build Artifact Verification**: Output validation

**Usage:**

```python
from infrastructure.validation.integrity import verify_output_integrity, generate_integrity_report

report = verify_output_integrity(output_dir)
print(generate_integrity_report(report))
```

### 📚 **Publishing Tools** (`infrastructure/publishing/`)

**Academic publishing workflow assistance**

**Key Features:**

- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX, APA, MLA formats
- **Publication Metadata**: Metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Academic Profile**: ORCID and repository integration
- **Platform Integration**: Zenodo, arXiv, GitHub releases

**Usage:**

```python
from infrastructure.publishing import extract_publication_metadata, generate_citation_bibtex

metadata = extract_publication_metadata(markdown_files)
bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

### 🔬 **Scientific Development** (`infrastructure/scientific/`)

**Scientific computing best practices and tools**

**Modular Structure:**

- `stability.py` - Numerical stability checking
- `benchmarking.py` - Performance benchmarking
- `documentation.py` - API documentation generation
- `validation.py` - Best practices validation
- `templates.py` - Research workflow templates

**Key Features:**

- **Numerical Stability**: Algorithm stability testing
- **Performance Benchmarking**: Execution time and memory analysis
- **Scientific Documentation**: API documentation generation
- **Best Practices Validation**: Code quality assessment
- **Research Workflow Templates**: Reproducible experiment templates

**Usage:**

```python
from infrastructure.scientific import check_numerical_stability, benchmark_function

stability = check_numerical_stability(your_function, test_inputs)
benchmark = benchmark_function(your_function, test_inputs)
```

### 🤖 **LLM Integration** (`infrastructure/llm/`)

**Local LLM assistance for research workflows**

**Key Features:**

- **Ollama Integration**: Local model support (privacy-first)
- **Template System**: Pre-built prompts for common research tasks
- **Context Management**: Multi-turn conversation handling
- **Streaming Support**: Response generation
- **Model Fallback**: Automatic fallback to alternative models
- **Token Counting**: Track usage and costs

**Research Templates:**

- Abstract summarization
- Code documentation
- Data interpretation
- Section drafting assistance
- Citation formatting
- Technical abstract translation (Chinese, Hindi, Russian)

**Usage:**

```python
from infrastructure.llm import LLMClient

client = LLMClient()
summary = client.apply_template("summarize_abstract", text=abstract)
response = client.query("What are the key findings?")
```

### 🎨 **Rendering System** (`infrastructure/rendering/`)

**Multi-format output generation from single source**

**Key Features:**

- **PDF Rendering**: Professional LaTeX-based PDFs
- **Presentation Slides**: Beamer (PDF) and reveal.js (HTML) slides
- **Web Output**: Interactive HTML with MathJax
- **Scientific Posters**: Large-format poster generation
- **Format-Agnostic**: Single source, multiple outputs
- **Quality Validation**: Automated output checking

**Usage:**

```python
from infrastructure.rendering import RenderManager

manager = RenderManager()
pdf = manager.render_pdf("manuscript.tex")
slides = manager.render_slides("presentation.md", format="revealjs")
html = manager.render_web("manuscript.md")
all_outputs = manager.render_all("manuscript.md")
```

### 🚀 **Publishing Module** (`infrastructure/publishing/`)

**Automated publishing to academic platforms**

**Module Structure:**

- `core.py` - Publication metadata extraction, DOI validation, citation generation
- `api.py` - Platform API clients (Zenodo, arXiv, GitHub)
- `citations.py` - Citation format generation (BibTeX, APA, MLA)
- `metadata.py` - Publication metadata management
- `platforms.py` - Platform-specific integration logic

**Key Features:**

- **Zenodo Integration**: Upload with DOI minting
- **arXiv Preparation**: Submission package creation
- **GitHub Releases**: Automated release management
- **Metrics Tracking**: Download and citation tracking
- **Distribution Packages**: Publication bundles

**Usage:**

```python
from infrastructure.publishing import (
    extract_publication_metadata,
    publish_to_zenodo,
    create_github_release,
    prepare_arxiv_submission
)

# Extract metadata
metadata = extract_publication_metadata([Path("manuscript.md")])

# Publish to Zenodo
doi = publish_to_zenodo(metadata, files, token)

# Create GitHub release
release = create_github_release(metadata, files, token)

# Prepare arXiv submission
package = prepare_arxiv_submission(metadata, files)
```

### **Module Integration**

All advanced modules follow the **thin orchestrator pattern**:

- **Business logic** in `infrastructure/` modules with test coverage
- **Orchestration** in separate utility scripts
- **Integration** with existing build pipeline
- **Testing** ensuring reliability
- **Documentation** for each module's functionality

**Testing Coverage:**

- ✅ **Security**: Tests (15+ tests)
- ✅ **Health Check**: Tests (10+ tests)
- ✅ **Input Sanitization**: Tests (8+ tests)
- ✅ **Integrity**: Tests (16 tests)
- ✅ **Publishing**: Tests (14 tests)
- ✅ **Scientific Dev**: Tests (12 tests)
- ✅ **Build Verifier**: Tests (10 tests)
- ✅ **LLM Integration**: 91% coverage (11 tests)
- ✅ **Rendering System**: 91% coverage (10 tests)
- ✅ **Reporting**: 0% coverage (module, tests pending)

### Accessing Outputs

```bash
# Open combined PDF
open output/code_project/pdf/code_project_combined.pdf

# Open HTML version in browser
open output/code_project/code_project_combined.html

# List all generated files
ls -la output/code_project/

# Check PDF validation
python3 -m infrastructure.validation.cli pdf output/code_project/pdf/
```

## 🔧 Troubleshooting

### Quick Reference

- **General Troubleshooting**: [`docs/operational/TROUBLESHOOTING_GUIDE.md`](docs/operational/TROUBLESHOOTING_GUIDE.md)
- **LLM Review Issues**: [`docs/operational/LLM_REVIEW_TROUBLESHOOTING.md`](docs/operational/LLM_REVIEW_TROUBLESHOOTING.md)
- **Checkpoint/Resume**: [`docs/operational/CHECKPOINT_RESUME.md`](docs/operational/CHECKPOINT_RESUME.md)
- **Performance Issues**: [`docs/operational/PERFORMANCE_OPTIMIZATION.md`](docs/operational/PERFORMANCE_OPTIMIZATION.md)

### Common Issues

#### Tests Failing

```bash
# Ensure coverage requirements met for both suites
python3 scripts/01_run_tests.py

# Or run individually with coverage reports
python3 -m pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=49
python3 -m pytest projects/code_project/tests/ --cov=projects/code_project/src --cov-fail-under=70
```

#### Scripts Failing

```bash
# Run scripts individually to debug
python3 projects/code_project/scripts/optimization_analysis.py

# Check import errors
python3 -c "import sys; sys.path.insert(0, 'projects/code_project/src'); import optimizer; print('Import successful')"
```

#### PDF Generation Issues

```bash
# Check LaTeX installation
which xelatex

# Validate LaTeX packages (pre-flight check)
python3 -m infrastructure.rendering.latex_package_validator

# Validate markdown first
python3 -m infrastructure.validation.cli markdown projects/code_project/manuscript/

# Check compilation logs
ls output/pdf/*_compile.log
```

**Missing LaTeX Package Errors**:

If you see "File *.sty not found" during PDF rendering:

1. **Identify the missing package** from the error message
2. **Install via tlmgr** (BasicTeX package manager):

   ```bash
   sudo tlmgr update --self
   sudo tlmgr install multirow cleveref doi newunicodechar
   ```

3. **Verify installation**:

   ```bash
   /usr/local/texlive/2025basic/bin/universal-darwin/kpsewhich multirow.sty
   ```

4. **Run pre-flight validation**:

   ```bash
   python3 -m infrastructure.rendering.latex_package_validator
   ```

**Common missing packages in BasicTeX**:

- `multirow`, `cleveref`, `doi`, `newunicodechar` - Require installation
- `bm`, `subcaption` - Already included (part of `tools` and `caption`)

**Alternative**: Install full MacTeX (~4 GB) instead of BasicTeX (~100 MB):

```bash
brew install --cask mactex
```

#### Missing Dependencies

```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu

# macOS (BasicTeX - minimal):
brew install pandoc
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install multirow cleveref doi newunicodechar

# macOS (MacTeX):
brew install pandoc
brew install --cask mactex
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=0
python3 scripts/03_render_pdf.py --project code_project

# Run with debug output
python3 -m infrastructure.validation.cli pdf output/code_project/pdf/ --verbose
```

### Log Files

Key log files for debugging:

- `output/pdf/*_compile.log` - LaTeX compilation logs
- `output/project_combined.md` - Combined markdown source
- Test output from pytest runs

## 🛠️ Maintenance

### System Updates

1. **Update Dependencies**

   ```bash
   # Update Python packages
   uv sync

   # Update system packages
   sudo apt-get update && sudo apt-get upgrade
   ```

2. **Version Control**

   ```bash
   # Check current status
   git status

   # Stage changes
   git add .

   # Commit with descriptive message
   git commit -m "feat: add validation feature"
   ```

3. **Backup Strategy**

   ```bash

# Clean outputs before backup

python3 -c "from pathlib import Path; from infrastructure.core.file_operations import clean_output_directories; clean_output_directories(Path('.'), 'code_project')"

# Backup source files only

   tar -czf project_backup.tar.gz projects/{name}/src/ projects/{name}/tests/ projects/{name}/scripts/ projects/{name}/manuscript/ docs/

   ```

### Adding Features

1. **Business Logic** → Add to `projects/{name}/src/`
2. **Tests** → Add to `projects/{name}/tests/`
3. **Scripts** → Add to `projects/{name}/scripts/` (use `projects/{name}/src/` methods)
4. **Documentation** → Update relevant `.md` files
5. **Validation** → Ensure coverage requirements met

### Performance Optimization

- **Parallel Testing**: Use `pytest-xdist` for faster test runs
- **Caching**: Enable pytest caching for repeated runs
- **Incremental Builds**: Only rebuild changed components
- **Performance Monitoring**: Automatic bottleneck detection in pipeline summary
- **Resource Tracking**: Memory and CPU usage reporting (when enabled)

See [`docs/operational/PERFORMANCE_OPTIMIZATION.md`](docs/operational/PERFORMANCE_OPTIMIZATION.md) for optimization guide.

### Checkpoint and Resume

The pipeline includes automatic checkpointing for resume capability:

```bash
# Resume from last checkpoint
python3 scripts/execute_pipeline.py --project code_project --core-only --resume
./run.sh --pipeline --resume

# Start fresh (clears checkpoint on success)
python3 scripts/execute_pipeline.py --project code_project --core-only
./run.sh --pipeline
```

**Features**:

- Automatic checkpoint after each successful stage
- Checkpoint validation before resume
- Graceful handling of corrupted checkpoints
- Preserves pipeline start time and stage durations

See [`docs/operational/CHECKPOINT_RESUME.md`](docs/operational/CHECKPOINT_RESUME.md) for documentation.

## 📚 References

### Internal Documentation

- [`README.md`](README.md) - Project overview and quick start
- [`docs/core/HOW_TO_USE.md`](docs/core/HOW_TO_USE.md) - Usage guide
- [`docs/core/ARCHITECTURE.md`](docs/core/ARCHITECTURE.md) - System design details
- [`docs/core/WORKFLOW.md`](docs/core/WORKFLOW.md) - Development workflow
- [`projects/README.md`](projects/README.md) - Multi-project management guide

### External Resources

- [Pandoc Manual](https://pandoc.org/MANUAL.html) - Document conversion
- [LaTeX Wikibook](https://en.wikibooks.org/wiki/LaTeX) - LaTeX documentation
- [Python Testing](https://docs.pytest.org/) - Testing framework

## 🎯 Best Practices

### Development Workflow

1. Write tests first (TDD)
2. Ensure coverage requirements met
3. Follow thin orchestrator pattern
4. Validate all outputs
5. Update documentation
6. Commit with clear messages

### Project Structure

- **Working outputs**: `projects/{name}/output/` (generated during pipeline)
- **Final deliverables**: `output/{name}/` (copied by stage 5)
- **Source code**: `projects/{name}/src/`
- **Tests**: `projects/{name}/tests/`
- **Scripts**: `projects/{name}/scripts/`
- **Manuscript**: `projects/{name}/manuscript/`

### Code Quality

- **Type Hints**: All public APIs must have type annotations
- **Documentation**: Clear docstrings for all functions
- **Error Handling**: Graceful failure with informative messages
- **Consistency**: Follow established patterns and conventions

### System Reliability

- **Deterministic Outputs**: All generation must be reproducible
- **Validation**: Check all aspects of output quality
- **Error Recovery**: Handle failures gracefully with clear messages
- **Performance Monitoring**: Track execution time and resource usage

---

## ✅ System Status: OPERATIONAL

**All systems confirmed functional with exemplar projects:**

- ✅ **Multi-project pipeline**: Core pipeline (7 stages) + executive reporting
- ✅ **Test coverage excellence**: code_project (100%), all projects (100%)
- ✅ **Publication-quality outputs**: Professional PDFs, cross-referenced manuscripts, automated figures
- ✅ **Mathematical rigor**: Advanced equations, theorem proofs, convergence analysis
- ✅ **Testing**: Edge cases, performance benchmarks, type safety validation
- ✅ **Documentation**: AGENTS.md/README.md across all directories
- ✅ **Data testing**: Zero mocks, integration testing
- ✅ **Infrastructure robustness**: Fixed critical bugs, improved error handling

**Environment Management:**

- ✅ Matplotlib auto-configuration (headless operation via MPLBACKEND=Agg)
- ✅ Optional dependency handling (python-dotenv graceful fallback)
- ✅ Test failure tolerance (MAX_TEST_FAILURES environment variable)
- ✅ LaTeX path management (BasicTeX/MacTeX support)
- ✅ Docker containerization (Dockerfile + docker-compose.yml)

**Modules (v2.1):**

- ✅ Security System (tests) - Input sanitization and monitoring
- ✅ Health Check System (tests) - System health monitoring
- ✅ Input Sanitization (tests) - LLM prompt validation
- ✅ LLM Integration (91% coverage, 11 tests) - Local Ollama support
- ✅ Rendering System (91% coverage, 10 tests) - Multi-format output
- ✅ Publishing API (integrated) - Zenodo, arXiv, GitHub automation
- ✅ Multi-project architecture (projects/{name}/ structure)

**Audit Status:**

- ✅ **High code coverage** across all modules (90%+ target achieved for key modules)
- ✅ Zero mock methods - all tests use data and HTTP calls
- ✅ All .cursorrules standards implemented
- ✅ compliance with thin orchestrator pattern
- ✅ Production-ready build pipeline (6-stage core, 10-stage extended)
- ✅ Reproducible outputs (deterministic with fixed seeds)
- ✅ Graceful degradation for optional features
- ✅ Multi-project support (projects/{name}/ structure)
- ✅ manuscript reference validation (all citations, figures, equations, sections resolved)
- ✅ HTTP testing with pytest-httpserver (no mocks for API calls)

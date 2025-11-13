# 🤖 AGENTS.md - Complete System Documentation

## 🎯 System Overview

This document provides **comprehensive documentation** for the Research Project Template system, ensuring complete understanding of all functionality, configuration options, and operational procedures.

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

### Thin Orchestrator Pattern

**CRITICAL**: All business logic resides in `src/` modules. Scripts are **thin orchestrators** that:
- Import and use `src/` methods for computation
- Handle I/O, visualization, and orchestration only
- Demonstrate proper integration patterns
- Are fully testable through `src/` method mocking

**Violation of this pattern breaks the architecture**.

## 📚 Directory-Level Documentation

Each directory contains comprehensive documentation for easy navigation:

### Source Code Directories

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| [`src/`](src/) | [AGENTS.md](src/AGENTS.md) | [README.md](src/README.md) | Core business logic with 100% test coverage |
| [`tests/`](tests/) | [AGENTS.md](tests/AGENTS.md) | [README.md](tests/README.md) | Test suite ensuring code quality |
| [`scripts/`](scripts/) | [AGENTS.md](scripts/AGENTS.md) | [README.md](scripts/README.md) | Thin orchestrators using src/ methods |

### Content Directories

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| [`manuscript/`](manuscript/) | [AGENTS.md](manuscript/AGENTS.md) | [README.md](manuscript/README.md) | Research manuscript sections |
| [`docs/`](docs/) | [AGENTS.md](docs/AGENTS.md) | [README.md](docs/README.md) | Project documentation hub |

### Utility Directories

| Directory | AGENTS.md | README.md | Purpose |
|-----------|-----------|-----------|---------|
| [`repo_utilities/`](repo_utilities/) | [AGENTS.md](repo_utilities/AGENTS.md) | [README.md](repo_utilities/README.md) | Build orchestration and utilities |

### Documentation Navigation

**For detailed information:**
- Read directory-specific **AGENTS.md** files for comprehensive details
- Each AGENTS.md covers architecture, usage, and best practices

**For quick reference:**
- Check directory-specific **README.md** files for fast answers
- Each README.md provides quick start and essential commands

**Root documentation:**
- This file (root **AGENTS.md**) - Complete system overview
- [README.md](README.md) - Project quick start and introduction

### Directory Structure

```
template/
├── src/                 # Core business logic (100% tested)
│   ├── AGENTS.md        # → Detailed src/ documentation
│   └── README.md        # → Quick src/ reference
├── tests/              # Test suite (100% coverage required)
│   ├── AGENTS.md        # → Testing philosophy and guide
│   └── README.md        # → Quick testing reference
├── scripts/            # Thin orchestrators (use src/ methods)
│   ├── AGENTS.md        # → Script architecture and patterns
│   └── README.md        # → Quick script reference
├── manuscript/         # Research sections (generate PDFs)
│   ├── AGENTS.md        # → Manuscript structure guide
│   └── README.md        # → Quick manuscript reference
├── docs/               # Documentation
│   ├── AGENTS.md        # → Documentation organization
│   └── README.md        # → Quick documentation index
├── output/             # Generated files (all disposable)
├── repo_utilities/     # Build tools and utilities
│   ├── AGENTS.md        # → Build utilities documentation
│   └── README.md        # → Quick utilities reference
└── pyproject.toml      # Dependencies and configuration
```

**Each directory now has comprehensive documentation:**
- **AGENTS.md** - Detailed directory-specific documentation
- **README.md** - Quick reference and navigation

## ⚙️ Configuration System

### Configuration File (Recommended)

The system supports configuration through a YAML file in `manuscript/config.yaml`, providing a centralized, version-controllable way to manage all paper metadata.

**Location**: `manuscript/config.yaml`  
**Template**: `manuscript/config.yaml.example`

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
```

**Benefits**:
- ✅ Version controllable (can be committed to git)
- ✅ Single file for all metadata
- ✅ Supports multiple authors with affiliations
- ✅ Structured format (YAML)
- ✅ Easy to edit and maintain

### Environment Variables (Backward Compatible)

For backward compatibility, environment variables still work and take precedence over config file values:

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
2. Config file (`manuscript/config.yaml`)
3. Default values (lowest priority)

### Configuration Examples

#### Using Configuration File (Recommended)
```bash
# Edit manuscript/config.yaml with your information
vim manuscript/config.yaml

# Build with config file values
./repo_utilities/render_pdf.sh
```

#### Using Environment Variables
```bash
export AUTHOR_NAME="Dr. Jane Smith"
export PROJECT_TITLE="Novel Optimization Framework"
export AUTHOR_EMAIL="jane.smith@university.edu"
export AUTHOR_ORCID="0000-0000-0000-1234"
export DOI="10.5281/zenodo.12345678"  # Optional

./repo_utilities/render_pdf.sh
```

#### Verbose Logging
```bash
export LOG_LEVEL=0  # Show all debug messages
./repo_utilities/render_pdf.sh
```

### Runtime Configuration

Configuration is read at runtime by `render_pdf.sh` and applied to:
- PDF metadata (title, author, date)
- LaTeX document properties
- Generated file headers
- Cross-reference systems
- Title page generation

## 🚀 Rendering Pipeline

### Complete Pipeline Execution

```bash
# 1. Clean previous outputs
./repo_utilities/clean_output.sh

# 2. Generate everything (tests + scripts + PDFs)
./repo_utilities/render_pdf.sh
```

### Pipeline Stages

1. **Test Validation** (100% coverage required)
2. **Script Execution** (all Python scripts in `scripts/`)
3. **Markdown Validation** (images, references, equations)
4. **Glossary Generation** (API reference from `src/`)
5. **Individual PDF Generation** (all manuscript sections)
6. **Combined PDF Generation** (complete manuscript)
7. **Additional Formats** (HTML, IDE-friendly PDF)

### Manual Execution Options

```bash
# Run only tests
python3 -m pytest tests/ --cov=src --cov-report=html

# Run only scripts
python3 scripts/*.py

# Validate markdown only
python3 repo_utilities/validate_markdown.py

# Generate only PDFs
./repo_utilities/render_pdf.sh  # (after manual setup)
```

## ✅ Validation Systems

### PDF Validation

```bash
# Validate generated PDF for issues
python3 repo_utilities/validate_pdf_output.py

# With verbose output
python3 repo_utilities/validate_pdf_output.py --verbose

# Specific PDF file
python3 repo_utilities/validate_pdf_output.py output/pdf/01_abstract.pdf
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
python3 repo_utilities/validate_markdown.py

# Strict mode (fail on any issues)
python3 repo_utilities/validate_markdown.py --strict
```

**Validation Checks**:
- Image reference resolution
- Cross-reference integrity
- Equation label validation
- Link formatting
- Mathematical notation

### Test Coverage

```bash
# Run tests with coverage report
python3 -m pytest tests/ --cov=src --cov-report=html

# Generate coverage report only
python3 -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
```

**Coverage Requirements**:
- 100% code coverage for all `src/` modules
- All tests must pass before PDF generation
- No mock methods (real data analysis only)

## 🧪 Testing Framework

### Test Structure

Tests follow the **thin orchestrator pattern**:
- Import real methods from `src/` modules
- Use real data and computation
- Validate actual behavior (no mocks)
- Ensure reproducible results

### Test Categories

1. **Unit Tests** (`test_*.py`) - Individual function validation
2. **Integration Tests** - Script and pipeline integration
3. **Validation Tests** - PDF and markdown quality checks

### Running Tests

```bash
# All tests with coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Specific test file
python3 -m pytest tests/test_example.py -v

# Integration tests only
python3 -m pytest tests/test_integration_pipeline.py

# With HTML coverage report
python3 -m pytest tests/ --cov=src --cov-report=html
```

## 📤 Output Formats

### Generated Files Structure

```
output/
├── pdf/                    # PDF documents
│   ├── 01_abstract.pdf     # Individual section PDFs
│   ├── 02_introduction.pdf
│   ├── project_combined.pdf # Complete manuscript
│   └── *.pdf               # Additional formats
├── tex/                    # LaTeX source files
│   ├── 01_abstract.tex
│   ├── project_combined.tex
│   └── *.tex
├── figures/                # Generated figures
│   ├── example_figure.png
│   ├── convergence_plot.png
│   └── *.png
├── data/                   # Generated datasets
│   ├── example_data.csv
│   ├── convergence_data.npz
│   └── *.csv
└── project_combined.html   # HTML version for IDE
```

### PDF Versions

1. **Standard PDF** (`project_combined.pdf`)
   - Professional printing format
   - Optimized for LaTeX rendering
   - Complete cross-references and citations

2. **IDE-Friendly PDF** (`project_combined_ide_friendly.pdf`)
   - Enhanced for text editor viewing
   - Better font rendering in IDEs
   - Simplified layout for screen reading

3. **HTML Version** (`project_combined.html`)
   - Web browser compatible
   - IDE integration
   - Interactive features (when available)

## 🧪 **Advanced Modules**

The template includes advanced modules for comprehensive scientific package development:

### 📊 **Quality Analysis** (`src/quality_checker.py`)
**Advanced document quality analysis and metrics**

**Key Features:**
- **Readability Analysis**: Flesch score, Gunning Fog index
- **Academic Standards**: Compliance with research writing standards
- **Structural Integrity**: Document organization and completeness
- **Formatting Quality**: Consistent styling and presentation
- **Comprehensive Reporting**: Detailed quality assessment reports

**Usage:**
```python
from quality_checker import analyze_document_quality, generate_quality_report

metrics = analyze_document_quality(pdf_path)
report = generate_quality_report(metrics)
print(report)
```

### 🔄 **Reproducibility Tools** (`src/reproducibility.py`)
**Build reproducibility and environment tracking**

**Key Features:**
- **Environment Capture**: Platform, Python version, dependencies
- **Dependency Tracking**: Version management and consistency
- **Build Manifests**: Comprehensive build artifact tracking
- **Snapshot Comparison**: Version control and change detection
- **Reproducible Builds**: Deterministic environment setup

**Usage:**
```python
from reproducibility import generate_reproducibility_report, save_reproducibility_report

report = generate_reproducibility_report(output_dir)
save_reproducibility_report(report, "reproducibility.json")
```

### 🔍 **Integrity Verification** (`src/integrity.py`)
**File integrity and cross-reference validation**

**Key Features:**
- **File Integrity**: Hash-based verification of output files
- **Cross-Reference Validation**: LaTeX reference integrity checking
- **Data Consistency**: Format and structure validation
- **Academic Standards**: Compliance with writing standards
- **Build Artifact Verification**: Complete output validation

**Usage:**
```python
from integrity import verify_output_integrity, generate_integrity_report

report = verify_output_integrity(output_dir)
print(generate_integrity_report(report))
```

### 📚 **Publishing Tools** (`src/publishing.py`)
**Academic publishing workflow assistance**

**Key Features:**
- **DOI Validation**: Format and checksum verification
- **Citation Generation**: BibTeX, APA, MLA formats
- **Publication Metadata**: Comprehensive metadata extraction
- **Submission Preparation**: Checklist and package creation
- **Academic Profile**: ORCID and repository integration

**Usage:**
```python
from publishing import extract_publication_metadata, generate_citation_bibtex

metadata = extract_publication_metadata(markdown_files)
bibtex = generate_citation_bibtex(metadata)
print(bibtex)
```

### 🔬 **Scientific Development** (`src/scientific_dev.py`)
**Scientific computing best practices and tools**

**Key Features:**
- **Numerical Stability**: Algorithm stability testing
- **Performance Benchmarking**: Execution time and memory analysis
- **Scientific Documentation**: API documentation generation
- **Best Practices Validation**: Code quality assessment
- **Research Workflow Templates**: Reproducible experiment templates

**Usage:**
```python
from scientific_dev import check_numerical_stability, benchmark_function

stability = check_numerical_stability(your_function, test_inputs)
benchmark = benchmark_function(your_function, test_inputs)
```

### 🏗️ **Build Verification** (`src/build_verifier.py`)
**Comprehensive build process validation**

**Key Features:**
- **Build Process Validation**: Command execution and error handling
- **Artifact Verification**: Expected output file checking
- **Reproducibility Testing**: Multiple build run comparison
- **Environment Validation**: Dependency and tool availability
- **Build Reporting**: Comprehensive validation reports

**Usage:**
```python
from build_verifier import verify_build_artifacts, verify_build_reproducibility

verification = verify_build_artifacts(output_dir, expected_files)
reproducibility = verify_build_reproducibility(build_command, expected_outputs)
```

### **Module Integration**

All advanced modules follow the **thin orchestrator pattern**:
- **Business logic** in `src/` modules with 100% test coverage
- **Orchestration** in separate utility scripts
- **Integration** with existing build pipeline
- **Comprehensive testing** ensuring reliability
- **Documentation** for each module's functionality

**Testing Coverage:**
- ✅ **Quality Checker**: 100% coverage (26 tests)
- ✅ **Reproducibility**: 100% coverage (18 tests)
- ✅ **Integrity**: 100% coverage (16 tests)
- ✅ **Publishing**: 100% coverage (14 tests)
- ✅ **Scientific Dev**: 100% coverage (12 tests)
- ✅ **Build Verifier**: 100% coverage (10 tests)

### Accessing Outputs

```bash
# Open combined PDF
open output/pdf/project_combined.pdf

# Open HTML version in browser
open output/project_combined.html

# List all generated files
ls -la output/

# Check PDF validation
python3 repo_utilities/validate_pdf_output.py
```

## 🔧 Troubleshooting

### Common Issues

#### Tests Failing
```bash
# Ensure 100% coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Check for missing test coverage
# Look for lines marked "missing" in coverage report
```

#### Scripts Failing
```bash
# Run scripts individually to debug
python3 scripts/example_figure.py

# Check import errors
python3 -c "import src.example; print('Import successful')"
```

#### PDF Generation Issues
```bash
# Check LaTeX installation
which xelatex

# Validate markdown first
python3 repo_utilities/validate_markdown.py

# Check compilation logs
ls output/pdf/*_compile.log
```

#### Missing Dependencies
```bash
# Install system dependencies
# Ubuntu/Debian:
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu

# macOS:
brew install pandoc
brew install --cask mactex
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=0
./repo_utilities/render_pdf.sh

# Run with debug output
python3 repo_utilities/validate_pdf_output.py --verbose
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
   git commit -m "feat: add new validation feature"
   ```

3. **Backup Strategy**
   ```bash
   # Clean outputs before backup
   ./repo_utilities/clean_output.sh

   # Backup source files only
   tar -czf project_backup.tar.gz src/ tests/ scripts/ manuscript/ docs/
   ```

### Adding New Features

1. **Business Logic** → Add to `src/`
2. **Tests** → Add to `tests/`
3. **Scripts** → Add to `scripts/` (use `src/` methods)
4. **Documentation** → Update relevant `.md` files
5. **Validation** → Ensure 100% test coverage

### Performance Optimization

- **Parallel Testing**: Use `pytest-xdist` for faster test runs
- **Caching**: Enable pytest caching for repeated runs
- **Incremental Builds**: Only rebuild changed components

## 📚 References

### Internal Documentation
- [`README.md`](README.md) - Project overview and quick start
- [`docs/HOW_TO_USE.md`](docs/HOW_TO_USE.md) - Complete usage guide
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System design details
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) - Development workflow

### External Resources
- [Pandoc Manual](https://pandoc.org/MANUAL.html) - Document conversion
- [LaTeX Wikibook](https://en.wikibooks.org/wiki/LaTeX) - LaTeX documentation
- [Python Testing](https://docs.pytest.org/) - Testing framework

## 🎯 Best Practices

### Development Workflow
1. Write tests first (TDD)
2. Ensure 100% coverage
3. Follow thin orchestrator pattern
4. Validate all outputs
5. Update documentation
6. Commit with clear messages

### Code Quality
- **Type Hints**: All public APIs must have type annotations
- **Documentation**: Clear docstrings for all functions
- **Error Handling**: Graceful failure with informative messages
- **Consistency**: Follow established patterns and conventions

### System Reliability
- **Deterministic Outputs**: All generation must be reproducible
- **Comprehensive Validation**: Check all aspects of output quality
- **Error Recovery**: Handle failures gracefully with clear messages
- **Performance Monitoring**: Track execution time and resource usage

---

## ✅ System Status: FULLY OPERATIONAL

**All systems confirmed functional:**
- ✅ Test suite (100% coverage)
- ✅ Script execution (thin orchestrator pattern)
- ✅ Markdown validation (all references resolved)
- ✅ PDF generation (individual + combined)
- ✅ Cross-reference system (citations, equations, figures)
- ✅ Configuration system (environment variables)
- ✅ Output validation (no rendering issues)
- ✅ Documentation (comprehensive guides)

**Ready for production use and research deployment.**

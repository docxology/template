# 📖 Glossary of Terms

> **Definitions** of key concepts and terminology

**Quick Reference:** [Cheatsheet](QUICK_START_CHEATSHEET.md) | [FAQ](FAQ.md) | [Complete Guide](HOW_TO_USE.md)

---

## A

### AGENTS.md
Comprehensive technical documentation files found in each directory. Contains detailed information for developers and advanced users. Complemented by README.md files for quick reference.

**See**: [Directory Documentation](#directory-documentation)

### Architecture Pattern
The overall system design that enforces separation of concerns between business logic (`src/`), tests, scripts, and documentation.

**See**: [ARCHITECTURE.md](ARCHITECTURE.md) | [Thin Orchestrator Pattern](#thin-orchestrator-pattern)

## B

### Branch Coverage
Testing metric ensuring all conditional branches (if/else, switch cases) are executed during tests. Required to be 100% for all `src/` code.

**See**: [Test Coverage](#test-coverage)

### Build Pipeline
Automated sequence of operations that validates tests, runs scripts, generates documentation, and builds PDFs. Orchestrated by `scripts/run_all.py` (6-stage pipeline).

**Stages**: Tests → Scripts → Validation → Glossary → Individual PDFs → Combined PDF

**See**: [BUILD_SYSTEM.md](BUILD_SYSTEM.md)

### Business Logic
Core algorithms, mathematical functions, and computational methods. Must reside in `src/` directory with comprehensive test coverage. Scripts should never implement business logic.

**See**: [Thin Orchestrator Pattern](#thin-orchestrator-pattern)

## C

### Combined PDF
Single PDF document containing all manuscript sections in proper order. Generated from individual section PDFs by the build pipeline.

**File**: `output/project_combined.pdf` (top-level, copied by stage 5)

**See**: [PDF Generation](#pdf-generation)

### Coverage Requirement
Comprehensive test coverage required: 70% minimum for project code, 49% minimum for infrastructure. Enforced by build pipeline before PDF generation.

**Check**: `pytest tests/ --cov=src --cov-report=term-missing`

**See**: [Test Coverage](#test-coverage)

### Cross-Reference
Internal link between document parts (sections, equations, figures, tables) using LaTeX `\ref{}` and `\eqref{}` commands.

**Examples**:
- Section: `\ref{sec:methodology}`
- Equation: `\eqref{eq:objective}`
- Figure: `\ref{fig:plot}`

**See**: [MARKDOWN_TEMPLATE_GUIDE.md](MARKDOWN_TEMPLATE_GUIDE.md)

## D

### Directory Documentation
Each major directory contains two documentation files:
- **AGENTS.md**: Comprehensive technical reference
- **README.md**: Quick reference and navigation

**Directories**: `src/`, `tests/`, `scripts/`, `manuscript/`, `docs/`, `repo_utilities/`

### DOI (Digital Object Identifier)
Persistent identifier for academic publications. Optional configuration for the template.

**Set**: `export DOI="10.5281/zenodo.12345678"`

**See**: [Project Metadata](#project-metadata)

## E

### Equation Environment
LaTeX structure for numbered mathematical equations with labels for cross-referencing.

**Syntax**:
```latex
\begin{equation}\label{eq:name}
f(x) = x^2
\end{equation}
```

**Reference**: `\eqref{eq:name}`

**See**: [MARKDOWN_TEMPLATE_GUIDE.md](MARKDOWN_TEMPLATE_GUIDE.md)

## F

### Figure Generation
Process of creating visual outputs from data using scripts that follow the thin orchestrator pattern. Figures saved to `output/figures/`.

**Pattern**: Script imports from `src/` → Uses tested methods → Handles visualization → Saves output

**See**: [Thin Orchestrator Pattern](#thin-orchestrator-pattern)

## G

### Glossary
Auto-generated API reference from `src/` code. Updated automatically during build pipeline.

**File**: `manuscript/98_symbols_glossary.md`

**Generation**: `python3 repo_utilities/generate_glossary.py`

### Guard Clause
Programming pattern that handles error conditions first, reducing nesting. Preferred style in this template.

**Example**:
```python
def process(value):
    if value is None:  # Guard clause
        return default
    # Main logic here
```

## H

### Headless Plotting
Running matplotlib without display server using `MPLBACKEND=Agg`. Required for CI/CD and automated builds.

**Set**: `export MPLBACKEND=Agg`

## I

### Individual PDF
Single PDF file generated for each manuscript section. Allows focused review of specific sections.

**Location**: `output/pdf/01_abstract.pdf`, `output/pdf/02_introduction.pdf`, etc.

**See**: [PDF Generation](#pdf-generation)

### Integration Test
Test that validates interaction between multiple components. Ensures scripts can import and use `src/` methods correctly.

**Example**: Testing that figure generation scripts successfully import and use `src/` functions

**See**: [Testing](#testing)

## L

### LaTeX Preamble
Document setup and styling configuration loaded before content. Defines packages, fonts, colors, and formatting.

**File**: `manuscript/preamble.md`

**Location**: [`manuscript/preamble.md`](../manuscript/preamble.md)

## M

### Manifest
List of generated files collected during build pipeline. Used to verify all expected outputs were created.

**Collected from**: Script stdout when they print output paths

### Manuscript
Research document composed of numbered sections in `manuscript/` directory. Converted to PDFs during build.

**Sections**: 01-09 (main), S01-S99 (supplemental), 98 (glossary), 99 (references)

**See**: [MANUSCRIPT_NUMBERING_SYSTEM.md](MANUSCRIPT_NUMBERING_SYSTEM.md)

### Markdown Validation
Automated checking of markdown files for broken references, missing images, invalid links, and syntax errors.

**Command**: `python3 repo_utilities/validate_markdown.py`

**See**: [MARKDOWN_TEMPLATE_GUIDE.md](MARKDOWN_TEMPLATE_GUIDE.md)

### Mock Method
Fake implementation of function for testing purposes. **NEVER USED** in this template - all tests use real data and real methods.

**Philosophy**: Test actual behavior, not mocked behavior

**See**: [Testing](#testing)

## O

### Orchestrator
Script that coordinates operations by importing and using methods from `src/`. Should not contain business logic.

**See**: [Thin Orchestrator Pattern](#thin-orchestrator-pattern)

### ORCID (Open Researcher and Contributor ID)
Unique persistent identifier for researchers. Optional configuration for the template.

**Format**: `0000-0001-2345-6789`

**Set**: `export AUTHOR_ORCID="0000-0001-2345-6789"`

### Output Directory
Location where all generated files are placed. **All files are disposable** and can be regenerated.

**Location**: `output/`

**Subdirectories**: `pdf/`, `figures/`, `data/`, `tex/`

## P

### Pandoc
Universal document converter used to transform markdown to LaTeX and PDF. Required system dependency.

**Install**: `brew install pandoc` (macOS) or `apt-get install pandoc` (Ubuntu)

**See**: [Prerequisites](#prerequisites)

### PDF Generation
Process of converting markdown sources to professional PDF documents using Pandoc and XeLaTeX.

**Pipeline**: Markdown → Pandoc → LaTeX → XeLaTeX → PDF

**Time**: ~58 seconds for complete rebuild

**See**: [BUILD_SYSTEM.md](BUILD_SYSTEM.md)

### PDF Validation
Automated checking of generated PDFs for rendering issues, unresolved references, and structural problems.

**Command**: `python3 repo_utilities/validate_pdf_output.py`

**Checks**: Unresolved references (??), missing citations, warnings, errors

**See**: [PDF_VALIDATION.md](PDF_VALIDATION.md)

### Prerequisites
Required system dependencies and software that must be installed before using the template.

**System**: pandoc, texlive-xetex, fonts
**Python**: uv or pip, python 3.9+

**See**: [GETTING_STARTED.md](GETTING_STARTED.md) | [README.md](../README.md)

### Project Metadata
Configuration information (author, title, DOI, etc.) applied to generated documents via environment variables.

**Variables**:
- `AUTHOR_NAME`
- `AUTHOR_EMAIL`
- `AUTHOR_ORCID`
- `PROJECT_TITLE`
- `DOI`

**See**: [Configuration System](../AGENTS.md#configuration-system)

## R

### Reference System
LaTeX-based cross-referencing that automatically numbers and links sections, equations, figures, and tables.

**Types**:
- Sections: `\ref{sec:name}`
- Equations: `\eqref{eq:name}`
- Figures: `\ref{fig:name}`
- Tables: `\ref{tab:name}`

**See**: [Cross-Reference](#cross-reference)

### Render Pipeline
Another name for [Build Pipeline](#build-pipeline). The complete sequence from tests to final PDF.

**Script**: `python3 scripts/run_all.py`

### Reproducibility
Ability to regenerate exact same results from source. Ensured through deterministic RNG seeds, fixed dependencies, and comprehensive testing.

**Tools**: Version locking, seed fixing, environment capture

**See**: [infrastructure/build/reproducibility.py](../infrastructure/build/reproducibility.py)

## S

### Script
Python file in `scripts/` directory that orchestrates operations. Must follow thin orchestrator pattern.

**Rules**:
- Import from `src/`
- Use `src/` methods for computation
- Handle only I/O, visualization, orchestration
- Print output paths

**See**: [Thin Orchestrator Pattern](#thin-orchestrator-pattern)

### Section Label
Unique identifier for manuscript section used in cross-references.

**Format**: `{#sec:section_name}`

**Example**: `# Introduction {#sec:introduction}`

**See**: [Cross-Reference](#cross-reference)

### Source Code
Core business logic residing in `src/` directory. Must have comprehensive test coverage.

**Requirements**:
- Type hints on public APIs
- Docstrings on all functions
- No circular imports
- Comprehensive test coverage

**See**: [infrastructure/AGENTS.md](../infrastructure/AGENTS.md), [project/src/AGENTS.md](../project/src/AGENTS.md)

### Statement Coverage
Testing metric ensuring every line of code is executed during tests. Required to be 100% for all `src/` code.

**Check**: Look for lines marked `>>>>>` in coverage report

**See**: [Test Coverage](#test-coverage)

### Supplemental Section
Additional manuscript content numbered S01-S99. Appears after main sections but before glossary.

**Example**: `S01_supplemental_methods.md`

**See**: [MANUSCRIPT_NUMBERING_SYSTEM.md](MANUSCRIPT_NUMBERING_SYSTEM.md)

## T

### TDD (Test-Driven Development)
Development methodology where tests are written before implementation code.

**Workflow**: Write test → Run (fails) → Implement → Run (passes) → Refactor

**See**: [WORKFLOW.md](WORKFLOW.md) | [HOW_TO_USE.md](HOW_TO_USE.md)

### Template Repository
GitHub repository type that can be used to create new repositories with same structure. This template is a template repository.

**Use**: Click "Use this template" button on GitHub

### Test Coverage
Percentage of code executed during test runs. This template requires 70% minimum coverage for project code and 49% minimum for infrastructure.

**Types**:
- Statement coverage (every line)
- Branch coverage (every conditional)

**Command**: `pytest tests/ --cov=src --cov-report=term-missing`

**See**: [Testing](#testing)

### Test Suite
Collection of all test files in `tests/` directory. Ensures all functionality works correctly.

**Status**: 878 tests passing (558 infra + 320 project, 100%)

**Run**: `pytest tests/`

**See**: [tests/AGENTS.md](../tests/AGENTS.md)

### Testing
Process of validating code correctness through automated test cases. No mocks allowed - all tests use real data.

**Requirements**:
- 70% minimum for project code (currently 99.88%)
- 49% minimum for infrastructure (currently 55.89%)
- Real data (no mocks)
- Deterministic results
- All tests must pass

**See**: [TEST_IMPROVEMENTS_SUMMARY.md](TEST_IMPROVEMENTS_SUMMARY.md)

### Thin Orchestrator Pattern
Core architectural principle where scripts are lightweight wrappers that import and use `src/` methods.

**Principles**:
- ALL business logic in `src/`
- Scripts only orchestrate
- Comprehensive test coverage of `src/`
- Clear separation of concerns

**Benefits**: Maintainability, testability, reusability, clarity

**See**: [THIN_ORCHESTRATOR_SUMMARY.md](THIN_ORCHESTRATOR_SUMMARY.md)

## U

### Unit Test
Test that validates a single function or method in isolation. Forms the foundation of the test suite.

**Example**:
```python
def test_add_numbers():
    result = add_numbers(2, 3)
    assert result == 5
```

**See**: [Testing](#testing)

### uv
Fast Python package manager used as default for this template. Alternative to pip.

**Commands**:
- `uv sync` - Install dependencies
- `uv run pytest` - Run tests

**Install**: `pip install uv`

## V

### Validation
Automated checking of various aspects: tests, markdown, PDFs, coverage, etc.

**Types**:
- Test validation (pytest)
- Markdown validation (validate_markdown.py)
- PDF validation (validate_pdf_output.py)
- Coverage validation (pyproject.toml `[tool.coverage.*]`)

**See**: [Build Pipeline](#build-pipeline)

## X

### XeLaTeX
LaTeX engine that supports Unicode and modern fonts. Used for PDF generation.

**Required**: Part of texlive-xetex package

**Install**: `brew install --cask mactex` (macOS)

**See**: [Prerequisites](#prerequisites)

## Acronyms & Abbreviations

| Term | Full Name | Description |
|------|-----------|-------------|
| API | Application Programming Interface | Public functions/methods in `src/` |
| CI/CD | Continuous Integration/Deployment | Automated build and test systems |
| CSV | Comma-Separated Values | Data file format |
| DOI | Digital Object Identifier | Persistent publication identifier |
| HTML | HyperText Markup Language | Web page format |
| I/O | Input/Output | Reading/writing files and data |
| LaTeX | (Lamport TeX) | Document preparation system |
| NPZ | NumPy Zipped | Compressed numpy array format |
| ORCID | Open Researcher and Contributor ID | Researcher identifier |
| PDF | Portable Document Format | Final output format |
| PNG | Portable Network Graphics | Image file format |
| RNG | Random Number Generator | Source of randomness |
| TDD | Test-Driven Development | Write tests before code |
| TOC | Table of Contents | Document navigation aid |
| UI | User Interface | Visual elements users interact with |
| UX | User Experience | Overall user interaction quality |

## Related Documentation

- **[Quick Start Cheatsheet](QUICK_START_CHEATSHEET.md)** - Essential commands
- **[Common Workflows](COMMON_WORKFLOWS.md)** - Step-by-step recipes
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[Complete Guide](HOW_TO_USE.md)** - All skill levels
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Documentation Index](DOCUMENTATION_INDEX.md)** - All documentation

---

**Can't find a term?** Check the **[FAQ](FAQ.md)** or **[Documentation Index](DOCUMENTATION_INDEX.md)**



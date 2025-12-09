# 🚀 Research Project Template

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](docs/BUILD_SYSTEM.md)
[![Test Coverage](https://img.shields.io/badge/coverage-99.88%25%20project%20|%2061.48%25%20infra-brightgreen)](docs/BUILD_SYSTEM.md)
[![Tests](https://img.shields.io/badge/tests-2175%2F2175%20passing%20(100%25)-brightgreen)](docs/BUILD_SYSTEM.md)
[![Documentation](https://img.shields.io/badge/docs-50%2B%20files-blue)](docs/DOCUMENTATION_INDEX.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16903352.svg)](https://doi.org/10.5281/zenodo.16903352)

> **Template Repository** - Click "Use this template" to create a new research project with this structure

A revolutionary system for research and development projects. This template provides a comprehensive, test-driven structure with automated PDF generation, professional documentation, and validated build pipelines.

## 🎯 What This Template Provides

This is a **GitHub Template Repository** that gives you:

- ✅ **Complete project structure** with clear separation of concerns
- ✅ **Test-driven development** setup with comprehensive coverage requirements
- ✅ **Automated PDF generation** from markdown sources
- ✅ **Thin orchestrator pattern** for maintainable code
- ✅ **Ready-to-use utilities** for any research project
- ✅ **Professional documentation** structure (50+ comprehensive guides)
- ✅ **Advanced quality analysis** and document metrics
- ✅ **Reproducibility tools** for scientific workflows
- ✅ **Integrity verification** and validation
- ✅ **Publishing tools** for academic dissemination
- ✅ **Scientific development** best practices
- ✅ **Comprehensive reporting** with error aggregation and performance metrics

## 🗺️ Choose Your Path

**Select your experience level to get started:**

<table>
<tr>
<td width="50%" valign="top">

### 📚 For New Users
**Just getting started?**

1. **[Quick Start Guide](#quick-start)** - Get running in 5 minutes
2. **[Getting Started Guide](docs/GETTING_STARTED.md)** - Complete beginner's guide (Levels 1-3)
3. **[Quick Start Cheatsheet](docs/QUICK_START_CHEATSHEET.md)** - One-page command reference
4. **[Common Workflows](docs/COMMON_WORKFLOWS.md)** - Step-by-step recipes for common tasks
5. **[How To Use Guide](docs/HOW_TO_USE.md)** - Complete usage from basic to advanced
6. **[Examples Showcase](docs/EXAMPLES_SHOWCASE.md)** - Real-world applications
7. **[FAQ](docs/FAQ.md)** - Common questions answered

**Learn by example:** See **[Template Description](docs/TEMPLATE_DESCRIPTION.md)** and **[Examples](docs/EXAMPLES.md)**

</td>
<td width="50%" valign="top">

### 💻 For Developers
**Ready to build?**

1. **[Architecture Guide](docs/ARCHITECTURE.md)** - System design overview
2. **[Thin Orchestrator Pattern](docs/THIN_ORCHESTRATOR_SUMMARY.md)** - Core architecture
3. **[Development Workflow](docs/WORKFLOW.md)** - Complete development process
4. **[Markdown Guide](docs/MARKDOWN_TEMPLATE_GUIDE.md)** - Writing and formatting
5. **[Manuscript Style Guide](.cursorrules/manuscript_style.md)** - Formatting standards and best practices

**Advanced topics:** Check **[Build System](docs/BUILD_SYSTEM.md)** and **[PDF Validation](docs/PDF_VALIDATION.md)**

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🤝 For Contributors
**Want to contribute?**

1. **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute
2. **[Code of Conduct](docs/CODE_OF_CONDUCT.md)** - Community standards
3. **[Development Roadmap](docs/ROADMAP.md)** - Future plans
4. **[Security Policy](docs/SECURITY.md)** - Security practices

**Recent improvements:** See **[Build System](docs/BUILD_SYSTEM.md)** and **[Test Improvements](docs/TEST_IMPROVEMENTS_SUMMARY.md)**

</td>
<td width="50%" valign="top">

### 🔬 For Advanced Users
**Need technical details?**

1. **[Complete System Reference](AGENTS.md)** - Everything you need to know
2. **[Build System](docs/BUILD_SYSTEM.md)** - Complete build system reference
3. **[Manuscript Numbering](docs/MANUSCRIPT_NUMBERING_SYSTEM.md)** - Section organization
4. **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Complete reference

**Technical resources:** See **[LaTeX Preamble](project/manuscript/preamble.md)** and **[Copypasta](docs/COPYPASTA.md)**

</td>
</tr>
</table>

## 🧭 Documentation Navigation Map

```mermaid
graph TB
    README[README.md<br/>You Are Here]
    
    subgraph Core["📖 Core Documentation"]
        AGENTS[AGENTS.md<br/>Complete System Reference]
        HOW_TO[HOW_TO_USE.md<br/>Usage Guide: Basic to Advanced]
        ARCH[ARCHITECTURE.md<br/>System Design]
        WORKFLOW[WORKFLOW.md<br/>Development Process]
    end
    
    subgraph Build["🔧 Build & Quality"]
        BUILD_SYS[BUILD_SYSTEM.md<br/>Complete Build Reference]
        PDF_VAL[PDF_VALIDATION.md<br/>Quality Checks]
    end
    
    subgraph Dev["💻 Development"]
        THIN_ORCH[THIN_ORCHESTRATOR_SUMMARY.md<br/>Architecture Pattern]
        MARKDOWN[MARKDOWN_TEMPLATE_GUIDE.md<br/>Writing Guide]
        MANUSCRIPT[MANUSCRIPT_NUMBERING_SYSTEM.md<br/>Section Organization]
        ELIM[Simplified Structure<br/>(Archived)]
    end
    
    subgraph Community["🤝 Community"]
        CONTRIB[CONTRIBUTING.md<br/>How to Contribute]
        COC[CODE_OF_CONDUCT.md<br/>Community Standards]
        ROADMAP[ROADMAP.md<br/>Future Plans]
        SECURITY[SECURITY.md<br/>Security Policy]
    end
    
    subgraph Examples["📚 Examples & Help"]
        EXAMPLES[EXAMPLES.md<br/>Usage Patterns]
        SHOWCASE[EXAMPLES_SHOWCASE.md<br/>Real-World Apps]
        FAQ_DOC[FAQ.md<br/>Common Questions]
        TEMPLATE_DESC[TEMPLATE_DESCRIPTION.md<br/>Overview]
    end
    
    subgraph Reference["📑 Reference"]
        DOC_INDEX[DOCUMENTATION_INDEX.md<br/>Complete Index]
        COPYPASTA[COPYPASTA.md<br/>Shareable Content]
        PREAMBLE[preamble.md<br/>LaTeX Styling]
        TEST_IMP[TEST_IMPROVEMENTS_SUMMARY.md<br/>Testing Enhancements]
    end
    
    README --> Core
    README --> Build
    README --> Dev
    README --> Community
    README --> Examples
    README --> Reference
    
    classDef default fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef core fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef build fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef community fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    
    class Core core
    class Build build
    class Community community
```

## 🚀 Quick Start {#quick-start}

### Option 1: Use This Template (Recommended)

1. **Click "Use this template"** above to create a new repository
2. **Clone your new repository**
3. **Install dependencies**: `uv sync`
4. **Generate your first document**: `python3 scripts/03_render_pdf.py`

**📖 Need help?** See **[Getting Started Guide](docs/GETTING_STARTED.md)** for beginners, **[Quick Start Cheatsheet](docs/QUICK_START_CHEATSHEET.md)** for quick reference, or **[How To Use Guide](docs/HOW_TO_USE.md)** for comprehensive guidance from basic usage to advanced workflows.

### Option 2: Quick Commands Reference

```bash
# Interactive menu (recommended) - 10-stage extended pipeline
./run.sh

# Or run full 10-stage pipeline directly (includes optional LLM review)
./run.sh --pipeline

# Alternative: Core 6-stage pipeline (no LLM dependencies)
python3 scripts/run_all.py

# Run tests with coverage (infrastructure + project)
python3 scripts/01_run_tests.py

# Open generated manuscript
open output/pdf/project_combined.pdf
```

## 📊 System Health & Metrics

**Current Build Status** (See **[Build System](docs/BUILD_SYSTEM.md)** for complete analysis):

```mermaid
graph LR
    subgraph Status["✅ System Status"]
        TESTS[Tests: 2175/2175 passing<br/>1855 infra + 320 project<br/>100% success rate]
        COV[Coverage: 99.88% project<br/>61.48% infra<br/>Exceeds requirements]
        BUILD[Build Time: 84s<br/>Optimal performance<br/>(without LLM review)]
        PDFS[PDFs: 14/14 generated<br/>All sections complete]
    end
    
    subgraph Documentation["📚 Documentation"]
        DOCS[50+ documentation files<br/>Comprehensive coverage]
        CROSS[Complete cross-referencing<br/>All links validated]
        EXAMPLES[Real-world examples<br/>Multiple use cases]
    end
    
    TESTS --> VERIFIED[✅ System Fully<br/>Operational]
    COV --> VERIFIED
    BUILD --> VERIFIED
    PDFS --> VERIFIED
    DOCS --> VERIFIED
    CROSS --> VERIFIED
    EXAMPLES --> VERIFIED
    
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:3px
    classDef metrics fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    
    class VERIFIED success
    class Status,Documentation metrics
```

**Key Metrics:**
- **Test Coverage**: 99.88% project, 61.48% infrastructure (exceeds requirements) - [Details](docs/BUILD_SYSTEM.md#stage-1-test-suite-27-seconds)
- **Build Time**: 84 seconds (optimal, without optional LLM review) - [Performance Analysis](docs/BUILD_SYSTEM.md#stage-breakdown)
- **Tests Passing**: 2175 tests (1855 infrastructure + 320 project) - [Test Report](docs/BUILD_SYSTEM.md#stage-1-test-suite-27-seconds)
- **PDFs Generated**: 14 (all sections) - [Output Summary](docs/BUILD_SYSTEM.md#generated-files)
- **Documentation**: 50+ comprehensive files - [Documentation Index](docs/DOCUMENTATION_INDEX.md)

## 🎓 Learning Paths

Choose your learning path based on your goals:

```mermaid
flowchart TD
    START[What do you need?]
    
    START -->|Just write documents| PATH1[📝 Basic Usage Path]
    START -->|Add code + figures| PATH2[🔧 Intermediate Path]
    START -->|Full TDD workflow| PATH3[🧪 Advanced Path]
    START -->|Understand system| PATH4[🏗️ Architecture Path]
    START -->|Contribute code| PATH5[🤝 Contributor Path]
    
    PATH1 --> HOW_TO1[HOW_TO_USE.md<br/>Levels 1-3:<br/>Document Creation]
    PATH1 --> MARKDOWN1[MARKDOWN_TEMPLATE_GUIDE.md<br/>Writing & Formatting]
    PATH1 --> EXAMPLES1[EXAMPLES.md<br/>Usage Patterns]
    
    PATH2 --> HOW_TO2[HOW_TO_USE.md<br/>Levels 4-6:<br/>Figures & Automation]
    PATH2 --> THIN_ORCH2[THIN_ORCHESTRATOR_SUMMARY.md<br/>Architecture Pattern]
    PATH2 --> SHOWCASE2[EXAMPLES_SHOWCASE.md<br/>Real-World Apps]
    
    PATH3 --> HOW_TO3[HOW_TO_USE.md<br/>Levels 7-9:<br/>Test-Driven Dev]
    PATH3 --> ARCH3[ARCHITECTURE.md<br/>System Design]
    PATH3 --> WORKFLOW3[WORKFLOW.md<br/>Development Process]
    PATH3 --> BUILD3[BUILD_SYSTEM.md<br/>Performance Metrics]
    
    PATH4 --> AGENTS4[AGENTS.md<br/>Complete Reference]
    PATH4 --> ARCH4[ARCHITECTURE.md<br/>Design Overview]
    PATH4 --> THIN_ORCH4[THIN_ORCHESTRATOR_SUMMARY.md<br/>Core Pattern]
    
    PATH5 --> CONTRIB5[CONTRIBUTING.md<br/>Contribution Guide]
    PATH5 --> COC5[CODE_OF_CONDUCT.md<br/>Community Standards]
    PATH5 --> ROADMAP5[ROADMAP.md<br/>Development Plans]
    PATH5 --> TEST_IMP5[TEST_IMPROVEMENTS_SUMMARY.md<br/>Testing Details]
    
    classDef path fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef doc fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    
    class PATH1,PATH2,PATH3,PATH4,PATH5 path
    class HOW_TO1,HOW_TO2,HOW_TO3,MARKDOWN1,EXAMPLES1,THIN_ORCH2,SHOWCASE2,ARCH3,WORKFLOW3,BUILD3,AGENTS4,ARCH4,THIN_ORCH4,CONTRIB5,COC5,ROADMAP5,TEST_IMP5 doc
```

### Path 1: Just Write Documents
**Goal:** Create professional documents without coding

1. Read **[HOW_TO_USE.md](docs/HOW_TO_USE.md)** (Levels 1-3)
2. Check **[MARKDOWN_TEMPLATE_GUIDE.md](docs/MARKDOWN_TEMPLATE_GUIDE.md)** for formatting
3. See **[EXAMPLES.md](docs/EXAMPLES.md)** for usage patterns

### Path 2: Add Figures and Analysis
**Goal:** Generate figures and automate workflows

1. Read **[HOW_TO_USE.md](docs/HOW_TO_USE.md)** (Levels 4-6)
2. Study **[THIN_ORCHESTRATOR_SUMMARY.md](docs/THIN_ORCHESTRATOR_SUMMARY.md)** for architecture
3. Review **[EXAMPLES_SHOWCASE.md](docs/EXAMPLES_SHOWCASE.md)** for real-world apps

### Path 3: Full Test-Driven Development
**Goal:** Build with comprehensive test coverage and automation

1. Read **[HOW_TO_USE.md](docs/HOW_TO_USE.md)** (Levels 7-9)
2. Study **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** and **[WORKFLOW.md](docs/WORKFLOW.md)**
3. Review **[BUILD_SYSTEM.md](docs/BUILD_SYSTEM.md)** for metrics

### Path 4: Understand the System
**Goal:** Deep dive into architecture and design

1. Read **[AGENTS.md](AGENTS.md)** - Complete system reference
2. Study **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** for design overview
3. Review **[THIN_ORCHESTRATOR_SUMMARY.md](docs/THIN_ORCHESTRATOR_SUMMARY.md)** for core pattern

### Path 5: Contribute to Template
**Goal:** Improve the template for everyone

1. Read **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** and **[CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md)**
2. Check **[ROADMAP.md](docs/ROADMAP.md)** for planned features
3. Review **[TEST_IMPROVEMENTS_SUMMARY.md](docs/TEST_IMPROVEMENTS_SUMMARY.md)** for testing standards

## 🏗️ Project Structure

The project follows a standardized structure with clear separation of concerns:

```mermaid
graph TB
    subgraph L1["Layer 1: Infrastructure"]
        INFRA[infrastructure/<br/>Generic tools<br/>Build and validation]
        INFRA_SCRIPTS[scripts/<br/>Entry point orchestrators<br/>6-stage core or 10-stage extended]
    end
    
    subgraph L2["Layer 2: Project-Specific"]
        SRC[project/src/<br/>Scientific algorithms<br/>100% tested]
        SCRIPTS[project/scripts/<br/>Analysis scripts<br/>Thin orchestrators]
    end
    
    subgraph PC["Project Components"]
        TESTS[tests/<br/>Test suite<br/>Comprehensive coverage]
        DOCS[docs/<br/>Documentation<br/>42+ guides]
        MANUSCRIPT[project/manuscript/<br/>Research sections<br/>Generate PDFs]
        OUTPUT[output/<br/>Generated files<br/>PDFs, figures, data]
    end
    
    SRC -->|import and use| SCRIPTS
    SRC -->|import and use| INFRA_SCRIPTS
    INFRA -->|provide utilities| SCRIPTS
    SCRIPTS -->|generate| OUTPUT
    INFRA_SCRIPTS -->|orchestrate pipeline| TESTS
    INFRA_SCRIPTS -->|orchestrate pipeline| SCRIPTS
    MANUSCRIPT -->|reference| OUTPUT
    TESTS -->|validate| SRC
    
    classDef layer1 fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef layer2 fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef output fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    
    class INFRA,INFRA_SCRIPTS layer1
    class SRC,SCRIPTS layer2
    class TESTS,DOCS,MANUSCRIPT core
    class OUTPUT output
```

**Directory Overview:**

- **`infrastructure/`** - **Generic build/validation tools** (Layer 1) - [Details](infrastructure/AGENTS.md)
- **`scripts/`** - **Entry point orchestrators** that discover and execute project-specific scripts - [Script Guide](scripts/AGENTS.md)
- **`tests/`** - Test files for infrastructure modules - [Testing Guide](tests/AGENTS.md)
- **`project/src/`** - **Project-specific scientific code** with comprehensive test coverage - [Project Details](project/src/AGENTS.md)
- **`project/scripts/`** - **Project-specific analysis scripts** that use project/src/ methods
- **`project/tests/`** - Project test suite
- **`docs/`** - Package-level documentation (50+ guides) - [Documentation Index](docs/DOCUMENTATION_INDEX.md)
- **`project/manuscript/`** - Research manuscript sections (generate PDFs) - [Manuscript Guide](project/manuscript/AGENTS.md)
- **`output/`** - Generated outputs (PDFs, figures, data) - **All files disposable**

## 🔑 Key Architectural Principles

### Thin Orchestrator Pattern

**[Complete details](docs/THIN_ORCHESTRATOR_SUMMARY.md)** | **[Architecture Overview](docs/ARCHITECTURE.md)**

The project follows a **thin orchestrator pattern** where:

- **`infrastructure/`** and **`project/src/`** contain **ALL** business logic, algorithms, and implementations
- **`scripts/`** are **lightweight wrappers** that coordinate pipeline stages
- **`tests/`** ensure **comprehensive coverage** of all functionality
- **`run.sh`** provides a unified interactive menu for all operations

**Benefits:** [Read more](docs/ARCHITECTURE.md#thin-orchestrator-pattern)

- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality
- **Reusability**: Scripts can use any `src/` method
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system

### Scripts as Integration Examples

**[Complete guide](scripts/AGENTS.md)** | **[Writing Guide](docs/MARKDOWN_TEMPLATE_GUIDE.md)**

Scripts in `project/scripts/` demonstrate proper integration with `project/src/` modules:

- **Import** scientific functions from `project/src/` modules
- **Use** tested methods for all computation
- **Handle** visualization, I/O, and orchestration
- **Generate** figures and data outputs
- **Validate** that module integration works correctly

**Example**: `example_figure.py` imports `add_numbers()`, `calculate_average()`, etc. from `project/src/example.py` and uses them to process data before visualization.

## ✨ Key Features

### Test-Driven Development
**[Complete guide](docs/WORKFLOW.md)** | **[Testing improvements](docs/TEST_IMPROVEMENTS_SUMMARY.md)**

All source code must meet **test coverage requirements** (90% project, 60% infrastructure) before PDF generation proceeds. This ensures that the methods used by scripts are fully validated.

**Current Coverage**: 99.88% project, 61.48% infrastructure (exceeds requirements) - [Test Report](docs/BUILD_SYSTEM.md#stage-1-test-suite-27-seconds)

### Automated Script Execution
**[Script guide](scripts/AGENTS.md)** | **[Examples](docs/EXAMPLES_SHOWCASE.md)**

Project-specific scripts in the `project/scripts/` directory are automatically executed to generate figures and data. These scripts **import and use** the tested methods from `project/src/`, demonstrating proper integration patterns.

### Markdown to PDF Pipeline
**[Markdown guide](docs/MARKDOWN_TEMPLATE_GUIDE.md)** | **[PDF validation](docs/PDF_VALIDATION.md)**

Manuscript sections are converted to individual PDFs with proper figure integration, and a combined manuscript document is generated with comprehensive cross-referencing.

**Build Performance**: 84 seconds for complete regeneration (without optional LLM review) - [Performance Analysis](docs/BUILD_SYSTEM.md#stage-breakdown)

### Build System Validation
**[Build System](docs/BUILD_SYSTEM.md)** - Complete reference (status, performance, fixes)

The build system has been comprehensively validated:
- All 14 PDFs generate successfully
- No critical errors or warnings
- Optimized 84-second build time (without optional LLM review)
- Complete documentation of system health

### Generic and Reusable
**[Template description](docs/TEMPLATE_DESCRIPTION.md)** | **[Copypasta](docs/COPYPASTA.md)**

The utility scripts can be used with any project that follows this structure, making it easy to adopt for new research projects.

## 🛠️ Installation & Setup

### 1. Prerequisites

Install required system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install -y pandoc texlive-xetex texlive-fonts-recommended fonts-dejavu

# macOS (using Homebrew)
brew install pandoc
brew install --cask mactex
```

### 2. Python Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip (if uv is not available)
pip install -e .
```

### 3. Generate Manuscript

```bash
# Interactive menu (recommended) - 10-stage extended pipeline with LLM review
./run.sh

# Or run full 10-stage pipeline directly (stages 0-9, includes optional LLM)
./run.sh --pipeline

# Alternative: Core 6-stage pipeline (stages 00-05, no LLM dependencies)
python3 scripts/run_all.py

# Or run stages individually (using generic entry point orchestrators)
python3 scripts/00_setup_environment.py      # Setup environment
python3 scripts/01_run_tests.py              # Run tests (infrastructure + project)
python3 scripts/02_run_analysis.py           # Execute project/scripts/
python3 scripts/03_render_pdf.py             # Render PDFs
python3 scripts/04_validate_output.py        # Validate output
python3 scripts/05_copy_outputs.py           # Copy final deliverables
```

**Pipeline Entry Points:**
- **`./run.sh --pipeline`**: 10 stages (0-9) - Extended pipeline with optional LLM review and translations
- **`python3 scripts/run_all.py`**: 6 stages (00-05) - Core pipeline only, no LLM dependencies
- **`./run.sh`**: Interactive menu with all options (individual stages, LLM operations, literature search)

**See [How To Use Guide](docs/HOW_TO_USE.md) for comprehensive setup instructions at all skill levels.**

**Architecture Note:** The project uses a **two-layer architecture**:
- **Layer 1 (infrastructure/)**: Generic, reusable tools
- **Layer 2 (project/)**: Project-specific scientific code

The root-level `scripts/` directory contains generic entry point orchestrators that discover and coordinate project-specific code in `project/scripts/`.

## 🔧 Customization

### Project Metadata Configuration

**[Complete configuration guide](AGENTS.md#configuration-system)**

The system supports **two configuration methods**:

#### Method 1: Configuration File (Recommended)

Edit `project/manuscript/config.yaml` with your paper metadata:

```yaml
paper:
  title: "Your Project Title"

authors:
  - name: "Your Name"
    orcid: "0000-0000-0000-0000"
    email: "your.email@example.com"
    affiliation: "Your Institution"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional
```

See `project/manuscript/config.yaml.example` for all available options.

#### Method 2: Environment Variables (Alternative)

```bash
# Basic configuration
export AUTHOR_NAME="Your Name"
export AUTHOR_ORCID="0000-0000-0000-0000"
export AUTHOR_EMAIL="your.email@example.com"
export PROJECT_TITLE="Your Project Title"

# Optional DOI (if available)
export DOI="10.5281/zenodo.12345678"

# Generate with custom configuration
python3 scripts/03_render_pdf.py
```

**Priority**: Environment variables override config file values.

**Configuration is applied to:**
- PDF metadata (title, author, creation date)
- LaTeX document properties - [Preamble details](project/manuscript/preamble.md)
- Generated file headers
- Cross-reference systems

### Adding Project-Specific Scripts

**[Script architecture guide](scripts/AGENTS.md)** | **[Thin orchestrator pattern](docs/THIN_ORCHESTRATOR_SUMMARY.md)**

Place Python scripts in the `project/scripts/` directory. They should:

- **Import methods from `project/src/` modules** (thin orchestrator pattern)
- **Use `project/src/` methods for all computation** (never implement algorithms)
- **Generate figures/data** using tested methods
- **Print file paths to stdout**
- **Handle errors gracefully**
- **Save outputs to appropriate directories**

Example script structure:

```python
#!/usr/bin/env python3
"""Example project script demonstrating thin orchestrator pattern."""

from project.src.example import add_numbers, calculate_average  # Import from src/

def main():
    # Use src/ methods for computation
    data = [1, 2, 3, 4, 5]
    avg = calculate_average(data)  # From project/src/example.py
    
    # Script handles visualization and output
    # ... visualization code ...
    
    # Print paths for the system to capture
    print("project/output/generated/file.png")

if __name__ == "__main__":
    main()
```

### Manuscript Structure

**[Manuscript guide](project/manuscript/AGENTS.md)** | **[Numbering system](docs/MANUSCRIPT_NUMBERING_SYSTEM.md)**

- `preamble.md` - LaTeX preamble and styling - [Details](project/manuscript/preamble.md)
- `01_abstract.md` through `06_conclusion.md` - Main sections
- `S01_supplemental_methods.md` - Supplemental sections
- `98_symbols_glossary.md` - Auto-generated API reference
- `99_references.md` - Bibliography

**Recent improvement**: Simplified structure with `markdown/` directory eliminated (see [Manuscript Numbering System](docs/MANUSCRIPT_NUMBERING_SYSTEM.md) for details)

## 📊 Testing

**[Testing guide](tests/AGENTS.md)** | **[Workflow](docs/WORKFLOW.md)** | **[Test improvements](docs/TEST_IMPROVEMENTS_SUMMARY.md)**

The system enforces comprehensive test coverage using TDD principles:

```bash
# Run all tests with coverage (infrastructure + project)
python3 scripts/01_run_tests.py

# Or run manually with coverage reports
pytest tests/infrastructure/ --cov=infrastructure --cov-report=html
pytest project/tests/ --cov=project/src --cov-report=html

# Generate detailed coverage report with missing lines
pytest tests/infrastructure/ --cov=infrastructure --cov-report=term-missing
pytest project/tests/ --cov=project/src --cov-report=term-missing

# Verify coverage requirements (infrastructure modules)
pytest tests/infrastructure/ --cov=infrastructure --cov-fail-under=49
```

**Test Requirements (Infrastructure Layer - Layer 1):**
- **60% minimum coverage**: Currently achieving 66.76%
- **No mocks**: All tests use real data and computations
- **Deterministic**: Fixed RNG seeds for reproducible results
- **Integration testing**: Cross-module interaction validation

**Test Requirements (Project Layer - Layer 2):**
- **90% minimum coverage**: Currently achieving 98.03%
- **Real data testing**: Use actual domain data, not synthetic test data
- **Reproducible**: Fixed seeds and deterministic computation

**Current Status**: 2175 tests passing (1855 infra + 320 project), 99.88% project coverage - [Full Analysis](docs/BUILD_SYSTEM.md#stage-1-test-suite-27-seconds)

## 📤 Output

**[Build System](docs/BUILD_SYSTEM.md)** | **[PDF validation](docs/PDF_VALIDATION.md)**

Generated outputs are organized in the `output/` directory:

```mermaid
graph TD
    OUTPUT[output/] --> PDFS[pdf/<br/>Individual + Combined PDFs<br/>14 files generated]
    OUTPUT --> FIGS[figures/<br/>PNG files from scripts<br/>23 figures]
    OUTPUT --> DATA[data/<br/>CSV, NPZ files<br/>5 datasets]
    OUTPUT --> TEX[tex/<br/>LaTeX source files<br/>For further processing]
    
    classDef dir fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef files fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class OUTPUT dir
    class PDFS,FIGS,DATA,TEX files
```

- **`output/pdf/`** - Individual manuscript section PDFs and combined manuscript PDF
- **`output/tex/`** - LaTeX source files
- **`output/data/`** - Data files (CSV, NPZ, etc.)
- **`output/figures/`** - Generated figures (PNG, etc.)

**All files in `output/` are disposable and regenerated by the build pipeline.**

**Generation Time**: 84 seconds for complete rebuild (without optional LLM review) - [Performance Details](docs/BUILD_SYSTEM.md#stage-breakdown)

## 🔍 How It Works

**[Complete workflow](docs/WORKFLOW.md)** | **[Architecture](docs/ARCHITECTURE.md)** | **[Build System](docs/BUILD_SYSTEM.md)** | **[Run Guide](RUN_GUIDE.md)**

The template provides **two pipeline entry points**:

### Entry Point 1: Extended Pipeline (`./run.sh --pipeline`)

**10-stage pipeline** (stages 0-9) with optional LLM review:

```mermaid
flowchart TD
    START([./run.sh --pipeline]) --> STAGE0[Stage 0: Clean Output Directories]
    STAGE0 --> STAGE1[Stage 1: Setup Environment]
    STAGE1 --> STAGE2[Stage 2: Infrastructure Tests<br/>60%+ coverage required]
    STAGE2 --> STAGE3[Stage 3: Project Tests<br/>90%+ coverage required]
    STAGE3 --> STAGE4[Stage 4: Project Analysis<br/>Execute project/scripts/]
    STAGE4 --> STAGE5[Stage 5: PDF Rendering<br/>Generate manuscript PDFs]
    STAGE5 --> STAGE6[Stage 6: Output Validation<br/>Quality checks]
    STAGE6 --> STAGE7[Stage 7: Copy Outputs<br/>Final deliverables]
    STAGE7 --> STAGE8[Stage 8: LLM Scientific Review<br/>Optional, requires Ollama]
    STAGE8 --> STAGE9[Stage 9: LLM Translations<br/>Optional, requires Ollama]
    STAGE9 --> SUCCESS[✅ Build Complete<br/>~84s core + LLM time]
    
    STAGE2 -->|Fail| FAIL[❌ Pipeline Failed]
    STAGE3 -->|Fail| FAIL
    STAGE4 -->|Fail| FAIL
    STAGE5 -->|Fail| FAIL
    STAGE6 -->|Fail| FAIL
    STAGE7 -->|Fail| FAIL
    STAGE8 -->|Skip| STAGE9[Graceful degradation]
    STAGE9 -->|Skip| SUCCESS[Optional stages skipped]
    
    FAIL --> END([Exit with error])
    SUCCESS --> END
    
    classDef success fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef failure fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef optional fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class SUCCESS success
    class FAIL failure
    class STAGE0,STAGE1,STAGE2,STAGE3,STAGE4,STAGE5,STAGE6,STAGE7 process
    class STAGE8,STAGE9 optional
```

### Entry Point 2: Core Pipeline (`python3 scripts/run_all.py`)

**6-stage core pipeline** (stages 00-05) without LLM dependencies:

| Stage | Script | Purpose |
|-------|--------|---------|
| 00 | `00_setup_environment.py` | Environment setup & validation |
| 01 | `01_run_tests.py` | Run complete test suite (infrastructure + project) |
| 02 | `02_run_analysis.py` | Discover & run `project/scripts/` |
| 03 | `03_render_pdf.py` | PDF rendering orchestration |
| 04 | `04_validate_output.py` | Output validation & reporting |
| 05 | `05_copy_outputs.py` | Copy final deliverables to `output/` |

**Stage Numbering:**
- `./run.sh`: Stages 0-9 (10 total). Stage 0 is cleanup (not tracked in progress), stages 1-9 are displayed as [1/9] to [9/9] in logs
- `run_all.py`: Stages 00-05 (zero-padded Python convention, 6 core stages)

**See [RUN_GUIDE.md](RUN_GUIDE.md) for complete pipeline documentation.**

## 📚 Complete Documentation Index

### Core Documentation (Essential Reading)
- **[AGENTS.md](AGENTS.md)** - Complete system reference - Everything you need to know
- **[docs/HOW_TO_USE.md](docs/HOW_TO_USE.md)** - Complete usage guide from basic to advanced (12 skill levels)
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and architecture overview
- **[docs/WORKFLOW.md](docs/WORKFLOW.md)** - Development workflow and best practices
- **[docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** - Complete documentation index

### Getting Started
- **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Complete beginner's guide (Levels 1-3)
- **[docs/QUICK_START_CHEATSHEET.md](docs/QUICK_START_CHEATSHEET.md)** - One-page command reference
- **[docs/COMMON_WORKFLOWS.md](docs/COMMON_WORKFLOWS.md)** - Step-by-step recipes for common tasks
- **[docs/TEMPLATE_DESCRIPTION.md](docs/TEMPLATE_DESCRIPTION.md)** - Template overview and features
- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Usage examples and customization patterns
- **[docs/EXAMPLES_SHOWCASE.md](docs/EXAMPLES_SHOWCASE.md)** - Real-world usage examples across domains
- **[docs/FAQ.md](docs/FAQ.md)** - Frequently asked questions and solutions

### Build System & Quality
- **[docs/BUILD_SYSTEM.md](docs/BUILD_SYSTEM.md)** - Complete build system reference (status, performance, fixes)
- **[docs/PDF_VALIDATION.md](docs/PDF_VALIDATION.md)** - PDF quality validation system

### Development & Architecture
- **[docs/THIN_ORCHESTRATOR_SUMMARY.md](docs/THIN_ORCHESTRATOR_SUMMARY.md)** - Thin orchestrator pattern implementation
- **[docs/MARKDOWN_TEMPLATE_GUIDE.md](docs/MARKDOWN_TEMPLATE_GUIDE.md)** - Markdown writing and cross-referencing guide
- **[.cursorrules/manuscript_style.md](.cursorrules/manuscript_style.md)** - Manuscript formatting standards and best practices
- **[docs/MANUSCRIPT_NUMBERING_SYSTEM.md](docs/MANUSCRIPT_NUMBERING_SYSTEM.md)** - Section organization system

### Community & Contribution
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines and process
- **[docs/CODE_OF_CONDUCT.md](docs/CODE_OF_CONDUCT.md)** - Community standards and behavior
- **[docs/SECURITY.md](docs/SECURITY.md)** - Security policy and vulnerability reporting
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Development roadmap and future plans

### Reference & Resources
- **[docs/COPYPASTA.md](docs/COPYPASTA.md)** - Shareable content for promoting the template
- **[project/manuscript/preamble.md](project/manuscript/preamble.md)** - LaTeX preamble and styling configuration
- **[docs/TEST_IMPROVEMENTS_SUMMARY.md](docs/TEST_IMPROVEMENTS_SUMMARY.md)** - Testing enhancements and standards

### Directory-Specific Documentation
- **[infrastructure/AGENTS.md](infrastructure/AGENTS.md)** - Infrastructure layer documentation
- **[infrastructure/README.md](infrastructure/README.md)** - Infrastructure quick reference
- **[tests/AGENTS.md](tests/AGENTS.md)** - Testing philosophy and guide
- **[tests/README.md](tests/README.md)** - Testing quick reference
- **[scripts/AGENTS.md](scripts/AGENTS.md)** - Entry point orchestrators documentation
- **[scripts/README.md](scripts/README.md)** - Entry points quick reference
- **[project/src/AGENTS.md](project/src/AGENTS.md)** - Project code documentation
- **[project/src/README.md](project/src/README.md)** - Project code quick reference
- **[project/scripts/AGENTS.md](project/scripts/AGENTS.md)** - Project scripts documentation
- **[project/scripts/README.md](project/scripts/README.md)** - Project scripts quick reference
- **[project/manuscript/AGENTS.md](project/manuscript/AGENTS.md)** - Manuscript structure guide
- **[project/manuscript/README.md](project/manuscript/README.md)** - Manuscript quick reference
- **[docs/AGENTS.md](docs/AGENTS.md)** - Documentation organization guide
- **[docs/README.md](docs/README.md)** - Documentation quick reference

### Advanced Modules
- **[docs/ADVANCED_MODULES_GUIDE.md](docs/ADVANCED_MODULES_GUIDE.md)** - Comprehensive guide for all advanced modules
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API documentation for all modules
- **[infrastructure/build/quality_checker.py](infrastructure/build/quality_checker.py)** - Document quality analysis and metrics
- **[infrastructure/build/reproducibility.py](infrastructure/build/reproducibility.py)** - Build reproducibility and environment tracking
- **[infrastructure/validation/integrity.py](infrastructure/validation/integrity.py)** - File integrity and cross-reference validation
- **[infrastructure/publishing/core.py](infrastructure/publishing/core.py)** - Academic publishing workflow tools
- **[infrastructure/scientific/](infrastructure/scientific/)** - Scientific computing best practices (modular: stability, benchmarking, documentation, validation, templates)
- **[infrastructure/build/build_verifier.py](infrastructure/build/build_verifier.py)** - Build process validation and verification

### Scientific Computing Modules
- **[docs/SCIENTIFIC_SIMULATION_GUIDE.md](docs/SCIENTIFIC_SIMULATION_GUIDE.md)** - Scientific simulation and analysis system guide
- **[docs/VISUALIZATION_GUIDE.md](docs/VISUALIZATION_GUIDE.md)** - Visualization system for publication-quality figures
- **[docs/IMAGE_MANAGEMENT.md](docs/IMAGE_MANAGEMENT.md)** - Image insertion, captioning, and cross-referencing guide
- **Data Processing** (`project/src/`): `data_generator.py`, `data_processing.py`, `statistics.py`, `metrics.py`, `validation.py`
- **Visualization** (`project/src/` + `infrastructure/documentation/`): `visualization.py`, `plots.py`, `figure_manager.py`, `image_manager.py`, `markdown_integration.py`
- **Simulation** (`project/src/`): `simulation.py`, `parameters.py`, `performance.py`, `reporting.py`

### Operational Guides
- **[docs/DEPENDENCY_MANAGEMENT.md](docs/DEPENDENCY_MANAGEMENT.md)** - Complete guide for uv package manager
- **[docs/PERFORMANCE_OPTIMIZATION.md](docs/PERFORMANCE_OPTIMIZATION.md)** - Build time optimization and caching strategies
- **[docs/CI_CD_INTEGRATION.md](docs/CI_CD_INTEGRATION.md)** - GitHub Actions and CI/CD integration guide
- **[docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md)** - Comprehensive troubleshooting guide

### Best Practices & Reference
- **[docs/BEST_PRACTICES.md](docs/BEST_PRACTICES.md)** - Consolidated best practices compilation
- **[docs/VERSION_CONTROL.md](docs/VERSION_CONTROL.md)** - Git workflows and version control best practices
- **[docs/MULTI_PROJECT_MANAGEMENT.md](docs/MULTI_PROJECT_MANAGEMENT.md)** - Managing multiple projects using the template
- **[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** - Step-by-step migration from other templates
- **[docs/BACKUP_RECOVERY.md](docs/BACKUP_RECOVERY.md)** - Backup strategies and recovery procedures

## 🤝 Contributing

**[Complete contribution guide](docs/CONTRIBUTING.md)** | **[Code of conduct](docs/CODE_OF_CONDUCT.md)** | **[Roadmap](docs/ROADMAP.md)**

We welcome contributions! To contribute:

1. Ensure all tests pass with coverage requirements met - [Testing Guide](tests/AGENTS.md)
2. Follow the established project structure - [Architecture](docs/ARCHITECTURE.md)
3. Add tests for new functionality - [Workflow](docs/WORKFLOW.md)
4. Update documentation as needed - [Documentation Guide](docs/AGENTS.md)
5. **Maintain thin orchestrator pattern** - scripts use src/ methods - [Pattern Guide](docs/THIN_ORCHESTRATOR_SUMMARY.md)

**Recent Improvements:**
- Build system optimizations - [Details](docs/BUILD_SYSTEM.md#historical-fixes)
- Test suite enhancements - [Details](docs/TEST_IMPROVEMENTS_SUMMARY.md)
- Simplified directory structure with markdown/ elimination

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## 📚 Citation

If you use this template in your research, please cite:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16903352.svg)](https://doi.org/10.5281/zenodo.16903352)

Archived as `docxology/template` 0.3 — DOI `10.5281/zenodo.16903351` (https://zenodo.org/records/17857724).

**BibTeX:**
```bibtex
@software{friedman_daniel_ari_2025_16903352,
  author       = {Daniel Ari Friedman},
  title        = {docxology/template: 0.1},
  month        = aug,
  year         = 2025,
  publisher    = {Zenodo},
  version      = {0.1},
  doi          = {10.5281/zenodo.16903352},
  url          = {https://doi.org/10.5281/zenodo.16903352}
}
```

**Plain text:**
Daniel Ari Friedman. (2025). docxology/template: 0.1 (0.1). Zenodo. https://doi.org/10.5281/zenodo.16903352

## 🆘 Troubleshooting

**[Complete troubleshooting guide](docs/TROUBLESHOOTING_GUIDE.md)** | **[FAQ](docs/FAQ.md)** | **[Build System](docs/BUILD_SYSTEM.md)**

### Common Issues

- **Tests Fail**: Ensure coverage requirements met and all tests pass - [Testing Guide](tests/AGENTS.md) | [Test Improvements](docs/TEST_IMPROVEMENTS_SUMMARY.md)
- **Scripts Fail**: Check Python dependencies and error handling - [Script Guide](scripts/AGENTS.md)
- **PDF Generation Fails**: Verify pandoc and xelatex installation - [Build System](docs/BUILD_SYSTEM.md#troubleshooting)
- **Coverage Below 100%**: Add tests for uncovered code - [Workflow](docs/WORKFLOW.md)
- **Build System Issues**: Check recent fixes - [Build System](docs/BUILD_SYSTEM.md#historical-fixes)
- **PDF Quality Issues**: Run validation - [PDF Validation](docs/PDF_VALIDATION.md)
- **Reference Issues**: Check markdown validation - [Markdown Guide](docs/MARKDOWN_TEMPLATE_GUIDE.md)

### Getting Help

- Check the **[FAQ](docs/FAQ.md)** for common questions and solutions
- Review the **[Build System](docs/BUILD_SYSTEM.md)** for system status
- Review the **[scripts/README.md](scripts/README.md)** for entry point information
- Review the test output for specific error messages
- Ensure all required dependencies are installed
- See **[DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)** for complete reference

### Debug Resources

- **Build System**: [BUILD_SYSTEM.md](docs/BUILD_SYSTEM.md) - Complete reference (performance, status, fixes)
- **PDF Quality**: [PDF_VALIDATION.md](docs/PDF_VALIDATION.md)

## 🔄 Migration from Other Projects

To adapt this template for your existing project:

1. Copy the `infrastructure/` and `scripts/` directories to your project
2. Adapt the `project/src/`, `project/tests/`, and `project/scripts/` structure
3. Update manuscript markdown files to match the expected format - [Markdown Guide](docs/MARKDOWN_TEMPLATE_GUIDE.md)
4. Set appropriate environment variables for your project - [Configuration](AGENTS.md#configuration-system)
5. Run the entry points to validate the setup - [Scripts Guide](scripts/AGENTS.md)

**See [EXAMPLES.md](docs/EXAMPLES.md) for project customization patterns.**

## 🏗️ Architecture Benefits

**[Complete architecture guide](docs/ARCHITECTURE.md)** | **[Thin orchestrator pattern](docs/THIN_ORCHESTRATOR_SUMMARY.md)**

The thin orchestrator pattern provides:

- **Maintainability**: Single source of truth for business logic
- **Testability**: Fully tested core functionality (99.88% project coverage)
- **Reusability**: Scripts can use any module's methods
- **Clarity**: Clear separation of concerns
- **Quality**: Automated validation of the entire system
- **Performance**: 84-second build time for complete regeneration (without optional LLM review)
- **Reliability**: 2175 tests passing (100% success rate)

**System Status**: ✅ **FULLY OPERATIONAL** - [Build System](docs/BUILD_SYSTEM.md)

---

## 🎯 Quick Links by User Type

### New Users
- [Quick Start Guide](#quick-start)
- [Getting Started Guide](docs/GETTING_STARTED.md) - Beginner's guide
- [Quick Start Cheatsheet](docs/QUICK_START_CHEATSHEET.md) - Command reference
- [Common Workflows](docs/COMMON_WORKFLOWS.md) - Step-by-step recipes
- [How To Use (Complete)](docs/HOW_TO_USE.md)
- [Examples Showcase](docs/EXAMPLES_SHOWCASE.md)
- [FAQ](docs/FAQ.md)

### Developers
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Thin Orchestrator Pattern](docs/THIN_ORCHESTRATOR_SUMMARY.md)
- [Development Workflow](docs/WORKFLOW.md)
- [Manuscript Style Guide](.cursorrules/manuscript_style.md)
- [Build System](docs/BUILD_SYSTEM.md)

### Contributors
- [Contributing Guidelines](docs/CONTRIBUTING.md)
- [Code of Conduct](docs/CODE_OF_CONDUCT.md)
- [Development Roadmap](docs/ROADMAP.md)
- [Test Improvements](docs/TEST_IMPROVEMENTS_SUMMARY.md)

### Advanced Users
- [Complete System Reference](AGENTS.md)
- [Build System](docs/BUILD_SYSTEM.md)
- [PDF Validation](docs/PDF_VALIDATION.md)
- [Documentation Index](docs/DOCUMENTATION_INDEX.md)

---

**Happy coding and writing! 🎉**

**Need help?** Start with **[How To Use Guide](docs/HOW_TO_USE.md)** or check the **[FAQ](docs/FAQ.md)**

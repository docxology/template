# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a research project template with a test-driven development workflow, automated PDF generation, and multi-project support. It uses a two-layer architecture separating generic infrastructure (Layer 1) from project-specific code (Layer 2), following a thin orchestrator pattern.

## Quick Reference

| Task | Command |
|------|---------|
| Interactive menu | `./run.sh` |
| Full pipeline | `./run.sh --pipeline` |
| Core pipeline (no LLM) | `python3 scripts/execute_pipeline.py --project {name} --core-only` |
| All tests | `python3 scripts/01_run_tests.py --project {name}` |
| Single test | `uv run pytest path/to/test.py::test_function -v` |
| Install deps | `uv sync` |

## Common Commands

### Pipeline Execution
```bash
# Interactive menu (recommended)
./run.sh

# Full pipeline (10 stages: clean, setup, infra tests, project tests, analysis, render, validate, LLM review, LLM translations, copy)
./run.sh --pipeline

# Core pipeline only (8 stages: no LLM)
python3 scripts/execute_pipeline.py --project {project_name} --core-only

# Resume from checkpoint
./run.sh --pipeline --resume
```

### Testing
```bash
# Run all tests (infrastructure + project)
python3 scripts/01_run_tests.py --project {project_name}

# Infrastructure tests only (60% coverage minimum)
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-fail-under=60

# Project tests only (90% coverage minimum)
uv run pytest projects/{project_name}/tests/ --cov=projects/{project_name}/src --cov-fail-under=90

# Run specific test file
uv run pytest tests/infra_tests/test_specific.py -v

# Run single test function
uv run pytest tests/infra_tests/test_specific.py::test_function_name -v

# Coverage files are isolated per suite (.coverage.infra, .coverage.project)
```

### Development Tools
```bash
# Install dependencies
uv sync

# Workspace management
uv run python scripts/manage_workspace.py status
uv run python scripts/manage_workspace.py add <package> --project <name>

# Linting and type checking
uv run mypy infrastructure/ projects/code_project/src/
uv run bandit -r infrastructure/

# Validate markdown
python3 -m infrastructure.validation.cli markdown projects/{project_name}/manuscript/

# Validate PDFs
python3 -m infrastructure.validation.cli pdf output/{project_name}/pdf/

# Generate API documentation
python3 -m infrastructure.documentation.generate_glossary_cli --project {project_name}
```

### Multi-Project Operations
```bash
# Run all projects with full pipeline
./run.sh --all-projects --pipeline

# Run all projects with core pipeline only
python3 scripts/execute_multi_project.py --no-llm

# List available projects
python3 -c "from infrastructure.project.discovery import discover_projects; from pathlib import Path; print([p.name for p in discover_projects(Path('.'))])"
```

**Active projects:** `code_project`, `blake_active_inference`
**Archived projects:** Located in `projects_archive/` (not executed by pipeline)

## Architecture

### Two-Layer System

**Layer 1: Infrastructure (Generic, Reusable)**
- `infrastructure/` - Generic build and validation tools
- `scripts/` - Entry point orchestrators (00-07)
- `tests/` - Infrastructure test suite

**Layer 2: Projects (Domain-Specific)**
- `projects/{name}/src/` - Project-specific algorithms and code
- `projects/{name}/tests/` - Project test suite
- `projects/{name}/scripts/` - Analysis scripts (thin orchestrators)
- `projects/{name}/manuscript/` - Markdown manuscript sections
- `projects/{name}/output/` - Working outputs (disposable)
- `output/{name}/` - Final deliverables

### Thin Orchestrator Pattern

**CRITICAL PRINCIPLE**: All business logic resides in either `infrastructure/` (generic) or `projects/{name}/src/` (project-specific). Scripts are lightweight coordinators that:

1. Import methods from infrastructure or project modules
2. Handle I/O, visualization, and orchestration
3. Never implement algorithms or business logic
4. Use tested methods for all computation

**Example**:
```python
# BAD: Logic in script
def calculate_average(data):
    return sum(data) / len(data)

# GOOD: Script imports from src/
from projects.code_project.src.statistics import calculate_average

data = [1, 2, 3, 4, 5]
avg = calculate_average(data)  # Use tested method
```

### Infrastructure Modules

- `infrastructure/core/` - Core utilities (logging, config, exceptions, file operations, pipeline)
- `infrastructure/validation/` - PDF and markdown validation, output validation
- `infrastructure/rendering/` - Multi-format rendering (PDF, HTML, slides)
- `infrastructure/documentation/` - Figure management, API docs, glossary generation
- `infrastructure/publishing/` - Academic publishing tools (DOI, citations, Zenodo, arXiv)
- `infrastructure/llm/` - Local LLM integration (Ollama) for reviews and translations
- `infrastructure/scientific/` - Scientific computing best practices
- `infrastructure/reporting/` - Pipeline reporting and error aggregation
- `infrastructure/project/` - Multi-project discovery and management

## Project Structure

### Active vs Archived Projects

- **`projects/`** - Active projects (discovered and executed by infrastructure)
- **`projects_archive/`** - Archived projects (preserved but not executed)

**Current active projects:** `code_project`, `blake_active_inference`

To archive: `mv projects/{name}/ projects_archive/{name}/`
To reactivate: `mv projects_archive/{name}/ projects/{name}/`

### Standard Project Layout
```
projects/{project_name}/
├── src/                    # Project-specific code (100% test coverage target)
│   ├── __init__.py
│   └── *.py               # Domain algorithms and logic
├── tests/                  # Project test suite (90% coverage minimum)
│   ├── __init__.py
│   └── test_*.py
├── scripts/                # Analysis scripts (thin orchestrators)
│   └── *.py
├── manuscript/             # Markdown manuscript sections
│   ├── config.yaml        # Project metadata
│   ├── preamble.md        # LaTeX preamble
│   ├── 01_*.md            # Main sections
│   ├── S01_*.md           # Supplemental sections
│   └── 99_references.md
├── output/                 # Working outputs (disposable)
└── pyproject.toml          # Project configuration
```

### Output Organization
```
output/
├── {project_name}/         # Project-specific outputs
│   ├── pdf/               # Individual + combined PDFs
│   ├── figures/           # Generated figures
│   ├── data/              # Analysis data files
│   ├── llm/               # LLM reviews and translations
│   └── reports/           # Validation reports
└── executive_summary/      # Cross-project reports (multi-project mode)
```

## Pipeline Stages

### Core Pipeline (8 stages)
1. **Clean Output Directories** - Remove previous outputs for a fresh run
2. **Setup Environment** - Validate dependencies, discover projects
3. **Infrastructure Tests** - Run infrastructure test suite (may be skipped)
4. **Project Tests** - Project test suite (90% coverage minimum)
5. **Run Analysis** - Execute `projects/{name}/scripts/` to generate figures/data
6. **Render PDF** - Convert markdown to professional PDFs
7. **Validate Output** - Quality checks on PDFs and content
8. **Copy Outputs** - Copy final deliverables to `output/<name>/`

### Extended Pipeline (Stages 9-10, Optional)
9. **LLM Scientific Review** - Requires Ollama (executive summary, quality review, methodology review, improvement suggestions)
10. **LLM Translations** - Multi-language abstract translations (configure in `config.yaml`)

**Note:** Executive Report (cross-project metrics and dashboards) runs automatically in multi-project mode when 2+ projects are executed.

## Testing Requirements

### No Mocks Policy
**ABSOLUTE REQUIREMENT**: Never use `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework. All tests must use data and computations.

**Patterns**:
- HTTP testing: Use `pytest-httpserver` for local test servers
- CLI testing: Execute subprocess commands
- PDF testing: Create PDFs with `reportlab`
- File operations: Use real temp files with `tmp_path` fixture

### Coverage Requirements
- **Infrastructure**: 60% minimum (currently 83.33%)
- **Projects**: 90% minimum (currently varies by project)
- **No mocks**: All tests use real numerical examples
- **Deterministic**: Fixed RNG seeds for reproducibility

### Running Tests
```bash
# All tests
python3 scripts/01_run_tests.py --project {project_name}

# With coverage report
uv run pytest tests/infra_tests/ --cov=infrastructure --cov-report=html
uv run pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-report=html

# Specific test
uv run pytest tests/infra_tests/test_specific.py::test_function -v
```

## Configuration

### Project Metadata (`projects/{name}/manuscript/config.yaml`)
```yaml
paper:
  title: "Your Research Title"
  version: "1.0"

authors:
  - name: "Author Name"
    orcid: "0000-0000-0000-0000"
    email: "author@example.com"
    affiliation: "Institution"
    corresponding: true

publication:
  doi: "10.5281/zenodo.12345678"  # Optional

keywords:
  - "keyword1"
  - "keyword2"

llm:
  translations:
    enabled: true
    languages: [zh, hi, ru]
```

### Environment Variables
- `LOG_LEVEL` - Logging verbosity (0=DEBUG, 1=INFO, 2=WARN, 3=ERROR)
- `AUTHOR_NAME` - Override config file author
- `PROJECT_TITLE` - Override config file title
- `MPLBACKEND=Agg` - Headless matplotlib (automatically set)

### IDE Integration
```bash
# Set Python path for IDE/editor integration
export PYTHONPATH=".:infrastructure:projects/code_project/src"
```

## Development Workflow

### Adding Features
1. Write tests first (TDD) in `projects/{name}/tests/` or `tests/infra_tests/`
2. Implement in `projects/{name}/src/` or `infrastructure/`
3. Ensure coverage requirements met
4. Update documentation if needed
5. Run full pipeline to validate

### Creating New Projects
```bash
# Create project structure
mkdir -p projects/my_project/{src,tests,scripts,manuscript}
touch projects/my_project/src/__init__.py
touch projects/my_project/tests/__init__.py

# Copy config template
cp projects/code_project/manuscript/config.yaml projects/my_project/manuscript/

# Create pyproject.toml (see existing projects for template)

# Run pipeline
./run.sh --project my_project --pipeline
```

### Working with Scripts
Scripts in `projects/{name}/scripts/` should:
- Import from `projects/{name}/src/` for computation
- Import from `infrastructure/` for utilities
- Handle only I/O, visualization, and orchestration
- Print output paths to stdout for manifest collection
- Use `MPLBACKEND=Agg` for headless plotting
- Generate deterministic outputs with fixed seeds

## Key Architectural Principles

1. **Single Source of Truth**: Business logic lives only in `infrastructure/` or `projects/{name}/src/`
2. **Test-Driven Development**: 90%+ coverage enforced before PDF generation
3. **Thin Orchestrator Pattern**: Scripts coordinate, modules implement
4. **No Mocks**: All tests use data and computations
5. **Multi-Project Support**: One repository, multiple independent projects
6. **Reproducibility**: Deterministic outputs with fixed seeds
7. **Disposable Outputs**: Everything in `output/` is regeneratable

## Common Patterns

### Adding a New Analysis Script
```python
#!/usr/bin/env python3
"""Analysis script following thin orchestrator pattern."""

from pathlib import Path
from projects.my_project.src.analysis import run_analysis
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def main():
    output_dir = Path("projects/my_project/output/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use project methods for computation
    results = run_analysis()  # From src/

    # Script handles visualization only
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(results)
    output_path = output_dir / "analysis.png"
    plt.savefig(output_path)

    # Print path for manifest collection
    print(str(output_path))

if __name__ == "__main__":
    main()
```

### Adding a Test
```python
#!/usr/bin/env python3
"""Test following no-mocks policy."""

import pytest
from pathlib import Path
from projects.my_project.src.analysis import run_analysis

def test_analysis_produces_correct_output(tmp_path):
    """Test with data and computation."""
    # Use data
    input_data = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Execute computation
    result = run_analysis(input_data)

    # Validate real output
    assert len(result) == 5
    assert abs(result[0] - 1.0) < 1e-6
```

### Adding Infrastructure Module
```python
#!/usr/bin/env python3
"""New infrastructure module.

All infrastructure modules must:
1. Have docstrings
2. Include type hints on all public APIs
3. Be generic and reusable across projects
4. Have 60%+ test coverage
"""

from pathlib import Path
from typing import List

def process_files(input_dir: Path) -> List[Path]:
    """Process files in directory.

    Args:
        input_dir: Directory containing files to process

    Returns:
        List of processed file paths
    """
    # Implementation
    pass
```

## Troubleshooting

### Common Issues

**Tests Failing**: Check coverage requirements met (60% infra, 90% project)
```bash
pytest --cov=infrastructure --cov-report=term-missing
```

**PDF Generation Fails**: Validate LaTeX packages
```bash
python3 -m infrastructure.rendering.latex_package_validator
sudo tlmgr install multirow cleveref doi newunicodechar
```

**Import Errors**: Ensure project structure correct
```bash
python3 -c "import sys; sys.path.insert(0, 'projects/{name}/src'); import {module}"
```

**Markdown Validation Errors**: Check image paths and references
```bash
python3 -m infrastructure.validation.cli markdown projects/{name}/manuscript/
```

### Debug Mode
```bash
export LOG_LEVEL=0  # Enable debug logging
python3 scripts/03_render_pdf.py --project {name}
```

## Documentation Resources

- **README.md** - Project overview and quick start
- **AGENTS.md** - System reference (configuration, modules, troubleshooting details)
- **RUN_GUIDE.md** - Pipeline execution documentation
- **docs/core/ARCHITECTURE.md** - Detailed architecture guide
- **docs/core/WORKFLOW.md** - Development workflow details
- **docs/core/HOW_TO_USE.md** - Usage guide (12 skill levels)
- **docs/DOCUMENTATION_INDEX.md** - Index of all 89+ documentation files

## Important Notes

- All files in `output/` are disposable and regeneratable
- Never commit generated outputs to version control
- Always run tests before committing changes
- Follow thin orchestrator pattern strictly
- No mocks allowed in tests (use `pytest-httpserver` for HTTP, real files for I/O)
- Maintain 90%+ test coverage for project code, 60%+ for infrastructure
- Use `uv` for dependency management (recommended)
- Pipeline can be resumed from checkpoints with `--resume`
- Tests timeout after 10 seconds by default (configurable in pyproject.toml)

# Projects Directory

This directory contains multiple **standalone research projects**, each with independent source code, tests, analysis scripts, and manuscripts. Each project operates completely independently while being executed, tested, and rendered by the overarching **[docxology/template](https://github.com/docxology/template/)** infrastructure.

## Active Projects

Directories under `projects/` **change over time** (promotion, archiving, or moving to `projects_in_progress/`). The set guaranteed to remain as **permanent canonical exemplars** is:

- [`template_code_project/`](template_code_project/) — code-centric exemplar (numerical optimization, dashboards, JSON-backed invariants)
- [`template_prose_project/`](template_prose_project/) — prose-centric exemplar (editorial review, BibTeX validation, readability metrics)

Both are **standalone** projects with the same directory layout (`src/`, `tests/`, `scripts/`, `manuscript/`, `docs/`, `output/`), the same 12-file `docs/` hub (agent_instructions, architecture, testing_philosophy, rendering_pipeline, style_guide, syntax_guide, faq, quickstart, troubleshooting, output_conventions, plus `AGENTS.md` and `README.md`), and the same verification commands. The optional `template_search_project` literature-search exemplar is **local-only** — it lives at [`projects_archive/template_search_project/`](../projects_archive/template_search_project/) and is **not git-tracked**. This is a public repo: only the two canonical exemplars are tracked; copy `template_search_project` under `projects/` *locally* to exercise literature-search workflows, but never commit it (`scripts/check_tracked_projects.py` blocks any non-template project in pre-push + CI). Examples in this documentation default to `projects/template_code_project/` unless a doc explicitly compares projects.

**Current** names from `discover_projects()` are listed in [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md) (regenerate after layout changes).

### The permanent exemplars at a glance

| Exemplar | Purpose | Algorithm? | Mutates `references.bib`? | Embeds figures? | Tests | Coverage |
|---|---|---|---|---|---|---|
| [`template_code_project`](template_code_project/) | Numerical experiment + analysis dashboard | yes (`src/optimizer.py`, `src/invariants.py`) | no (curated) | yes (6 figures) | see canonical facts | see canonical facts |
| [`template_prose_project`](template_prose_project/) | Editorial review (readability + structure + bibliography) | no | no (read-only validation) | no (3 diagnostic PNGs in review report) | see canonical facts | see canonical facts |

The measured test and coverage totals drift as the exemplars evolve; confirm
current numbers in
[`docs/_generated/canonical_facts.md`](../docs/_generated/canonical_facts.md).
The two permanent exemplars cover the computational and prose-review paths. Use
the archived search exemplar when the project needs literature discovery,
auto-populated BibTeX, or optional LLM synthesis. **Important:** run each
project's `tests/` in **its own** `pytest` invocation — pointing pytest at
`projects/*/tests/` simultaneously triggers `ImportPathMismatchError` because
every project ships a `tests/conftest.py`.

Additional siblings under `projects/` today are real projects for this
checkout, not permanent fixtures. They are usually symlinks from the sibling
private lifecycle repo at `/Users/4d/Documents/GitHub/projects/active/`; inspect
planned syncs with
`uv run python -m infrastructure.orchestration link-projects --dry-run`.

### In-progress projects (under `projects_in_progress/`)

These are actively being developed under [`projects_in_progress/`](../projects_in_progress/) but are not yet pipeline-ready. The roster is deliberately not copied here; use `ls projects_in_progress/` for the current checkout and [`docs/_generated/active_projects.md`](../docs/_generated/active_projects.md) for projects actually discovered by `./run.sh`.

**Note:** Use `projects/template_code_project/` for concrete paths, commands, and layout examples unless a document explicitly compares project shapes. Promote projects from `projects_in_progress/` or `projects_archive/` to `projects/` when they are ready for pipeline execution.

### Archived exemplars (not in `projects/`)

Preserved under [`projects_archive/`](../projects_archive/) until moved back; the pipeline does not discover them. See [`projects_archive/README.md`](../projects_archive/README.md) and [`docs/_generated/canonical_facts.md`](../docs/_generated/canonical_facts.md) for the current roster — do not hard-code names here.

## Standalone Project Paradigm

Each project in `projects/` is **completely self-contained** with three critical guarantees:

### 🔒 **Tests**: Independent Test Suites

- Each project has its own `tests/` directory with 90%+ coverage requirement
- Tests use data only (no mocks policy)
- Tests import from `projects/{name}/src/` and `infrastructure/`
- Can be run independently: `pytest projects/{name}/tests/`

### 🧠 **Methods**: Business Logic Isolation

- All research algorithms in `projects/{name}/src/`
- No cross-project imports or dependencies
- Can import from `infrastructure/` modules for shared utilities
- Scripts in `projects/{name}/scripts/` are thin orchestrators

### 📝 **Manuscript**: Independent Content

- Each project has its own `manuscript/` directory
- Independent config.yaml, references.bib, and markdown sections
- Rendered independently via infrastructure.rendering
- Own publication metadata and cross-references

## Active vs Archived Projects

### 📁 **Project Organization**

The template distinguishes between **active projects** and **archived projects**:

#### ✅ **Active Projects (`projects/`)**

Projects in the `projects/` directory are **actively discovered and executed** by infrastructure:

- **Discovered** by `infrastructure.project.discovery.discover_projects()`
- **Listed** in `run.sh` interactive menu for selection
- **Executed** by all pipeline scripts (`01_run_tests.py`, `02_run_analysis.py`, etc.)
- **Rendered** independently with project-specific manuscripts
- **Outputs** organized in `projects/{name}/output/` and `output/{name}/`

#### 📦 **Archived Projects (`projects_archive/`)**

Projects in the `projects_archive/` directory are **preserved but not executed**:

- **NOT discovered** by infrastructure discovery functions
- **NOT listed** in `run.sh` menu
- **NOT executed** by any pipeline scripts
- **Preserved** for historical reference and potential reactivation

```bash
# Move project to archive
mv projects/myproject projects_archive/myproject

# Move project back to active
mv projects_archive/myproject projects/myproject

# Project will be automatically discovered on next run.sh execution
```

For confidential work, prefer the sibling private lifecycle repo:
`/Users/4d/Documents/GitHub/projects/active/` is linked into this directory,
while `passive/` and `archive/` remain unlinked. Move private work between those
folders instead of committing it here.

| Directory            | Role                      | Tests | Coverage |
|----------------------|---------------------------|-------|----------|
| `template_code_project/`    | Code-centric exemplar (optimization + dashboard) | see canonical facts | see canonical facts |
| `template_prose_project/`   | Prose-centric exemplar (review + BibTeX validation) | see canonical facts | see canonical facts |

The two permanent exemplars share the same `docs/` hub structure (12 files: `AGENTS.md`, `README.md`, `agent_instructions.md`, `architecture.md`, `testing_philosophy.md`, `rendering_pipeline.md`, `style_guide.md`, `syntax_guide.md`, `faq.md`, `quickstart.md`, `output_conventions.md`, `troubleshooting.md`) and the same per-directory `AGENTS.md` + `README.md` convention.

**Private active projects** live in `/Users/4d/Documents/GitHub/projects/active/`
and are linked into this directory automatically by `run.sh`/orchestration.
Set `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root` to use another
private repo; set `TEMPLATE_SKIP_LINK_SYNC=1` to skip one auto-sync.
**In-progress projects** live in `projects_in_progress/`.
**Archived projects** live in `projects_archive/`.

```mermaid
graph TD
    subgraph projects["projects/ - Multi-Project Container"]
        PROJ[template_code_project/<br/>The Master Exemplar]
        CUSTOM[your_project/<br/>Custom research<br/>Your algorithms here]

        PROJ --> PROJ_SRC[src/<br/>Pure scientific logic]
        PROJ --> PROJ_TESTS[tests/<br/>Zero-mock test suite]
        PROJ --> PROJ_SCRIPTS[scripts/<br/>Thin orchestrators]
        PROJ --> PROJ_MANUSCRIPT[manuscript/<br/>Research paper]
        PROJ --> PROJ_DOCS[docs/<br/>Modular documentation]
        PROJ --> PROJ_OUTPUT[output/<br/>Generated outputs<br/>Disposable]
        PROJ --> PROJ_CONFIG[pyproject.toml<br/>Project metadata]
    end

    subgraph Infrastructure["🔧 Shared Infrastructure"]
        INFRA[infrastructure/<br/>Generic tools<br/>Reusable across projects]
        SCRIPTS_ROOT[scripts/<br/>Entry points<br/>Orchestrate pipeline]
        VALIDATION[validation/<br/>Quality assurance<br/>PDF/markdown checks]
        RENDERING[rendering/<br/>Multi-format output<br/>PDF/HTML generation]
        REPORTING[reporting/<br/>Pipeline metrics<br/>Error aggregation]
    end

    subgraph Compliance["Template standards"]
        STANDARDS[Root .cursorrules + docs/rules/<br/>Development norms<br/>Testing · docs · style]
        RULEFILES[testing_standards.md<br/>documentation_standards.md<br/>under docs/rules/]
    end

    PROJ -->|Validated by| VALIDATION
    PROJ -->|Rendered by| RENDERING
    PROJ -->|Reported by| REPORTING
    PROJ -->|Discovered by| SCRIPTS_ROOT

    PROJ_SRC -->|Imports from| INFRA
    PROJ_SCRIPTS -->|Imports from| INFRA
    PROJ_SCRIPTS -->|Orchestrated by| SCRIPTS_ROOT

    PROJ -->|Complies with| STANDARDS
    STANDARDS --> RULEFILES

    PROJ_MANUSCRIPT -->|Rendered to| PROJ_OUTPUT

    classDef project fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef infra fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef compliance fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px

    class PROJ,PROJ_SRC,PROJ_TESTS,PROJ_SCRIPTS,PROJ_MANUSCRIPT,PROJ_OUTPUT,PROJ_CONFIG project
    class INFRA,SCRIPTS_ROOT,VALIDATION,RENDERING,REPORTING infra
    class STANDARDS,RULEFILES compliance
```

## Infrastructure Compliance

Each project is **operated upon** by infrastructure modules while maintaining independence:

### 🔍 **Project Discovery** (`infrastructure.project.discovery`)

```python
from infrastructure.project import discover_projects, validate_project_structure

# Automatically discovers all valid projects
projects = discover_projects(Path("."))  # Finds template_code_project, etc.

# Validates project structure
is_valid, message = validate_project_structure(Path("projects/template_code_project"))
# Returns: (True, "Valid project structure")
```

### 🧪 **Test Execution** (`scripts/01_run_tests.py`)

```bash
# Runs project-specific tests with infrastructure orchestration
uv run python scripts/01_run_tests.py --project {name}

# Infrastructure validates structure, then runs:
# pytest projects/{name}/tests/ --cov=projects/{name}/src --cov-fail-under=90
```

### ⚙️ **Analysis Scripts** (`scripts/02_run_analysis.py`)

```bash
# Discovers and executes project scripts
uv run python scripts/02_run_analysis.py --project {name}

# Infrastructure finds and runs:
# projects/{name}/scripts/analysis_pipeline.py
# projects/{name}/scripts/generate_figures.py
```

### 📄 **PDF Rendering** (`scripts/03_render_pdf.py`)

```bash
# Renders project manuscript using infrastructure.rendering
uv run python scripts/03_render_pdf.py --project {name}

# Infrastructure processes:
# projects/{name}/manuscript/*.md -> PDF with figures
```

### ✅ **Quality Validation** (`scripts/04_validate_output.py`)

```bash
# Validates project outputs using infrastructure.validation
uv run python scripts/04_validate_output.py --project {name}

# Checks PDF integrity, markdown references, file integrity
```

### 📋 **Output Management** (`scripts/05_copy_outputs.py`)

```bash
# Organizes final deliverables
uv run python scripts/05_copy_outputs.py --project {name}

# Copies from projects/{name}/output/ to output/{name}/
```

## Project Isolation Principles

### ✅ **Independence**

- **Source Code**: Each project has independent `src/` with unique algorithms
- **Test Suites**: Separate `tests/` directories with project-specific coverage
- **Manuscripts**: Independent `manuscript/` with own content and references
- **Dependencies**: Can specify project-specific requirements in `pyproject.toml`

### ✅ **Shared Infrastructure Access**

- **Import Pattern**: Projects import from `infrastructure/` but not from each other
- **Common Utilities**: Logging, validation, rendering, reporting shared across projects
- **Quality Standards**: Projects align with root **[`.cursorrules`](../.cursorrules)** and **[`docs/rules/`](../docs/rules/)**

### ❌ **No Cross-Project Dependencies**

- Projects cannot import from other projects
- No shared business logic between projects
- Each project maintains its own scientific domain and methodology

## Standards compliance checklist

Every project aligns with the root **[`.cursorrules`](../.cursorrules)** file (Cursor routing) and the guides under **[`docs/rules/`](../docs/rules/)**:

### Testing Standards ([`docs/rules/testing_standards.md`](../docs/rules/testing_standards.md))

- [ ] **90% minimum coverage** for project code (`projects/{name}/src/`)
- [ ] **data only** - No mocks in test suites
- [ ] **integration tests** for critical workflows
- [ ] **Deterministic results** with seeded randomness

### Documentation Standards ([`docs/rules/documentation_standards.md`](../docs/rules/documentation_standards.md))

- [ ] **`AGENTS.md`** in each directory with technical documentation
- [ ] **`README.md`** in each directory with quick reference and Mermaid diagrams
- [ ] **docstrings** with examples for all public APIs
- [ ] **Cross-references** to related documentation sections

### Type Hints Standards ([`docs/rules/type_hints_standards.md`](../docs/rules/type_hints_standards.md))

- [ ] **type annotations** on all public APIs
- [ ] **Generic types** where appropriate (List, Dict, Optional, etc.)
- [ ] **Consistent type hint patterns** across modules

### Error Handling Standards ([`docs/rules/error_handling.md`](../docs/rules/error_handling.md))

- [ ] **Custom exception hierarchy** from `infrastructure.core.exceptions`
- [ ] **Context preservation** with exception chaining
- [ ] **Informative error messages** with actionable guidance

### Logging Standards ([`docs/rules/python_logging.md`](../docs/rules/python_logging.md))

- [ ] **Unified logging** via `infrastructure.core.logging.utils.get_logger(__name__)`
- [ ] **Appropriate log levels** (DEBUG, INFO, WARNING, ERROR)
- [ ] **Context-rich messages** for debugging

### Infrastructure Module Standards ([`docs/rules/infrastructure_modules.md`](../docs/rules/infrastructure_modules.md))

- [ ] **Thin orchestrator pattern** in scripts (import from `src/`, handle I/O only)
- [ ] **Business logic isolation** in `src/` modules
- [ ] **Infrastructure imports** for shared utilities
- [ ] **Domain independence** in imported infrastructure modules

### Code Style Standards ([`docs/rules/code_style.md`](../docs/rules/code_style.md))

- [ ] **Ruff format/check** on CI-scoped paths (`uvx ruff format`, `uvx ruff check`; line length 88 by default)
- [ ] **Descriptive variable names** and clear function signatures
- [ ] **Consistent import organization** (stdlib, third-party, local)
- [ ] **PEP 8 compliance** with template-specific extensions

## Directory Structure

Each project follows this structure:

```mermaid
flowchart TB
    PR[/projects//]
    PR --> CP[/template_code_project/<br/>Master exemplar/]
    PR --> MY[/myresearch/<br/>Custom project 1/]
    PR --> EX[/experiment2/<br/>Custom project 2/]

    CP --> CP_F[src · tests · scripts ·<br/>manuscript · docs · output ·<br/>pyproject.toml]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef pkg fill:#1e3a8a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class PR d
    class CP,MY,EX pkg
    class CP_F f
```

## Creating a New Project

### Option 1: Copy the Template

```bash
# Copy an existing project as a starting point
cp -r projects/template_code_project projects/myresearch

# Customize pyproject.toml
vim projects/myresearch/pyproject.toml

# Update project name and metadata
# name = "myresearch"
# description = "My research project"

# Add your code
vim projects/myresearch/src/mymodule.py

# Write your manuscript
vim projects/myresearch/manuscript/01_introduction.md
```

### Option 2: Manual Creation

```bash
# Create project structure
mkdir -p projects/myresearch/{src,tests,scripts,manuscript}

# Create pyproject.toml
cat > projects/myresearch/pyproject.toml << 'EOF'
[project]
name = "myresearch"
version = "0.1.0"
description = "My research project"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
EOF

# Add initial modules
touch projects/myresearch/src/__init__.py
touch projects/myresearch/src/mymodule.py

# Add initial tests
touch projects/myresearch/tests/__init__.py
touch projects/myresearch/tests/test_mymodule.py

# Add manuscript files
touch projects/myresearch/manuscript/01_introduction.md
```

## Workspace Management

This template uses uv workspaces for unified dependency management across projects. All projects share common dependencies while maintaining project-specific packages.

### Workspace Commands

```bash
# Sync all workspace dependencies
uv sync

# Add dependency to specific project
uv run python scripts/manage_workspace.py add numpy --project project

# Show workspace status
uv run python scripts/manage_workspace.py status

# Update all dependencies
uv run python scripts/manage_workspace.py update
```

### Workspace Benefits

- **Unified Dependencies**: Shared packages managed centrally
- **Faster Builds**: Single dependency resolution
- **Consistent Environments**: Same versions across projects
- **Simplified Maintenance**: Update once, benefit all projects

## Running the Pipeline

### Interactive Menu

```bash
# Launch interactive menu
./run.sh

# Select project from list
# Then select pipeline operation
```

### Command Line - Single Project

```bash
# Run pipeline for specific project
./run.sh --project myresearch --pipeline

# Run individual stages
uv run python scripts/01_run_tests.py --project myresearch
uv run python scripts/02_run_analysis.py --project myresearch
uv run python scripts/03_render_pdf.py --project myresearch
uv run python scripts/04_validate_output.py --project myresearch
```

### Command Line - All Projects

```bash
# Run pipeline for all projects
./run.sh --all-projects --pipeline

# Run tests for all projects
./run.sh --all-projects --tests
```

**Note**: In multi-project mode (`--all-projects`), infrastructure tests run **once** for all projects at the start, then are **skipped** for individual project executions. This avoids redundant testing while ensuring infrastructure quality across all projects.

### Default Project

When no `--project` is specified, the default template project is used:

```bash
# These are equivalent:
./run.sh --pipeline
./run.sh --project project --pipeline
```

## Project Requirements

Each project must have:

- ✅ `src/` directory with Python modules
- ✅ `tests/` directory with test files

Optional but recommended:

- `scripts/` - Analysis scripts (discovered by `02_run_analysis.py`)
- `manuscript/` - Manuscript markdown files (rendered by `03_render_pdf.py`)
- `pyproject.toml` - Project configuration
- `README.md` - Project documentation

## Output Structure

Each project's outputs are stored in two locations:

### Working Directory: `projects/{name}/output/`

Generated during pipeline execution:

- `pdf/` - PDF manuscripts
- `figures/` - Generated figures
- `data/` - Data files
- `reports/` - Analysis reports
- `slides/` - Presentation slides
- `web/` - HTML outputs
- `llm/` - LLM reviews
- `logs/` - Pipeline logs

### Final Directory: `output/{name}/`

Copied by `05_copy_outputs.py`:

- Same structure as working directory
- All project outputs in one place
- Ready for distribution

**Important**: The root `output/` directory should only contain project-specific folders. Root-level directories (`data/`, `figures/`, `pdf/`, etc.) are automatically cleaned during the pipeline to maintain proper organization.

Example:

```mermaid
flowchart LR
    OUT[/output//]
    OUT --> CP[/template_code_project/<br/>active inference meta-analysis/]
    OUT --> YP[/your_project/<br/>your custom research project/]
    CP --> CP_F[pdf/ · figures/ · ...]

    classDef d fill:#0f172a,stroke:#0f172a,color:#fff
    classDef f fill:#0f766e,stroke:#0f172a,color:#fff
    class OUT,CP,YP d
    class CP_F f
```

## Project Isolation

Each project is completely independent:

- ✅ Separate source code
- ✅ Separate test suites
- ✅ Separate outputs
- ✅ Separate dependencies (via pyproject.toml)
- ❌ No cross-project imports

For shared utilities, use the `infrastructure/` modules.

## Validation

Check if your project is valid:

```python
from infrastructure.project import validate_project_structure

is_valid, message = validate_project_structure(Path("projects/myresearch"))
print(f"Valid: {is_valid}, Message: {message}")
```

Required checks:

- Directory exists
- Has `src/` with Python files
- Has `tests/` directory

## .cursorrules Compliance

### ✅ **Standards Compliance Across All Projects**

All projects in this directory comply with template development standards:

- **Testing**: 90%+ coverage, data only, integration tests
- **Documentation**: AGENTS.md + README.md in each directory
- **Type Safety**: Full type hints on all public APIs
- **Code Quality**: Black formatting, descriptive naming, proper imports
- **Error Handling**: Context preservation, informative messages
- **Logging**: Unified logging system throughout

### Compliance Verification

```bash
# Run tests across all projects (prefer per-project invocation to avoid conftest collisions)
uv run python scripts/01_run_tests.py --project-only --all-projects

# Verify documentation completeness
find projects/ -name "*.py" -exec grep -L '"""' {} \;

# Check type hints
uv run mypy projects/myproject/src/
```

## Best Practices

### Do's ✅

- Keep each project independent
- Use meaningful project names (not `project1`, `project2`)
- Include `README.md` in each project
- Add `pyproject.toml` with metadata
- Write tests
- Document your code
- Follow .cursorrules standards for all development

### Don'ts ❌

- Don't share code between projects (use `infrastructure/`)
- Don't commit `output/` directories (in `.gitignore`)
- Don't use spaces or special characters in project names
- Don't create projects without `src/` and `tests/`
- Don't violate .cursorrules standards (testing, documentation, type hints, etc.)

## Migration from Single Project

If you have an existing single-project template:

```bash
# Check if migration needed
if [[ -d "project" ]] && [[ ! -d "projects" ]]; then
    echo "Migrating to multi-project structure..."
    mkdir -p projects
    mv project projects/project
    echo "✓ Migration"
fi
```

Available projects are automatically discovered - use `--project {name}` to specify which project to run.

## Real Project Examples

### **The Master Exemplar** (`projects/template_code_project/`)

The fully-featured research exemplar demonstrating the Generalized Research Template:

**Standalone Guarantees:**

- **Tests**: Test suite validating analysis algorithms
- **Methods**: Meta-analysis implementation in `src/`
- **Manuscript**: Research manuscript with analysis and figures

**Infrastructure Operations:**

```bash
# Pipeline execution
uv run python scripts/execute_pipeline.py --project template_code_project --core-only
```

## Creating New Projects

### Method 1: Copy Existing Project (Recommended)

```bash
# Copy an existing project as template
cp -r projects/template_code_project projects/my_research
cd projects/my_research

# Update project metadata
vim pyproject.toml  # Change name, description, authors

# Customize research content
vim manuscript/01_abstract.md
vim manuscript/02_introduction.md

# Add your algorithms
vim src/my_algorithm.py

# Add corresponding tests
vim tests/test_my_algorithm.py

# Run infrastructure validation
cd ../..
uv run python -c "from infrastructure.project import validate_project_structure; print(validate_project_structure(Path('projects/my_research')))"
```

### Method 2: Start from Scratch

```bash
# Create minimal project structure
mkdir -p projects/my_new_project/{src,tests,scripts,manuscript}
touch projects/my_new_project/src/__init__.py
touch projects/my_new_project/tests/__init__.py

# Add your research algorithms
vim projects/my_new_project/src/my_algorithm.py

# Add corresponding tests
vim projects/my_new_project/tests/test_my_algorithm.py

# Update manuscript content
vim projects/my_new_project/manuscript/01_introduction.md
vim projects/my_new_project/manuscript/02_methodology.md
```

## Troubleshooting

### "Project directory not found"

```bash
# Check project exists and has required structure
ls -la projects/

# Use infrastructure to list all valid projects
uv run python -c "
from infrastructure.project import discover_projects
projects = discover_projects(Path('.'))
for p in projects:
    print(f'✓ {p.name}: {p.path} (valid: {p.is_valid})')
"

# Interactive menu shows available projects
./run.sh
```

### "Project not found - is it archived?"

```bash
# Check if project is in archive directory
ls -la projects_archive/

# If found in archive, reactivate it
mv projects_archive/myproject projects/myproject

# Verify project structure is valid
uv run python -c "from infrastructure.project import validate_project_structure; print(validate_project_structure(Path('projects/myproject')))"

# Project should now be discoverable
./run.sh
```

**Symptoms:**

- Project exists but not listed in `run.sh` menu
- Infrastructure reports "project not found"
- Project appears to be missing from `projects/` directory

**Solution:**

1. Check if project exists in `projects_archive/` directory
2. If archived, move it back to `projects/` directory
3. Validate project structure (must have `src/` and `tests/`)
4. Project will be automatically discovered on next execution

### "Missing required directory: src" or "src/ directory contains no Python files"

```bash
# Create required directories and files
mkdir -p projects/myproject/src projects/myproject/tests

# Add minimal Python module
cat > projects/myproject/src/__init__.py << 'EOF'
"""My research project."""
EOF

cat > projects/myproject/src/example.py << 'EOF'
"""Example research module."""

def hello_research():
    """Return a research greeting."""
    return "Hello, research world!"
EOF

# Add minimal test
cat > projects/myproject/tests/__init__.py << 'EOF'
"""Test suite for my research project."""
EOF

cat > projects/myproject/tests/test_example.py << 'EOF'
"""Test example module."""
from src.example import hello_research

def test_hello_research():
    """Test hello_research function."""
    result = hello_research()
    assert "research" in result
EOF

# Validate with infrastructure
uv run python -c "from infrastructure.project import validate_project_structure; print(validate_project_structure(Path('projects/myproject')))"
```

### "No analysis scripts found"

This is not an error - `scripts/` directory is optional. Create it for computational workflows:

```bash
# Create scripts directory with analysis pipeline
mkdir -p projects/myproject/scripts

cat > projects/myproject/scripts/analysis_pipeline.py << 'EOF'
#!/usr/bin/env python3
"""Analysis pipeline for my research project."""

from src.example import hello_research
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

def main():
    """Run analysis pipeline."""
    logger.info("Starting analysis pipeline")
    result = hello_research()
    logger.info(f"Analysis result: {result}")
    print(f"Pipeline completed: {result}")

if __name__ == "__main__":
    main()
EOF

# Make executable and run via infrastructure
chmod +x projects/myproject/scripts/analysis_pipeline.py
uv run python scripts/02_run_analysis.py --project myproject
```

### "Test coverage below 90%"

```bash
# Run tests with coverage report
uv run pytest projects/myproject/tests/ --cov=projects/myproject/src --cov-report=html

# Open coverage report
open htmlcov/index.html

# Add missing tests
vim projects/myproject/tests/test_missing_functionality.py
```

### "Infrastructure compliance issues"

```bash
# Check markdown validation compliance
uv run python -m infrastructure.validation.cli markdown projects/myproject/manuscript/

# Check type hints with mypy
uv run mypy projects/myproject/src/
```

### "Manuscript rendering issues"

```bash
# Validate markdown before rendering
uv run python -m infrastructure.validation.cli markdown projects/myproject/manuscript/

# Check for missing references or figures
uv run python -m infrastructure.validation.cli pdf projects/myproject/output/pdf/

# Render with verbose output
LOG_LEVEL=0 uv run python scripts/03_render_pdf.py --project myproject
```

## See Also

- [Infrastructure Project Discovery](../infrastructure/project/AGENTS.md) - Project discovery API
- [Scripts Documentation](../scripts/AGENTS.md) - Pipeline orchestration
- [Root AGENTS.md](../AGENTS.md) - system documentation

## Summary

The `projects/` directory implements a **standalone project paradigm** with infrastructure compliance:

### 🔒 **Standalone Guarantees**

- **Tests**: Independent test suites (90%+ coverage, data only)
- **Methods**: Isolated business logic with no cross-project imports
- **Manuscript**: Independent content with own references and metadata

### 🔧 **Infrastructure Integration**

- **Discovery**: Automatic project detection via `infrastructure.project.discovery`
- **Validation**: Structure compliance checking
- **Execution**: Test/analysis/rendering via root `scripts/`
- **Quality Assurance**: PDF/markdown validation via `infrastructure.validation`

### 📋 **Compliance Framework**

- **.cursorrules Standards**: Testing, documentation, type hints, error handling, logging
- **Quality Gates**: 90% coverage, documentation, type safety
- **Infrastructure Access**: Import from `infrastructure/` modules for shared utilities

### 🎯 **Permanent Exemplars**

- **template_code_project**: Optimization research exemplar (measured tests/coverage in `docs/_generated/canonical_facts.md`)
- **template_prose_project**: Prose-review exemplar (measured tests/coverage in `docs/_generated/canonical_facts.md`)

Additional rotating projects are discovered from `docs/_generated/active_projects.md`.

**Note:** In-progress projects are in `projects_in_progress/`; archived projects are preserved in `projects_archive/`.

### 🚀 **Workflow**

1. **Create**: Copy existing project or start from template
2. **Develop**: Add algorithms to `src/`, tests to `tests/`, content to `manuscript/`
3. **Validate**: Ensure .cursorrules compliance and infrastructure integration
4. **Execute**: Run via infrastructure scripts for testing, analysis, rendering
5. **Deliver**: Final outputs organized in `output/{project}/`

Each project is **completely independent** yet integrated with the template's infrastructure for quality assurance, rendering, and validation.

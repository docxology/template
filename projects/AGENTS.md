# Projects Directory - Technical Documentation

## Overview

The `projects/` directory implements a **standalone project paradigm** where each research project is completely self-contained with independent source code, tests, analysis scripts, and manuscripts, while leveraging shared infrastructure for common operations like testing, rendering, and validation.

## Standalone Project Paradigm

Each project in `projects/{name}/` provides **three critical guarantees**:

### 🔒 **Tests**: Independent Test Suites (90%+ Coverage, Real Data Only)
- **Location**: `projects/{name}/tests/`
- **Coverage**: 90% minimum for `projects/{name}/src/` code
- **Policy**: No mocks - all tests use real data and computations
- **Execution**: Can run independently via `pytest projects/{name}/tests/`
- **Infrastructure Integration**: Orchestrated by `scripts/01_run_tests.py`

### 🧠 **Methods**: Business Logic Isolation (No Cross-Project Imports)
- **Location**: `projects/{name}/src/`
- **Isolation**: Cannot import from other projects
- **Infrastructure Access**: Can import from `infrastructure/` modules
- **Script Pattern**: Thin orchestrators in `projects/{name}/scripts/` import from `src/`
- **Domain Independence**: Each project maintains unique scientific algorithms

### 📝 **Manuscript**: Independent Content (Own References, Metadata)
- **Location**: `projects/{name}/manuscript/`
- **Content**: Independent markdown sections, config.yaml, references.bib
- **Rendering**: Processed independently via `infrastructure.rendering`
- **References**: Own cross-reference system and bibliography
- **Metadata**: Project-specific publication information

## Active vs Archived Projects

### Infrastructure Discovery Scope

The template distinguishes between **active projects** and **archived projects**:

#### ✅ **Active Projects (`projects/`)**
Active projects in the `projects/` directory are:
- **Discovered** by `infrastructure.project.discovery.discover_projects()`
- **Listed** in `run.sh` interactive menu
- **Executed** by all pipeline scripts (`01_run_tests.py`, `02_run_analysis.py`, etc.)
- **Rendered** by `03_render_pdf.py` with independent manuscript processing
- **Validated** by `04_validate_output.py`
- **Copied** to `output/{name}/` by `05_copy_outputs.py`

#### ❌ **Archived Projects (`projects_archive/`)**
Archived projects in the `projects_archive/` directory are:
- **NOT discovered** by infrastructure discovery functions
- **NOT listed** in `run.sh` menu
- **NOT executed** by any pipeline scripts
- **Preserved** for historical reference and potential reactivation

```mermaid
graph TD
    subgraph Active["Active Projects (projects/)"]
        P1[code_project<br/>Active - Discovered]
        P2[prose_project<br/>Active - Discovered]
    end

    subgraph Archive["Archived Projects (projects_archive/)"]
        A1[ento_linguistics<br/>Archived - NOT Discovered]
        A2[active_inference_meta_pragmatic<br/>Archived - NOT Discovered]
    end

    subgraph Infrastructure["Infrastructure Discovery"]
        DISCOVER[discover_projects<br/>Scans projects/ only]
        RUNSH[run.sh<br/>Lists active projects]
        PIPELINE[Pipeline Scripts<br/>Execute active projects]
    end

    P1 -->|Discovered| DISCOVER
    P2 -->|Discovered| DISCOVER
    A1 -.->|NOT Scanned| DISCOVER
    A2 -.->|NOT Scanned| DISCOVER

    DISCOVER -->|Active Projects| RUNSH
    RUNSH -->|Selected Project| PIPELINE
    PIPELINE -->|Executes| P1
    PIPELINE -->|Executes| P2
```

### Project Lifecycle

#### Archiving a Project
To archive an active project:
1. Move project from `projects/{name}/` to `projects_archive/{name}/`
2. Project will no longer appear in discovery or execution
3. Can be reactivated by moving back to `projects/`

#### Reactivating an Archived Project
To reactivate an archived project:
1. Move project from `projects_archive/{name}/` to `projects/{name}/`
2. Ensure project structure is valid (has `src/` and `tests/`)
3. Project will be automatically discovered on next `run.sh` execution

## Project Structure Requirements

### Required Directories (Must Exist)

Every valid project **must** have these directories:

```
projects/{name}/
├── src/                    # Python source code (algorithms, data processing)
│   ├── __init__.py        # Package initialization
│   └── *.py               # Research algorithms and methods
├── tests/                  # Test suite (90%+ coverage required)
│   ├── __init__.py        # Test package
│   └── test_*.py          # Unit and integration tests
└── pyproject.toml         # Project metadata and dependencies
```

### Optional Directories (Recommended for Full Functionality)

```
projects/{name}/
├── scripts/                # Analysis workflows (thin orchestrators)
│   ├── analysis_pipeline.py    # Main analysis script
│   └── generate_*.py          # Figure/table generation
├── manuscript/             # Research manuscript (markdown)
│   ├── config.yaml         # Publication metadata
│   ├── references.bib      # Bibliography
│   ├── 01_abstract.md      # Manuscript sections
│   └── *.md                # Additional sections
├── output/                 # Generated outputs (disposable)
│   ├── figures/            # PNG/PDF figures
│   ├── data/               # CSV/NPZ data files
│   ├── pdf/                # Generated PDFs
│   └── reports/            # Analysis reports
└── docs/                   # Project documentation (optional)
    ├── AGENTS.md           # Technical docs
    └── README.md           # Quick reference
```

## Infrastructure Compliance

Projects are **operated upon** by infrastructure modules while maintaining complete independence:

### 🔍 **Project Discovery** (`infrastructure.project.discovery`)

```python
from infrastructure.project import discover_projects, validate_project_structure

# Discover all valid projects in projects/ directory
repo_root = Path("/path/to/template")
projects = discover_projects(repo_root)

for project in projects:
    print(f"✓ {project.name}: {project.path}")
    print(f"  Valid: {project.is_valid}")
    print(f"  Has manuscript: {project.has_manuscript}")
    print(f"  Has scripts: {project.has_scripts}")

# Validate specific project
is_valid, message = validate_project_structure(Path("projects/ento_linguistics"))
assert is_valid  # (True, "Valid project structure")
```

**Key Functions:**
- `discover_projects(repo_root)` - Scans `projects/` for valid project directories
- `validate_project_structure(project_dir)` - Checks required directories exist
- `get_project_metadata(project_dir)` - Extracts metadata from pyproject.toml/config.yaml

### 🧪 **Test Execution** (`scripts/01_run_tests.py`)

```bash
# Execute project tests via infrastructure
python3 scripts/01_run_tests.py --project ento_linguistics

# Infrastructure performs:
# 1. Validates project structure
# 2. Runs pytest with coverage: pytest projects/ento_linguistics/tests/ --cov=projects/ento_linguistics/src
# 3. Enforces 90% coverage requirement
# 4. Generates coverage reports
```

**Infrastructure Operations:**
- Validates project has required `src/` and `tests/` directories
- Sets PYTHONPATH to include project source and infrastructure modules
- Runs pytest with coverage collection
- Fails pipeline if coverage below 90% for project code

### ⚙️ **Analysis Execution** (`scripts/02_run_analysis.py`)

```bash
# Execute project analysis scripts via infrastructure
python3 scripts/02_run_analysis.py --project active_inference_meta_pragmatic

# Infrastructure discovers and runs:
# - projects/active_inference_meta_pragmatic/scripts/analysis_pipeline.py
# - projects/active_inference_meta_pragmatic/scripts/generate_quadrant_matrix.py
# - All other scripts in projects/active_inference_meta_pragmatic/scripts/
```

**Script Discovery Process:**
1. Infrastructure validates project structure exists
2. Scans `projects/{name}/scripts/` for executable Python files
3. Sets PYTHONPATH including project `src/` and `infrastructure/`
4. Executes each script in order with proper environment
5. Collects outputs to `projects/{name}/output/`

### 📄 **Manuscript Rendering** (`scripts/03_render_pdf.py`)

```bash
# Render project manuscript via infrastructure
python3 scripts/03_render_pdf.py --project code_project

# Infrastructure processes:
# - Validates markdown references and structure
# - Combines manuscript sections into single document
# - Generates LaTeX with cross-references and citations
# - Compiles to PDF with figure integration
# - Validates output quality
```

**Rendering Pipeline:**
1. **Markdown Validation**: Checks references and structure via `infrastructure.validation`
2. **Content Assembly**: Combines sections from `projects/{name}/manuscript/`
3. **LaTeX Generation**: Converts via pandoc with template processing
4. **Figure Integration**: Embeds registered figures with captions
5. **PDF Compilation**: XeLaTeX rendering with bibliography processing
6. **Quality Validation**: PDF integrity checks via `infrastructure.validation`

### ✅ **Quality Validation** (`scripts/04_validate_output.py`)

```bash
# Validate project outputs via infrastructure
python3 scripts/04_validate_output.py --project project

# Infrastructure validates:
# - PDF rendering quality (no unresolved references)
# - Markdown structure integrity
# - File integrity and checksums
# - Cross-reference resolution
```

**Validation Checks:**
- **PDF Validation**: Unresolved references, LaTeX errors, document structure
- **Markdown Validation**: Image references, cross-references, equation labels
- **Integrity Validation**: File checksums, data consistency, academic standards

### 📋 **Output Management** (`scripts/05_copy_outputs.py`)

```bash
# Organize final deliverables via infrastructure
python3 scripts/05_copy_outputs.py --project ento_linguistics

# Infrastructure operations:
# - Cleans root-level output/ directories (keeps only project folders)
# - Copies from projects/ento_linguistics/output/ to output/ento_linguistics/
# - Validates all files copied successfully
# - Organizes by project for distribution
```

**Output Organization:**
```
output/
├── ento_linguistics/           # Final deliverables
│   ├── pdf/                    # Manuscript PDFs
│   ├── figures/                # Publication figures
│   ├── data/                   # Analysis datasets
│   └── reports/                # Pipeline reports
└── active_inference_meta_pragmatic/  # Other projects
    └── ...
```

## Import Patterns and Dependencies

### ✅ **Correct Import Patterns**

**Within Project (Business Logic):**
```python
# projects/ento_linguistics/src/domain_analysis.py
from .term_extraction import TerminologyExtractor        # ✅ Import from same project
from .literature_mining import LiteratureCorpus         # ✅ Import from same project

# Infrastructure utilities (allowed)
from infrastructure.core.logging_utils import get_logger  # ✅ Infrastructure access
from infrastructure.figure_manager import FigureManager   # ✅ Infrastructure access
```

**Project Scripts (Thin Orchestrators):**
```python
# projects/ento_linguistics/scripts/analysis_pipeline.py
from src.domain_analysis import DomainAnalyzer           # ✅ Import project algorithms
from src.term_extraction import TerminologyExtractor     # ✅ Import project methods
from infrastructure.core.logging_utils import get_logger # ✅ Infrastructure utilities
```

### ❌ **Incorrect Import Patterns (Violate Isolation)**

**Cross-Project Imports (Forbidden):**
```python
# ❌ NEVER: Import from other projects
from projects.active_inference_meta_pragmatic.src.generative_models import GenerativeModel
from projects.code_project.src.optimizer import Optimizer
```

**Infrastructure Business Logic (Forbidden):**
```python
# ❌ NEVER: Import infrastructure algorithms (infrastructure is utilities only)
from infrastructure.rendering.core import RenderManager  # ❌ Business logic
from infrastructure.validation.pdf_validator import PDFValidator  # ❌ Business logic

# ✅ ALLOWED: Infrastructure utilities
from infrastructure.core.logging_utils import get_logger  # ✅ Utility
from infrastructure.core.config_loader import load_config  # ✅ Utility
```

## Testing Standards and Requirements

### Coverage Requirements

**Project Code (`projects/{name}/src/`):**
- **90% minimum coverage** required (currently achieved: 100% for most projects)
- **Infrastructure Code**: 60% minimum (currently achieved: 83.33%)

**Coverage Verification:**
```bash
# Check project coverage
pytest projects/ento_linguistics/tests/ --cov=projects/ento_linguistics/src --cov-fail-under=90

# Generate coverage report
pytest projects/ento_linguistics/tests/ --cov=projects/ento_linguistics/src --cov-report=html
open htmlcov/index.html
```

### No Mocks Policy (Absolute Requirement)

**ABSOLUTE PROHIBITION**: Under no circumstances use `MagicMock`, `mocker.patch`, `unittest.mock`, or any mocking framework.

**Rationale:**
- Tests must validate actual behavior, not mocked behavior
- Integration points must be truly tested
- Code must work with real data and computations
- No false confidence from mocked tests

**Correct Testing Patterns:**
```python
# ✅ GOOD: Test with real data and computations
def test_term_extraction_real_data():
    """Test term extraction with real entomological texts."""
    extractor = TerminologyExtractor()
    real_texts = [
        "Ant colonies exhibit complex social behavior with division of labor.",
        "The queen ant lays eggs while worker ants forage for food."
    ]
    terms = extractor.extract_terms(real_texts, min_frequency=2)
    assert len(terms) > 0
    assert "ant" in terms.lower() or "colony" in terms.lower()

# ❌ ABSOLUTELY FORBIDDEN: Never use mocks
# def test_term_extraction_mock():
#     mock_extractor = MagicMock()
#     mock_extractor.extract_terms.return_value = {"ant": 5, "colony": 3}
```

**Network-Dependent Testing:**
```python
# ✅ GOOD: Use pytest-httpserver for real HTTP testing
@pytest.mark.requires_ollama
def test_llm_integration_real_http(ollama_test_server):
    """Test LLM integration with real HTTP server."""
    config = LLMConfig(base_url=ollama_test_server.url_for("/"))
    client = LLMClient(config)
    response = client.query("test prompt")  # Real HTTP request
    assert "response" in response.lower()
```

### Test Organization

**Directory Structure:**
```
projects/{name}/tests/
├── __init__.py                      # Test package
├── conftest.py                      # Shared fixtures and configuration
├── test_domain_analysis.py          # Unit tests for domain analysis
├── test_term_extraction.py          # Unit tests for term extraction
├── test_integration.py              # Integration tests across modules
├── test_performance.py              # Performance and scaling tests
└── test_validation.py               # Validation and error handling tests
```

**Test Categories:**
- **Unit Tests**: Individual functions and methods
- **Integration Tests**: Cross-module interactions
- **Performance Tests**: Algorithm efficiency and scaling
- **Validation Tests**: Error handling and edge cases

## Validation and Structure Checking

### Project Structure Validation

**Infrastructure Validation:**
```python
from infrastructure.project import validate_project_structure

# Check if directory is valid project
project_dir = Path("projects/ento_linguistics")
is_valid, message = validate_project_structure(project_dir)

if is_valid:
    print("✅ Valid project structure")
else:
    print(f"❌ Invalid: {message}")
    # Common errors:
    # - "Missing required directory: src"
    # - "src/ directory contains no Python files"
    # - "Missing required directory: tests"
```

**Validation Rules:**
- ✅ **Must have**: `src/` directory with at least one `.py` file
- ✅ **Must have**: `tests/` directory
- ✅ **Optional but recommended**: `scripts/`, `manuscript/`
- ✅ **Metadata**: `pyproject.toml` for project information
- ❌ **Forbidden**: Cross-project imports or dependencies

### Script Discovery and Execution

**Analysis Script Discovery:**
```python
# Infrastructure discovers executable scripts
from infrastructure.core.script_discovery import discover_analysis_scripts

project_root = Path("projects/ento_linguistics")
scripts = discover_analysis_scripts(project_root)

for script in scripts:
    print(f"Found script: {script.name}")
    # Output: analysis_pipeline.py, domain_analysis_script.py, etc.
```

**Script Execution Environment:**
- **PYTHONPATH**: Includes project `src/` and `infrastructure/`
- **Working Directory**: Set to project root
- **Environment Variables**: MPLBACKEND=Agg for headless plotting
- **Error Handling**: Captures stdout/stderr, returns exit codes

## Output Management

### Working Directory (`projects/{name}/output/`)

**Generated during pipeline execution:**
```
projects/ento_linguistics/output/
├── figures/                 # PNG/PDF figures for manuscript
├── data/                    # CSV/NPZ datasets from analysis
├── pdf/                     # Generated PDF manuscripts
├── tex/                     # LaTeX source files
├── slides/                  # Presentation slides (PDF/HTML)
├── web/                     # HTML versions for web viewing
├── llm/                     # LLM reviews and translations
├── logs/                    # Pipeline execution logs
└── reports/                 # Analysis reports and summaries
```

**Characteristics:**
- **Disposable**: Regenerated on each pipeline run
- **Working**: Used during analysis and rendering
- **Not in git**: Added to `.gitignore`
- **Project-specific**: Isolated per project

### Final Directory (`output/{name}/`)

**Copied by `scripts/05_copy_outputs.py`:**
```
output/ento_linguistics/
├── pdf/                     # Final manuscript PDFs
├── figures/                 # Publication-quality figures
├── data/                    # Analysis datasets for sharing
├── slides/                  # Presentation materials
└── reports/                 # Pipeline and analysis reports
```

**Characteristics:**
- **Persistent**: Final deliverables for distribution
- **Organized**: All project outputs in one location
- **Ready for distribution**: Can be archived or shared independently
- **Cross-project**: Multiple projects in `output/` directory

## .cursorrules Compliance Verification

All projects in this directory fully comply with the template's development standards defined in `.cursorrules/`.

### ✅ **Testing Standards Compliance**
- **90%+ coverage**: Both projects achieve required coverage thresholds (code_project: 96.49%, prose_project: 100%)
- **Real data only**: All tests use real computations, no mocks
- **Comprehensive integration**: Tests cover algorithm convergence, mathematical functions, and figure generation
- **Deterministic results**: Fixed seeds ensure reproducible test outcomes

### ✅ **Documentation Standards Compliance**
- **AGENTS.md + README.md**: Complete technical documentation in each directory
- **Type hints**: All public APIs have complete type annotations
- **Docstrings**: Comprehensive docstrings with examples for all functions
- **Cross-references**: Links between related documentation sections

### ✅ **Type Hints Standards Compliance**
- **Complete annotations**: All public functions have type hints
- **Generic types**: Uses `List`, `Dict`, `Optional`, `Callable` appropriately
- **Consistent patterns**: Follows template conventions throughout

### ✅ **Error Handling Standards Compliance**
- **Custom exceptions**: Uses infrastructure exception hierarchy when available
- **Context preservation**: Exception chaining with `from` keyword
- **Informative messages**: Clear error messages with actionable guidance

### ✅ **Logging Standards Compliance**
- **Unified logging**: Uses `infrastructure.core.logging_utils.get_logger(__name__)`
- **Appropriate levels**: DEBUG, INFO, WARNING, ERROR as appropriate
- **Context-rich messages**: Includes relevant context in log messages

### ✅ **Code Style Standards Compliance**
- **Black formatting**: 88-character line limits, consistent formatting
- **Descriptive names**: Clear variable and function names
- **Import organization**: Standard library, third-party, local imports properly organized

### Compliance Verification Results

**✅ VERIFICATION COMPLETED - ALL STANDARDS MET**

#### Testing Standards Results
- **code_project**: 96.00% coverage (13 tests passed) ✅
- **prose_project**: 93.13% coverage (15 tests passed) ✅
- **Combined**: All tests use real data, no mocks detected ✅

#### Documentation Standards Results
- **AGENTS.md**: Complete in all directories (projects/, code_project/, prose_project/) ✅
- **README.md**: Complete in all directories (projects/, code_project/, prose_project/) ✅
- **Docstrings**: 100% coverage - all Python files have docstrings ✅
- **Type hints**: All public APIs have complete annotations ✅

#### Code Quality Standards Results
- **Black formatting**: Applied consistently across all projects ✅
- **Import organization**: Standard library, third-party, local imports properly organized ✅
- **Error handling**: Context preservation with `from` keyword usage ✅
- **Logging**: Unified logging system throughout ✅

#### Pipeline Integration Results
- **Import errors**: Fixed in `infrastructure/validation/output_validator.py` ✅
- **Figure generation**: Both projects generate and register figures correctly ✅
- **Manuscript integration**: All equations and figures properly referenced ✅

```bash
# Compliance verification commands (all pass):
python3 -m pytest projects/*/tests/ --cov=projects/*/src --cov-report=html
find projects/ -name "*.py" -exec grep -L '"""' {} \;  # Returns empty (all have docstrings)
python3 -c "from infrastructure.validation.output_validator import validate_output_structure"  # Imports successfully
```

## Best Practices and Compliance

### .cursorrules Standards Compliance

All projects must follow standards defined in `.cursorrules/`:

#### ✅ **Testing Standards** (`.cursorrules/testing_standards.md`)
- [ ] 90%+ coverage for project code
- [ ] Real data only (no mocks)
- [ ] Comprehensive integration tests
- [ ] Deterministic results with seeded randomness

#### ✅ **Documentation Standards** (`.cursorrules/documentation_standards.md`)
- [ ] `AGENTS.md` in each directory with complete technical docs
- [ ] `README.md` in each directory with quick reference
- [ ] Complete docstrings with examples for public APIs
- [ ] Cross-references to related documentation

#### ✅ **Type Hints Standards** (`.cursorrules/type_hints_standards.md`)
- [ ] Complete type annotations on all public functions
- [ ] Generic types (List, Dict, Optional, etc.)
- [ ] Consistent patterns across modules

#### ✅ **Error Handling Standards** (`.cursorrules/error_handling.md`)
- [ ] Custom exception hierarchy from `infrastructure.core.exceptions`
- [ ] Exception chaining with context preservation
- [ ] Informative error messages with actionable guidance

#### ✅ **Logging Standards** (`.cursorrules/python_logging.md`)
- [ ] Unified logging via `infrastructure.core.logging_utils.get_logger(__name__)`
- [ ] Appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Context-rich log messages for debugging

#### ✅ **Code Style Standards** (`.cursorrules/code_style.md`)
- [ ] Black formatting with 88-character line limits
- [ ] Descriptive variable names and function signatures
- [ ] Consistent import organization (stdlib, third-party, local)

### Thin Orchestrator Pattern

**Project Scripts (Correct Pattern):**
```python
# projects/ento_linguistics/scripts/analysis_pipeline.py
from src.term_extraction import TerminologyExtractor      # ✅ Import business logic
from src.domain_analysis import DomainAnalyzer           # ✅ Import algorithms
from infrastructure.figure_manager import FigureManager  # ✅ Import utilities

def main():
    """Run complete analysis pipeline."""
    # Import and use project algorithms
    extractor = TerminologyExtractor()
    terms = extractor.extract_terms(texts)
    
    analyzer = DomainAnalyzer()
    results = analyzer.analyze_all_domains(terms, texts)
    
    # Use infrastructure utilities
    fm = FigureManager()
    fm.register_figure("domain_analysis.png", "Domain analysis results")

if __name__ == "__main__":
    main()
```

**Anti-Patterns (Violate Architecture):**
```python
# ❌ WRONG: Business logic in scripts
def analyze_terms(texts):  # Should be in src/
    # Algorithm implementation in script
    pass

# ❌ WRONG: No infrastructure utilities
import matplotlib.pyplot as plt  # Should use infrastructure.figure_manager
plt.savefig("figure.png")
```

## API Reference

### infrastructure.project Module

**Project Discovery:**
```python
def discover_projects(repo_root: Path | str) -> list[ProjectInfo]:
    """Discover all valid projects in projects/ directory.

    Args:
        repo_root: Repository root directory

    Returns:
        List of ProjectInfo objects for valid projects
    """

def validate_project_structure(project_dir: Path) -> tuple[bool, str]:
    """Validate that directory has required project structure.

    Args:
        project_dir: Path to potential project directory

    Returns:
        Tuple of (is_valid, message)
    """

def get_project_metadata(project_dir: Path) -> dict:
    """Extract project metadata from pyproject.toml and config.yaml.

    Args:
        project_dir: Project directory path

    Returns:
        Dictionary with project metadata
    """
```

**ProjectInfo Dataclass:**
```python
@dataclass
class ProjectInfo:
    """Information about a discovered project."""
    name: str
    path: Path
    has_src: bool
    has_tests: bool
    has_scripts: bool
    has_manuscript: bool
    metadata: dict

    @property
    def is_valid(self) -> bool:
        """Check if project has minimum required structure."""
        return self.has_src and self.has_tests
```

## Troubleshooting

### "Project directory not found"

**Symptoms:**
- Infrastructure scripts fail with "Project directory not found"
- Project not listed in `./run.sh` menu

**Solutions:**
```bash
# Check project exists
ls -la projects/

# Verify project name spelling
./run.sh  # Shows available projects

# Check for hidden directories or incorrect naming
find projects/ -maxdepth 1 -type d -not -path '*/.*'
```

### "Missing required directory: src"

**Symptoms:**
- `validate_project_structure()` returns `(False, "Missing required directory: src")`
- Pipeline fails at validation stage

**Solutions:**
```bash
# Create required directories
mkdir -p projects/myproject/src projects/myproject/tests

# Add minimal Python module
touch projects/myproject/src/__init__.py
echo '"""Research algorithms."""' > projects/myproject/src/example.py

# Validate
python3 -c "from infrastructure.project import validate_project_structure; print(validate_project_structure(Path('projects/myproject')))"
```

### "src/ directory contains no Python files"

**Symptoms:**
- Project has `src/` directory but validation fails
- Empty or non-Python files in `src/`

**Solutions:**
```bash
# Check src/ contents
ls -la projects/myproject/src/

# Add Python files with proper extensions
touch projects/myproject/src/__init__.py
touch projects/myproject/src/algorithms.py

# Remove non-Python files if present
find projects/myproject/src/ -not -name "*.py" -type f
```

### "Test coverage below 90%"

**Symptoms:**
- Pipeline fails at test stage with coverage error
- `pytest --cov-fail-under=90` exits with failure

**Solutions:**
```bash
# Run tests with coverage report
pytest projects/myproject/tests/ --cov=projects/myproject/src --cov-report=html

# Open coverage report to identify gaps
open htmlcov/index.html

# Add missing test cases
vim projects/myproject/tests/test_missing_functionality.py

# Verify coverage meets requirements
pytest projects/myproject/tests/ --cov=projects/myproject/src --cov-fail-under=90
```

### "No analysis scripts found"

**Symptoms:**
- `scripts/02_run_analysis.py` reports "No analysis scripts found"
- Optional `scripts/` directory missing or empty

**Solutions:**
```bash
# Create scripts directory (optional but recommended)
mkdir -p projects/myproject/scripts

# Add analysis script following thin orchestrator pattern
cat > projects/myproject/scripts/analysis_pipeline.py << 'EOF'
#!/usr/bin/env python3
"""Analysis pipeline for myproject."""

from src.algorithms import MyAlgorithm
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)

def main():
    """Run analysis pipeline."""
    logger.info("Starting analysis")
    algo = MyAlgorithm()
    results = algo.run()
    logger.info(f"Analysis complete: {results}")

if __name__ == "__main__":
    main()
EOF

# Make executable
chmod +x projects/myproject/scripts/analysis_pipeline.py
```

### "Import errors in scripts"

**Symptoms:**
- Analysis scripts fail with import errors
- "ModuleNotFoundError" for local or infrastructure modules

**Solutions:**
```bash
# Check PYTHONPATH setup by infrastructure
# Infrastructure sets: repo_root + infrastructure/ + project/src/

# Verify imports in script
python3 -c "
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'infrastructure')
from projects.myproject.src.algorithms import MyAlgorithm
print('Import successful')
"

# Fix import paths if needed
# Correct: from src.algorithms import MyAlgorithm
# Wrong: from algorithms import MyAlgorithm
```

### "Manuscript rendering issues"

**Symptoms:**
- PDF generation fails with LaTeX errors
- Missing references or figures in output

**Solutions:**
```bash
# Validate markdown before rendering
python3 -m infrastructure.validation.cli markdown projects/myproject/manuscript/

# Check for missing figure registrations
python3 -m infrastructure.validation.cli integrity projects/myproject/output/

# Render with verbose logging
LOG_LEVEL=0 python3 scripts/03_render_pdf.py --project myproject

# Check LaTeX compilation logs
ls projects/myproject/output/pdf/*_compile.log
```

## Real Project Examples

### Ento-Linguistic Research (`projects/ento_linguistics/`)

**Standalone Guarantees:**
- **Tests**: 484 tests, 83.74% coverage, real PubMed/arXiv API testing
- **Methods**: 6-domain analysis framework, term extraction algorithms
- **Manuscript**: Independent Ento-Linguistic research with literature corpus

**Infrastructure Operations:**
```bash
# Infrastructure discovers and validates
python3 scripts/01_run_tests.py --project ento_linguistics

# Infrastructure executes analysis scripts
python3 scripts/02_run_analysis.py --project ento_linguistics

# Infrastructure renders manuscript
python3 scripts/03_render_pdf.py --project ento_linguistics
```

### Active Inference Framework (`projects/active_inference_meta_pragmatic/`)

**Standalone Guarantees:**
- **Tests**: 90%+ coverage, theoretical EFE calculation validation
- **Methods**: 2×2 matrix framework, generative models, meta-cognition
- **Manuscript**: Independent meta-pragmatic analysis with mathematical derivations

**Infrastructure Operations:**
```bash
# Complete pipeline via infrastructure
python3 scripts/execute_pipeline.py --project active_inference_meta_pragmatic --core-only
```

## See Also

- [README.md](README.md) - Quick reference and getting started
- [PROJECTS_PARADIGM.md](PROJECTS_PARADIGM.md) - Philosophical explanation of standalone paradigm
- [../infrastructure/project/AGENTS.md](../infrastructure/project/AGENTS.md) - Infrastructure project management
- [../infrastructure/project/README.md](../infrastructure/project/README.md) - Project management quick reference
- [../.cursorrules/AGENTS.md](../.cursorrules/AGENTS.md) - Development standards overview
- [../AGENTS.md](../AGENTS.md) - Complete template documentation

## Summary

The `projects/` directory implements **standalone project paradigm** with infrastructure compliance:

### 🔒 **Standalone Guarantees**
- **Tests**: Independent 90%+ coverage test suites with real data only
- **Methods**: Isolated business logic with no cross-project dependencies
- **Manuscript**: Independent content with own references and publication metadata

### 🔧 **Infrastructure Integration**
- **Discovery**: Automatic project detection via `infrastructure.project.discovery`
- **Validation**: Structure and quality compliance checking
- **Execution**: Test/analysis/rendering via root `scripts/` orchestrators
- **Quality Assurance**: PDF/markdown validation and integrity checking

### 📋 **Compliance Framework**
- **.cursorrules Standards**: Complete adherence to testing, documentation, type hints, error handling, and logging standards
- **Quality Gates**: Automated coverage checks, documentation validation, type safety verification
- **Operational Patterns**: Thin orchestrator scripts, infrastructure utility imports, project isolation

Each project maintains complete independence while benefiting from shared infrastructure for common research operations, ensuring reproducible, high-quality scientific computing with rigorous testing and validation.
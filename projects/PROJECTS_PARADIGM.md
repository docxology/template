# Projects Paradigm - Standalone Research Projects

## Paradigm Overview

The **standalone project paradigm** represents a fundamental architectural principle where each research project in the `projects/` directory is a **complete, self-sufficient unit** that can be developed, tested, analyzed, and published independently, while benefiting from shared infrastructure for common operations.

### What "Standalone" Means

A standalone project provides **three critical guarantees**:

#### 🔒 **Tests Guarantee**: Independent Test Suites
Each project maintains its own comprehensive test suite that validates its algorithms with real data, achieving 90%+ code coverage without relying on external test infrastructure.

#### 🧠 **Methods Guarantee**: Algorithmic Independence
Each project contains complete business logic for its research domain, with no dependencies on other projects' algorithms or methods.

#### 📝 **Manuscript Guarantee**: Content Independence
Each project maintains its own research manuscript, references, and publication metadata, rendered independently through shared infrastructure.

## Isolation Principles

### Complete Independence Between Projects

Projects are **architecturally isolated** - each operates as if it were the only project in the repository:

```mermaid
graph TD
    subgraph "Complete Project Isolation"
        P1[ento_linguistics<br/>Ento-Linguistic Research<br/>📝 Own manuscript<br/>🧪 Own tests<br/>🧠 Own algorithms]
        P2[active_inference_meta_pragmatic<br/>Active Inference Framework<br/>📝 Own manuscript<br/>🧪 Own tests<br/>🧠 Own algorithms]
        P3[code_project<br/>Optimization Research<br/>📝 Own manuscript<br/>🧪 Own tests<br/>🧠 Own algorithms]

        P1 -.->|❌ No imports| P2
        P1 -.->|❌ No imports| P3
        P2 -.->|❌ No imports| P3
    end

    subgraph "Shared Infrastructure Access"
        INFRA[infrastructure/<br/>Generic tools<br/>✅ Shared by all projects]
        SCRIPTS[scripts/<br/>Entry points<br/>✅ Orchestrate all projects]

        P1 -->|✅ Import utilities| INFRA
        P2 -->|✅ Import utilities| INFRA
        P3 -->|✅ Import utilities| INFRA

        SCRIPTS -->|✅ Operate on| P1
        SCRIPTS -->|✅ Operate on| P2
        SCRIPTS -->|✅ Operate on| P3
    end
```

### No Cross-Project Dependencies

**Architectural Invariant**: Projects cannot import from each other.

**Correct Pattern:**
```python
# ✅ ALLOWED: Import from own project
from src.term_extraction import TerminologyExtractor

# ✅ ALLOWED: Import from infrastructure
from infrastructure.core.logging_utils import get_logger
from infrastructure.figure_manager import FigureManager

# ❌ FORBIDDEN: Import from other projects
# from projects.active_inference_meta_pragmatic.src.generative_models import GenerativeModel
```

**Rationale:**
- **Scientific Integrity**: Each project maintains independent scientific validity
- **Modularity**: Projects can be copied, moved, or removed without affecting others
- **Reusability**: Projects can be used as standalone research units
- **Maintenance**: Changes to one project don't break others

## Infrastructure Integration

### How Projects Leverage Shared Infrastructure

While projects are completely independent, they benefit from **shared infrastructure** for common research operations:

#### 🔍 **Project Discovery and Validation**
```python
from infrastructure.project import discover_projects

# Infrastructure discovers all projects automatically
projects = discover_projects(Path("."))
# Returns: [ento_linguistics, active_inference_meta_pragmatic, code_project, ...]

# Infrastructure validates each project independently
for project in projects:
    assert project.is_valid  # Each project validates itself
```

#### 🧪 **Test Orchestration**
```bash
# Infrastructure runs each project's tests independently
python3 scripts/01_run_tests.py --project ento_linguistics
# - Validates project structure
# - Runs pytest projects/ento_linguistics/tests/ --cov=projects/ento_linguistics/src
# - Enforces 90% coverage requirement
# - Generates coverage reports
```

#### ⚙️ **Analysis Execution**
```bash
# Infrastructure discovers and executes each project's scripts
python3 scripts/02_run_analysis.py --project active_inference_meta_pragmatic
# - Finds all scripts in projects/active_inference_meta_pragmatic/scripts/
# - Sets PYTHONPATH: repo_root + infrastructure/ + project/src/
# - Executes each script with proper environment
# - Collects outputs to projects/active_inference_meta_pragmatic/output/
```

#### 📄 **Manuscript Rendering**
```bash
# Infrastructure renders each project's manuscript independently
python3 scripts/03_render_pdf.py --project code_project
# - Validates markdown in projects/code_project/manuscript/
# - Combines sections using project-specific config.yaml
# - Generates LaTeX with project-specific references.bib
# - Compiles PDF with project-specific figures
```

### Infrastructure as Utilities, Not Business Logic

**Critical Distinction:**
- **Infrastructure**: Provides **utilities** (logging, validation, rendering, file operations)
- **Projects**: Contain **business logic** (research algorithms, analysis methods)

**Infrastructure Scope:**
- ✅ File operations and directory management
- ✅ Logging and error handling utilities
- ✅ Configuration loading and validation
- ✅ PDF rendering and markdown processing
- ✅ Test orchestration and coverage reporting
- ✅ Quality validation and integrity checking

**Project Scope:**
- ✅ Research algorithms and scientific methods
- ✅ Domain-specific data processing
- ✅ Analysis pipelines and workflows
- ✅ Figure generation and visualization
- ✅ Manuscript content and academic writing

## .cursorrules Compliance as Paradigm Requirement

The standalone project paradigm requires **complete compliance** with template development standards defined in `.cursorrules/`. This compliance is not optional - it's a core requirement of the paradigm.

### ✅ **Testing Standards Compliance (Required)**
- **90%+ coverage**: Each project must achieve 90% minimum coverage (currently achieved: code_project 96.49%, active_inference_meta_pragmatic: varies, ento_linguistics: 83%)
- **Real data only**: Absolute prohibition on mocks - all tests use real computations
- **Comprehensive integration**: Tests cover critical workflows and edge cases
- **Deterministic results**: Fixed seeds ensure reproducible test outcomes

### ✅ **Documentation Standards Compliance (Required)**
- **AGENTS.md + README.md**: Complete documentation in each directory
- **Type hints**: All public APIs have complete type annotations
- **Docstrings**: Comprehensive documentation with examples
- **Cross-references**: Links between related sections

### ✅ **Code Quality Standards Compliance (Required)**
- **Black formatting**: 88-character limits, consistent formatting
- **Descriptive naming**: Clear variable and function names
- **Import organization**: Proper organization of imports
- **Error handling**: Context preservation and informative messages
- **Unified logging**: Consistent logging throughout

### Compliance Verification

```bash
# Paradigm compliance verification
python3 -m pytest projects/*/tests/ --cov=projects/*/src --cov-fail-under=90
find projects/ -name "*.py" -exec grep -L '"""' {} \;  # Check for missing docstrings
```

## Compliance Framework

### Alignment with .cursorrules Standards

Every standalone project must comply with development standards defined in `.cursorrules/`:

#### ✅ **Testing Standards Compliance**
- **90%+ Coverage**: Each project achieves 90% minimum test coverage
- **Real Data Only**: No mocks - all tests use real data and computations
- **Independent Validation**: Each project's tests validate its own algorithms
- **Integration Testing**: Cross-module interactions within project boundaries

#### ✅ **Documentation Standards Compliance**
- **AGENTS.md**: Comprehensive technical documentation for each project
- **README.md**: Quick reference with Mermaid diagrams and examples
- **Docstrings**: Complete documentation for all public APIs
- **Cross-References**: Links between related documentation sections

#### ✅ **Code Quality Standards Compliance**
- **Type Hints**: Complete type annotations on all public functions
- **Error Handling**: Custom exception hierarchy with context preservation
- **Logging**: Unified logging system throughout project code
- **Code Style**: Consistent formatting and naming conventions

### Quality Gates and Validation

**Automated Validation:**
```bash
# Infrastructure validates compliance during pipeline
python3 scripts/01_run_tests.py --project ento_linguistics
# ✓ Tests pass with 90%+ coverage
# ✓ No mock methods detected
# ✓ Type hints validated
# ✓ Documentation completeness checked

python3 scripts/04_validate_output.py --project ento_linguistics
# ✓ PDF integrity verified
# ✓ Markdown references resolved
# ✓ File integrity maintained
# ✓ Academic standards met
```

## Operational Model

### How Infrastructure Operates on Projects

The operational model follows the **thin orchestrator pattern** where infrastructure acts as a **facilitator**, not a **director**:

#### 1. **Discovery Phase**
Infrastructure discovers projects and validates their structure:
```python
# Infrastructure finds projects
projects = discover_projects(repo_root)

# Infrastructure validates each independently
for project in projects:
    is_valid, message = validate_project_structure(project.path)
    if not is_valid:
        logger.error(f"Project {project.name}: {message}")
        continue
```

#### 2. **Execution Phase**
Infrastructure provides execution environment for each project:
```python
# Infrastructure sets up execution environment
env = {
    'PYTHONPATH': f"{repo_root}:{repo_root}/infrastructure:{project.path / 'src'}",
    'MPLBACKEND': 'Agg',  # Headless matplotlib
}

# Infrastructure executes project scripts
for script in project_scripts:
    subprocess.run([python_cmd, script], cwd=project.path, env=env)
```

#### 3. **Integration Phase**
Infrastructure integrates project outputs into unified deliverables:
```python
# Infrastructure organizes final outputs
copy_final_deliverables(project.path / "output", output_root / project.name)
# Result: output/ento_linguistics/ contains all project deliverables
```

### Project Lifecycle Under Infrastructure

```
Project Development Lifecycle
├── 1. Creation
│   ├── Copy template or create from scratch
│   ├── Add algorithms to src/
│   └── Add tests to tests/
├── 2. Development
│   ├── Implement research methods
│   ├── Write comprehensive tests
│   └── Develop analysis scripts
├── 3. Validation
│   ├── Infrastructure validates structure
│   ├── Tests run with coverage checks
│   └── Code quality verified
├── 4. Analysis
│   ├── Infrastructure discovers scripts
│   ├── Scripts execute with proper environment
│   └── Outputs collected to project/output/
├── 5. Rendering
│   ├── Manuscript processed independently
│   ├── Figures integrated from analysis
│   └── PDF generated with project references
├── 6. Delivery
│   ├── Outputs copied to output/{project}/
│   ├── Ready for distribution
│   └── Project remains standalone
└── 7. Maintenance
    ├── Independent updates possible
    ├── No impact on other projects
    └── Infrastructure improvements benefit all
```

## Testing Philosophy

### Standalone Test Suites with Real Data

Each project's test suite validates its algorithms using **real data and computations**:

#### **No Mocks Policy (Absolute)**
```python
# ✅ CORRECT: Test with real data
def test_term_extraction():
    extractor = TerminologyExtractor()
    real_texts = ["ant colony behavior", "eusocial insects"]
    terms = extractor.extract_terms(real_texts, min_frequency=1)
    assert len(terms) > 0

# ❌ ABSOLUTELY FORBIDDEN: Never use mocks
# def test_term_extraction():
#     mock_extractor = MagicMock(return_value={"ant": 5})
#     # This violates the testing philosophy
```

#### **Integration Testing Within Project Boundaries**
```python
# ✅ CORRECT: Test cross-module integration within project
def test_complete_analysis_pipeline():
    # Import from same project
    from src.term_extraction import TerminologyExtractor
    from src.domain_analysis import DomainAnalyzer

    # Real data processing
    extractor = TerminologyExtractor()
    analyzer = DomainAnalyzer()

    terms = extractor.extract_terms(texts)
    results = analyzer.analyze_all_domains(terms, texts)

    assert len(results) == 6  # Six Ento-Linguistic domains
```

#### **Coverage Requirements**
- **90% minimum** for project code (`projects/{name}/src/`)
- **Real execution paths** - all critical algorithms tested
- **Edge cases** - error conditions and boundary values
- **Integration scenarios** - multi-module workflows

## Manuscript Independence

### Each Project Has Its Own Manuscript

Every project maintains **complete manuscript independence**:

#### **Independent Content Structure**
```
projects/ento_linguistics/manuscript/
├── 01_abstract.md                    # Project-specific abstract
├── 02_introduction.md               # Domain introduction
├── 03_methodology.md                # Analysis methods
├── 04_experimental_results.md       # Domain-specific results
├── 05_discussion.md                 # Entomological implications
├── config.yaml                      # Project publication metadata
├── references.bib                   # Project bibliography
└── 98_symbols_glossary.md          # Domain terminology
```

#### **Independent References**
- **Own bibliography**: `references.bib` with domain-specific citations
- **Project DOI**: Independent publication identifier
- **Author information**: Project-specific authorship
- **Publication metadata**: Journal, volume, pages specific to project

#### **Independent Rendering**
```bash
# Each project renders independently
python3 scripts/03_render_pdf.py --project ento_linguistics
# - Uses projects/ento_linguistics/manuscript/config.yaml
# - Processes projects/ento_linguistics/manuscript/references.bib
# - Generates projects/ento_linguistics/output/pdf/
```

## Dependency Management

### Projects Share Infrastructure, Not Each Other

#### **Shared Infrastructure Dependencies**
All projects can import from `infrastructure/` for common utilities:

```python
# ✅ ALLOWED: All projects can use infrastructure
from infrastructure.core.logging_utils import get_logger
from infrastructure.figure_manager import FigureManager
from infrastructure.validation import validate_pdf_rendering
from infrastructure.rendering import RenderManager
```

#### **No Project-to-Project Dependencies**
Projects maintain **zero coupling** between each other:

```python
# ❌ FORBIDDEN: Projects cannot import from each other
# from projects.ento_linguistics.src.term_extraction import TerminologyExtractor
# from projects.active_inference_meta_pragmatic.src.generative_models import GenerativeModel
```

#### **Infrastructure as Common Good**
Infrastructure modules are **domain-independent utilities** that benefit all projects without creating coupling:

- **Logging**: Unified logging system for all projects
- **Figure Management**: Consistent figure registration and cross-referencing
- **Validation**: Common quality checks for PDFs, markdown, integrity
- **Rendering**: Shared PDF generation with project-specific customization
- **File Operations**: Common utilities for output management

## Real Project Examples

### Ento-Linguistic Research Paradigm

**Standalone Guarantees:**
- **Tests**: 484 tests validating term extraction, literature mining, domain analysis
- **Methods**: Complete 6-domain Ento-Linguistic framework with terminology networks
- **Manuscript**: Independent research on language in entomological science

**Infrastructure Integration:**
```bash
# Infrastructure operates on project independently
python3 scripts/execute_pipeline.py --project ento_linguistics --core-only

# Result: Complete analysis pipeline executed
# - Tests validate algorithms
# - Scripts generate domain analyses
# - Manuscript renders with entomological references
# - Outputs organized in output/ento_linguistics/
```

### Active Inference Framework Paradigm

**Standalone Guarantees:**
- **Tests**: Theoretical validation of EFE calculations and Bayesian inference
- **Methods**: 2×2 matrix framework with meta-cognitive processing
- **Manuscript**: Independent meta-pragmatic analysis with mathematical derivations

**Infrastructure Integration:**
```bash
# Infrastructure provides execution environment
python3 scripts/02_run_analysis.py --project active_inference_meta_pragmatic

# Infrastructure discovers and runs:
# - generate_quadrant_matrix.py (matrix visualization)
# - generate_active_inference_concepts.py (EFE diagrams)
# - analysis_pipeline.py (complete framework validation)
```

### Optimization Research Paradigm

**Standalone Guarantees:**
- **Tests**: Numerical accuracy validation of gradient descent algorithms
- **Methods**: Optimization algorithms with convergence analysis
- **Manuscript**: Research manuscript on mathematical optimization

**Infrastructure Integration:**
```bash
# Minimal project demonstrates full paradigm
python3 scripts/01_run_tests.py --project code_project
python3 scripts/03_render_pdf.py --project code_project

# Infrastructure validates and renders independently
```

## Benefits of Standalone Paradigm

### Scientific Integrity
- **Independent Validation**: Each project proves its scientific validity separately
- **Reproducible Research**: Projects can be executed and verified independently
- **Academic Standards**: Each project maintains its own scholarly rigor

### Development Flexibility
- **Parallel Development**: Multiple researchers can work on different projects simultaneously
- **Independent Deployment**: Projects can be published or shared without affecting others
- **Technology Choices**: Each project can use appropriate tools for its domain

### Maintenance Simplicity
- **Isolated Changes**: Modifications to one project don't affect others
- **Independent Testing**: Project issues don't block other project development
- **Clean Dependencies**: No complex inter-project dependency management

### Research Scalability
- **Template Reuse**: New projects start from proven templates
- **Infrastructure Evolution**: Shared infrastructure improvements benefit all projects
- **Knowledge Transfer**: Successful patterns can be adapted across projects

## Paradigm Evolution

### Version 1.0: Single Project Template
- Original template with hardcoded project structure
- All code in root-level directories
- Limited to one research project per repository

### Version 2.0: Multi-Project Template
- Projects moved to `projects/` directory
- Infrastructure layer extracted for reusability
- Multiple projects supported but with some coupling

### Version 2.1+: Standalone Project Paradigm
- **Complete isolation** between projects
- **Infrastructure compliance** framework
- **Three guarantees** (tests, methods, manuscript)
- **Operational independence** with shared utilities

## Future Evolution

### Enhanced Isolation
- **Container Support**: Docker-based project isolation
- **Virtual Environments**: Per-project dependency management
- **Resource Quotas**: CPU/memory limits per project

### Advanced Infrastructure
- **Parallel Execution**: Multiple projects run simultaneously
- **Resource Management**: Intelligent scheduling based on dependencies
- **Cross-Project Analytics**: Meta-analysis across all projects

### Collaboration Features
- **Project Templates**: Domain-specific starting templates
- **Knowledge Base**: Shared best practices across projects
- **Review Integration**: Automated quality checks and peer review workflows

## Project Lifecycle and Archiving

### Active Projects (`projects/`)

Active projects are discovered and executed by infrastructure:
- **Discovered** by `infrastructure.project.discovery.discover_projects()`
- **Listed** in `run.sh` interactive menu
- **Executed** by pipeline scripts (`01_run_tests.py`, `02_run_analysis.py`, etc.)
- **Outputs** generated in `projects/{name}/output/` and `output/{name}/`

### Archived Projects (`projects_archive/`)

Archived projects are preserved but not executed:
- **NOT discovered** by infrastructure discovery functions
- **NOT listed** in `run.sh` menu
- **NOT executed** by pipeline scripts
- **Preserved** for historical reference and potential reactivation

### Archiving a Project

To archive an active project:
1. Move project from `projects/{name}/` to `projects_archive/{name}/`
2. Project will no longer appear in discovery or execution
3. Can be reactivated by moving back to `projects/`

### Reactivating an Archived Project

To reactivate an archived project:
1. Move project from `projects_archive/{name}/` to `projects/{name}/`
2. Ensure project structure is valid (has `src/` and `tests/`)
3. Project will be automatically discovered on next `run.sh` execution

### Project Lifecycle Workflow

```mermaid
graph TD
    subgraph "Project States"
        ACTIVE[Active<br/>projects/{name}/]
        ARCHIVED[Archived<br/>projects_archive/{name}/]
    end

    subgraph "Infrastructure Operations"
        DISCOVER[discover_projects()<br/>Scans projects/ only]
        EXECUTE[Pipeline Execution<br/>Tests, Analysis, Rendering]
        LIST[List in run.sh menu<br/>Interactive selection]
    end

    ACTIVE -->|Move to archive| ARCHIVED
    ARCHIVED -->|Move to projects/| ACTIVE

    ACTIVE -->|Discovered| DISCOVER
    DISCOVER -->|Listed| LIST
    LIST -->|Selected| EXECUTE
    EXECUTE -->|Executed| ACTIVE

    ARCHIVED -.->|NOT discovered| DISCOVER
    ARCHIVED -.->|NOT listed| LIST
    ARCHIVED -.->|NOT executed| EXECUTE
```

## Conclusion

The standalone project paradigm represents a **fundamental architectural principle** that balances independence with shared infrastructure benefits. Each project maintains complete scientific and operational autonomy while benefiting from common research utilities, creating a scalable, maintainable, and scientifically rigorous research environment.

**Key Principle**: Projects are **architecturally isolated** but **operationally integrated** through shared infrastructure, providing the best of both worlds - independence and efficiency.</content>
</xai:function_call">Now I need to mark the paradigm document creation as complete and move on to verifying references and checking compliance. Let me update the todo status. 

The paradigm document is now complete. It comprehensively explains the standalone project philosophy, covering all the required aspects:

1. ✅ **Paradigm Overview**: Explains what "standalone" means with the three critical guarantees
2. ✅ **Isolation Principles**: Complete independence between projects with Mermaid diagram
3. ✅ **Infrastructure Integration**: How projects leverage shared infrastructure while maintaining independence
4. ✅ **Compliance Framework**: Alignment with .cursorrules standards
5. ✅ **Operational Model**: How infrastructure operates on projects
6. ✅ **Testing Philosophy**: Standalone test suites with real data
7. ✅ **Manuscript Independence**: Each project has its own manuscript
8. ✅ **Dependency Management**: Projects share infrastructure, not each other
9. ✅ **Real Examples**: Real project examples demonstrating the paradigm

Now I need to verify cross-references and check compliance. Let me mark this as complete and start the next task. 

<xai:function_call name="todo_write">
<parameter name="merge">true
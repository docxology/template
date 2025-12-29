# Architecture Documentation

## Overview

The `docs/architecture/` directory contains comprehensive documentation of the Research Project Template's system architecture, design patterns, and implementation decisions. This directory provides the technical foundation for understanding how the template is structured and why.

## Directory Structure

```
docs/architecture/
├── AGENTS.md                    # This technical documentation
├── DECISION_TREE.md            # Code placement decision guide
├── README.md                   # Quick reference and navigation
├── THIN_ORCHESTRATOR_SUMMARY.md # Thin orchestrator pattern details
└── TWO_LAYER_ARCHITECTURE.md   # Complete architecture specification
```

## Key Documentation Files

### Two-Layer Architecture (`TWO_LAYER_ARCHITECTURE.md`)

**Comprehensive architecture specification covering:**
- **Layer 1 (Infrastructure)**: Generic, reusable build/validation tools
- **Layer 2 (Project)**: Domain-specific algorithms and analysis
- **Separation principles**: Clear boundaries between generic and project-specific code
- **Reusability patterns**: How infrastructure modules work across projects
- **Integration mechanisms**: How layers communicate and coordinate

**Key Concepts:**
- Infrastructure layer contains tools usable by any research project
- Project layer contains domain-specific scientific code
- Thin orchestrator pattern for clean separation of concerns
- Modular design enabling independent development and testing

### Thin Orchestrator Pattern (`THIN_ORCHESTRATOR_SUMMARY.md`)

**Detailed implementation of the thin orchestrator architectural pattern:**

**Pattern Principles:**
- **Business Logic Location**: All computation in `projects/{name}/src/` or `infrastructure/` modules
- **Orchestrator Role**: Scripts coordinate execution, handle I/O only
- **Dependency Direction**: Scripts import from modules, not vice versa
- **Violation Prevention**: Pattern enforced through code review and testing

**Implementation Details:**
- Root entry points (`scripts/`) discover and invoke `project/scripts/`
- Project scripts import from `projects/{name}/src/` for computation
- Infrastructure scripts import from `infrastructure/` modules
- All orchestration is thin: minimal logic, maximum delegation

### Decision Tree (`DECISION_TREE.md`)

**Practical guide for code placement decisions:**

**Decision Framework:**
- **New generic tool?** → `infrastructure/`
- **Project-specific algorithm?** → `project/src/`
- **Analysis workflow?** → `project/scripts/`
- **Build orchestration?** → `scripts/` (generic) or `project/scripts/` (project-specific)

**Placement Rules:**
- Infrastructure code must be domain-independent
- Project code can import from infrastructure but not vice versa
- Scripts orchestrate but don't implement business logic
- Tests mirror code structure for clear organization

## Architecture Principles

### 1. Two-Layer Separation

**Infrastructure Layer (Layer 1)**
- Generic tools reusable across projects
- Domain-independent functionality
- Comprehensive testing (60-100% coverage)
- Version-controlled with project

**Project Layer (Layer 2)**
- Domain-specific scientific algorithms
- Project-specific analysis workflows
- High testing standards (90%+ coverage)
- Customizable per research project

### 2. Thin Orchestrator Pattern

**Business Logic Placement:**
- Core algorithms in `projects/{name}/src/` modules
- Infrastructure tools in `infrastructure/` modules
- Scripts contain only orchestration logic

**Orchestration Responsibilities:**
- Discover and execute appropriate modules
- Handle input/output operations
- Coordinate between components
- Provide user interface and error handling

### 3. Modular Design

**Module Organization:**
- Each module has single responsibility
- Clear public APIs with type hints
- Comprehensive documentation
- Independent testability

**Inter-Module Communication:**
- Explicit imports (no circular dependencies)
- Shared utilities in `infrastructure/core/`
- Consistent error handling patterns
- Standardized configuration management

## Implementation Details

### File Organization

**Infrastructure Modules:**
```
infrastructure/
├── core/          # Shared utilities (logging, config, exceptions)
├── validation/    # Quality assurance tools
├── documentation/ # Documentation generation
├── rendering/     # Multi-format output generation
├── publishing/    # Academic publishing workflows
└── llm/          # Local LLM integration
```

**Project Structure:**
```
project/
├── src/          # Scientific algorithms and analysis
├── scripts/      # Analysis workflow orchestration
├── tests/        # Project test suite
└── manuscript/   # Research manuscript
```

### Build Pipeline Integration

**Stage Execution:**
1. **Setup** (`00_setup_environment.py`): Environment validation
2. **Testing** (`01_run_tests.py`): Coverage validation for both layers
3. **Analysis** (`02_run_analysis.py`): Execute `project/scripts/` workflows
4. **Rendering** (`03_render_pdf.py`): Generate outputs using infrastructure tools
5. **Validation** (`04_validate_output.py`): Quality checks with infrastructure validators
6. **Copy** (`05_copy_outputs.py`): Deliver final outputs

**Infrastructure Usage:**
- Rendering stage uses `infrastructure/rendering/`
- Validation stage uses `infrastructure/validation/`
- Documentation generation uses `infrastructure/documentation/`
- Publishing workflows use `infrastructure/publishing/`

## Quality Assurance

### Testing Architecture

**Test Organization:**
- `tes../../infrastructure/` mirrors `infrastructure/` structure
- `tes../../projects/project/` mirrors `project/` structure
- Integration tests in `tests/integration/`
- 100% coverage requirement for project code
- 60%+ coverage requirement for infrastructure

**Test Principles:**
- Real data analysis (no mocks)
- Deterministic, reproducible results
- Integration testing for end-to-end workflows
- Performance benchmarking included

### Validation Gates

**Pre-Build Validation:**
- Markdown structure validation
- Cross-reference integrity checking
- Image and link resolution verification

**Post-Build Validation:**
- PDF rendering quality assessment
- File integrity verification
- Output completeness checking

## Configuration Management

### Environment Variables

**Standard Variables:**
- `LOG_LEVEL`: Logging verbosity (0-3)
- `AUTHOR_NAME`: Manuscript author
- `PROJECT_TITLE`: Research title
- `AUTHOR_ORCID`: Academic identifier

**Module-Specific Variables:**
- `OLLAMA_HOST`: LLM service endpoint
- `ZENODO_TOKEN`: Publishing API token
- `GITHUB_TOKEN`: Repository automation

### Configuration Files

**Project Configuration (`project/manuscript/config.yaml`):**
```yaml
paper:
  title: "Research Title"
  version: "1.0"

authors:
  - name: "Dr. Jane Smith"
    orcid: "0000-0000-0000-1234"

llm:
  translations:
    enabled: true
```

## Usage Examples

### Architecture Navigation

```bash
# Start with system overview
cat do../core/ARCHITECTURE.md

# Understand layer separation
cat docs/architecture/TWO_LAYER_ARCHITECTURE.md

# Learn orchestrator pattern
cat docs/architecture/THIN_ORCHESTRATOR_SUMMARY.md

# Make code placement decisions
cat docs/architecture/DECISION_TREE.md
```

### Development Workflow

```bash
# 1. Understand where code belongs
# Use DECISION_TREE.md to determine placement

# 2. Implement business logic
# Place in appropriate module (infrastructure/ or projects/{name}/src/)

# 3. Create orchestrator script
# Thin script in scripts/ or project/scripts/

# 4. Add comprehensive tests
# Mirror code structure in tests/ directory

# 5. Update documentation
# Modify AGENTS.md files for changed modules
```

## Common Patterns

### Adding Infrastructure Tools

1. **Create module directory**: `infrastructure/new_module/`
2. **Implement core logic**: `infrastructure/new_module/core.py`
3. **Add CLI interface**: `infrastructure/new_module/cli.py` (optional)
4. **Write comprehensive tests**: `tes../../infrastructure/test_new_module/`
5. **Document functionality**: `infrastructure/new_module/AGENTS.md`
6. **Update system docs**: Modify root `AGENTS.md` and architecture docs

### Adding Project Features

1. **Implement algorithm**: `projects/{name}/src/new_feature.py`
2. **Create analysis script**: `project/scripts/analyze_new_feature.py`
3. **Add tests**: `proje../../tests/test_new_feature.py`
4. **Update documentation**: `projects/{name}/src/AGENTS.md`
5. **Integrate with pipeline**: Modify `scripts/02_run_analysis.py` if needed

## Troubleshooting

### Architecture Violations

**Symptom**: Code placement confusion, circular imports

**Diagnosis:**
- Review `DECISION_TREE.md` for placement guidance
- Check `THIN_ORCHESTRATOR_SUMMARY.md` for pattern compliance
- Examine import structure for violations

**Resolution:**
- Move misplaced code to correct location
- Refactor orchestrators to be thin
- Update import statements accordingly

### Testing Coverage Issues

**Symptom**: Coverage requirements not met

**Diagnosis:**
- Run coverage analysis: `pytest --cov=infrastructure --cov-report=html`
- Identify untested code paths
- Check test organization matches code structure

**Resolution:**
- Add missing test cases
- Refactor code for better testability
- Update test structure to mirror code organization

## Future Architecture Evolution

### Planned Enhancements

**Modular Expansion:**
- Additional infrastructure modules (data visualization, collaboration tools)
- Enhanced LLM integration capabilities
- Extended publishing platform support

**Architecture Improvements:**
- Plugin system for custom modules
- Enhanced configuration management
- Improved cross-project reusability

### Maintenance Guidelines

**Regular Reviews:**
- Quarterly architecture documentation review
- Annual pattern compliance audit
- Continuous integration testing validation

**Evolution Process:**
- Document architecture changes in `TWO_LAYER_ARCHITECTURE.md`
- Update decision trees for new patterns
- Maintain backward compatibility
- Communicate changes through documentation updates

## See Also

**Related Documentation:**
- [`../core/ARCHITECTURE.md`](../core/ARCHITECTURE.md) - System architecture overview
- [`../core/WORKFLOW.md`](../core/WORKFLOW.md) - Development workflow
- [`../../infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md) - Infrastructure implementation
- [`../../projects/project/src/AGENTS.md`](../../projects/project/src/AGENTS.md) - Project implementation

**System Documentation:**
- [`../../AGENTS.md`](../../AGENTS.md) - Complete system overview
- [`../DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md) - Documentation index
- [`../../README.md`](../../README.md) - Project overview
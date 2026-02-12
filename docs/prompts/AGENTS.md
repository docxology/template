# docs/prompts/ - AI Prompt Templates

> **Technical Documentation** for expertly crafted prompt templates that ensure compliance with Research Project Template standards

**Quick Reference:** [README.md](README.md) | [Manuscript Creation](manuscript_creation.md) | [Code Development](code_development.md)

## Overview

The `docs/prompts/` directory contains specialized prompt templates designed to guide AI assistants and developers in creating work that complies with the template's standards and architecture. Each prompt leverages specific documentation sources to ensure high-quality, standards-compliant output.

## Architecture Integration

### Two-Layer Architecture Compliance

All prompts enforce the template's two-layer architecture:

**Infrastructure Layer (Generic)**
- Reusable across research projects
- Domain-independent utilities
- testing (60%+ coverage)
- Stable, version-controlled APIs

**Project Layer (Domain-Specific)**
- Custom research algorithms
- Project-specific analysis
- High testing standards (90%+ coverage)
- Flexible and adaptable

**Prompt Enforcement:**
- Infrastructure prompts target generic layer development
- Project prompts target domain-specific layer development
- All prompts validate architecture compliance

### Thin Orchestrator Pattern Integration

Prompts requiring code development enforce the thin orchestrator pattern:

**Business Logic in Modules:**
- Computational algorithms in `src/` modules
- Data processing in dedicated functions
- Analysis methods in pure functions
- Error handling with custom exceptions

**Orchestration in Scripts:**
- Thin coordination layer in `scripts/`
- Import and call module functions
- Handle I/O and configuration
- Provide user feedback

## Prompt File Structure

Each prompt file follows a standardized structure:

```markdown
# Prompt Title

## Purpose
Brief description of when to use this prompt

## Context
What documentation and standards this prompt leverages

## Prompt Template
The actual prompt text that can be copied and customized

## Key Requirements
- Checklist of requirements
- References to specific documentation
- Standards compliance notes

## Example Usage
Example of how to use the prompt

## Related Documentation
Links to relevant docs
```

## Prompt Technical Documentation

### Manuscript Creation Prompt (`manuscript_creation.md`)

**Technical Details:**
- **Target:** manuscript generation from research description
- **Complexity:** High - requires understanding of full research workflow
- **Output:** manuscript structure with all sections

**Documentation Leveraged:**
- [`../../.cursorrules/manuscript_style.md`](../../.cursorrules/manuscript_style.md) - Section numbering, cross-references, equation formatting
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing and standards compliance
- [`../core/workflow.md`](../core/workflow.md) - Research workflow integration

**Key Requirements Enforced:**
- Section numbering system (01-09, S01-S0N, 98-99)
- Cross-referencing patterns (\ref{}, \eqref{}, \cite{})
- Equation formatting (equation environment, labels)
- Figure/table integration (relative paths, captions, labels)
- Testing requirements (90% coverage for project code)
- Validation compliance (markdown and PDF validation)

**Architecture Compliance:**
- Generates project structure following two-layer architecture
- Includes scripts for analysis workflows
- Creates tests with data (no mocks)
- Produces documentation following AGENTS.md patterns

### Code Development Prompt (`code_development.md`)

**Technical Details:**
- **Target:** Standards-compliant code development
- **Complexity:** Medium - requires understanding of multiple standards
- **Output:** Production-ready code with tests and documentation

**Documentation Leveraged:**
- [`../../.cursorrules/`](../../.cursorrules/) directory - All development standards
- [`../core/workflow.md`](../core/workflow.md) - Development workflow
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Standards compliance

**Key Requirements Enforced:**
- Type hints on all public APIs (mypy compliant)
- Error handling with custom exceptions and proper chaining
- Logging using unified `get_logger(__name__)` system
- Code style following Black formatting and isort
- API design with consistent signatures and keyword-only parameters
- docstrings (Google-style)

**Architecture Compliance:**
- Places code in appropriate layer (infrastructure vs project)
- Follows thin orchestrator pattern for scripts
- Includes testing with data
- Provides documentation (AGENTS.md, README.md)

### Test Creation Prompt (`test_creation.md`)

**Technical Details:**
- **Target:** test suite creation
- **Complexity:** Medium - requires understanding of testing standards
- **Output:** test suite with high coverage

**Documentation Leveraged:**
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing standards and no-mocks policy
- [`../development/testing-guide.md`](../development/testing-guide.md) - Testing expansion strategy

**Key Requirements Enforced:**
- **No Mocks Policy:** data testing only (pytest-httpserver for HTTP)
- **Coverage Requirements:** 90% project, 60% infrastructure minimum
- **Test Organization:** Clear structure with fixtures and parametrization
- **TDD Approach:** Tests written before/alongside code
- **Data Patterns:** Use actual datasets, not synthetic mocks

**Architecture Compliance:**
- Tests appropriate layer (infrastructure vs project tests)
- Validates thin orchestrator pattern implementation
- Ensures module isolation and proper imports
- Confirms documentation accuracy through testing

### Refactoring Prompt (`refactoring.md`)

**Technical Details:**
- **Target:** Code improvement following clean break approach
- **Complexity:** High - requires understanding of refactoring standards
- **Output:** Improved code with maintained functionality

**Documentation Leveraged:**
- [`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md) - Code quality standards
- [`../core/workflow.md`](../core/workflow.md) - Development workflow and refactoring

**Key Requirements Enforced:**
- **Clean Break Approach:** No backward compatibility, full migration
- **Modularization:** Clear separation of concerns, single responsibility
- **Testing During Refactor:** Full coverage before changes, validation after
- **Safety Measures:** Incremental changes with rollback procedures
- **Documentation Updates:** AGENTS.md and README.md updates during refactor

**Architecture Compliance:**
- Maintains two-layer architecture separation
- Preserves thin orchestrator pattern
- Updates module interfaces appropriately
- Ensures infrastructure reusability

### Feature Addition Prompt (`feature_addition.md`)

**Technical Details:**
- **Target:** feature development with architecture compliance
- **Complexity:** High - requires understanding of full development workflow
- **Output:** feature implementation with all supporting elements

**Documentation Leveraged:**
- [`../core/workflow.md`](../core/workflow.md) - Development workflow
- [`../core/architecture.md`](../core/architecture.md) - Architecture principles
- [`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md) - Module development standards

**Key Requirements Enforced:**
- **Two-Layer Architecture:** Correct layer placement (infrastructure vs project)
- **Thin Orchestrator Pattern:** Proper separation of computation and coordination
- **Workflow:** Planning through validation
- **Testing Requirements:** 90% coverage for project features, 60% for infrastructure
- **Documentation:** AGENTS.md, README.md, and inline documentation

**Architecture Compliance:**
- Validates feature placement in appropriate layer
- Ensures proper module organization
- Confirms script orchestration patterns
- Validates cross-module integration

### Documentation Creation Prompt (`documentation_creation.md`)

**Technical Details:**
- **Target:** Standards-compliant documentation creation
- **Complexity:** Medium - requires understanding of documentation standards
- **Output:** AGENTS.md and README.md files

**Documentation Leveraged:**
- [`../../.cursorrules/documentation_standards.md`](../../.cursorrules/documentation_standards.md) - Documentation writing standards
- [`../../docs/AGENTS.md`](../../docs/AGENTS.md) - Documentation organization guide

**Key Requirements Enforced:**
- **AGENTS.md Structure:** technical documentation with all required sections
- **README.md Pattern:** Quick reference with Mermaid diagrams
- **Code Documentation:** Google-style docstrings with examples
- **Cross-References:** Proper linking between documents using relative paths
- **Show Don't Tell:** Examples rather than lengthy explanations

**Architecture Compliance:**
- Documents appropriate layer (infrastructure vs project)
- Explains architectural patterns and decisions
- Provides clear usage examples
- Maintains documentation hierarchy

### Infrastructure Module Prompt (`infrastructure_module.md`)

**Technical Details:**
- **Target:** Generic, reusable infrastructure module development
- **Complexity:** High - requires understanding of infrastructure standards
- **Output:** Production-ready infrastructure module with testing

**Documentation Leveraged:**
- [`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md) - Infrastructure development standards
- [`../core/architecture.md`](../core/architecture.md) - Infrastructure layer architecture

**Key Requirements Enforced:**
- **Generic Focus:** Reusable across research projects, domain-independent
- **60% Coverage:** Minimum test coverage requirement
- **Public API:** Clear `__init__.py` exports, documentation
- **Error Handling:** Custom exceptions with proper context
- **Type Hints:** type annotations on all APIs

**Architecture Compliance:**
- Strictly infrastructure layer (generic utilities)
- Clear separation from project-specific code
- Reusable across multiple projects
- Stable, version-controlled APIs

### Validation Quality Prompt (`validation_quality.md`)

**Technical Details:**
- **Target:** Quality assurance and validation procedures
- **Complexity:** Medium - requires understanding of validation frameworks
- **Output:** validation and quality assessment

**Documentation Leveraged:**
- [`../../infrastructure/validation/AGENTS.md`](../../infrastructure/validation/AGENTS.md) - Validation procedures
- [`../../infrastructure/validation/`](../../infrastructure/validation/) modules - Validation implementation

**Key Requirements Enforced:**
- **Input Validation:** Data quality and format compliance checking
- **Process Validation:** Workflow correctness and error handling
- **Output Validation:** Result quality and format standards
- **Quality Metrics:** assessment frameworks
- **Validation Reporting:** Clear error reporting and recommendations

**Architecture Compliance:**
- Uses infrastructure validation modules
- Validates both infrastructure and project layers
- Ensures thin orchestrator pattern compliance
- Confirms documentation completeness

## Prompt Integration with Development Workflow

### Development Phase Integration

**Phase 1: Planning**
- Use `feature_addition.md` for feature planning
- Use `infrastructure_module.md` for infrastructure planning
- Use `manuscript_creation.md` for new project planning

**Phase 2: Implementation**
- Use `code_development.md` for code implementation
- Use `test_creation.md` for test development
- Use `documentation_creation.md` for documentation

**Phase 3: Quality Assurance**
- Use `validation_quality.md` for quality checking
- Use `refactoring.md` for code improvement
- Use `test_creation.md` for additional testing

### Standards Compliance Verification

Each prompt includes verification checklists:

**Code Quality Standards:**
- [ ] Type hints on all public APIs
- [ ] Error handling with custom exceptions
- [ ] Logging using unified system
- [ ] Code style compliance (Black, isort)
- [ ] API design consistency

**Testing Standards:**
- [ ] No mocks policy (data only)
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] Test organization (fixtures, parametrization)
- [ ] TDD approach followed

**Documentation Standards:**
- [ ] AGENTS.md structure - [ ] README.md with Mermaid diagrams
- [ ] Cross-references working
- [ ] Examples runnable and accurate

**Architecture Standards:**
- [ ] Two-layer architecture maintained
- [ ] Thin orchestrator pattern followed
- [ ] Module organization correct
- [ ] Layer separation enforced

## Best Practices for Using Prompts

### Prompt Customization

**Context Provision:**
- Provide specific project context when extending existing work
- Include clear objectives and constraints
- Specify expected deliverables and quality criteria

**Documentation References:**
- Include relevant documentation paths in prompts
- Reference specific standards being enforced
- Provide examples from existing codebase

**Validation Integration:**
- Include validation steps in prompts
- Reference appropriate validation modules
- Require compliance verification

### Quality Assurance

**Prompt Output Validation:**
- Verify standards compliance after generation
- Test all code examples for functionality
- Validate documentation structure and links
- Confirm architecture pattern adherence

**Integration Testing:**
- Test generated code in full workflow context
- Validate integration with existing modules
- Confirm end-to-end functionality
- Verify performance and resource usage

### Continuous Improvement

**Prompt Refinement:**
- Update prompts based on successful usage patterns
- Incorporate lessons learned from validation failures
- Add new requirements as standards evolve
- Maintain prompt accuracy with documentation changes

**Usage Analytics:**
- Track which prompts are most effective
- Identify areas where additional guidance is needed
- Monitor compliance rates and success metrics
- Update prompts based on user feedback

## Integration with CI/CD Pipeline

### Automated Validation

**Prompt Output Checks:**
```yaml
# CI/CD pipeline for prompt-generated content
prompt_validation:
  - name: Validate generated code
    run: python -m pytest generated_code/ --cov=generated_code --cov-fail-under=90

  - name: Check documentation standards
    run: ./validate_documentation.sh generated_docs/

  - name: Verify architecture compliance
    run: ./check_architecture_compliance.sh generated_code/
```

**Standards Enforcement:**
- Automated linting and formatting checks
- Coverage validation with minimum thresholds
- Documentation structure validation
- Architecture pattern verification

## See Also

### Related Documentation
- [`README.md`](README.md) - Quick reference guide
- [`../core/architecture.md`](../core/architecture.md) - System design principles
- [`../core/workflow.md`](../core/workflow.md) - Development workflow

### Standards Reference
- [`../../.cursorrules/README.md`](../../.cursorrules/README.md) - Development standards overview
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing standards
- [`../../.cursorrules/infrastructure_modules.md`](../../.cursorrules/infrastructure_modules.md) - Infrastructure standards

### Project Documentation
- [`../../projects/code_project/AGENTS.md`](../../projects/code_project/AGENTS.md) - Code project documentation
- [`../core/workflow.md`](../core/workflow.md) - Development workflow guide
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Standards compliance

---

## Technical Implementation Notes

**Prompt Structure Consistency:**
- All prompts follow identical structure for predictability
- Documentation references use relative paths for portability
- Requirements checklists ensure coverage
- Examples demonstrate practical application

**Standards Integration:**
- Prompts reference specific `.cursorrules/` files
- Requirements map directly to standards compliance matrix
- Validation procedures align with infrastructure validation modules
- Architecture patterns enforced through specific requirements

**Maintenance Strategy:**
- Prompts updated when standards evolve
- New requirements added as project matures
- Examples refreshed with successful implementations
- Cross-references validated regularly
# Assessment and Review Prompt

## Purpose

Conduct a assessment and review of all methods, tests, documentation, sections, and markdown files in the research template system. Ensure full test success, validate all real (no mocks) data analysis, and verify proper matched manuscript references.

## Assessment Scope

### 1. Test Suite Analysis
**Current Status**: ✅ All tests passing, 83.33% infrastructure coverage (exceeds 60% requirement), code_project coverage exceeds 90% requirement

**Completed Actions**:
- ✅ All project tests passing (code_project: 28/28, active_inference_meta_pragmatic: varies)
- ✅ Infrastructure test coverage: 83.33% (exceeds 60% minimum by 39%)
- ✅ Project test coverage: code_project 94.1% (exceeds 90% minimum)
- ✅ No mock methods - all tests use data and computations
- ✅ Deterministic test results with fixed seeds

### 2. Code Quality Review

#### Infrastructure Modules
- **Path Import Issues**: Fix infrastructure import failures in scripts (generate_research_figures.py)
- **Error Handling**: Ensure graceful degradation when infrastructure unavailable
- **Module Dependencies**: Validate proper cross-module imports
- **Function Signatures**: Verify type hints and docstrings
- **Code Patterns**: Ensure consistent logging, error handling, configuration

#### Project Scripts
- **Thin Orchestrator Pattern**: Verify scripts only orchestrate, don't implement business logic
- **Path Management**: Ensure robust path detection for different execution environments
- **Error Recovery**: Test failure handling and informative error messages
- **Output Validation**: Confirm proper file generation and path reporting

#### Source Modules
- **Business Logic**: Ensure all algorithms in src/ modules
- **Data Processing**: Validate no mock data usage
- **API Consistency**: Check function signatures and return types
- **Edge Case Handling**: Test boundary conditions and error scenarios

### 3. Documentation Audit

#### AGENTS.md Files
**Required for every directory**:
- `infrastructure/` - Module architecture and usage
- `infrastructure/core/` - Foundation utilities
- `infrastructure/build/` - Build and reproducibility tools
- `infrastructure/validation/` - Quality assurance systems
- `infrastructure/documentation/` - Figure and content management
- `infrastructure/scientific/` - Scientific computing utilities
- `infrastructure/llm/` - AI assistance integration
- `infrastructure/rendering/` - Multi-format output generation
- `infrastructure/publishing/` - Academic dissemination
- `infrastructure/reporting/` - Pipeline reporting and aggregation
- `scripts/` - Orchestrator scripts and pipeline stages
- `tests/` - Test suite architecture and coverage requirements
- `projects/` - Multi-project management
- `projects/{name}/` - research unit (e.g., code_project, active_inference_meta_pragmatic)
- `projects/{name}/src/` - Scientific algorithms
- `projects/{name}/tests/` - Project validation
- `projects/{name}/scripts/` - Analysis workflows
- `projects/{name}/manuscript/` - Research content

**Content Requirements**:
- function signatures with type hints
- Usage examples and integration patterns
- Architecture diagrams (Mermaid format)
- Cross-reference validation
- Best practices and anti-patterns

#### README.md Files
- Quick start guides
- Essential commands and workflows
- Navigation aids and signposting
- Integration with broader system

### 4. Manuscript Reference Validation

#### Cross-Reference Integrity
- **Figure References**: Validate all `@fig:` references match generated figures
- **Equation References**: Ensure `@eq:` labels correspond to equations
- **Citation References**: Verify `@cite:` entries exist in bibliography
- **Section References**: Check `@sec:` links point to valid sections

#### Content Consistency
- **Figure Captions**: Match between markdown and generated figures
- **Table References**: Validate table numbering and content
- **Algorithm References**: Ensure algorithm labels are consistent
- **Appendix References**: Verify appendix cross-references

### 5. Build System Validation

#### Pipeline Stages
- **Stage 0**: Environment cleanup and preparation
- **Stage 1**: Test execution (infrastructure + project)
- **Stage 2**: Analysis script execution
- **Stage 3**: PDF rendering with validation
- **Stage 4**: Output integrity verification
- **Stage 5**: Deliverable copying
- **Stage 6**: Extended LLM review (optional)
- **Stage 7**: Multi-format rendering (optional)
- **Stage 8**: Publishing preparation (optional)
- **Stage 9**: Executive reporting (optional)

#### Quality Gates
- **Test Success**: All tests must pass before PDF generation
- **Coverage Requirements**: Infrastructure ≥60%, Project ≥90%
- **Manuscript Validation**: No unresolved references or broken links
- **Output Integrity**: All generated files must be valid and ### 6. Integration Testing

#### End-to-End Workflows
- **Data Generation → Analysis → Visualization**: pipeline testing
- **Manuscript → PDF → Validation**: Document generation verification
- **Multi-Project Execution**: Parallel project processing
- **Cross-Component Integration**: Module interoperability validation

#### Error Scenarios
- **Missing Dependencies**: Graceful handling of optional components
- **Network Failures**: Robust error recovery for external services
- **File System Issues**: Proper handling of permission and space problems
- **Configuration Errors**: Clear error messages for invalid settings

### 7. Performance and Scalability

#### Execution Time
- **Test Suite**: execution under 60 seconds
- **Individual Tests**: No test exceeding 10 seconds
- **Build Pipeline**: Full pipeline completion under 5 minutes
- **Memory Usage**: Reasonable resource consumption

#### Scalability Testing
- **Large Datasets**: Performance with increased data volumes
- **Complex Manuscripts**: Handling of extensive documents
- **Multiple Projects**: Concurrent project processing
- **Resource Monitoring**: CPU, memory, and disk usage tracking

### 8. Security and Reliability

#### Input Validation
- **LLM Prompts**: Sanitization and threat detection
- **File Paths**: Secure path handling and validation
- **Configuration**: Safe configuration loading
- **External Data**: Validation of imported datasets

#### Error Handling
- **Graceful Degradation**: System functionality when components fail
- **Informative Messages**: Clear error reporting for debugging
- **Recovery Mechanisms**: Automatic retry and recovery logic
- **Logging**: operation tracking

## Assessment Methodology

### 1. Automated Analysis
```bash
# Test coverage and success
python3 scripts/01_run_tests.py --project project

# Manuscript validation
python3 -m infrastructure.validation.cli markdown projects/code_project/manuscript/

# Output integrity
python3 -m infrastructure.validation.cli integrity projects/code_project/output/

# Cross-reference checking
python3 -m infrastructure.validation.cli refs projects/code_project/manuscript/
```

### 2. Manual Code Review
- **Function Signatures**: Verify type hints and parameter validation
- **Error Handling**: Check exception catching and user feedback
- **Code Patterns**: Ensure consistent logging and configuration
- **Documentation**: Validate docstrings and comments
- **Test Quality**: Assess test completeness and realism

### 3. Integration Verification
- **Pipeline Execution**: End-to-end workflow testing
- **Cross-Module Dependencies**: Import and interaction validation
- **Configuration Management**: Settings propagation and validation
- **Output Consistency**: Generated file verification

### 4. Documentation Review
- **Completeness**: All required AGENTS.md and README.md files present
- **Accuracy**: Technical information matches implementation
- **Navigation**: Clear signposting and cross-references
- **Examples**: Working code samples and usage patterns

## Quality Metrics

### Test Coverage Targets
- **Infrastructure**: ≥60% coverage (currently 83.33% - exceeds requirement by 39%)
- **Project Code**: ≥90% coverage (code_project: 94.1% - exceeds requirement)
- **Integration Tests**: workflow coverage (21/21 tests passing)
- **Error Paths**: Exception handling validation

### Documentation Standards
- **Function Documentation**: 100% of public APIs documented
- **Module Documentation**: AGENTS.md for all modules
- **Usage Examples**: Working code samples in documentation
- **Cross-References**: Valid internal and external links

### Code Quality Standards
- **Type Hints**: All public functions with type annotations
- **Error Handling**: exception management
- **Logging**: Consistent structured logging
- **Patterns**: Adherence to thin orchestrator principles

## Required Improvements

### Immediate Priority (Blocking)
1. ✅ Fix all 19 failing project tests - COMPLETED
2. ✅ Achieve minimum test coverage requirements - COMPLETED (exceeds all targets)
3. ✅ Resolve infrastructure import issues - COMPLETED
4. ✅ Validate manuscript cross-reference integrity - COMPLETED

### High Priority (Quality)
1. AGENTS.md documentation audit
2. Implement error handling
3. Add missing type hints and docstrings
4. Validate integration test coverage

### Medium Priority (Enhancement)
1. Performance optimization and monitoring
2. Security hardening and input validation
3. Documentation example validation
4. Build system robustness improvements

### Low Priority (Polish)
1. Code formatting and style consistency
2. Additional test scenarios and edge cases
3. Documentation clarity and navigation
4. Performance benchmarking and reporting

## Success Criteria

### Test Suite
- ✅ 0 failing tests
- ✅ ≥60% infrastructure coverage
- ✅ ≥90% project coverage
- ✅ All data analysis (no mocks)

### Documentation
- ✅ AGENTS.md coverage
- ✅ Accurate technical documentation
- ✅ Working code examples
- ✅ Clear navigation and signposting

### Manuscript
- ✅ All cross-references resolved
- ✅ Figure/table citations match generated content
- ✅ Bibliography entries - ✅ Mathematical notation validated

### Build System
- ✅ All pipeline stages functional
- ✅ Error recovery mechanisms
- ✅ Output validation passing
- ✅ Multi-project support working

### Code Quality
- ✅ Type hints on all public APIs
- ✅ error handling
- ✅ Consistent logging patterns
- ✅ Thin orchestrator pattern compliance

## Assessment Checklist

### Pre-Assessment
- [ ] Run full test suite and document failures
- [ ] Generate coverage reports
- [ ] Validate manuscript cross-references
- [ ] Check AGENTS.md completeness

### During Assessment
- [ ] Review each failing test and fix root cause
- [ ] Audit each module for code quality issues
- [ ] Validate documentation accuracy
- [ ] Test integration workflows

### Post-Assessment
- [ ] Verify all tests passing
- [ ] Confirm coverage requirements met
- [ ] Validate manuscript integrity
- [ ] Ensure documentation completeness

## Reporting Format

### Summary Report
```
Assessment Results
==================

Test Status: ✅ PASSED | ❌ FAILED
- Infrastructure: X% coverage (target: 60%)
- Project: X% coverage (target: 90%)
- Failures: X (target: 0)

Documentation: ✅ | ❌ INCOMPLETE
- AGENTS.md files: X/Y present
- README.md files: X/Y present
- Cross-references: ✅ VALID | ❌ BROKEN

Manuscript: ✅ VALID | ❌ INVALID
- References resolved: X/Y
- Figures matched: X/Y
- Citations: X/Y

Code Quality: ✅ PASSING | ❌ FAILING
- Type hints: X% coverage
- Error handling: ✅ ADEQUATE | ❌ INSUFFICIENT
- Patterns: ✅ CONSISTENT | ❌ INCONSISTENT
```

### Detailed Findings
- **Issues Found**: Categorized list of problems
- **Root Causes**: Technical analysis of failures
- **Fixes Applied**: Changes made during assessment
- **Remaining Work**: Outstanding improvements needed

### Recommendations
- **Priority Actions**: Immediate fixes required
- **Quality Improvements**: Non-blocking enhancements
- **Future Considerations**: Long-term improvements

## Usage

This prompt should be used for:
- **Code Reviews**: assessment of codebase health
- **Pre-Release Validation**: Ensuring system readiness
- **Quality Assurance**: Maintaining high standards
- **Onboarding**: Understanding system requirements and status

## Integration

This assessment integrates with:
- **Build Pipeline**: Automatic quality gates
- **CI/CD System**: Automated testing and validation
- **Documentation System**: Self-documenting requirements
- **Development Workflow**: TDD and quality assurance practices
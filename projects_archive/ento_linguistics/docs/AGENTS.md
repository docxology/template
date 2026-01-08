# Project Documentation

## Overview

The `project/docs/` directory contains project-specific documentation that complements the generic template infrastructure. This documentation covers implementation details, research methodologies, and operational procedures specific to the example research project.

## Directory Structure

```
project/docs/
├── AGENTS.md                       # This technical documentation
├── infrastructure_usage.md         # Infrastructure module usage guide
├── manuscript_style_guide.md       # Manuscript style features and examples
├── refactor_hotspots.md            # Code refactoring analysis
├── refactor_playbook.md            # Refactoring procedures and best practices
├── testing_expansion_plan.md       # Test coverage improvement plan
└── validation_guide.md             # Validation procedures and standards
```

## Key Documentation Files

### Infrastructure Usage Guide (`infrastructure_usage.md`)

**guide for using template infrastructure modules:**

**Module Integration Patterns:**
- How to import and use infrastructure modules in project code
- Best practices for infrastructure dependency management
- Examples of infrastructure module usage in research workflows

**Common Usage Patterns:**
```python
# Configuration management
from infrastructure.core import load_config
config = load_config()

# Logging integration
from infrastructure.core import get_logger
logger = get_logger(__name__)

# Validation usage
from infrastructure.validation import validate_pdf_rendering
validation_result = validate_pdf_rendering('output/manuscript.pdf')
```

**Infrastructure API Reference:**
- Core utilities (logging, config, exceptions)
- Validation modules (PDF, Markdown, integrity)
- Rendering capabilities (PDF, HTML, slides)
- Publishing workflows (Zenodo, GitHub, arXiv)

*See [`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md) for infrastructure development standards, [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) for logging patterns, and [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) for exception handling.*

### Manuscript Style Guide (`manuscript_style_guide.md`)

**documentation of manuscript style features with real examples:**

**Style Feature Documentation:**
- Section numbering system (01-09, S01-S0N, 98-99)
- Cross-referencing patterns (\ref{}, \eqref{}, \cite{})
- Citation styles and bibliography management
- Equation formatting (inline vs display, labels, numbering)
- Figure and table integration (placement, sizing, captions)
- Configuration and metadata management
- LaTeX preamble customization

**Implementation Examples:**
- Real examples extracted from all manuscript files
- Cross-reference patterns from `02_introduction.md`, `03_methodology.md`
- Equation examples from `03_methodology.md`, `S01_supplemental_methods.md`
- Figure/table examples from `04_experimental_results.md`
- Configuration examples from `config.yaml` and `config.yaml.example`
- Bibliography examples from `references.bib` and `99_references.md`

**Best Practices:**
- Common patterns used successfully in the manuscript
- Consistency guidelines across sections
- Common mistakes to avoid based on validation

*See [`.cursorrules/manuscript_style.md`](../../../.cursorrules/manuscript_style.md) for formatting standards, [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) for manuscript structure, and [`validation_guide.md`](validation_guide.md) for quality assurance.*

### Refactoring Analysis (`refactor_hotspots.md`)

**Code quality analysis and refactoring opportunities:**

**Code Quality Metrics:**
- Complexity analysis of existing code
- Test coverage assessment
- Performance bottleneck identification
- Maintainability evaluation

**Refactoring Opportunities:**
- Function decomposition recommendations
- Class hierarchy improvements
- Import organization optimization
- Error handling standardization

**Implementation Examples:**
```python
# Before: Monolithic function
def process_data(data):
    # Validation
    if not data:
        raise ValueError("No data provided")

    # Processing
    result = []
    for item in data:
        processed = item * 2
        result.append(processed)

    # Logging
    print(f"Processed {len(result)} items")

    return result

# After: Modular functions
def validate_data(data: List[float]) -> None:
    """Validate input data."""
    if not data:
        raise ValueError("No data provided")

def process_item(item: float) -> float:
    """Process individual data item."""
    return item * 2

def process_data(data: List[float]) -> List[float]:
    """Process data with validation and logging."""
    validate_data(data)

    result = [process_item(item) for item in data]

    logger.info(f"Processed {len(result)} items")
    return result
```

### Refactoring Playbook (`refactor_playbook.md`)

**Systematic approach to code refactoring:**

**Refactoring Process:**
1. **Identify Target**: Select code section for improvement
2. **Analyze Impact**: Assess changes required
3. **Plan Refactoring**: Design improvement approach
4. **Implement Changes**: Apply refactoring with tests
5. **Validate Results**: Ensure functionality preserved

**Refactoring Techniques:**
- Extract method/function
- Rename variables and functions
- Simplify conditional logic
- Remove code duplication
- Improve error handling

*See [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) for clean break refactoring standards, [`.cursorrules/api_design.md`](../../../.cursorrules/api_design.md) for API design patterns, and [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) for type annotation requirements.*

**Safety Measures:**
- test coverage before refactoring
- Incremental changes with validation
- Rollback procedures for failed refactoring
- Documentation updates during refactoring

### Testing Expansion Plan (`testing_expansion_plan.md`)

**Strategic plan for improving test coverage:**

**Current Coverage Assessment:**
- Infrastructure modules: 60% target achieved
- Project modules: 90% target achieved
- Integration tests: Critical path coverage
- Edge case testing: Gap identification

**Expansion Strategy:**
```python
# Test coverage improvement plan
class TestingExpansionPlan:
    """Plan for systematic test coverage improvement."""

    def assess_current_coverage(self):
        """Analyze current test coverage gaps."""
        return {
            'infrastructure_modules': self._analyze_infrastructure_coverage(),
            'project_modules': self._analyze_project_coverage(),
            'integration_scenarios': self._analyze_integration_coverage(),
            'edge_cases': self._identify_edge_cases()
        }

    def prioritize_improvements(self):
        """Prioritize testing improvements by impact."""
        priorities = [
            'critical_path_integration_tests',
            'error_condition_handling',
            'performance_regression_tests',
            'user_interface_validation'
        ]
        return priorities

    def implement_test_improvements(self):
        """Execute systematic test coverage improvements."""
        # 1. Add missing unit tests
        # 2. Implement integration test scenarios
        # 3. Add edge case validations
        # 4. Create performance benchmarks
        pass
```

**Implementation Roadmap:**
- Phase 1: Critical path integration tests
- Phase 2: Error handling and edge cases
- Phase 3: Performance and regression testing
- Phase 4: User experience validation

*See [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) for testing standards including no-mocks policy, [`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md) for infrastructure testing requirements, and [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) for error testing patterns.*

### Validation Guide (`validation_guide.md`)

**validation procedures and standards:**

**Validation Framework:**
- Input validation patterns
- Output quality assessment
- Error detection and reporting
- Validation result interpretation

**Quality Standards:**
```python
# Validation standards implementation
class ValidationStandards:
    """Standards for validation implementation."""

    def validate_input_data(self, data) -> ValidationResult:
        """Validate input data quality."""
        checks = [
            self._check_data_completeness(data),
            self._check_data_consistency(data),
            self._check_data_reasonableness(data)
        ]

        return ValidationResult(
            is_valid=all(checks),
            errors=[check for check in checks if not check.passed],
            warnings=[check for check in checks if check.warning]
        )

    def validate_output_quality(self, output) -> QualityResult:
        """Assess output quality metrics."""
        metrics = {
            'accuracy': self._measure_accuracy(output),
            'completeness': self._measure_completeness(output),
            'consistency': self._measure_consistency(output),
            'performance': self._measure_performance(output)
        }

        return QualityResult(
            score=self._calculate_overall_score(metrics),
            metrics=metrics,
            recommendations=self._generate_recommendations(metrics)
        )
```

**Validation Categories:**
- Data validation (input quality, format compliance)
- Process validation (workflow correctness, error handling)
- Output validation (result quality, format standards)
- Performance validation (efficiency, scalability)

*See [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) for testing patterns, [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) for error handling patterns, and [`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md) for infrastructure validation standards.*

## Documentation Integration

### Template Infrastructure Connection

**Infrastructure Usage Examples:**
```python
# Using infrastructure modules in project code
from infrastructure.core.logging_utils import get_logger
from infrastructure.validation.markdown_validator import validate_markdown

class ResearchAnalyzer:
    """Example research analysis class using infrastructure."""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)

    def analyze_data(self, data_path):
        """Analyze research data with infrastructure integration."""

        self.logger.info(f"Starting analysis of {data_path}")

        # Validate input if markdown documentation
        if str(data_path).endswith('.md'):
            validation = validate_markdown(data_path)
            if not validation.is_valid:
                self.logger.error(f"Invalid markdown: {validation.errors}")
                return None

        # Perform analysis
        results = self._perform_analysis(data_path)

        # Log completion
        self.logger.info(f"Analysis completed: {len(results)} findings")

        return results
```

### Quality Assurance Integration

**Testing and Validation Workflow:**
```python
# Integrated testing and validation approach
def research_workflow_with_quality_assurance():
    """research workflow with quality checks."""

    # 1. Load and validate configuration
    config = load_config()
    config_validation = validate_configuration(config)
    assert config_validation.is_valid, f"Invalid config: {config_validation.errors}"

    # 2. Set up logging
    logger = get_logger(__name__)
    logger.info("Starting research workflow")

    # 3. Validate input data
    data_validation = validate_input_data(input_files)
    if not data_validation.is_valid:
        logger.error(f"Data validation failed: {data_validation.errors}")
        return False

    # 4. Execute analysis with error handling
    try:
        results = perform_analysis(input_files, config)
    except AnalysisError as e:
        logger.error(f"Analysis failed: {e}")
        return False

    # 5. Validate output quality
    output_validation = validate_output_quality(results)
    if not output_validation.meets_standards:
        logger.warning(f"Output quality issues: {output_validation.issues}")

    # 6. Generate reports
    generate_analysis_report(results, output_validation)

    logger.info("Research workflow completed successfully")
    return True
```

## Maintenance and Evolution

### Documentation Updates

**Regular Maintenance Tasks:**
- Update infrastructure usage examples with features
- Refresh refactoring analysis based on code evolution
- Update testing plans as coverage improves
- Maintain validation standards as requirements change

**Version Synchronization:**
- Keep documentation aligned with code versions
- Update examples when APIs change
- Mark deprecated practices and migration paths
- Archive outdated documentation appropriately

### Quality Metrics

**Documentation Effectiveness:**
- Usage analytics (which docs are most accessed)
- User feedback on documentation clarity
- Example code execution success rates
- Documentation update frequency compliance

**Continuous Improvement:**
```python
# Documentation quality assessment
def assess_documentation_quality():
    """Evaluate documentation effectiveness."""

    metrics = {
        'completeness': check_documentation_completeness(),
        'accuracy': verify_example_accuracy(),
        'usability': measure_user_satisfaction(),
        'freshness': assess_update_frequency()
    }

    # Generate improvement recommendations
    improvements = []
    if metrics['accuracy'] < 0.9:
        improvements.append("Update outdated examples")
    if metrics['completeness'] < 0.8:
        improvements.append("Add missing documentation sections")

    return {
        'metrics': metrics,
        'improvements': improvements,
        'overall_score': sum(metrics.values()) / len(metrics)
    }
```

## Integration with Development Workflow

### Code Review Integration

**Documentation in Code Reviews:**
- Require AGENTS.md updates for modules
- Validate infrastructure usage examples
- Check testing expansion alignment
- Review validation guide compliance

**Quality Gates:**
```yaml
# CI/CD quality gates for documentation
documentation_checks:
  - name: Validate examples
    run: ./validate_documentation_examples.sh project/docs/

  - name: Check infrastructure usage
    run: ./validate_infrastructure_usage.sh project/docs/infrastructure_usage.md

  - name: Assess test coverage
    run: ./check_test_coverage_alignment.sh project/docs/testing_expansion_plan.md
```

### Development Standards

**Documentation Requirements:**
- All modules require AGENTS.md documentation
- Infrastructure usage must be documented
- Testing plans must be maintained and updated
- Validation procedures must be documented

**Review Checklist:**
- [ ] AGENTS.md exists for modules
- [ ] Infrastructure usage examples are current
- [ ] Testing plans reflect actual coverage
- [ ] Validation procedures are documented
- [ ] Examples execute successfully
- [ ] Cross-references are valid

## Future Enhancements

### Planned Documentation Improvements

**Content:**
- **Interactive Examples**: Executable code examples with live results
- **Video Tutorials**: Visual guides for complex procedures
- **API Playground**: Interactive infrastructure module testing
- **Best Practices Database**: Curated collection of implementation patterns

**Automation Integration:**
- **Auto-generated Examples**: Extract working examples from tests
- **Usage Analytics**: Track which documentation is most valuable
- **Feedback Integration**: User feedback directly improves documentation
- **Version Synchronization**: Automatic documentation updates with code changes

### Community Collaboration

**Documentation Contribution Process:**
1. **Identify Gap**: Find missing or unclear documentation
2. **Create Content**: Write documentation following standards
3. **Add Examples**: Include working code examples and use cases
4. **Validate**: Ensure examples work and documentation is accurate
5. **Review**: Get feedback from maintainers and contributors
6. **Publish**: Integrate into documentation system

## See Also

**Development Standards:**
- [`.cursorrules/AGENTS.md`](../../../.cursorrules/AGENTS.md) - Development standards overview
- [`.cursorrules/documentation_standards.md`](../../../.cursorrules/documentation_standards.md) - Documentation writing guide
- [`.cursorrules/infrastructure_modules.md`](../../../.cursorrules/infrastructure_modules.md) - Infrastructure module development standards
- [`.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing patterns and coverage standards
- [`.cursorrules/refactoring.md`](../../../.cursorrules/refactoring.md) - Refactoring standards and clean break approach
- [`.cursorrules/error_handling.md`](../../../.cursorrules/error_handling.md) - Error handling and exception patterns
- [`.cursorrules/python_logging.md`](../../../.cursorrules/python_logging.md) - Logging standards and best practices
- [`.cursorrules/type_hints_standards.md`](../../../.cursorrules/type_hints_standards.md) - Type annotation patterns
- [`.cursorrules/code_style.md`](../../../.cursorrules/code_style.md) - Code formatting and style standards
- [`.cursorrules/api_design.md`](../../../.cursorrules/api_design.md) - API design and interface standards

**Project Documentation:**
- [`../src/AGENTS.md`](../src/AGENTS.md) - Project source code documentation
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) - Project scripts documentation
- [`../tests/AGENTS.md`](../tests/AGENTS.md) - Project testing documentation

**Template Documentation:**
- [`../../docs/core/AGENTS.md`](../../docs/core/AGENTS.md) - Core template documentation
- [`../../infrastructure/AGENTS.md`](../../infrastructure/AGENTS.md) - Infrastructure overview
- [`../../AGENTS.md`](../../AGENTS.md) - Root template documentation
# Validation Quality Prompt

## Purpose

Perform comprehensive validation and quality assurance on Research Project Template components, ensuring all outputs meet standards and requirements through systematic validation procedures.

## Context

This prompt leverages the validation infrastructure to ensure quality and compliance:

- [`../../projects/project/docs/validation_guide.md`](../../projects/project/docs/validation_guide.md) - Validation procedures
- [`../../infrastructure/validation/`](../../infrastructure/validation/) modules - Validation implementation
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Quality standards

## Prompt Template

```
You are performing comprehensive validation and quality assurance for the Research Project Template. Use the validation infrastructure to ensure all components meet standards and requirements.

VALIDATION TARGET: [Specify what to validate: "code", "documentation", "manuscript", "project", "infrastructure"]
TARGET SCOPE: [Specify scope: "module", "project", "all_projects", "infrastructure"]
QUALITY LEVEL: [Specify level: "basic", "comprehensive", "production"]

VALIDATION REQUIREMENTS:

## 1. Validation Framework Integration

### Using Infrastructure Validation Modules
```python
# Import validation infrastructure
from infrastructure.validation import (
    validate_module_implementation,
    validate_project_structure,
    validate_manuscript_quality,
    validate_code_quality,
    validate_documentation_completeness
)

# Comprehensive validation result
from infrastructure.validation.core import ValidationResult, ValidationReport

def run_comprehensive_validation(target: str, scope: str) -> ValidationReport:
    """Run comprehensive validation suite.

    Args:
        target: What to validate ('code', 'documentation', 'manuscript', 'project', 'infrastructure')
        scope: Scope of validation ('module', 'project', 'all_projects', 'infrastructure')

    Returns:
        Comprehensive validation report
    """
    report = ValidationReport(target=target, scope=scope)

    # Run appropriate validations based on target and scope
    if target == 'code':
        report.add_result(validate_code_quality(scope))
    elif target == 'documentation':
        report.add_result(validate_documentation_completeness(scope))
    elif target == 'manuscript':
        report.add_result(validate_manuscript_quality(scope))
    elif target == 'project':
        report.add_result(validate_project_structure(scope))
    elif target == 'infrastructure':
        report.add_result(validate_module_implementation(scope))

    # Cross-validation checks
    report.add_result(validate_cross_references(scope))
    report.add_result(validate_integration_points(scope))

    return report
```

### Validation Categories

**Input Validation:**
```python
def validate_input_data(data: Any, requirements: Dict[str, Any]) -> ValidationResult:
    """Validate input data against requirements.

    Args:
        data: Input data to validate
        requirements: Validation requirements dictionary

    Returns:
        Validation result with pass/fail status and details
    """
    result = ValidationResult("input_validation")

    # Completeness checks
    if requirements.get('required', False) and data is None:
        result.add_error("Required data is missing")
        return result

    # Type validation
    expected_type = requirements.get('type')
    if expected_type and not isinstance(data, expected_type):
        result.add_error(f"Data type {type(data)} does not match expected {expected_type}")
        return result

    # Content validation
    if hasattr(data, '__len__') and len(data) == 0:
        if requirements.get('allow_empty', True) is False:
            result.add_error("Data cannot be empty")
            return result

    # Range validation
    min_val = requirements.get('min_value')
    max_val = requirements.get('max_value')
    if min_val is not None and data < min_val:
        result.add_error(f"Value {data} is below minimum {min_val}")
    if max_val is not None and data > max_val:
        result.add_error(f"Value {data} is above maximum {max_val}")

    result.mark_passed()
    return result
```

**Process Validation:**
```python
def validate_process_execution(process_func, inputs, expected_outputs) -> ValidationResult:
    """Validate process execution correctness.

    Args:
        process_func: Function to execute and validate
        inputs: Input parameters for the function
        expected_outputs: Expected output characteristics

    Returns:
        Validation result with execution details
    """
    result = ValidationResult("process_validation")

    try:
        # Execute process
        start_time = time.time()
        actual_output = process_func(*inputs)
        execution_time = time.time() - start_time

        # Validate execution time
        max_time = expected_outputs.get('max_execution_time')
        if max_time and execution_time > max_time:
            result.add_warning(f"Execution time {execution_time:.2f}s exceeds maximum {max_time}s")

        # Validate output type
        expected_type = expected_outputs.get('output_type')
        if expected_type and not isinstance(actual_output, expected_type):
            result.add_error(f"Output type {type(actual_output)} does not match expected {expected_type}")
            return result

        # Validate output characteristics
        output_checks = expected_outputs.get('output_checks', [])
        for check_func in output_checks:
            check_result = check_func(actual_output)
            if not check_result.passed:
                result.add_error(f"Output check failed: {check_result.message}")

        # Performance validation
        if 'performance_requirements' in expected_outputs:
            perf_result = validate_performance(execution_time, expected_outputs['performance_requirements'])
            if not perf_result.passed:
                result.add_warning(f"Performance requirement not met: {perf_result.message}")

        result.mark_passed()
        result.add_metric('execution_time', execution_time)
        result.add_metric('output_size', len(actual_output) if hasattr(actual_output, '__len__') else 0)

    except Exception as e:
        result.add_error(f"Process execution failed: {e}")

    return result
```

**Output Validation:**
```python
def validate_output_quality(output: Any, quality_standards: Dict[str, Any]) -> ValidationResult:
    """Validate output quality against standards.

    Args:
        output: Output to validate
        quality_standards: Quality standards dictionary

    Returns:
        Validation result with quality metrics
    """
    result = ValidationResult("output_quality")

    # Accuracy validation
    if 'accuracy_threshold' in quality_standards:
        accuracy = calculate_accuracy(output, quality_standards.get('reference_data'))
        if accuracy < quality_standards['accuracy_threshold']:
            result.add_error(f"Accuracy {accuracy:.3f} below threshold {quality_standards['accuracy_threshold']}")

    # Completeness validation
    if 'completeness_checks' in quality_standards:
        for check_name, check_func in quality_standards['completeness_checks'].items():
            check_result = check_func(output)
            if not check_result:
                result.add_error(f"Completeness check '{check_name}' failed")

    # Consistency validation
    if 'consistency_checks' in quality_standards:
        for check_name, check_func in quality_standards['consistency_checks'].items():
            check_result = check_func(output)
            if not check_result:
                result.add_error(f"Consistency check '{check_name}' failed")

    # Format validation
    if 'format_requirements' in quality_standards:
        format_result = validate_output_format(output, quality_standards['format_requirements'])
        if not format_result.passed:
            result.add_error(f"Format validation failed: {format_result.message}")

    result.mark_passed()
    return result

def calculate_accuracy(output: Any, reference: Any) -> float:
    """Calculate accuracy metric for output validation."""
    # Implementation depends on output type
    if isinstance(output, (list, np.ndarray)) and isinstance(reference, (list, np.ndarray)):
        return np.mean(np.abs(np.array(output) - np.array(reference)) < 1e-6)
    # Add more accuracy calculations as needed
    return 1.0  # Default to perfect accuracy if can't calculate

def validate_output_format(output: Any, format_reqs: Dict[str, Any]) -> ValidationResult:
    """Validate output format against requirements."""
    result = ValidationResult("format_validation")

    # Type checking
    if 'type' in format_reqs and not isinstance(output, format_reqs['type']):
        result.add_error(f"Output type {type(output)} does not match required {format_reqs['type']}")

    # Structure validation
    if 'structure' in format_reqs:
        structure_result = validate_data_structure(output, format_reqs['structure'])
        if not structure_result.passed:
            result.add_error(f"Structure validation failed: {structure_result.message}")

    result.mark_passed()
    return result
```

## 2. Quality Assurance Procedures

### Code Quality Validation
```python
def validate_code_quality(module_path: Path) -> ValidationReport:
    """Comprehensive code quality validation.

    Args:
        module_path: Path to module to validate

    Returns:
        Code quality validation report
    """
    report = ValidationReport("code_quality", str(module_path))

    # Type checking
    type_check_result = run_mypy_check(module_path)
    report.add_result(type_check_result)

    # Linting
    lint_result = run_flake8_check(module_path)
    report.add_result(lint_result)

    # Import sorting
    import_sort_result = run_isort_check(module_path)
    report.add_result(import_sort_result)

    # Test coverage
    coverage_result = run_coverage_check(module_path)
    report.add_result(coverage_result)

    # Code complexity
    complexity_result = analyze_code_complexity(module_path)
    report.add_result(complexity_result)

    # Documentation completeness
    doc_result = validate_docstring_completeness(module_path)
    report.add_result(doc_result)

    return report

def run_mypy_check(module_path: Path) -> ValidationResult:
    """Run mypy type checking."""
    result = ValidationResult("mypy_check")

    try:
        # Run mypy
        cmd = ["mypy", str(module_path), "--ignore-missing-imports"]
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode == 0:
            result.mark_passed()
        else:
            result.add_error(f"MyPy errors: {process.stdout}")

    except Exception as e:
        result.add_error(f"MyPy check failed: {e}")

    return result

def run_coverage_check(module_path: Path) -> ValidationResult:
    """Run test coverage analysis."""
    result = ValidationResult("coverage_check")

    try:
        # Determine coverage requirement based on module type
        is_infrastructure = 'infrastructure' in str(module_path)
        min_coverage = 60 if is_infrastructure else 90

        # Run pytest with coverage
        cmd = [
            "pytest",
            f"--cov={module_path}",
            f"--cov-fail-under={min_coverage}",
            "--cov-report=term-missing"
        ]
        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode == 0:
            result.mark_passed()
            result.add_metric('coverage_percentage', min_coverage)
        else:
            result.add_error(f"Coverage check failed: {process.stdout}")

    except Exception as e:
        result.add_error(f"Coverage check failed: {e}")

    return result
```

### Documentation Validation
```python
def validate_documentation_completeness(doc_path: Path) -> ValidationReport:
    """Validate documentation completeness and quality.

    Args:
        doc_path: Path to documentation to validate

    Returns:
        Documentation validation report
    """
    report = ValidationReport("documentation", str(doc_path))

    # Structure validation
    structure_result = validate_doc_structure(doc_path)
    report.add_result(structure_result)

    # Cross-reference validation
    cross_ref_result = validate_cross_references(doc_path)
    report.add_result(cross_ref_result)

    # Example validation
    example_result = validate_code_examples(doc_path)
    report.add_result(example_result)

    # Link validation
    link_result = validate_links(doc_path)
    report.add_result(link_result)

    return report

def validate_doc_structure(doc_path: Path) -> ValidationResult:
    """Validate documentation structure."""
    result = ValidationResult("doc_structure")

    try:
        content = doc_path.read_text()

        # Check for required sections
        required_sections = ["## Overview", "## API Reference", "## See Also"]
        for section in required_sections:
            if section not in content:
                result.add_warning(f"Missing section: {section}")

        # Check for proper heading hierarchy
        if content.count("# ") > 1:
            result.add_warning("Multiple H1 headings found")

        result.mark_passed()

    except Exception as e:
        result.add_error(f"Structure validation failed: {e}")

    return result

def validate_code_examples(doc_path: Path) -> ValidationResult:
    """Validate that code examples in documentation are syntactically correct."""
    result = ValidationResult("code_examples")

    try:
        content = doc_path.read_text()

        # Extract code blocks
        code_blocks = extract_markdown_code_blocks(content)

        for i, code_block in enumerate(code_blocks):
            if not validate_python_syntax(code_block):
                result.add_error(f"Code block {i+1} has syntax errors")

        result.mark_passed()

    except Exception as e:
        result.add_error(f"Example validation failed: {e}")

    return result
```

### Manuscript Validation
```python
def validate_manuscript_quality(manuscript_path: Path) -> ValidationReport:
    """Validate manuscript quality and compliance.

    Args:
        manuscript_path: Path to manuscript directory

    Returns:
        Manuscript validation report
    """
    report = ValidationReport("manuscript", str(manuscript_path))

    # Structure validation
    structure_result = validate_manuscript_structure(manuscript_path)
    report.add_result(structure_result)

    # Cross-reference validation
    cross_ref_result = validate_manuscript_cross_references(manuscript_path)
    report.add_result(cross_ref_result)

    # Content validation
    content_result = validate_manuscript_content(manuscript_path)
    report.add_result(content_result)

    # PDF compilation validation
    pdf_result = validate_pdf_compilation(manuscript_path)
    report.add_result(pdf_result)

    return report

def validate_manuscript_structure(manuscript_path: Path) -> ValidationResult:
    """Validate manuscript file structure and naming."""
    result = ValidationResult("manuscript_structure")

    # Check for required files
    required_files = [
        "01_abstract.md", "02_introduction.md", "03_methodology.md",
        "04_experimental_results.md", "05_discussion.md", "06_conclusion.md",
        "99_references.md", "config.yaml", "references.bib"
    ]

    for filename in required_files:
        if not (manuscript_path / filename).exists():
            result.add_error(f"Missing required file: {filename}")

    # Check section numbering
    md_files = list(manuscript_path.glob("*.md"))
    for file_path in md_files:
        filename = file_path.name
        if not validate_section_numbering(filename):
            result.add_error(f"Invalid section numbering: {filename}")

    result.mark_passed()
    return result

def validate_section_numbering(filename: str) -> bool:
    """Validate manuscript section numbering."""
    # Main sections: 01-09
    # Supplemental: S01-S0N
    # Reference: 98-99

    if filename.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_',
                          'S01_', 'S02_', 'S03_', 'S04_', 'S05_',
                          '98_', '99_')):
        return True

    return False
```

### Project Validation
```python
def validate_project_structure(project_path: Path) -> ValidationReport:
    """Validate complete project structure and compliance.

    Args:
        project_path: Path to project directory

    Returns:
        Project validation report
    """
    report = ValidationReport("project", str(project_path))

    # Required directories
    required_dirs = ["src", "tests", "manuscript"]
    for dir_name in required_dirs:
        dir_path = project_path / dir_name
        if not dir_path.exists():
            report.add_error(f"Missing required directory: {dir_name}")
        elif not dir_path.is_dir():
            report.add_error(f"{dir_name} is not a directory")

    # Test coverage validation
    coverage_result = validate_test_coverage(project_path)
    report.add_result(coverage_result)

    # Code quality validation
    quality_result = validate_code_quality(project_path / "src")
    report.add_result(quality_result)

    # Documentation validation
    docs_result = validate_documentation_completeness(project_path / "docs")
    report.add_result(docs_result)

    # Manuscript validation
    manuscript_result = validate_manuscript_quality(project_path / "manuscript")
    report.add_result(manuscript_result)

    return report

def validate_test_coverage(project_path: Path) -> ValidationResult:
    """Validate test coverage meets requirements."""
    result = ValidationResult("test_coverage")

    try:
        # Run coverage analysis
        coverage_cmd = [
            "pytest",
            str(project_path / "tests"),
            f"--cov={project_path / 'src'}",
            "--cov-report=json"
        ]

        process = subprocess.run(coverage_cmd, capture_output=True, text=True)

        if process.returncode == 0:
            # Parse coverage data
            coverage_data = json.loads((project_path / ".coverage.json").read_text())
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)

            if total_coverage >= 90:
                result.mark_passed()
                result.add_metric('coverage_percentage', total_coverage)
            else:
                result.add_error(f"Coverage {total_coverage:.1f}% below required 90%")
        else:
            result.add_error(f"Coverage analysis failed: {process.stderr}")

    except Exception as e:
        result.add_error(f"Coverage validation failed: {e}")

    return result
```

## 3. Validation Reporting and Analysis

### Comprehensive Validation Reports
```python
@dataclass
class ValidationReport:
    """Comprehensive validation report with detailed results."""

    target: str
    scope: str
    timestamp: datetime = field(default_factory=datetime.now)
    results: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: ValidationResult) -> None:
        """Add validation result to report."""
        self.results.append(result)
        self._update_summary()

    def _update_summary(self) -> None:
        """Update summary statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        self.summary.update({
            'total_validations': total,
            'passed': passed,
            'failed': failed,
            'success_rate': passed / total if total > 0 else 0,
            'overall_status': 'PASSED' if failed == 0 else 'FAILED'
        })

    def generate_report(self) -> str:
        """Generate human-readable validation report."""
        lines = [
            f"Validation Report for {self.target} ({self.scope})",
            f"Generated: {self.timestamp}",
            "=" * 50,
            "",
            "SUMMARY:",
            f"  Total Validations: {self.summary['total_validations']}",
            f"  Passed: {self.summary['passed']}",
            f"  Failed: {self.summary['failed']}",
            f"  Success Rate: {self.summary['success_rate']:.1%}",
            f"  Overall Status: {self.summary['overall_status']}",
            "",
            "DETAILED RESULTS:",
        ]

        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            lines.append(f"  {status}: {result.validation_type}")

            if result.errors:
                for error in result.errors:
                    lines.append(f"    ERROR: {error}")

            if result.warnings:
                for warning in result.warnings:
                    lines.append(f"    WARNING: {warning}")

            if result.metrics:
                lines.append("    METRICS:"                for key, value in result.metrics.items():
                    lines.append(f"      {key}: {value}")

            lines.append("")

        return "\n".join(lines)

    def save_report(self, output_path: Path) -> None:
        """Save validation report to file."""
        report_content = self.generate_report()
        output_path.write_text(report_content)

        # Also save JSON version for programmatic access
        json_data = {
            'target': self.target,
            'scope': self.scope,
            'timestamp': self.timestamp.isoformat(),
            'summary': self.summary,
            'results': [result.to_dict() for result in self.results]
        }

        json_path = output_path.with_suffix('.json')
        json_path.write_text(json.dumps(json_data, indent=2, default=str))
```

## Key Requirements

- [ ] Use infrastructure validation modules for all checks
- [ ] Validate appropriate quality standards (90% project, 60% infrastructure coverage)
- [ ] Perform comprehensive input, process, and output validation
- [ ] Generate detailed validation reports with metrics
- [ ] Check cross-references and integration points
- [ ] Validate documentation completeness and accuracy
- [ ] Ensure manuscript structure and content compliance
- [ ] Verify code quality and standards compliance

## Standards Compliance Checklist

### Quality Standards ([`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md))
- [ ] Coverage requirements met (90% project, 60% infrastructure)
- [ ] No mocks policy maintained
- [ ] Real data validation throughout

### Validation Standards ([`../../projects/project/docs/validation_guide.md`](../../projects/project/docs/validation_guide.md))
- [ ] Input validation patterns implemented
- [ ] Process validation procedures followed
- [ ] Output quality assessment completed
- [ ] Comprehensive reporting generated

### Code Quality Standards ([`../../.cursorrules/code_style.md`](../../.cursorrules/code_style.md))
- [ ] Type hints validated
- [ ] Error handling verified
- [ ] Documentation standards checked
- [ ] Code formatting confirmed

## Example Usage

**Input:**
```
VALIDATION TARGET: project
TARGET SCOPE: projects/project
QUALITY LEVEL: comprehensive
```

**Expected Output:**
- Complete validation report with pass/fail status for all components
- Coverage analysis (90%+ for project code)
- Code quality assessment (linting, type checking, formatting)
- Documentation validation (completeness, cross-references, examples)
- Manuscript validation (structure, references, PDF compilation)
- Integration testing results
- Detailed metrics and recommendations for improvements

## Related Documentation

- [`../../projects/project/docs/validation_guide.md`](../../projects/project/docs/validation_guide.md) - Complete validation procedures
- [`../../infrastructure/validation/`](../../infrastructure/validation/) - Validation implementation modules
- [`../../.cursorrules/testing_standards.md`](../../.cursorrules/testing_standards.md) - Testing and quality standards
```

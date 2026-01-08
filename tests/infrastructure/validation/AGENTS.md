# Validation Infrastructure Tests

## Overview

The `tests/infrastructure/validation/` directory contains tests for the validation infrastructure. These tests validate the quality assurance systems that ensure research outputs meet academic and technical standards, including PDF validation, markdown validation, integrity checking, and content quality assessment.

## Directory Structure

```
tests/infrastructure/validation/
├── AGENTS.md                           # This technical documentation
├── __init__.py                        # Test package initialization
├── conftest.py                        # Test configuration and fixtures
├── test_cli.py                        # CLI interface tests
├── test_config.py                     # Configuration tests
├── test_doc_completeness.py           # Document completeness tests
├── test_doc_scanner.py                # Document scanning tests
├── test_figure_validator.py           # Figure validation tests
├── test_integrity.py                  # File integrity tests
├── test_markdown_validator.py         # Markdown validation tests
├── test_package_validator.py          # Package validation tests
├── test_pdf_validator.py              # PDF validation tests
├── test_validation_cli.py             # Validation CLI tests
└── test_validation_integration.py     # Integration tests
```

## Test Categories

### PDF Validation Tests

**PDF Validator Tests (`test_pdf_validator.py`)**
- PDF file parsing and text extraction validation
- Cross-reference resolution testing
- Citation completeness checking
- Mathematical notation rendering verification
- Document structure integrity assessment

**Key Test Scenarios:**
```python
def test_pdf_validation_complete():
    """Test PDF validation."""
    # Create test PDF with various elements
    pdf_path = create_test_pdf_with_elements(
        text_content="Sample research content",
        citations=["[1]", "[2]", "[3]"],
        references=["??", "fig:figure1"],  # Unresolved reference
        equations=["$E = mc^2$", "$$\\sum_{i=1}^n x_i$$"]
    )

    validator = PDFValidator()
    result = validator.validate_pdf(pdf_path)

    # Check validation results
    assert result['valid'] is False  # Should fail due to unresolved reference
    assert 'unresolved_references' in result['issues']
    assert len(result['issues']['unresolved_references']) > 0
    assert 'citations_found' in result
    assert result['citations_found'] == 3

def test_pdf_text_extraction():
    """Test PDF text extraction accuracy."""
    # Create PDF with known text content
    original_text = """
    This is a test document for PDF validation.
    It contains multiple paragraphs and various text elements.
    The quick brown fox jumps over the lazy dog.
    """

    pdf_path = create_pdf_from_text(original_text)

    # Extract text
    extracted_text = extract_text_from_pdf(pdf_path)

    # Validate extraction accuracy
    similarity = calculate_text_similarity(original_text, extracted_text)
    assert similarity > 0.9, f"Text extraction accuracy too low: {similarity}"

    # Check essential content preservation
    assert "test document" in extracted_text.lower()
    assert "quick brown fox" in extracted_text.lower()
```

### Markdown Validation Tests

**Markdown Validator Tests (`test_markdown_validator.py`)**
- Markdown syntax validation
- Cross-reference integrity checking
- Image reference resolution
- Link validity verification
- Document structure assessment

**Test Implementation:**
```python
def test_markdown_validation_comprehensive():
    """Test markdown validation."""
    markdown_content = """
# Research Paper Title

## Abstract

This paper presents novel findings in machine learning.
See Figure 1 for methodology overview.

## Introduction

Machine learning has revolutionized data analysis [1].
The proposed method achieves state-of-the-art performance.

## Methodology

![Methodology Overview](figures/method.png){#fig:method}

The experimental setup is shown in Figure 1.

## References

[1]: Smith et al. (2023). Deep Learning Advances.
"""

    validator = MarkdownValidator()
    result = validator.validate_markdown_content(markdown_content, base_path=Path("."))

    # Check validation results
    assert result['valid'] is False  # Missing figure file
    assert 'missing_images' in result['issues']
    assert 'figures/method.png' in result['issues']['missing_images']

    # Check successful validations
    assert result['cross_references_valid'] is True
    assert result['citations_valid'] is True
    assert 'headings_found' in result
    assert result['headings_found'] >= 4

def test_markdown_cross_references():
    """Test markdown cross-reference validation."""
    content_with_refs = """
# Main Document

See Section 2 for details.
Also check out Figure 3 and Table 1.

## Section 2: Details {#sec:details}

This section provides detailed information.

## Results

![Result Visualization](result.png){#fig:result3}

| Method | Accuracy |
|--------|----------|
| Ours | 95.2% |

Table: Performance comparison {#tbl:comparison}
"""

    validator = MarkdownValidator()
    result = validator.validate_cross_references(content_with_refs)

    # Validate reference resolution
    assert result['resolved_references'] == 3  # sec:details, fig:result3, tbl:comparison
    assert result['unresolved_references'] == 1  # fig:result3 != fig:result3 reference
    assert result['reference_consistency'] is True
```

### Integrity Validation Tests

**Integrity Tests (`test_integrity.py`)**
- File integrity verification
- Hash-based content validation
- Cross-reference consistency checking
- Academic standards compliance

**Test Coverage:**
```python
def test_file_integrity_validation():
    """Test file integrity validation."""
    # Create test files with known content
    test_files = create_test_file_set()

    # Modify one file to change integrity
    corrupt_file(test_files['manuscript.md'])

    # Validate integrity
    integrity_result = validate_file_integrity(test_files)

    assert integrity_result['overall_valid'] is False
    assert 'modified_files' in integrity_result
    assert 'manuscript.md' in integrity_result['modified_files']

    # Check hash verification
    assert 'file_hashes' in integrity_result
    assert len(integrity_result['file_hashes']) == len(test_files)

def test_cross_reference_integrity():
    """Test cross-reference integrity across documents."""
    document_set = {
        'main.md': """
# Main Document

See Appendix A for details.
Also refer to Figure 1 in chapter 2.
""",
        'appendix.md': """
# Appendix A {#appendix-a}

This is the appendix content.

![Appendix Figure](appendix_fig.png){#fig:appendix1}
""",
        'chapter2.md': """
# Chapter 2

![Chapter Figure](chapter_fig.png){#fig:chapter1}
"""
    }

    integrity_checker = IntegrityValidator()
    result = integrity_checker.validate_cross_document_references(document_set)

    # Validate cross-document references
    assert result['unresolved_external_refs'] == 1  # Figure 1 reference not found in chapter 2
    assert result['resolved_external_refs'] == 1    # Appendix A reference resolved
    assert result['internal_refs_valid'] is True
```

### Document Scanning Tests

**Document Scanner Tests (`test_doc_scanner.py`)**
- Document structure analysis
- Content completeness checking
- Academic formatting validation
- Research document standards compliance

**Test Scenarios:**
```python
def test_document_structure_scanning():
    """Test document structure scanning."""
    research_paper = """
# Novel Machine Learning Algorithm

## Abstract

This paper introduces a novel algorithm...

## Introduction

Machine learning has advanced significantly...

## Related Work

Previous research includes...

## Methodology

We propose the following approach...

## Experiments

We evaluate on standard datasets...

## Results

Our method achieves 95.2% accuracy...

## Conclusion

We presented a novel algorithm...

## References

[1] Smith et al. Deep Learning, 2023.
"""

    scanner = DocumentScanner()
    structure = scanner.scan_document_structure(research_paper)

    # Validate academic structure
    required_sections = ['abstract', 'introduction', 'methodology', 'experiments', 'results', 'conclusion']
    for section in required_sections:
        assert section in structure['sections'], f"Missing required section: {section}"

    assert structure['citation_count'] == 1
    assert structure['word_count'] > 200
    assert structure['academic_structure_score'] > 0.8
```

### Figure Validation Tests

**Figure Validator Tests (`test_figure_validator.py`)**
- Figure file existence verification
- Image format validation
- Figure reference consistency checking
- Caption and label validation

**Test Implementation:**
```python
def test_figure_validation_comprehensive():
    """Test figure validation."""
    # Create test document with figure references
    document = """
# Research Paper

## Results

The results are shown in Figure 1.

![Result Plot](results/plot.png){#fig:results width=80%}

Additional analysis in Figure 2.

![Analysis Plot](analysis.png){#fig:analysis}
"""

    # Create some figure files, missing others
    figure_dir = Path("figures")
    figure_dir.mkdir(exist_ok=True)
    (figure_dir / "plot.png").write_bytes(create_test_png())

    validator = FigureValidator()
    result = validator.validate_figures(document, base_path=Path("."))

    # Check validation results
    assert result['total_figures'] == 2
    assert result['existing_figures'] == 1  # Only plot.png exists
    assert result['missing_figures'] == 1   # analysis.png missing
    assert 'results/plot.png' in result['found_figures']
    assert 'analysis.png' in result['missing_figures']
```

## Test Design Principles

### Quality Assurance Focus

**Validation Testing:**
- Tests validate the validators themselves
- Real document parsing and analysis
- File system operations with actual files
- Cross-reference resolution with complex documents
- Academic standards compliance checking

**Integration Testing Approach:**
```python
def test_validation_pipeline_integration():
    """Test validation pipeline integration."""

    # Create test manuscript
    manuscript_files = create_complete_manuscript_set()

    # Run full validation pipeline
    validation_results = run_complete_validation(manuscript_files)

    # Validate pipeline results
    assert 'pdf_validation' in validation_results
    assert 'markdown_validation' in validation_results
    assert 'integrity_check' in validation_results

    # Check cross-validation consistency
    pdf_refs = validation_results['pdf_validation']['references']
    md_refs = validation_results['markdown_validation']['references']

    # References should be consistent between formats
    assert set(pdf_refs.keys()).issubset(set(md_refs.keys()))

    # Overall validation status
    assert validation_results['overall_valid'] is False  # Expected due to test setup
    assert len(validation_results['blocking_issues']) > 0
```

### Test Organization

**Validation-Specific Test Structure:**
- Format-specific validation test suites
- Integration tests combining multiple validators
- Academic document standards test collections
- Error condition and edge case test categories

**Test Data Management:**
```python
@pytest.fixture
def comprehensive_test_manuscript():
    """Create test manuscript with various elements."""
    return {
        'markdown': create_markdown_with_all_elements(),
        'pdf': create_pdf_from_markdown(markdown_content),
        'figures': create_test_figure_set(),
        'bibliography': create_test_bibliography(),
        'expected_issues': {
            'unresolved_refs': ['fig:missing'],
            'missing_files': ['missing_figure.png'],
            'formatting_issues': ['inconsistent_citation_style']
        }
    }

@pytest.fixture
def academic_document_standards():
    """Provide academic document standards for testing."""
    return {
        'required_sections': [
            'abstract', 'introduction', 'methodology',
            'experiments', 'results', 'conclusion', 'references'
        ],
        'citation_formats': ['[1]', '(Smith et al., 2023)', '@smith2023'],
        'figure_formats': ['.png', '.jpg', '.svg', '.pdf'],
        'minimum_word_counts': {
            'abstract': 150,
            'introduction': 500,
            'methodology': 800,
            'conclusion': 300
        }
    }
```

## Test Infrastructure

### Validation Fixtures

**Document Creation Fixtures:**
```python
@pytest.fixture
def valid_markdown_document():
    """Create valid markdown document for testing."""
    return """
# Research Paper Title

## Abstract

This paper presents important findings in the field of research.

## Introduction

Research has advanced significantly in recent years.

## Methodology

We employed a rigorous methodology for our research.

## Results

Our results show significant improvements over previous work.

## Conclusion

We conclude that our approach is effective.

## References

[1] Author et al. (2023). Previous work.
"""

@pytest.fixture
def document_with_validation_issues():
    """Create document with known validation issues."""
    return """
# Incomplete Research Paper

## Abstract

This abstract is too short.

## Introduction

Missing methodology section entirely.

## Results

![Missing Figure](nonexistent.png){#fig:missing}

See also Figure 2 which doesn't exist.

## References

[1] Incomplete citation.
[2] Another incomplete citation.
"""
```

### Validation Helpers

**Result Comparison Utilities:**
```python
def compare_validation_results(actual, expected):
    """Compare validation results with expected outcomes."""

    # Check overall validity
    assert actual['valid'] == expected['valid'], f"Validity mismatch: {actual['valid']} != {expected['valid']}"

    # Check issue categories
    for issue_type, expected_issues in expected.get('issues', {}).items():
        assert issue_type in actual.get('issues', {}), f"Missing issue type: {issue_type}"

        actual_issues = actual['issues'][issue_type]
        assert len(actual_issues) == len(expected_issues), f"Issue count mismatch for {issue_type}"

        # Check specific issues
        for expected_issue in expected_issues:
            assert expected_issue in actual_issues, f"Missing specific issue: {expected_issue}"

def validate_academic_standards(document, standards):
    """Validate document against academic standards."""

    # Check required sections
    for section in standards['required_sections']:
        assert section in document.lower(), f"Missing required section: {section}"

    # Check word counts
    word_counts = analyze_section_word_counts(document)
    for section, min_words in standards['minimum_word_counts'].items():
        assert word_counts.get(section, 0) >= min_words, f"Section {section} too short: {word_counts.get(section, 0)} words"

    # Check citation formats
    citations = extract_citations(document)
    valid_formats = 0
    for citation in citations:
        if any(fmt in citation for fmt in standards['citation_formats']):
            valid_formats += 1

    assert valid_formats / len(citations) > 0.8, f"Too many invalid citations: {valid_formats}/{len(citations)}"
```

### Output Validator Test Patterns

**Output Validation Tests (`test_output_validator.py`)**
- Copied outputs validation with correct PDF locations
- Output structure validation with proper directory hierarchies
- File readability and permission testing
- Directory completeness assessment

**PDF Location Requirements:**
- PDFs must be located in `output_dir/pdf/project_combined.pdf` (or `{project_name}_combined.pdf`)
- Tests create realistic output directory structures
- Validation functions expect PDFs in `pdf/` subdirectory, not root level

**Test Structure Patterns:**
```python
def test_validate_complete_structure(output_directory_structure):
    """Test validation with output structure."""
    output_dir = output_directory_structure

    # Create PDF in pdf/ directory (where it's actually expected)
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir(exist_ok=True)  # Already exists from fixture
    (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 1000)

    # Create subdirectories with files (skip pdf/ since already handled)
    for subdir in ["web", "slides", "figures", "data", "reports", "simulations"]:
        subdir_path = output_dir / subdir
        (subdir_path / f"{subdir}_file.txt").write_text("content")

    result = validate_copied_outputs(output_dir)
    assert result is True

def test_validate_small_pdf(tmp_path):
    """Test validation with suspiciously small PDF."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pdf_dir = output_dir / "pdf"
    pdf_dir.mkdir()

    # Create very small PDF (< 100KB) in pdf/ directory
    (pdf_dir / "project_combined.pdf").write_bytes(b"PDF" * 100)

    result = validate_output_structure(output_dir)
    # Small PDF is still valid but flagged as suspicious
    assert result["valid"] is True
    assert any("unusually small" in s for s in result["suspicious_sizes"])
```

**Common Test Fixtures:**
```python
@pytest.fixture
def output_directory_structure(tmp_path):
    """Create standard output directory structure."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create all expected subdirectories
    subdirs = ["pdf", "web", "slides", "figures", "data", "reports", "simulations", "llm", "logs"]
    for subdir in subdirs:
        (output_dir / subdir).mkdir()

    return output_dir

@pytest.fixture
def output_with_pdf(output_directory_structure, pdf_file_fixture):
    """Create output directory with PDF in correct location."""
    output_dir = output_directory_structure

    # Copy PDF to correct location
    pdf_dest = output_dir / "pdf" / "project_combined.pdf"
    pdf_dest.write_bytes(pdf_file_fixture.read_bytes())

    return output_dir
```

## Running Tests

### Test Execution

```bash
# Run all validation tests
pytest tests/infrastructure/validation/

# Run specific validation type tests
pytest tests/infrastructure/validation/test_pdf_validator.py

# Run integration tests
pytest tests/infrastructure/validation/test_validation_integration.py

# Run with detailed output
pytest tests/infrastructure/validation/ -v
```

### Conditional Test Execution

**Format-Specific Testing:**
```bash
# PDF validation tests only
pytest tests/infrastructure/validation/ -k "pdf"

# Markdown validation tests only
pytest tests/infrastructure/validation/ -k "markdown"

# Integrity tests only
pytest tests/infrastructure/validation/ -k "integrity"
```

## Test Coverage and Quality

### Coverage Goals

**Validation Module Coverage:**
- PDF validation: 95%+ coverage
- Markdown validation: 95%+ coverage
- Integrity checking: 90%+ coverage
- Document scanning: 85%+ coverage
- CLI interface: 90%+ coverage

### Quality Metrics

**Validation Accuracy:**
- Tests validate actual validation logic correctness
- False positive/negative rates within acceptable limits
- Academic standards compliance properly assessed
- Error messages provide actionable diagnostic information

## Common Test Issues

### Document Creation Problems

**PDF Generation Issues:**
```python
def debug_pdf_creation():
    """Debug PDF creation issues in tests."""

    # Test basic LaTeX compilation
    test_latex = create_minimal_latex()
    pdf_path = compile_latex_to_pdf(test_latex)

    if not pdf_path.exists():
        # Check LaTeX installation
        check_latex_installation()

        # Test compilation manually
        result = subprocess.run(['xelatex', '--interaction=nonstopmode', test_latex])
        print(f"LaTeX exit code: {result.returncode}")

        if result.returncode != 0:
            # Check for specific LaTeX errors
            analyze_latex_errors(test_latex)

    return pdf_path.exists()
```

**Markdown Parsing Issues:**
```python
def debug_markdown_parsing():
    """Debug markdown parsing issues."""

    test_markdown = create_test_markdown()

    # Test basic parsing
    try:
        ast = parse_markdown_to_ast(test_markdown)
        print("Basic parsing: SUCCESS")
    except Exception as e:
        print(f"Basic parsing failed: {e}")
        return False

    # Test specific elements
    elements_to_test = ['headings', 'references', 'citations', 'images']
    for element_type in elements_to_test:
        try:
            elements = extract_elements(test_markdown, element_type)
            print(f"{element_type} extraction: SUCCESS ({len(elements)} found)")
        except Exception as e:
            print(f"{element_type} extraction: FAILED ({e})")

    return True
```

### File System Dependencies

**Path Resolution Issues:**
```python
def debug_path_resolution():
    """Debug file path resolution issues."""

    # Test basic path operations
    base_path = Path(".")
    test_file = base_path / "test.txt"

    # Create test file
    test_file.write_text("test content")
    assert test_file.exists()

    # Test relative path resolution
    relative_paths = ["./test.txt", "test.txt", "../current/test.txt"]
    for rel_path in relative_paths:
        try:
            resolved = (base_path / rel_path).resolve()
            print(f"Resolved {rel_path}: {resolved} (exists: {resolved.exists()})")
        except Exception as e:
            print(f"Failed to resolve {rel_path}: {e}")

    # Clean up
    test_file.unlink()
```

## Integration Testing

### Validation Pipeline

**End-to-End Validation Testing:**
```python
def test_complete_validation_pipeline():
    """Test validation pipeline from document to final assessment."""

    # Create test case
    test_case = create_validation_test_case()

    # Run individual validations
    pdf_result = validate_pdf(test_case['pdf_path'])
    markdown_result = validate_markdown(test_case['markdown_path'])
    integrity_result = check_integrity(test_case['files'])

    # Combine results
    combined_result = combine_validation_results([
        pdf_result,
        markdown_result,
        integrity_result
    ])

    # Validate combined assessment
    assert 'overall_score' in combined_result
    assert 'critical_issues' in combined_result
    assert 'recommendations' in combined_result

    # Check consistency across validators
    check_validation_consistency(pdf_result, markdown_result)

    # Verify final recommendation
    if combined_result['overall_score'] < 0.7:
        assert len(combined_result['recommendations']) > 0
        assert 'critical' in combined_result['recommendations'][0].lower()
```

## Future Test Enhancements

### Advanced Validation Testing

**Planned Improvements:**
- **Visual PDF Comparison**: Automated visual regression testing
- **Academic Standards Validation**: Peer review criteria automated checking
- **Multi-Format Consistency**: Validation consistency across output formats
- **Performance Validation**: Validation speed and resource usage testing

**Integration Enhancements:**
- **CI/CD Validation**: Automated validation in deployment pipelines
- **Progressive Validation**: Incremental validation during document creation
- **Collaborative Validation**: Multi-author validation workflow testing

## Troubleshooting

### Test Debugging

**Validation Logic Debugging:**
```bash
# Debug validation logic step by step
def debug_validation_logic():
    """Debug validation logic systematically."""

    # Test with simple inputs first
    simple_doc = create_simple_test_document()
    simple_result = validate_document(simple_doc)
    print(f"Simple document: {'PASS' if simple_result['valid'] else 'FAIL'}")

    # Gradually add complexity
    complexity_levels = ['basic', 'intermediate', 'complex', 'edge_case']
    for level in complexity_levels:
        test_doc = create_complexity_level_document(level)
        result = validate_document(test_doc)

        print(f"{level.capitalize()} document: {'PASS' if result['valid'] else 'FAIL'}")

        if not result['valid']:
            print(f"  Issues: {result.get('issues', [])}")
            break

    return True
```

**Cross-Validator Consistency:**
```bash
# Check consistency between validators
def validate_cross_validator_consistency():
    """Ensure validators give consistent results for same content."""

    # Create document that should validate the same way
    test_content = create_consistent_test_content()

    # Validate with different methods
    markdown_result = validate_markdown_content(test_content)
    pdf_result = validate_pdf_content(convert_to_pdf(test_content))

    # Check consistency
    consistency_issues = []

    if markdown_result['valid'] != pdf_result['equivalent_valid']:
        consistency_issues.append("Validity inconsistency between formats")

    if abs(markdown_result.get('quality_score', 0) - pdf_result.get('quality_score', 0)) > 0.2:
        consistency_issues.append("Quality score inconsistency")

    if consistency_issues:
        print("Consistency issues found:")
        for issue in consistency_issues:
            print(f"  - {issue}")
        return False

    print("Validators are consistent")
    return True
```

### Environment Validation

**Validation Dependencies Check:**
```bash
# Check validation test dependencies
python3 -c "
# Core dependencies
import sys
print(f'Python: {sys.version}')

deps = ['PyPDF2', 'markdown', 'pathlib']
for dep in deps:
    try:
        __import__(dep)
        print(f'{dep}: ✓')
    except ImportError:
        print(f'{dep}: ✗')

# LaTeX for PDF tests
import shutil
print(f'LaTeX (xelatex): {\"✓\" if shutil.which(\"xelatex\") else \"✗\"}')

# Test file creation
import tempfile
with tempfile.NamedTemporaryFile() as f:
    f.write(b'test')
    print('File system: ✓')
"
```

## See Also

**Related Documentation:**
- [`../../../infrastructure/validation/AGENTS.md`](../../../infrastructure/validation/AGENTS.md) - Validation module details
- [`../AGENTS.md`](../AGENTS.md) - Infrastructure test suite overview
- [`../../../AGENTS.md`](../../../AGENTS.md) - System documentation

**Testing Standards:**
- [`../../../.cursorrules/testing_standards.md`](../../../.cursorrules/testing_standards.md) - Testing standards
- [`../../../docs/development/TESTING_GUIDE.md`](../../../docs/development/TESTING_GUIDE.md) - Testing guide
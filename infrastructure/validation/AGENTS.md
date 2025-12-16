# Validation Module

## Purpose

The Validation module provides comprehensive quality assurance and validation tools for research documents. It ensures PDF rendering integrity, markdown structure validity, and data consistency across the research project.

## Architecture

### Core Components

**pdf_validator.py**
- PDF text extraction and analysis
- Rendering issue detection (unresolved references, warnings, errors)
- Document structure verification
- First-N-words extraction for preview

**markdown_validator.py**
- Markdown file discovery and collection
- Manuscript directory discovery at `project/manuscript/`
- Image reference validation
- Cross-reference verification
- Mathematical equation validation
- Link and URL integrity checking
- Section anchor validation

**integrity.py**
- File integrity verification (SHA-256 hashing)
- Cross-reference validation across documents
- Data consistency checking
- Academic standards compliance
- Build artifact verification
- Completeness validation

## Key Features

### PDF Validation
```python
from infrastructure.validation import validate_pdf_rendering

report = validate_pdf_rendering(Path("output/pdf/manuscript.pdf"))
# Returns: issues, text preview, document structure validation
```

### Markdown Validation
```python
from infrastructure.validation import validate_markdown, find_manuscript_directory

# Find manuscript directory at standard location
manuscript_dir = find_manuscript_directory(Path("."))
# Returns project/manuscript/ directory

problems, exit_code = validate_markdown("manuscript/", ".")
# Validates images, references, equations, links
```

**Manuscript Directory Discovery**: The `find_manuscript_directory()` function locates the manuscript directory at `project/manuscript/`.

### Integrity Verification
```python
from infrastructure.validation import verify_output_integrity

report = verify_output_integrity(Path("output/"))
# Comprehensive file, cross-ref, data, and academic standards checks
```

## Testing

Run validation tests with:
```bash
pytest tests/infrastructure/test_validation/
```

## Configuration

No specific configuration required. All validation operates with sensible defaults.

## Integration

Validation module is used by:
- Build pipeline (4-validate_output.py) for quality gates
- Quality checker for document analysis
- CI/CD systems for automated validation

## Troubleshooting

### PDF Validation Fails

**Issue**: `validate_pdf_rendering()` fails to extract text or analyze PDF.

**Solutions**:
- Verify PDF file exists and is readable
- Check PDF is not password-protected
- Ensure PDF contains extractable text (not just images)
- Review PDF file permissions
- Try with a different PDF to isolate file-specific issues

### Markdown Validation Errors

**Issue**: `validate_markdown()` reports false positives or misses issues.

**Solutions**:
- Verify manuscript directory path is correct
- Check markdown file encoding (UTF-8 required)
- Review image paths are relative to manuscript directory
- Ensure figure files exist before validation
- Check LaTeX syntax in markdown files

### Image References Not Found

**Issue**: Validation reports missing image files.

**Solutions**:
- Verify image paths are relative to manuscript directory
- Check image file extensions match references
- Ensure images are generated before validation
- Review path resolution logic for your directory structure
- Check for case sensitivity issues (Linux vs macOS/Windows)

### Cross-Reference Validation Fails

**Issue**: Cross-references reported as unresolved.

**Solutions**:
- Verify reference labels match exactly (case-sensitive)
- Check that referenced sections/equations/figures exist
- Ensure LaTeX label syntax is correct (`\label{...}`)
- Review reference format (`\ref{...}`, `\eqref{...}`, etc.)
- Check for typos in reference keys

### Integrity Check False Positives

**Issue**: Integrity verification reports issues that don't exist.

**Solutions**:
- Verify file paths are correct
- Check file modification times (may affect hash comparison)
- Review integrity check configuration
- Ensure files are not being modified during check
- Compare integrity reports over time

## Best Practices

### PDF Validation

- **Validate Early**: Check PDFs immediately after generation
- **Check Structure**: Verify document structure before content
- **Review Warnings**: Address warnings before they become errors
- **Track Issues**: Log all validation issues for tracking

### Markdown Validation

- **Validate Before Rendering**: Check markdown before PDF generation
- **Use Strict Mode**: Enable strict mode in CI/CD pipelines
- **Fix References**: Resolve all reference issues before proceeding
- **Validate Images**: Ensure all referenced images exist

### Integrity Verification

- **Run Regularly**: Integrate integrity checks into build pipeline
- **Compare Baselines**: Compare against known-good baselines
- **Track Changes**: Monitor integrity reports for unexpected changes
- **Document Issues**: Document any expected integrity differences

### Cross-Reference Management

- **Use Consistent Labels**: Follow consistent naming conventions
- **Validate References**: Check references before final rendering
- **Document Patterns**: Document reference patterns for team
- **Automate Checks**: Integrate reference validation into workflow

### Error Reporting

- **Provide Context**: Include file paths and line numbers in errors
- **Actionable Messages**: Give specific steps to fix issues
- **Categorize Issues**: Distinguish errors from warnings
- **Track Trends**: Monitor validation results over time

## See Also

- [README.md](README.md) - Quick reference guide
- [`core/`](../core/) - Foundation utilities

